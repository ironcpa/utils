# -*-coding:utf-8-*-

import sys
import urllib
import subprocess
import os
import functools
import urllib.request
from PyQt5 import QtCore, QtGui, QtWidgets
import time
import asyncio

import ui_util
import web_scrapper as wsc
from defines import ColumnDef
from widgets import *


column_def = ColumnDef(['chk', 'state', 'desc', 'torrent', 'img'],
                       {'chk': ''})


class SearchWorker(QObject):
    fetched = pyqtSignal(int, int)
    finished = pyqtSignal(list)

    def __init__(self, lazy_content_load=True):
        super().__init__()
        self.lazy_content_load = lazy_content_load

    def on_search_keyword_req(self, keyword, max_count):
        print('on_search_req')
        results = wsc.search_detail_list(keyword, max_count, not self.lazy_content_load)
        self.finished.emit(results)

    def on_search_today_req(self, page_count):
        print('on_search_today_req')
        results = wsc.search_main_page(page_count, not self.lazy_content_load)
        self.finished.emit(results)

    def on_stop_req(self):
        print('on_stop_req')


# class ContentLoadWorker(QObject):
#     fetched = pyqtSignal(int, str, str)
#
#     def __init__(self):
#         super().__init__()
#
#     def on_load_req(self, rows, urls):
#         print('on_load_req, {}, {}'.format(len(rows), len(urls)))
#         for row, url in zip(rows, urls):
#             self.fetched.emit(*self.load(row, url))
#
#     def load(self, row, url):
#         print('load: {}, {}'.format(row, url))
#         torrent_url, _, img_url = wsc.get_content_detail(url)
#         return row, torrent_url, img_url


class ContentLoadWorker(QObject):
    fetched = pyqtSignal(int, str, QtGui.QImage)

    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def on_load_req(self, rows, urls):
        print('on_load_req, {}, {}'.format(len(rows), len(urls)))
        self.loop.run_until_complete(self.fetch_contents(rows, urls))
        # self.loop.close()

    async def fetch_contents(self, rows, urls):
        futures = [asyncio.ensure_future(self.load(row, url)) for row, url in zip(rows, urls)]
        for f in asyncio.as_completed(futures):
            row, torrent_url, img_url = await f
            print('fetch_contents finished: {}'.format(row))
            self.fetched.emit(row, torrent_url, img_url)

    async def load(self, row, url):
        try:
            print('load: {}, {}'.format(row, url))
            torrent_url, _, image = await self.loop.run_in_executor(None, wsc.get_content_with_image, url)
            return row, torrent_url, image
        except Exception as e:
            print('exception on {}, {}'.format(row, url))


class ContentLoader:
    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def load_all(self, rows, urls):
        print('load_all, {}, {}'.format(len(rows), len(urls)))
        results = self.loop.run_until_complete(self.fetch_contents(rows, urls))
        self.loop.close()
        return results

    async def fetch_contents(self, rows, urls):
        futures = [asyncio.ensure_future(self.load(row, url)) for row, url in zip(rows, urls)]
        results = await asyncio.gather(*futures)
        return results

    async def load(self, row, url):
        print('load: {}, {}'.format(row, url))
        torrent_url, _, img_url = await self.loop.run_in_executor(None, wsc.get_content_detail, url)
        return row, torrent_url, img_url


class MyEventFilter(QObject):
    def eventFilter(self, obj: 'QObject', e: 'QEvent'):
        if e.type() == QEvent.KeyPress:
            if e.key() == Qt.Key_Space and e.modifiers() == Qt.ControlModifier:
                return True
        return False


class MainWindow(TabledUtilWindow):
    search_keyword_req = pyqtSignal(str, int)
    search_today_req = pyqtSignal(int)
    search_stop_req = pyqtSignal()
    content_load_req = pyqtSignal(list, list)

    def __init__(self, search_text):
        super().__init__('web search')

        self.start_t = None

        self.is_lazy_content_load = True

        self.thread = QThread()
        self.thread.start()

        self.search_worker = SearchWorker(self.is_lazy_content_load)
        self.search_worker.moveToThread(self.thread)
        self.search_worker.finished.connect(self.on_search_finished)

        self.search_keyword_req.connect(self.search_worker.on_search_keyword_req)
        self.search_today_req.connect(self.search_worker.on_search_today_req)
        self.search_stop_req.connect(self.search_worker.on_stop_req)

        self.content_load_worker = ContentLoadWorker()
        self.content_load_worker.moveToThread(self.thread)
        self.content_load_worker.fetched.connect(self.on_content_fetched)

        self.content_load_req.connect(self.content_load_worker.on_load_req)

        self.btn_search.clicked.connect(self.search_product)
        self.btn_get_today.clicked.connect(self.search_today)
        self.btn_download_torrent.clicked.connect(self.download_checked_torrents)
        self.btn_stop_search.clicked.connect(self.stop_search)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.model.setHorizontalHeaderLabels(column_def.header_titles)
        self.tableview.setModel(self.model)
        self.tableview.installEventFilter(MyEventFilter())

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

    def init_setting_ui(self):
        self.setting_ui = WebSearchSettingUI(self)
        self.setting_ui.hide()

    def load_settings(self):
        self.txt_max_count.set_text(str(ui_util.load_settings(self, self.app_name, 'max count', 10)))
        row_image_size = ui_util.load_settings(self, self.app_name, self.setting_ui.KEY_ROW_IMAGE_SIZE, QSize(210, 268))
        self.setting_ui.set_row_image_size(row_image_size.width(), row_image_size.height())
        super().load_settings()

    def save_settings(self):
        super().save_settings()
        ui_util.save_settings(self, self.app_name, 'max count', self.get_max_count())
        ui_util.save_settings(self, self.app_name, self.setting_ui.KEY_ROW_IMAGE_SIZE, self.setting_ui.row_image_size())

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
        cur_chk_index = self.model.index(self.tableview.currentIndex().row(), column_def['chk'])
        chk = self.tableview.indexWidget(cur_chk_index)
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

            desc_item = QtGui.QStandardItem(r.title + '\n' + r.desc)
            desc_item.setData(r) # save content url for later use
            self.model.setItem(row, column_def['desc'], desc_item)
            ui_util.add_checkbox_on_tableview(self.tableview, row, column_def['chk'], '', 40, None, True)
            slot = functools.partial(self.download_torrent, r.torrent_url, r.content_url)
            ui_util.add_button_on_tableview(self.tableview, row, column_def['torrent'], 'download', None, 0, slot)
            if r.img_url is not '':
                ui_util.add_image_widget_on_tableview(self.tableview, row, column_def['img'], self.load_image(r.img_url), self.setting_ui.row_image_size())

        self.arrange_table()
        self.arrange_table()    # need to be double arrange call here : to perfect fit row height(for long text)

    def search_product(self):
        # self.update_model(wsc.search_detail_list(self.search_text()))

        print('search_product')
        self.start_t = time.time()
        self.disable_search()
        self.search_keyword_req.emit(self.get_search_text(), self.get_max_count())

    def search_today(self):
        # self.update_model(wsc.search_main_page(3))

        print('search_today')
        self.disable_search()
        self.search_today_req.emit(3)
        if self.is_lazy_content_load:
            self.load_content_data_background()

    def on_search_finished(self, results):
        print('on_search_finishied')
        self.update_model(results)
        self.enable_search()
        if self.is_lazy_content_load:
            self.load_content_data_background()
        self.show_elapsed()

    def show_elapsed(self):
        print('elapse={}'.format(time.time() -self.start_t))

    def load_content_data_background(self):
        rows, content_urls = [], []
        for r in range(self.model.rowCount()):
            rows.append(r)
            content_urls.append(self.model.item(r, column_def['desc']).data().content_url)

        self.content_load_req.emit(rows, content_urls)

    def on_content_fetched(self, row, torrent_url, image):
        print('on content fetched, {}, {}'.format(row, torrent_url))

        row_data = self.model.item(row, column_def['desc']).data()
        row_data.torrent_url = torrent_url

        self.model.setItem(row, column_def['state'], QtGui.QStandardItem('loaded'))
        ui_util.add_image_widget_on_tableview(self.tableview, row, column_def['img'], image,
                                              self.setting_ui.row_image_size())
        self.show_elapsed()

    def download_torrent(self, url, content_url):
        print(url)
        command = 'start chrome "{}"'.format(content_url)
        os.system(command)

        if url is '':
            url, _, _ = wsc.get_content_detail(content_url)
        else:
            time.sleep(0.1)
        command = 'start chrome "{}"'.format(url)
        os.system(command)

        # wsc.download_torrents([(content_url, url)])

    def download_checked_torrents(self):
        for r in range(self.model.rowCount()):
            if self.is_checked(r):
                self.tableview.indexWidget(self.model.index(r, column_def['torrent'])).clicked.emit()

    def stop_search(self):
        self.search_stop_req.emit()
        self.enable_search()

    def show_big_picture(self):
        content_url = self.row_content_url()
        image = self.load_content_big_image_from_cache(content_url)
        if not image:
            _, _, img_url = wsc.get_content_detail(content_url)
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