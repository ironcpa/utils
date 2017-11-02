import collections
import os
import sqlite3 as sqlite

Product = collections.namedtuple('Product', ['product_no', 'desc', 'rate', 'disk_name', 'location', 'size', 'cdate'])


class DB:
    def __init__(self):
        self.db_file = os.path.dirname(__file__) + '\\data\\product.db'

    def update_product(self, product):
        p = product

        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "select count(*) from product\n"\
                  "where p_no = ? and disk = ? and location = ? and size = ? and cdate = ?"
            cur.execute(sql, (p.product_no, p.disk_name, p.location, p.size, p.cdate))

            result = cur.fetchone()[0]

            if result > 0:
                sql = "update product\n" \
                      "set desc=?, rate=?\n" \
                      "where p_no = ? and disk = ? and location = ? and size = ? and cdate = ?"
                cur.execute(sql, (p.desc, p.rate, p.product_no, p.disk_name, p.location, p.size, p.cdate))
                c.commit()
            else:
                sql = 'insert into product(p_no, desc, rate, disk, location, size, cdate)\n'\
                      'values(?, ?, ?, ?, ?, ?, ?)'
                cur.execute(sql, (p.product_no, p.desc, p.rate, p.disk_name, p.location, p.size, p.cdate))
                c.commit()

    def to_product(self, db_rows):
        products = []
        for r in db_rows:
            products.append(Product(*r))
        return products

    def search(self, text, is_all_match = False):
        # # test
        # return [Product('aaa-123', 'ddd', 'xxx', 'disk', 'c:/aaa.txt', '10.00', '2017-07-11'),
        #         Product('bbb-456', 'bbb', 'xxx', 'disk', 'c:/aaa.txt', '5.00', '2017-08-01aa)]

        if text == '':
            return self.search_all()

        tokens = text.split()
        if len(tokens) > 0:
            if is_all_match:
                return self.search_all_tokens(tokens)
            else:
                return self.search_any_tokens(tokens)

        # # test multi field search
        # with sqlite.connect(self.db_file) as c:
        #     cur = c.cursor()
        #     sql = "select p_no, desc, rate, disk, location from product\n"\
        #           "where p_no || desc like ?"
        #     cur.execute(sql, ('%' + text + '%',))
        #     result = cur.fetchall()
        #
        #     return self.to_product(result)

    def search_any_tokens(self, tokens):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql, params = self.make_union_sql(['p_no', 'desc', 'rate', 'location', 'disk'], tokens)
            cur.execute(sql, tuple(params))
            result = cur.fetchall()

            return self.to_product(result)

    def search_all_tokens(self, tokens):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql, params = self.make_all_match_sql(['p_no', 'desc', 'rate', 'location', 'disk'], tokens)
            print(sql)
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
                sql += "select p_no, desc, rate, disk, location, size, cdate from product\n" \
                       "where {} like ?\n".format(f)
            for t in tokens:
                params.append('%' + t + '%')
        sql += ' order by p_no'

        return sql, params

    def make_all_match_sql(self, target_fields, tokens):
        sql = "select p_no, desc, rate, disk, location, size, cdate from product\n" \
              "where "
        params = []
        for i, f in enumerate(target_fields):
            where_cond = '(' if i == 0 else ' or ('
            for j, t in enumerate(tokens):
                where_cond += '' if j == 0 else ' and'
                where_cond += ' {} like ?'.format(f)
                params.append('%' + t + '%')
            sql += where_cond + ')\n'
        sql += ' order by p_no'

        return sql, params

    def search_all(self):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "select p_no, desc, rate, disk, location, size, cdate from product limit 100"
            cur.execute(sql)
            result = cur.fetchall()

            return self.to_product(result)

    def better_filename(self, product):
        p = product
        return '{}_{}_{}'.format(p.p_no, p.desc.replace(' ', '_'), p.rate)