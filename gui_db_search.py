# -*-coding:utf-8-*-

import sys

from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import *

import ui_util
from db_util import DB

form_class = uic.loadUiType("C:/__devroot/utils/resource/gui_db_search.ui")[0]
column_def = {'no': 0, 'disk': 1, 'rate': 2, 'desc': 3, 'open': 4, 'dir': 5, 'location': 6}


class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.btn_search.clicked.connect(self.search_db)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.tbl_result.setModel(self.model)

        self.db = DB()

    def get_search_text(self):
        return self.txt_search.text()

    def search_db(self):
        products = self.db.search(self.get_search_text())

        for p in products:
            print(p)
            row = self.model.rowCount()

            self.model.setItem(row, column_def['no'], QtGui.QStandardItem(p.product_no))
            self.model.setItem(row, column_def['disk'], QtGui.QStandardItem(p.disk_name))
            self.model.setItem(row, column_def['rate'], QtGui.QStandardItem(p.rate))
            self.model.setItem(row, column_def['desc'], QtGui.QStandardItem(p.desc))
            self.model.setItem(row, column_def['location'], QtGui.QStandardItem(p.location))

        self.tbl_result.resizeColumnsToContents()
        self.tbl_result.resizeRowsToContents()
        self.tbl_result.scrollToBottom()


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec_()