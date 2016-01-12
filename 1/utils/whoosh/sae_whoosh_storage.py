# coding: utf-8
#
# xiaoyu <xiaokong1937@gmail.com>
#
# 2015/02/03
#
"""
FileStorage of SAE for whoosh.

"""
import datetime
import threading

from whoosh.filedb.filestore import Storage as WhooshStorage
from whoosh.filedb.filestore import ReadOnlyError
from whoosh.filedb.structfile import StructFile
from whoosh.compat import BytesIO

from django.core.files.base import File

from utils.kvdb.bucket import Bucket


class SAEFile(File):

    def __init__(self, name, mode, bucket, *args, **kwargs):
        self.name = name
        self.mode = mode
        self.data = BytesIO()
        self.bucket = bucket
        self._is_dirty = False
        self.value = kwargs.get('value', '')

    @classmethod
    def loadfile(cls, name, mode, bucket):
        value = bucket.get_object_contents(name)
        file = cls(name, mode, bucket=bucket, value=value)
        file.data = BytesIO(file.value)
        return file

    def close(self):
        self.value = self.getvalue()
        self.bucket.put_object(self.name, self.value)

    def tell(self):
        return self.data.tell()

    def write(self, data):
        return self.data.write(data)

    def read(self, length):
        return self.data.read(length)

    def seek(self, *args):
        return self.data.seek(*args)

    def readline(self):
        return self.data.readline()

    def getvalue(self):
        return self.data.getvalue()


class SAEFileStorage(WhooshStorage):
    supports_mmap = True

    def __init__(self, path, supports_mmap=True, readonly=False, debug=False):
        self.folder = path
        self.supports_mmap = supports_mmap
        self.readonly = readonly
        self._debug = debug
        self.locks = {}
        self.bucket = Bucket(path)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.folder)

    def create(self):
        return self

    def destory(self):
        self.clean()
        self.bucket.delete()

    def create_file(self, name, excl=False, mode='wb', **kwargs):
        if self.readonly:
            raise ReadOnlyError

        # Of course SAE bucket does not support `exclusive` mode.
        # fileobj = self.bucket.get_object(name)
        fileobj = SAEFile(name, mode, self.bucket)
        f = StructFile(fileobj, name=name, **kwargs)
        return f

    def open_file(self, name, **kwargs):
        fileobj = SAEFile.loadfile(name, mode='rb', bucket=self.bucket)
        f = StructFile(fileobj, name=name, **kwargs)
        return f

    def clean(self, ignore=False):
        if self.readonly:
            raise ReadOnlyError

        files = self.list()
        for fname in files:
            self.bucket.delete_object(fname)

    def list(self):
        return self.bucket.list()

    def file_exists(self, name):
        return self.bucket.exists(name)

    def file_modified(self, name):
        last_modified = self.bucket.stat_object(name)['last_modified']
        mtime = datetime.datetime.strptime(last_modified,
                                           '%Y-%m-%dT%H:%M:%S.%f')
        return mtime

    def file_length(self, name):
        try:
            data = self.bucket.stat_object(name)
        except Exception as e:
            print e
            return 0
        else:
            bytes_ = data['bytes']
            return int(bytes_)

    def delete_file(self, name):
        if self.readonly:
            raise ReadOnlyError

        self.bucket.delete_object(name)

    def rename_file(self, oldname, newname, safe=False):
        if self.readonly:
            raise ReadOnlyError

        if self.file_exists(newname):
            if safe:
                raise NameError("File %r exists" % newname)
            else:
                self.delete_file(newname)
        self.bucket.put_object(newname,
                               self.bucket.get_object_contents(oldname))

    def lock(self, name):
        if name not in self.locks:
            self.locks[name] = threading.Lock()
        return self.locks[name]

    def temp_storage(self, name=None):
        name = "whooshtmp"
        tempstore = SAEFileStorage(name)
        return tempstore
