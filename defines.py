import collections
import win32api
import os
import file_util


FileInfo = collections.namedtuple('FileInfo', ['path', 'size', 'cdate'])
Product = collections.namedtuple('Product', ['id', 'product_no', 'desc', 'rate', 'disk_name', 'location', 'size', 'cdate'])


class DBException(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg