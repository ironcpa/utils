#-*-coding:utf-8-*-

import subprocess
import sys
import os
import re

from PyQt5 import uic, QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from send2trash import send2trash

form_class = uic.loadUiType("C:/__devroot/utils/resource/gui_ffmpeg_main.ui")[0]
column_def = {'dir': 0, 'open': 1, 'del': 2, 'reclip' : 3, 'path': 4}


class MainWindow(QMainWindow, form_class):
    def __init__(self, src_path):
        super().__init__()
        self.setupUi(self)

        self.lbl_src_file.setText(src_path)

        src_name_only, src_ext = os.path.splitext(os.path.basename(src_path))
        clip_name = 'clip_' + src_name_only
        self.txt_clip_name.setText(clip_name + '_{}_{}' + src_ext)

        self.btn_encode.clicked.connect(self.on_encode_clicked)

        self.tbl_clip_result.setColumnCount(5)
        self.tbl_clip_result.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # test
        self.txt_start_time.setText('000000')
        self.txt_end_time.setText('000010')

    def on_encode_clicked(self):
        start_time = self.txt_start_time.text().replace(' ', '')
        end_time = self.txt_end_time.text().replace(' ', '')
        clip_file_form = self.txt_clip_name.text()
        out_clip_path = clip_file_form.format(start_time.replace(':', ''), end_time.replace(':', ''))

        ok, err = self.run_ffmpeg_make_clip(start_time, end_time, out_clip_path)
        if ok:
            QMessageBox.information(self, 'info', 'encoding complete')
            # self.close()
        else:
            print(err)
            QMessageBox.critical(self, 'error', 'encoding failed\n{}'.format(err))

    def run_ffmpeg_make_clip(self, start_time, end_time, out_clip_path):
        src_file = self.lbl_src_file.text()
        command = ''
        if self.chk_reencode.isChecked():
            command = 'ffmpeg -i "{}" -ss {} -to {} {} -y'.format(src_file, start_time, end_time, out_clip_path)
        else:
            command = 'ffmpeg -i "{}" -ss {} -to {} -c copy {} -y'.format(src_file, start_time, end_time,
                                                                          out_clip_path)
        print(command)
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
            self.add_clip_result(out_clip_path)
            return True, None
        except subprocess.CalledProcessError as e:
            return False, e

    def add_clip_result(self, path):
        row = self.tbl_clip_result.rowCount()
        self.tbl_clip_result.insertRow(row)

        btn_open_dir = QPushButton(self.tbl_clip_result)
        btn_open_dir.setText('folder')
        btn_open_dir.clicked.connect(lambda state, x=row: self.on_open_dir_clicked(x))
        self.tbl_clip_result.setCellWidget(row, column_def['dir'], btn_open_dir)

        btn_open_file = QPushButton(self.tbl_clip_result)
        btn_open_file.setText('open')
        btn_open_file.clicked.connect(lambda state, x=row: self.on_open_file_clicked(x))
        self.tbl_clip_result.setCellWidget(row, column_def['open'], btn_open_file)

        btn_delete_file = QPushButton(self.tbl_clip_result)
        btn_delete_file.setText('delete')
        btn_delete_file.clicked.connect(lambda state, x=row: self.on_del_file_clicked(x))
        self.tbl_clip_result.setCellWidget(row, column_def['del'], btn_delete_file)

        btn_reclip = QPushButton(self.tbl_clip_result)
        btn_reclip.setText('reclip')
        btn_reclip.clicked.connect(lambda state, x=row: self.on_reclip_clicked(x))
        self.tbl_clip_result.setCellWidget(row, column_def['reclip'], btn_reclip)

        self.tbl_clip_result.setItem(row, column_def['path'], QTableWidgetItem(path))

        self.tbl_clip_result.resizeColumnsToContents()
        self.tbl_clip_result.resizeRowsToContents()

    def on_open_dir_clicked(self, row):
        path = self.tbl_clip_result.item(row, column_def['path']).text()
        subprocess.Popen('explorer /select,"{}"'.format(path))

    def on_open_file_clicked(self, row):
        path = self.tbl_clip_result.item(row, column_def['path']).text()
        subprocess.Popen('explorer "{}"'.format(path))

    def on_del_file_clicked(self, row):
        reply = QMessageBox.question(self, 'alert', 'Sure to delete?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            path = self.tbl_clip_result.item(row, column_def['path']).text()
            send2trash(path)

    def on_reclip_clicked(self, row):
        path = self.tbl_clip_result.item(row, column_def['path']).text()

        clip_name = os.path.splitext(path)[0]
        time_form_len = 6 + 1 + 6   # 000000_000000
        if len(clip_name) < time_form_len + 1: # at least 1 more than form
            return False, None
        time_form = clip_name[-time_form_len:]
        p = re.compile('[0-9]{6}_[0-9]{6}')
        if not p.match(clip_name[-time_form_len:]):
            return False, None

        start_time = time_form[0:6]
        end_time = time_form[-6:]
        clip_file_form = self.txt_clip_name.text()
        out_clip_path = clip_file_form.format(start_time.replace(':', ''), end_time.replace(':', ''))

        ok, err = self.run_ffmpeg_make_clip(start_time, end_time, out_clip_path)
        if ok:
            QMessageBox.information(self, 'info', 'encoding complete')
            # self.close()
        else:
            print(err)
            QMessageBox.critical(self, 'error', 'encoding failed\n{}'.format(err))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    src_file = sys.argv[1] if len(sys.argv) > 1 else ''
    mywindow = MainWindow(src_file)
    mywindow.show()
    app.exec_()
