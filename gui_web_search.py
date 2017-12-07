# -*-coding:utf-8-*-

import sys
import urllib
import subprocess
import os
import functools
import urllib.request
from PyQt5 import QtCore, QtGui, QtWidgets
import time

import ui_util
import web_scrapper
from defines import ColumnDef
from widgets import *



column_def = ColumnDef(['chk', 'desc', 'torrent', 'img'],
                       {'chk': ''})


class SearchWorker(QObject):
    fetched = pyqtSignal(int, int)
    finished = pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def on_search_keyword_req(self, keyword, max_count):
        print('on_search_req')
        results = web_scrapper.search_detail_list(keyword, max_count)
        self.finished.emit(results)

    def on_search_today_req(self, page_count):
        print('on_search_today_req')
        results = web_scrapper.search_main_page(page_count)
        self.finished.emit(results)

    def on_stop_req(self):
        print('on_stop_req')


class MainWindow(TabledUtilWindow):
    search_keyword_req = pyqtSignal(str, int)
    search_today_req = pyqtSignal(int)
    stop_req = pyqtSignal()

    def __init__(self, search_text):
        super().__init__('web search')

        self.thread = QThread()
        self.thread.start()

        self.search_worker = SearchWorker()
        self.search_worker.moveToThread(self.thread)
        self.search_worker.finished.connect(self.on_search_finished)

        self.search_keyword_req.connect(self.search_worker.on_search_keyword_req)
        self.search_today_req.connect(self.search_worker.on_search_today_req)
        self.stop_req.connect(self.search_worker.on_stop_req)

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
        self.txt_max_count = LabeledLineEdit('max', '100', 80, 100)
        self.btn_search = QPushButton('search')
        self.btn_get_today = QPushButton('get today')
        self.btn_download_torrent = QPushButton('download torrent')
        self.btn_stop_search = QPushButton('stop')
        self.tableview = SearchView()
        self.set_default_table(self.tableview)

        self.setCentralWidget(QWidget())

        base_layout = QVBoxLayout()
        self.centralWidget().setLayout(base_layout)

        control_group = QVBoxLayout()
        base_layout.addLayout(control_group)

        control_sub1 = QHBoxLayout()
        control_sub1.addWidget(self.txt_search_text)
        control_sub1.addWidget(self.txt_max_count)
        control_sub1.addWidget(self.btn_search)
        control_group.addLayout(control_sub1)

        control_sub2 = QHBoxLayout()
        control_sub2.addWidget(self.btn_get_today)
        control_sub2.addWidget(self.btn_download_torrent)
        control_sub2.addWidget(self.btn_stop_search)
        control_group.addLayout(control_sub2)

        base_layout.addWidget(self.tableview)

        self.img_big_picture = ImageWidget(None, 600, 400, self)
        self.img_big_picture.hide()

        self.search_counter = SearchCounter(self)
        self.search_counter.hide()

    def load_settings(self):
        self.txt_max_count.set_text(str(ui_util.load_settings(self, self.app_name, 'max count', 10)))
        super().load_settings()

    def save_settings(self):
        ui_util.save_settings(self, self.app_name, 'max count', self.get_max_count())

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        mod = event.modifiers()
        if key == Qt.Key_Return and mod == Qt.ControlModifier:
            self.show_big_picture()
        elif key == Qt.Key_Return:
            if self.is_search_enabled():
                self.search_product()
        elif key == Qt.Key_Escape:
            if self.img_big_picture.isVisible():
                self.img_big_picture.hide()
                event.accept()
        elif key == Qt.Key_C and mod == Qt.ControlModifier:
            self.toggle_checked()
        else:
            super().keyPressEvent(event)

    def arrange_table(self):
        self.tableview.resizeRowsToContents()
        self.tableview.resizeColumnsToContents()

    def get_search_text(self):
        return self.txt_search_text.text()

    def get_max_count(self):
        return int(self.txt_max_count.text())

    def is_checked(self, row):
        return self.tableview.indexWidget(self.model.index(row, column_def['chk'])).isChecked()

    def toggle_checked(self, row=None):
        chk = self.tableview.indexWidget(self.tableview.currentIndex())
        if chk:
            chk.setChecked(not chk.isChecked())

    def row_content_url(self, row=None):
        if not row:
            row = self.tableview.currentIndex().row()

        return self.model.item(row, column_def['desc']).data()

    def enable_search(self):
        self.btn_search.setEnabled(True)
        self.btn_get_today.setEnabled(True)

    def disable_search(self):
        self.btn_search.setEnabled(False)
        self.btn_get_today.setEnabled(False)

    def is_search_enabled(self):
        return self.btn_search.isEnabled() and self.btn_get_today.isEnabled()

    def load_image(self, url):
        image = self.img_cache[url] if url in self.img_cache else None
        if not image and url:
            data = urllib.request.urlopen(url).read()
            image = QtGui.QImage()
            image.loadFromData(data)
            self.img_cache[url] = image
        return image

    def load_content_big_image_from_cache(self, content_url):
        return self.img_cache[content_url] if content_url in self.img_cache else None

    def update_model(self, results):
        self.model.removeRows(0, self.model.rowCount())

        for r in results:
            row = self.model.rowCount()

            desc_item = QtGui.QStandardItem(r[0] + '\n' + r[1])
            desc_item.setData(r[4]) # save content url for later use
            self.model.setItem(row, column_def['desc'], desc_item)
            ui_util.add_checkbox_on_tableview(self.tableview, row, column_def['chk'], '', 20, None, True)
            ui_util.add_button_on_tableview(self.tableview, row, column_def['torrent'], 'download', None, 0, functools.partial(self.download_torrent, r[3], r[4]))
            img_url = r[2]
            # self.tableview.setIndexWidget(self.model.index(row, column_def['img']), ImageWidget(self.load_image(img_url), 210, 268))
            self.tableview.setIndexWidget(self.model.index(row, column_def['img']), ImageWidget(self.load_image(img_url), 400, 600))
            # self.tableview.setIndexWidget(self.model.index(row, column_def['img']), ImageWidget(self.load_image(img_url), 50, 50))

        self.arrange_table()
        self.arrange_table()    # need to be double arrange call here : to perfect fit row height(for long text)

    def search_product(self):
        # self.update_model(web_scrapper.search_detail_list(self.search_text()))

        print('search_product')
        self.disable_search()
        self.search_keyword_req.emit(self.get_search_text(), self.get_max_count())

    def search_today(self):
        # self.update_model(web_scrapper.search_main_page(3))

        print('search_today')
        self.disable_search()
        self.search_today_req.emit(3)

    def on_search_finished(self, results):
        print('on_search_finishied')
        self.update_model(results)
        self.enable_search()

    def download_torrent(self, url, content_url):
        print(url)
        command = 'start chrome "{}"'.format(content_url)
        os.system(command)
        time.sleep(0.1)
        command = 'start chrome "{}"'.format(url)
        os.system(command)

        # web_scrapper.download_torrents([(content_url, url)])

    def download_checked_torrents(self):
        for r in range(self.model.rowCount()):
            if self.is_checked(r):
                self.tableview.indexWidget(self.model.index(r, column_def['torrent'])).clicked.emit()

    def show_big_picture(self):
        content_url = self.row_content_url()
        image = self.load_content_big_image_from_cache(content_url)
        if not image:
            _, _, img_url = web_scrapper.get_content_detail(content_url)
            image = self.load_image(img_url)
            self.img_cache[content_url] = image
        self.img_big_picture.show_img(image, False)
        self.img_big_picture.show()


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == '__main__':
    app = QApplication(sys.argv)

    search_text = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(search_text)
    window.show()
    app.exec_()