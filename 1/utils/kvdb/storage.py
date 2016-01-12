# coding: utf-8
#
# xiaoyu <xiaokong1937@gmail.com>
#
# 2015/01/21
#
"""
Custom storage for django.

"""
import sys
import StringIO

from django.core.files.base import File
from django.core.files.storage import Storage
from django.contrib.sites.models import Site

from bucket import Bucket


class Error(Exception):
    pass


class Storage(Storage):

    """
    Custom storage for django.

    """

    def __init__(self):
        self.bucket = Bucket()

    def _open(self, name, mode="rb"):
        name = self._normalize_name(name)
        return StorageFile(name, mode, self)

    def _save(self, name, content):
        name = self._normalize_name(name)
        try:
            self.bucket.save(name, content)
        except Error, e:
            raise IOError("Storage Error:{}".format(e))
        return name

    def delete(self, name):
        name = self._normalize_name(name)
        try:
            self.bucket.delete_object(name)
        except Error, e:
            raise IOError('Storage Error: %s' % e.args)

    def exists(self, name):
        name = self._normalize_name(name)
        return self.bucket.exists(name)

    def size(self, name):
        name = self._normalize_name(name)
        try:
            attrs = self.bucket.stat_object(name)
            return attrs['bytes']
        except Error, e:
            raise IOError('Storage Error: %s' % e.args)

    def _open_read(self, name):
        name = self._normalize_name(name)

        class _:

            def __init__(self, chunks):
                self.buf = ''

            def read(self, num_bytes=None):
                if num_bytes is None:
                    num_bytes = sys.maxint
                try:
                    while len(self.buf) < num_bytes:
                        self.buf += chunks.next()
                except StopIteration:
                    pass
                except Error, e:
                    raise IOError('Storage Error: %s' % e.args)
                retval = self.buf[:num_bytes]
                self.buf = self.buf[num_bytes:]
                return retval
        chunks = self.bucket.get_object_contents(name, chunk_size=8192)
        return _(chunks)

    def _normalize_name(self, name):
        return name.lstrip('/').replace("\\", '/')

    def url(self, name):
        current_site = Site.objects.get_current()
        domain = current_site.domain
        return 'http://{}/backends/kvdb/{}'.format(domain, name)


class StorageFile(File):

    def __init__(self, name, mode, storage):
        self.name = name
        self.mode = mode
        self.file = StringIO.StringIO()
        self._storage = storage
        self._is_dirty = False

    @property
    def size(self):
        if hasattr(self, '_size'):
            self._size = self.storage.size(self.name)
        return self._size

    def read(self, num_bytes=None):
        if not hasattr(self, '_obj'):
            self._obj = self._storage._open_read(self.name)
        return self._obj.read(num_bytes)

    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was opened for read-only access.")
        self.file = StringIO(content)
        self._is_dirty = True

    def close(self):
        if self._is_dirty:
            self._storage._save(self.name, self.file.getvalue())
        self.file.close()
