import os
import sqlite3 as sqlite

import common_util as cu
from defines import Product


class DB:
    def __init__(self):
        self.db_file = os.path.dirname(__file__) + '\\data\\product_using.db'

    def insert_products(self, products):
        params = [(p.product_no, p.desc, p.rate, p.disk_name, p.location, p.size, p.cdate) for p in products]

        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = 'insert into product(p_no, desc, rate, disk, location, size, cdate)\n' \
                  'values(?, ?, ?, ?, ?, ?, ?)'
            cur.executemany(sql, params)
            c.commit()

    def insert_product_w_fileinfos(self, fileinfos):
        self.insert_products([cu.conv_fileinfo_to_product(fi) for fi in fileinfos])

    def update_product(self, product):
        p = product
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = 'update product\n' \
                  'set p_no = ?, disk = ?, location = ?, size = ?, cdate = ?\n' \
                  'where id = ?'
            rows = cur.execute(sql, (p.product_no, p.disk_name, p.location, p.size, p.cdate, p.id))
            c.commit()

            return rows.rowcount

    def delete_product(self, product):
        p = product
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "delete from product\n" \
                  "where id = ?"
            rows = cur.execute(sql, (p.id,))
            c.commit()

            return rows.rowcount

    def delete_by_disk(self, disk):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "delete from product\n" \
                  "where disk = ?"
            rows = cur.execute(sql, (disk,))
            c.commit()

            return rows.rowcount

    def delete_by_dir(self, dir):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "delete from product\n" \
                  "where location like ?"
            rows = cur.execute(sql, (dir + '%',))
            c.commit()

            return rows.rowcount

    def delete_by_path(self, path):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "delete from product\n" \
                  "where location = ?"
            rows = cur.execute(sql, (path,))
            c.commit()

            return rows.rowcount

    def to_product(self, db_rows):
        products = []
        for r in db_rows:
            products.append(Product(*r))
        return products

    def search(self, text, is_all_match=False):
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
                if not (i == 0 and j == 0):
                    sql += "union\n"
                sql += "select id, p_no, desc, rate, disk, location, size, cdate from product\n" \
                       "where {} like ?\n".format(f)
            for t in tokens:
                params.append('%' + t + '%')
        sql += ' order by p_no'

        return sql, params

    def make_all_match_sql(self, target_fields, tokens):
        sql = "select id, p_no, desc, rate, disk, location, size, cdate from product\n" \
              "where "
        params = []
        for i, f in enumerate(target_fields):
            where_cond = '(' if i == 0 else ' or ('
            for j, t in enumerate(tokens):
                where_cond += '' if j == 0 else ' and'
                # where_cond += ' {} like ?'.format(f)
                where_cond += " {} like ? escape '\\'".format(f)
                params.append('%' + t + '%')
            sql += where_cond + ')\n'
        sql += ' order by p_no'

        return sql, params

    def search_all(self):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "select id, p_no, desc, rate, disk, location, size, cdate\n" \
                  "from product\n" \
                  "where rate = ''\n" \
                  "order by cdate desc\n" \
                  "limit 200"
            cur.execute(sql)
            result = cur.fetchall()

            return self.to_product(result)

    def search_dup_list(self):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "select p.id, p.p_no, p.desc, p.rate, p.disk, p.location, p.size, p.cdate \n" \
                  "from product as p join \n" \
                  "     (select p_no from product group by p_no having count(p_no) > 1) as d \n" \
                  "     on p.p_no = d.p_no \n" \
                  "order by p.p_no"
            cur.execute(sql)
            result = cur.fetchall()

            return self.to_product(result)
