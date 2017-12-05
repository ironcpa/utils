# -*-coding:utf-8-*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets

import ui_util
import web_scrapper
from defines import ColumnDef
from widgets import *


column_def = ColumnDef(['chk', 'title', 'desc', 'img'],
                       {'chk': ''})


class MainWindow(TabledUtilWindow):
    def __init__(self, search_text):
        super().__init__('web search')

        self.btn_search.clicked.connect(self.search_product)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.model.setHorizontalHeaderLabels(column_def.header_titles)
        self.tableview.setModel(self.model)

        self.load_settings()

        self.img_cache = {}

    def setup_ui(self):
        super().setup_ui()

        self.setGeometry(0, 0, 1000, 600)

        self.txt_search_text = LabeledLineEdit('search text')
        self.btn_search = QPushButton('search')
        self.btn_get_today = QPushButton('get today')
        self.btn_download_torrent = QPushButton('download torrent')
        self.tableview = SearchView()
        self.set_default_table(self.tableview)

        self.setCentralWidget(QWidget())

        base_layout = QVBoxLayout()
        self.centralWidget().setLayout(base_layout)

        control_group = QVBoxLayout()
        base_layout.addLayout(control_group)

        control_sub1 = QHBoxLayout()
        control_sub1.addWidget(self.txt_search_text)
        control_sub1.addWidget(self.btn_search)
        control_group.addLayout(control_sub1)

        control_sub2 = QHBoxLayout()
        control_sub2.addWidget(self.btn_get_today)
        control_sub2.addWidget(self.btn_download_torrent)
        control_group.addLayout(control_sub2)

        base_layout.addWidget(self.tableview)

    def arrange_table(self):
        self.tableview.resizeRowsToContents()
        self.tableview.resizeColumnsToContents()

    def search_text(self):
        return self.txt_search_text.text()

    def search_product(self):
        results = web_scrapper.search_detail_list(self.search_text())

        for r in results:
            row = self.model.rowCount()

            ui_util.add_checkbox_on_tableview(self.tableview, row, column_def['chk'], '', 20, None, True)
            self.model.setItem(row, column_def['title'], QtGui.QStandardItem(r[0]))
            self.model.setItem(row, column_def['desc'], QtGui.QStandardItem(r[1]))
            url = r[2]
            image = self.img_cache[url] if url in self.img_cache else None
            if not image:
                data = urllib.request.urlopen(url).read()
                image = QtGui.QImage()
                image.loadFromData(data)
            self.tableview.setIndexWidget(self.model.index(row, column_def['img']), ImageWidget(image))

        self.arrange_table()


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == '__main__':
    app = QApplication(sys.argv)

    search_text = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(search_text)
    window.show()
    app.exec_()