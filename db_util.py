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
            sql = "select count(*) from product where p_no = '{}'".format(product.product_no)
            cur.execute(sql)

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

    def search(self, text):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "select p_no, desc, rate, disk, location from product"
            cur.execute(sql)
            result = cur.fetchall()

            # return result
            products = []
            for r in result:
                products.append(Product(*r))
            return products
