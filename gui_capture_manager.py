# -*-coding:utf-8-*-

import sys
import os

from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import *

import capture_util

form_class = uic.loadUiType('C:/__devroot/utils/resource/gui_capture_tool.ui')[0]
column_def = {'time': 0, 'duration': 1, 'del': 2}


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

    def src_path(self):
        return self.lbl_src_path.text()

    def cap_dir(self):
        return self.txt_selected_cap_dir.text()

    def clip_dir(self):
        return self.txt_selected_clip_dir.text()

    def load_rel_caps(self):
        dir, fname = os.path.split(os.path.splitext(self.src_path())[0])
        dir = '.' if dir == '' else dir
        rel_cap_paths = [os.path.join(self.cap_dir(), x) for x in os.listdir(self.cap_dir()) if x.startswith(fname)]
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
        pass

    def open_clip_tool(self):
        pass

    def add_cap_result(self, cap_path):
        row = self.cap_model.rowCount()

        time = capture_util.to_time_form(capture_util.get_time(cap_path))
        self.cap_model.setItem(row, column_def['time'], QtGui.QStandardItem(time))

        if row % 2 == 1:
            duration = capture_util.get_duration_in_time_form(self.cap_model.item(row-1).text(), time)
            self.cap_model.setItem(row, column_def['duration'], QtGui.QStandardItem(str(duration)))

        btn_w = 60

        btn_delete_file = QPushButton()
        btn_delete_file.setText('delete')
        btn_delete_file.setFixedWidth(btn_w)
        btn_delete_file.clicked.connect(self.on_item_del_file_clicked)
        self.tbl_caps.setIndexWidget(self.cap_model.index(row, column_def['del']), btn_delete_file)

        self.tbl_caps.resizeColumnsToContents()
        self.tbl_caps.resizeRowsToContents()

    def on_item_del_file_clicked(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)

    src_path = sys.argv[1]
    window = MainWindow(src_path)
    window.show()
    app.exec_()
