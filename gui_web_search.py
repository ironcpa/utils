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
import file_util
import web_scrapper as wsc
from defines import ColumnDef
from widgets import *

import threading


column_def = ColumnDef(['chk', 'state', 'desc', 'torrent', 'img'],
                       {'chk': ''})


class SearchWorker(QObject):
    finished = pyqtSignal(list)

    def __init__(self, lazy_content_load=True):
        super().__init__()
        self.lazy_content_load = lazy_content_load

    def on_search_keyword_req(self, keyword, max_count, page_no):
        print('on_search_req')
        results = wsc.search_detail_list(keyword, max_count, page_no, not self.lazy_content_load)
        self.finished.emit(results)

    def on_search_today_req(self, start_page, page_count):
        print('on_search_today_req')
        #results = wsc.search_main_page(start_page, page_count, not self.lazy_content_load)
        results = wsc.search_javtorrent(start_page, page_count)
        self.finished.emit(results)

    def on_stop_req(self):
        print('on_stop_req')


class ContentLoadWorker(QObject):
    # row, date, torrent_url, desc, img_url
    detail_fetched = pyqtSignal(int, str, str, str, str)
    detail_fetch_finished = pyqtSignal()
    # type, row, img_data
    image_fetched = pyqtSignal(str, int, str, bytes)
    torrent_link_fetched = pyqtSignal(int, str)
    torrent_link_fetch_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        print(threading.current_thread())
        if sys.platform == 'win32':
            self.loop = asyncio.ProactorEventLoop()
        else:
            self.loop = asyncio.new_event_loop()

        asyncio.set_event_loop(self.loop)
        self.sema = asyncio.Semaphore(5)

    def on_detail_load_req(self, rows, detail_urls, small_img_urls, product_ids):
        print('on_load_req, {}, {}'.format(len(rows), len(detail_urls)))
        load_detail_tasks = [wsc.load_detail(row, url) for row, url in zip(rows, detail_urls)]
        done, _ = self.loop.run_until_complete(asyncio.wait(load_detail_tasks))

        #self.load_images('small', rows, small_img_urls)

        img_rows = []
        bigimg_detail_urls = []
        for dr in done:
            idx, url = dr.result()
            img_rows.append(idx)
            bigimg_detail_urls.append(url)
        self.load_images('big', img_rows, bigimg_detail_urls)

        self.detail_fetch_finished.emit()

        self.load_torrent_links(rows, product_ids)

    def on_stop_req(self):
        print('on_stop_req : content load worker is_running={}'.format(self.loop.is_running()))
        if self.loop.is_running():
            self.loop.stop()
            self.detail_fetch_finished.emit()

    def load_images(self, img_type, rows, urls):
        print('>>>>>>>>> load_images:', img_type)
        load_bigimg_tasks = [wsc.load_image_data(idx, url) for idx, url in zip(rows, urls)]
        done, _ = self.loop.run_until_complete(asyncio.wait(load_bigimg_tasks))

        for task in done:
            row, url, data = task.result()
            self.image_fetched.emit(img_type, row, url, data)

    def load_torrent_links(self, rows, product_ids):
        tasks = [wsc.load_torrent_link(row, pid, self.sema) for row, pid in zip(rows, product_ids)]

        done, _ = self.loop.run_until_complete(asyncio.wait(tasks))

        for task in done:
            row, link = task.result()
            self.torrent_link_fetched.emit(row, link)

        self.torrent_link_fetch_finished.emit()

    def get_chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i+n]


class MyEventFilter(QObject):
    def eventFilter(self, obj: 'QObject', e: 'QEvent'):
        if e.type() == QEvent.KeyPress:
            if e.key() == Qt.Key_Space and e.modifiers() == Qt.ControlModifier:
                return True
        return False


class MainWindow(TabledUtilWindow):
    cur_page = 0
    cur_search_type = None

    search_keyword_req = pyqtSignal(str, int, int)
    search_today_req = pyqtSignal(int, int)
    search_stop_req = pyqtSignal()
    # rows, detail_page_urls, small_img_urls, product_ids
    content_load_req = pyqtSignal(list, list, list, list)
    content_load_stop_req = pyqtSignal()

    def __init__(self, search_text):
        super().__init__('web search')

        self.is_lazy_content_load = True

        self.img_cache = {}

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
        self.content_load_worker.detail_fetched.connect(self.on_detail_page_fetched)
        self.content_load_worker.detail_fetch_finished.connect(self.arrange_table)
        self.content_load_worker.image_fetched.connect(self.on_image_fetched)
        self.content_load_worker.torrent_link_fetched.connect(self.on_torrent_link_fetched)
        self.content_load_worker.torrent_link_fetch_finished.connect(self.on_all_torrent_link_fetched)

        self.content_load_req.connect(self.content_load_worker.on_detail_load_req)
        self.content_load_stop_req.connect(self.content_load_worker.on_stop_req)

        self.btn_search.clicked.connect(self.search_keyword)
        self.btn_get_today.clicked.connect(self.search_today)
        self.btn_1_more_page.clicked.connect(self.search_next_page)
        self.btn_download_torrent.clicked.connect(self.download_checked_torrents)
        self.btn_stop_search.clicked.connect(self.stop_search)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.model.setHorizontalHeaderLabels(column_def.header_titles)
        self.tableview.setModel(self.model)
        self.tableview.installEventFilter(MyEventFilter())

        self.load_settings()


        if search_text and search_text != '':
            self.txt_search_text.set_text(search_text)
            self.search_keyword()

    def setup_ui(self):
        super().setup_ui()

        self.setGeometry(0, 0, 1000, 600)

        self.txt_search_text = LabeledLineEdit('search text')
        self.txt_max_count = LabeledLineEdit('max', '100', 80, 100)
        self.btn_search = QPushButton('search')
        self.btn_get_today = QPushButton('get today')
        self.btn_1_more_page = QPushButton('1 more page')
        self.btn_download_torrent = QPushButton('download torrent')
        self.btn_stop_search = QPushButton('stop')
        self.tableview = SearchView(column_def['chk'])
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
        control_sub2.addWidget(self.btn_1_more_page)
        control_sub2.addWidget(self.btn_download_torrent)
        control_sub2.addWidget(self.btn_stop_search)
        control_group.addLayout(control_sub2)

        base_layout.addWidget(self.tableview)

        self.img_big_picture = ImageWidget(None, 768, 1024, self)
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
        if key == Qt.Key_Return and mod == Qt.ShiftModifier:
            self.show_big_picture()
        elif key == Qt.Key_D and mod == Qt.ControlModifier:
            self.open_db_search()
        elif key == Qt.Key_Return:
            if self.is_search_enabled():
                self.search_keyword()
        elif key == Qt.Key_Tab and mod == Qt.ControlModifier:
            self.close()
        elif key == Qt.Key_Escape:
            if self.img_big_picture.isVisible():
                self.img_big_picture.hide()
                event.accept()
            else:
                ui_util.focus_to_text(self.txt_search_text)
        elif key == Qt.Key_C and mod == Qt.ControlModifier:
            self.tableview.toggle_checked()
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

    def detail_format(self, row_data):
        return row_data.date + '\n' + row_data.title + '\n' + row_data.desc

    def row_data(self, row=None):
        if not row:
            row = self.tableview.currentIndex().row()

        return self.model.item(row, column_def['desc']).data()

    def row_content_url(self, row=None):
        return self.row_data().content_url

    def enable_search(self):
        self.btn_search.setEnabled(True)
        self.btn_get_today.setEnabled(True)
        self.btn_1_more_page.setEnabled(True)

    def disable_search(self):
        self.btn_search.setEnabled(False)
        self.btn_get_today.setEnabled(False)
        self.btn_1_more_page.setEnabled(False)

    def is_search_enabled(self):
        return self.btn_search.isEnabled() and self.btn_get_today.isEnabled()

    def load_image(self, url):
        image = self.img_cache[url] if url in self.img_cache else None
        if not image and url:
            req = urllib.request.Request(url, headers=wsc.REQ_HEADER)
            data = urllib.request.urlopen(req).read()
            image = QtGui.QImage()
            image.loadFromData(data)
            self.img_cache[url] = image
        return image

    def load_content_big_image_from_cache(self, content_url):
        return self.img_cache[content_url] if content_url in self.img_cache else None

    def update_model_w_text_data(self, results):
        self.model.removeRows(0, self.model.rowCount())

        for r in results:
            row = self.model.rowCount()

            desc_item = QtGui.QStandardItem(self.detail_format(r))
            desc_item.setData(r) # save content url for later use
            self.model.setItem(row, column_def['desc'], desc_item)
            ui_util.add_checkbox_on_tableview(self.tableview, row, column_def['chk'], '', 60, None)
            slot = functools.partial(self.download_torrent2, r.product_no, r.torrent_url)
            ui_util.add_button_on_tableview(self.tableview, row, column_def['torrent'], 'download', None, 0, slot)
            if r.img_url is not '':
                # pass for lazy loading small images to fast text only loading
                #add_image_widget_on_tableview(self.tableview, row, column_def['img'], self.load_image(r.img_url), self.setting_ui.row_image_size())
                pass

        self.arrange_table()
        self.arrange_table()    # need to be double arrange call here : to perfect fit row height(for long text)

    def search_keyword(self):
        # self.update_model(wsc.search_detail_list(self.search_text()))

        print('search_product')
        self.set_start_time()
        self.disable_search()
        self.cur_page = 1
        self.cur_search_type = 'keyword'
        self.search_keyword_req.emit(self.get_search_text(), self.get_max_count(), self.cur_page)

    def search_today(self):
        # self.update_model(wsc.search_main_page(3))

        print('search_today')
        self.set_start_time()
        self.disable_search()
        self.cur_page = 1
        self.cur_search_type = 'today'
        self.search_today_req.emit(1, 1)

    def search_next_page(self):
        self.set_start_time()
        self.disable_search()
        self.cur_page += 1
        if self.cur_search_type == 'today':
            self.search_today_req.emit(self.cur_page, 1)
        elif self.cur_search_type == 'keyword':
            self.search_keyword_req.emit(self.get_search_text(), self.get_max_count(), self.cur_page)

    def on_search_finished(self, results):
        print('on_search_finishied')
        self.update_model_w_text_data(results)
        self.enable_search()
        self.tableview.setFocus()
        if self.is_lazy_content_load:
            self.load_content_data_background()
        self.show_elapsed_time()

    def load_content_data_background(self):
        rows, content_urls, small_img_urls, pids = [], [], [], []
        for r in range(self.model.rowCount()):
            rows.append(r)
            #content_urls.append(self.model.item(r, column_def['desc']).data().content_url)
            #small_img_urls.append(self.model.item(r, column_def['desc']).data().img_url)
            row_data = self.row_data(r)
            content_urls.append(row_data.content_url)
            small_img_urls.append(row_data.img_url)
            pids.append(row_data.product_no)

        self.content_load_req.emit(rows, content_urls, small_img_urls, pids)

    def on_detail_page_fetched(self, row, date, torrent_url, desc, image):
        print('on content fetched, {}, {}'.format(row, torrent_url))
        # nothing to do on javtorrent right now

        ''' # old code for old site
        row_data = self.model.item(row, column_def['desc']).data()
        row_data.date = date if date != '' else row_data.date
        row_data.torrent_url = torrent_url
        row_data.desc = desc if desc != '' else row_data.desc

        self.model.setItem(row, column_def['state'], QtGui.QStandardItem('loaded'))
        self.model.item(row, column_def['desc']).setText(self.detail_format(row_data))

        #add_image_widget_on_tableview(self.tableview, row, column_def['img'], image,
        #                              self.setting_ui.row_image_size())
        self.show_elapsed_time()
        '''

    def on_image_fetched(self, itype, row, img_url, img_data):
        print('on image fetched, {} {} {}'.format(itype, row, img_url))
        image = QtGui.QImage()
        image.loadFromData(img_data)
        self.img_cache[img_url] = image

        add_image_widget_on_tableview(self.tableview, row, column_def['img'], image,
                                      self.setting_ui.row_image_size())
        if itype == 'big':
            self.row_data(row).big_img_url = img_url

        self.show_elapsed_time()

    def on_torrent_link_fetched(self, row, link):
        self.row_data(row).torrent_url = link

    def on_all_torrent_link_fetched(self):
        QMessageBox.information(self, 'info', 'torrent link fetch finished')

    def download_torrent(self, url, content_url):
        print(url)
        command = 'start chrome "{}"'.format(content_url)
        os.system(command)

        if url is '':
            _, url, _, _ = wsc.get_content_detail(content_url)
        else:
            time.sleep(0.1)

        command = 'start chrome "{}"'.format(url)
        os.system(command)

        # wsc.download_torrents([(content_url, url)])
        # wsc.download_torrents_chromedriver([(content_url, url)])

    def download_torrent2(self, product_id, torrent_url):
        #wsc.download_torrent_file(product_id, torrent_url)
        wsc.run_torrent_magnet(torrent_url)

    def download_checked_torrents(self):
        for r in range(self.model.rowCount()):
            if self.is_checked(r):
                #self.tableview.indexWidget(self.model.index(r, column_def['torrent'])).clicked.emit()
                row_data = self.row_data(r)
                self.download_torrent2(row_data.product_no, row_data.torrent_url)

    def stop_search(self):
        self.search_stop_req.emit()
        self.content_load_stop_req.emit()
        self.enable_search()

    def calc_big_picture_size(self):
        h = self.height()
        w = h * (768.0 / 1024.0)
        return QSize(w, h)

    def show_big_picture(self):
        url = self.row_data().big_img_url
        image = self.load_content_big_image_from_cache(url)
        ''' # this is not impl yet, complete ithis if needed
        if not image:
            self.content_load_worker.fetch_image_req.emit()
            '''
        if image:
            self.img_big_picture.show_img(image, True, self.calc_big_picture_size())
            self.img_big_picture.show()

    def open_db_search(self):
        pno = file_util.parse_product_no(self.row_data().title)
        fixed_pno = pno[:8] if len(pno) >= 7 else pno
        command = 'pythonw c:/__devroot/utils/gui_db_search.py "{}"'.format(fixed_pno)
        subprocess.Popen(command)


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == '__main__':
    ui_util.kill_same_script()

    app = QApplication(sys.argv)

    search_text = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(search_text)
    window.show()
    app.exec_()