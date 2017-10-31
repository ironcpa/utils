import collections
import os
import sqlite3 as sqlite

Product = collections.namedtuple('Product', ['product_no', 'desc', 'rate', 'disk_name', 'location'])


class DB:
    def __init__(self):
        self.db_file = os.path.dirname(__file__) + '\\data\\product.db'

    def update_product(self, product):
        print('db_file', self.db_file)
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "select count(*) from product\n"\
                  "where p_no = ?"
            cur.execute(sql, (product.product_no,))

            result = cur.fetchone()[0]
            print('fetch', result)

            if result > 0:
                sql = "update product\n" \
                      "set desc=?, rate=?, disk=?, location=?\n" \
                      "where p_no = ?"
                print(sql)
                cur.execute(sql, (product.desc, product.rate, product.disk_name, product.location, product.product_no))
                c.commit()
            else:
                sql = 'insert into product(p_no, desc, rate, disk, location)\n'\
                      'values(?, ?, ?, ?, ?)'
                print(product)
                cur.execute(sql, (product.product_no, product.desc, product.rate, product.disk_name, product.location))
                c.commit()

    def to_product(self, db_rows):
        products = []
        for r in db_rows:
            products.append(Product(*r))
        return products

    def search(self, text):
        # # test
        # return [Product('aaa-123', 'ddd', 'xxx', 'disk', 'c:/aaa.txt'),
        #         Product('bbb-456', 'bbb', 'xxx', 'disk', 'c:/aaa.txt')]

        if text == '':
            return self.search_all()

        tokens = text.split()
        if len(tokens) > 0:
            return self.search_tokens(tokens)

        # # test multi field search
        # with sqlite.connect(self.db_file) as c:
        #     cur = c.cursor()
        #     sql = "select p_no, desc, rate, disk, location from product\n"\
        #           "where p_no || desc like ?"
        #     cur.execute(sql, ('%' + text + '%',))
        #     result = cur.fetchall()
        #
        #     return self.to_product(result)

    def search_tokens(self, tokens):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql, params = self.make_union_sql(['p_no', 'desc', 'location'], tokens)
            cur.execute(sql, tuple(params))
            result = cur.fetchall()

            return self.to_product(result)

    def make_union_sql(self, target_fields, tokens):
        sql = ''
        params = []
        for i, f in enumerate(target_fields):
            for j, t in enumerate(tokens):
                if not(i == 0 and j == 0):
                    sql += "union\n"
                sql += "select p_no, desc, rate, disk, location from product\n" \
                       "where {} like ?\n".format(f)
            for t in tokens:
                params.append('%' + t + '%')

        return sql, params

    def search_all(self):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "select p_no, desc, rate, disk, location from product limit 100"
            cur.execute(sql)
            result = cur.fetchall()

            return self.to_product(result)
