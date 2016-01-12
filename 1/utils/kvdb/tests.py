# coding: utf-8
#
# xiaoyu <xiaokong1937@gmail.com>
#
# 2015/02/04
#
"""
Tests.

"""
import unittest
import os
import binascii

import bucket


class BucketTestCase(unittest.TestCase):

    def setUp(self):
        self.bucket = bucket.Bucket('test')
        os.environ['sae.kvdb.file'] = 'kvdb.file'

    def test_save(self):
        filelike = open('jieba.cache', 'rb').read()
        self.bucket.save('new_jieba.cache', filelike)
        contents = self.bucket.get_object_contents('new_jieba.cache')
        self.assertEqual(binascii.crc32(filelike) & 0xffffffff,
                         binascii.crc32(contents) & 0xffffffff)
        self.bucket.delete_object('new_jieba.cache')

    def test_delete_object(self):
        filelike = open('jieba.cache', 'rb').read()
        self.bucket.save('new_jieba.cache', filelike)
        self.bucket.delete_object('new_jieba.cache')
        resp = self.bucket.stat_object('new_jieba.cache')
        self.assertEqual(resp, None)

    def test_list(self):
        self.bucket.delete_object('new_jieba.cache')
        for i in range(200):
            self.bucket.save('_{}'.format(i), str(i))
        ls = self.bucket.list()
        self.assertEqual(len(ls), 200)

    def test_delete(self):
        for i in range(200):
            self.bucket.save('x_{}'.format(i), 'x_{}'.format(i))
        self.bucket.delete()
        self.assertEqual(self.bucket.stat_object('x_42'), None)


if __name__ == "__main__":
    unittest.main()
