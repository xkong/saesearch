# coding: utf-8
#
# xiaoyu <xiaokong1937>
#
# 2015/02/04
#
"""
KVDB as file storage.

"""
import binascii
import time
import base64
import StringIO

import sae.kvdb

MAX_VALUE_LENGTH = 1048576  # 4 MB
MAX_KEY_LENGTH = 168
VALUE_OFFSET = 1024
DELIMITER = '_blacksheepwall_'


class KVDBError(StandardError):

    def __init__(self, error_code, error):
        self.error_code = error_code
        self.error = error
        super(KVDBError, self).__init__(error)

    def __str__(self):
        return "{0} : {1}".format(self.error_code, self.error)


class Bucket(object):

    """
    Save file to kvdb use filename as filekey.

    """

    def __init__(self, path=''):
        self.kv = sae.kvdb.KVClient()
        self.path = path
        # Default kvdb's key prefix is `_storage`
        self._prefix = '_{}'.format(self.path or 'storage')

    def _get_file_length(self, content):
        """
        Helper function to get the length of file object.
        """
        # StringIO object that has a `len` attribute.
        if hasattr(content, 'len'):
            return content.len

        # str object that has a `__len__` attribute.
        if hasattr(content, '__len__'):
            return len(content)

        # content object.
        if hasattr(content, 'seek') and hasattr(content, 'tell'):
            content.seek(0, 2)
            total_length = content.tell()
            # Move file point to the start.
            content.seek(0)
            return total_length

    def _block_generator(self, content):
        """
        Helper function to yield file block data.
        """
        while True:
            data = content.read(MAX_VALUE_LENGTH)
            if not data:
                break
            yield data

    def _get_mimetype(self, name, content):
        """
        Get mimetype of a filelike object.
        """
        return "todo"

    def _encode(self, filekey):
        """
        Encode a normal filekey(or filename) to a kvdb key.
        """
        return '{}_{}'.format(self._prefix,
                              base64.urlsafe_b64encode(filekey))

    def put_object(self, name, content, *args, **kwargs):
        """
        Save a filelike object to kvdb.
        """
        return self.save(name, content, *args, **kwargs)

    def save(self, name, content, update=True, *args, **kwargs):
        """
        Save a filelike object to kvdb.

        Split a filelike object into pieces with 4MB one piece and save the

        pieces and crc32 of them to kvdb. Finally, save the keys of the pieces

        and file infomation to kvdb with encoded filename as key.

        """
        name = self._encode(name)
        if len(name) > MAX_KEY_LENGTH:
            raise KVDBError(901, "filekey too large")
        if self.exists(name) and not update:
            raise KVDBError(902, 'file exists but not update')
        if hasattr(content, 'read'):
            content = content.read()
        crc32 = binascii.crc32(content) & 0xffffffff
        blocks = []
        content = StringIO.StringIO(content)
        for index, block in enumerate(self._block_generator(content)):
            filekey = '{}{}{}'.format(name, DELIMITER, index)
            block_info = {
                'contents': block,
                'crc32': binascii.crc32(block) & 0xffffffff
            }
            self.kv.set(filekey, block_info)
            blocks.append(filekey)

        file_info = {
            'crc32': crc32,
            'bytes': self._get_file_length(content),
            'last_modified': time.strftime('%Y-%m-%dT%H:%M:%S.0000',
                                           time.gmtime()),
            'timestamp': time.time(),
            'mime_type': self._get_mimetype(name, content),
            'blocks': ','.join(key for key in blocks),
        }
        self.kv.set(name, file_info)

    def get_object_contents(self, name, chunk_size=8192):
        """
        Get object contents.
        """
        if not self.exists(name):
            return ''
        name = self._encode(name)
        file_info = self.kv.get(name)
        data = ''
        for block_filekey in file_info['blocks'].split(','):
            block_info = self.kv.get(block_filekey)
            contents = block_info['contents']
            data += contents
        return data

    def exists(self, name):
        name = self._encode(name)
        return (self.kv.get(name) is not None)

    def stat_object(self, name):
        """
        Get status of an object.

        Returns:
        file_info = {
            'crc32': crc32,
            'bytes': self._get_file_length(content),
            'last_modified': time.strftime('%Y-%m-%dT%H:%M:%S.0000',
                                           time.gmtime()),
            'time_stamp': time.time(),
            'mime_type': self._get_mimetype(name, content),
            'blocks': ','.join(key for key in blocks),
        }
        """
        name = self._encode(name)
        return self.kv.get(name)

    def delete_object(self, name):
        """
        Delete an object.

        All blocks of the object and file_info will be removed.

        """
        name = self._encode(name)
        self.keys = []
        self._getkeys_by_prefix(name)
        keys = self.keys[:]
        self.keys = []
        for key in keys:
            self.kv.delete(key)

    def delete(self, marker=None):
        """
        Delete the whole bucket.
        """
        self.keys = []
        self._getkeys_by_prefix(self._prefix)
        keys = self.keys[:]
        self.keys = []
        for key in keys:
            self.kv.delete(key)

    def list(self):
        """
        List current bucket, return all files of it.

        Note: this method will return all the `true` filenames of files but

        not the encoded keys of kvdb.
        """
        self.files = []
        self._list()
        ret = self.files[:]
        self.files = []
        return ret

    def _list(self, marker=None):
        """
        List current bucket, return all files of it.

        Note: this method will return all the `true` filenames of files but

        not the encoded keys of kvdb.
        """
        keys = self.kv.getkeys_by_prefix(self._prefix, marker=marker)
        keys = list(keys)
        if len(keys) == 0:
            return
        else:
            for key in keys:
                if DELIMITER not in key:
                    real_filekey = key.replace('{}_'.format(self._prefix), '')
                    real_filekey = base64.urlsafe_b64decode(real_filekey)
                    self.files.append(real_filekey)
            self._list(marker=keys[-1])

    def _getkeys_by_prefix(self, prefix, marker=None):
        """
        Get all the keys by prefix.

        """
        keys = self.kv.getkeys_by_prefix(prefix, marker=marker)
        keys = list(keys)
        if len(keys) == 0:
            return
        else:
            self.keys.extend(keys)
            self._getkeys_by_prefix(prefix, marker=keys[-1])
