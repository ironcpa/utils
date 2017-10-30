# -*-coding:utf-8-*-

import sys
import os

from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import capture_util
import ui_util
import file_util

form_class = uic.loadUiType('C:/__devroot/utils/resource/gui_capture_tool.ui')[0]
column_def = {'time': 0, 'duration': 1, 'del': 2, 'file':3}


class MainWindow(QMainWindow, form_class):
    def __init__(self, src_path):
        super().__init__()
        self.setupUi(self)

        self.lbl_src_path.setText(src_path)

        self.btn_open_src.clicked.connect(self.open_src_path)
        self.btn_open_cap_dir.clicked.connect(self.open_cap_dir)
        self.btn_open_clip_dir.clicked.connect(self.open_clip_dir)

        self.btn_select_cap_dir.clicked.connect(self.open_dir_dialog)
        self.btn_select_clip_dir.clicked.connect(self.open_dir_dialog)

        self.btn_make_clips.clicked.connect(self.make_clips)
        self.btn_open_clip_tool.clicked.connect(self.open_clip_tool)

        self.cap_model = QtGui.QStandardItemModel(0, len(column_def))
        self.tbl_caps.setModel(self.cap_model)

        #init setting
        self.txt_selected_cap_dir.setText('c:/__potplayer_capture_for_clip')
        self.txt_selected_clip_dir.setText('c:/__clips')

        self.load_rel_caps()

        self.txt_sync_time.setText(str(10))

        self.chk_auto_sync.setChecked(True)
        self.chk_auto_sync.stateChanged.connect(self.auto_sync_changed)

        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.load_rel_caps)
        if self.sync_on():
            self.sync_timer.start(self.sync_miliseconds())

    def src_path(self):
        return self.lbl_src_path.text()

    def cap_dir(self):
        return self.txt_selected_cap_dir.text()

    def clip_dir(self):
        return self.txt_selected_clip_dir.text()

    def sync_on(self):
        return self.chk_auto_sync.isChecked()

    def sync_miliseconds(self):
        return int(self.txt_sync_time.text()) * 1000

    def get_table_row(self, widget):
        return self.tbl_caps.indexAt(widget.pos()).row()

    def load_rel_caps(self):
        self.cap_model.clear()

        dir, fname = os.path.split(os.path.splitext(self.src_path())[0])
        dir = '.' if dir == '' else dir

        # fname으로 찾는 옵션 고려
        rel_cap_paths = [os.path.join(self.cap_dir(), x) for x in os.listdir(self.cap_dir()) if x.startswith(file_util.get_product_no(fname))]
        for c in rel_cap_paths:
            self.add_cap_result(c)

    def open_src_path(self):
        pass

    def open_cap_dir(self):
        pass

    def open_clip_dir(self):
        pass

    def open_dir_dialog(self):
        pass

    def make_clips(self):
        capture_util.create_clips_from_captures(self.src_path(), self.cap_dir(), self.clip_dir(), False)

    def open_clip_tool(self):
        command = 'python c:/__devroot/utils/gui_ffmpeg.py "{}"'.format(self.src_path())
        os.system(command)

    def auto_sync_changed(self, int):
        if self.chk_auto_sync.isChecked():
            self.sync_timer.start(self.sync_miliseconds())
        else:
            self.sync_timer.stop()

    def add_cap_result(self, cap_path):
        row = self.cap_model.rowCount()

        time = capture_util.to_time_form(capture_util.get_time(cap_path))
        time_item = QtGui.QStandardItem(time)
        font = time_item.font()
        font.setPointSize(20)
        time_item.setFont(font)
        self.cap_model.setItem(row, column_def['time'], time_item)

        if row % 2 == 1:
            duration = capture_util.get_duration_in_time_form(self.cap_model.item(row-1).text(), time)
            duration_item = QtGui.QStandardItem(str(duration))
            duration_item.setFont(font)
            self.cap_model.setItem(row, column_def['duration'], duration_item )

        file_item = QtGui.QStandardItem(os.path.basename(cap_path))
        file_item.setData(cap_path)
        file_item.setFont(font)
        self.cap_model.setItem(row, column_def['file'], file_item)

        btn_w = 60

        btn_delete_file = QPushButton()
        btn_delete_file.setText('delete')
        btn_delete_file.setFixedWidth(btn_w)
        btn_delete_file.clicked.connect(self.on_item_del_file_clicked)
        self.tbl_caps.setIndexWidget(self.cap_model.index(row, column_def['del']), btn_delete_file)

        self.tbl_caps.resizeColumnsToContents()
        self.tbl_caps.resizeRowsToContents()
        self.tbl_caps.scrollToBottom()

    def on_item_del_file_clicked(self):
        row = self.get_table_row(self.sender())
        path = self.cap_model.item(row, column_def['file']).data()
        if ui_util.delete_path(self, path):
            self.cap_model.removeRow(row)


# def catch_exceptions(self, t, val, tb):
#     QMessageBox.critical(None, 'exception', '{}'.format(t))
#     old_hook(t, val, tb)


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == "__main__":
    ui_util.kill_same_script()

    app = QApplication(sys.argv)

    src_path = sys.argv[1]
    window = MainWindow(src_path)
    window.show()
    app.exec_()
