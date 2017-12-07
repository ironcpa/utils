# -*-coding:utf-8-*-

import sys
import urllib
import subprocess
import os
import functools
import urllib.request
from PyQt5 import QtCore, QtGui, QtWidgets

import ui_util
import web_scrapper
from defines import ColumnDef
from widgets import *


column_def = ColumnDef(['chk', 'desc', 'torrent', 'img'],
                       {'chk': ''})


class MainWindow(TabledUtilWindow):
    def __init__(self, search_text):
        super().__init__('web search')

        self.btn_search.clicked.connect(self.search_product)
        self.btn_get_today.clicked.connect(self.search_today)
        self.btn_download_torrent.clicked.connect(self.download_checked_torrents)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.model.setHorizontalHeaderLabels(column_def.header_titles)
        self.tableview.setModel(self.model)
        # self.model.setItem(0, 1, QtGui.QStandardItem('[FHD]JUX-999 타니하라 노조미(谷原希美, Nozomi Tanihara)'))

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

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        mod = event.modifiers()
        if key == Qt.Key_Return:
            self.search_product()
        else:
            super().keyPressEvent(event)

    def arrange_table(self):
        self.tableview.resizeRowsToContents()
        self.tableview.resizeColumnsToContents()

    def search_text(self):
        return self.txt_search_text.text()

    def update_model(self, results):
        self.model.removeRows(0, self.model.rowCount())

        for r in results:
            row = self.model.rowCount()

            self.model.setItem(row, column_def['desc'], QtGui.QStandardItem(r[0] + '\n' + r[1]))
            ui_util.add_checkbox_on_tableview(self.tableview, row, column_def['chk'], '', 20, None, True)
            ui_util.add_button_on_tableview(self.tableview, row, column_def['torrent'], 'download', None, 0, functools.partial(self.download_torrent, r[3], r[4]))
            img_url = r[2]
            image = self.img_cache[img_url] if img_url in self.img_cache else None
            if not image and img_url:
                data = urllib.request.urlopen(img_url).read()
                image = QtGui.QImage()
                image.loadFromData(data)
            # self.tableview.setIndexWidget(self.model.index(row, column_def['img']), ImageWidget(image, 210, 268))
            self.tableview.setIndexWidget(self.model.index(row, column_def['img']), ImageWidget(image, 50, 50))

        self.arrange_table()
        self.arrange_table()    # need to be double arrange call here : to perfect fit row height(for long text)

    def search_product(self):
        self.update_model(web_scrapper.search_detail_list(self.search_text()))

    def search_today(self):
        self.update_model(web_scrapper.search_main_page(3))

    def download_torrent(self, url, content_url):
        # opener = urllib.request.build_opener()
        # opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36')]
        # urllib.request.install_opener(opener)
        # urllib.request.urlretrieve(url, 'test_download.torrent')

        # subprocess.Popen('explorer')
        # # command = 'start "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" "{}"'.format(url)
        print(url)
        command = 'start chrome "{}"'.format(content_url)
        os.system(command)
        command = 'start chrome "{}"'.format(url)
        # subprocess.Popen(command)
        os.system(command)

        # QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def download_checked_torrents(self):
        for r in range(self.model.rowCount()):
            if self.is_checked(r):
                self.tableview.indexWidget(self.model.index(r, column_def['torrent'])).clicked.emit()

    def is_checked(self, row):
        return self.tableview.indexWidget(self.model.index(row, column_def['chk']).isChecked())


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == '__main__':
    app = QApplication(sys.argv)

    search_text = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(search_text)
    window.show()
    app.exec_()