import os
import sqlite3 as sqlite
import time

import common_util as cu
from defines import Product, DBException


class DB:
    def __init__(self):
        self.db_file = os.path.dirname(__file__) + '\\data\\product_using.db'
        self.create_tables()

    def create_tables(self):
        sql_create_product_table = """CREATE TABLE
                                        IF NOT EXISTS product(
                                        id integer primary key autoincrement,
                                        p_no text not null,
                                        disk text,
                                        location text,
                                        rate text,
                                        desc text, size text, cdate text);"""

        sql_create_search_history_table = """CREATE TABLE 
                                                IF NOT EXISTS search_history (
                                                token text,
                                                count integer,
                                                last_date text
                                                );"""

        sql_create_view_history_tabel = """CREATE TABLE 
                                                IF NOT EXISTS view_history (
                                                p_no text,
                                                count integer,
                                                last_date text
                                                );"""

        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            cur.execute(sql_create_product_table)
            cur.execute(sql_create_search_history_table)
            cur.execute(sql_create_view_history_tabel)

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
                  'set p_no = ?, desc = ?, rate = ?, disk = ?, location = ?, size = ?, cdate = ?\n' \
                  'where id = ?'
            rows = cur.execute(sql, (p.product_no, p.desc, p.rate, p.disk_name, p.location, p.size, p.cdate, p.id))
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

    def add_search_history(self, search_text):
        tokens = search_text.split()
        now = time.strftime('%Y%m%d-%H%M%S')

        with sqlite.connect(self.db_file) as c:
            for t in tokens:
                cur = c.cursor()
                sql = "update search_history " \
                      "set count = count + 1, " \
                      "    last_date = ? " \
                      "where token = ?"
                rows = cur.execute(sql, (now, t))
                if rows.rowcount == 0:
                    sql = "insert into search_history(token, count, last_date) " \
                          "values (?, 1, ?)"
                    cur.execute(sql, (t, now))

    def add_view_history(self, pno):
        now = time.strftime('%Y%m%d-%H%M%S')

        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            sql = "update view_history " \
                  "set count = count + 1, " \
                  "    last_date = ? " \
                  "where p_no = ?"
            rows = cur.execute(sql, (now, pno))
            if rows.rowcount == 0:
                sql = "insert into view_history(p_no, count, last_date) " \
                      "values (?, 1, ?)"
                cur.execute(sql, (pno, now))

    def search(self, text, limit_filter_text, limit_count, order_text, is_all_match=False):
        # # test
        # return [Product('aaa-123', 'ddd', 'xxx', 'disk', 'c:/aaa.txt', '10.00', '2017-07-11'),
        #         Product('bbb-456', 'bbb', 'xxx', 'disk', 'c:/aaa.txt', '5.00', '2017-08-01aa)]

        if text == '':
            return self.search_all(limit_filter_text, limit_count, order_text)

        tokens = text.split()
        if len(tokens) > 0:
            products = []
            if is_all_match:
                products = self.search_all_tokens(tokens)
            else:
                products = self.search_any_tokens(tokens)

            if len(products) > 0:
                self.add_search_history(text)
            return products

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

    def search_all(self, limit_filter_test='', limit_count='', order_text=''):
        with sqlite.connect(self.db_file) as c:
            cur = c.cursor()
            default_limit_filter = "p_no not in ('sample', 't', 'clip') and rate = '' and desc not like '%삼성중앙%'"
            limit_filter_test = 'where ' + (limit_filter_test if limit_filter_test is not '' else default_limit_filter)
            order_text = order_text if order_text is not '' else ' order by cdate desc'
            sql = "select id, p_no, desc, rate, disk, location, size, cdate\n" \
                  "from (select * from product {} limit {})".format(limit_filter_test + order_text, limit_count)
            try:
                cur.execute(sql)
                result = cur.fetchall()
            except Exception as e:
                raise DBException(str(e))

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
