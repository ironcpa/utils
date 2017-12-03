import collections
import win32api
import os
import file_util


FileInfo = collections.namedtuple('FileInfo', ['path', 'size', 'cdate'])
Product = collections.namedtuple('Product', ['id', 'product_no', 'desc', 'rate', 'disk_name', 'location', 'size', 'cdate'])


class ColumnDef:
    def __init__(self, cols, title_def_map):
        self.cols = cols
        self.column_def = {k: v for v, k in enumerate(cols)}
        self.header_titles = list(self.column_def.keys())
        for k in title_def_map.keys():
            self.header_titles[self.column_def[k]] = title_def_map[k]

    def size(self):
        return len(self.cols)

    def __getitem__(self, key):
        return self.column_def[key]


class DBException(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg