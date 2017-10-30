# -*-coding:utf-8-*-

import subprocess
import sys
import os
import re

from PyQt5 import uic, QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from send2trash import send2trash

import ui_util

form_class = uic.loadUiType("C:/__devroot/utils/resource/gui_ffmpeg_main.ui")[0]
column_def = {'dir': 0, 'open': 1, 'del': 2, 'reclip': 3, 'copy setting':4, 'path': 5}


class MainWindow(QMainWindow, form_class):
    def __init__(self, parent, src_path):
        super().__init__(parent)
        self.parent = parent
        self.setupUi(self)

        self.lbl_src_file.setText(src_path)

        src_name_only, src_ext = os.path.splitext(os.path.basename(src_path))
        clip_name = 'clip_' + src_name_only
        self.txt_clip_name.setText('c:\\__clips\\' + clip_name + '_{}_{}' + src_ext)

        self.btn_encode.clicked.connect(self.on_encode_clicked)
        self.btn_merge_all_clips.clicked.connect(self.merge_all_clips)
        self.btn_dir_src.clicked.connect(self.on_dir_src_clicked)
        self.btn_open_src.clicked.connect(self.on_open_src_clicked)
        self.btn_del_src.clicked.connect(self.on_del_src_clicked)
        self.btn_to_start_time.clicked.connect(self.copy_end_to_start_time)
        self.btn_to_end_time.clicked.connect(self.copy_start_to_end_time)

        self.clip_model = QtGui.QStandardItemModel(0, len(column_def))
        self.tbl_clip_result.setModel(self.clip_model)

        self.load_rel_clips()

        # # test
        # self.txt_start_time.setText('000000')
        # self.txt_end_time.setText('000010')

    def src_path(self):
        return self.lbl_src_file.text()

    def load_rel_clips(self):
        dir, fname = os.path.split(os.path.splitext(self.src_path())[0])
        dir = '.' if dir == '' else dir
        # rel_clip_paths = [x for x in os.listdir(dir) if x.startswith('clip_{}'.format(fname))]
        clip_dir = 'c:\\__clips\\'
        rel_clip_paths = [clip_dir + x for x in os.listdir(clip_dir) if x.startswith('clip_{}'.format(fname))]
        for p in rel_clip_paths:
            self.add_clip_result(p)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        if key == Qt.Key_Return:
            self.on_encode_clicked()
        else:
            event.ignore()

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

    def merge_all_clips(self):
        if self.clip_model.rowCount() < 1:
            return

        tmp_list_file_name = 'tmp_list.txt'
        with open(tmp_list_file_name, 'w') as tmp_list_file:
            for r in range(self.clip_model.rowCount()):
                path = self.clip_model.item(r, column_def['path']).text()
                tmp_list_file.write("file '{}'\n".format(path))
        merged_file = 'con_' + os.path.basename(self.src_path())

        command = 'ffmpeg -f concat -safe 0 -i {} -c copy "{}" -y'.format(tmp_list_file_name, merged_file)
        subprocess.check_output(command)
        os.remove(tmp_list_file_name)

    def on_dir_src_clicked(self):
        ui_util.open_path_dir(self.lbl_src_file.text())

    def on_open_src_clicked(self):
        ui_util.open_path(self.lbl_src_file.text())

    def on_del_src_clicked(self):
        ui_util.delete_path(self, self.lbl_src_file.text())

    def copy_end_to_start_time(self):
        self.txt_start_time.setText(self.txt_end_time.text())

    def copy_start_to_end_time(self):
        self.txt_end_time.setText(self.txt_start_time.text())

    def run_ffmpeg_make_clip(self, start_time, end_time, out_clip_path):
        # if os.path.exists(out_clip_path):
        #     return False, 'already exists'

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
            self.remove_old_same_result(out_clip_path)
            self.add_clip_result(out_clip_path)
            return True, None
        except subprocess.CalledProcessError as e:
            return False, e

    def add_clip_result(self, path):
        row = self.clip_model.rowCount()

        self.clip_model.setItem(self.clip_model.rowCount(), column_def['path'], QtGui.QStandardItem(path))

        btn_w = 60

        btn_open_dir = QPushButton()
        btn_open_dir.setText('folder')
        btn_open_dir.setFixedWidth(btn_w)
        btn_open_dir.clicked.connect(self.on_item_open_dir_clicked)
        self.tbl_clip_result.setIndexWidget(self.clip_model.index(row, column_def['dir']), btn_open_dir)

        btn_open_file = QPushButton()
        btn_open_file.setText('open')
        btn_open_file.setFixedWidth(btn_w)
        btn_open_file.clicked.connect(self.on_item_open_file_clicked)
        self.tbl_clip_result.setIndexWidget(self.clip_model.index(row, column_def['open']), btn_open_file)

        btn_delete_file = QPushButton()
        btn_delete_file.setText('delete')
        btn_delete_file.setFixedWidth(btn_w)
        btn_delete_file.clicked.connect(self.on_item_del_file_clicked)
        self.tbl_clip_result.setIndexWidget(self.clip_model.index(row, column_def['del']), btn_delete_file)

        btn_reclip = QPushButton()
        btn_reclip.setText('reclip')
        btn_reclip.setFixedWidth(btn_w)
        btn_reclip.clicked.connect(self.on_item_reclip_clicked)
        self.tbl_clip_result.setIndexWidget(self.clip_model.index(row, column_def['reclip']), btn_reclip)

        btn_copy_setting = QPushButton()
        btn_copy_setting.setText('copy setting')
        btn_copy_setting.clicked.connect(self.on_item_copy_setting)
        self.tbl_clip_result.setIndexWidget(self.clip_model.index(row, column_def['copy setting']), btn_copy_setting)

        self.tbl_clip_result.resizeColumnsToContents()
        self.tbl_clip_result.resizeRowsToContents()

    def remove_old_same_result(self, path):
        for r in range(self.clip_model.rowCount()):
            item_at = self.clip_model.item(r, column_def['path'])
            if item_at and item_at.text() == path:
                self.clip_model.removeRow(item_at.row())

    def on_item_open_dir_clicked(self):
        ui_util.open_path_dir(self.get_selected_path(self.sender()))

    def on_item_open_file_clicked(self):
        ui_util.open_path(self.get_selected_path(self.sender()))

    def on_item_del_file_clicked(self):
        row = self.get_table_row(self.sender())
        ok = self.delete_path(self.clip_model.item(row, column_def['path']).text())
        if ok:
            self.clip_model.removeRow(row)

    def on_item_reclip_clicked(self):
        path = self.get_selected_path(self.sender())

        time_form = self.get_time_form(path)
        if time_form is '':
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

    def on_item_copy_setting(self):
        path = self.get_selected_path(self.sender())
        time_form = self.get_time_form(path)

        if time_form is not '':
            self.txt_start_time.setText(time_form[0:6])
            self.txt_end_time.setText(time_form[-6:])

    def get_time_form(self, path):
        clip_name = os.path.splitext(path)[0]

        time_form_len = 6 + 1 + 6  # 000000_000000
        if len(clip_name) < time_form_len + 1:  # at least 1 more than form
            return ''

        time_form = clip_name[-time_form_len:]
        p = re.compile('[0-9]{6}_[0-9]{6}')
        if p.match(clip_name[-time_form_len:]):
            return time_form

        return ''

    def get_table_row(self, widget):
        return self.tbl_clip_result.indexAt(widget.pos()).row()

    def get_selected_path(self, widget):
        row = self.get_table_row(widget)
        return self.clip_model.item(row, column_def['path']).text()

def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)

old_hook = sys.excepthook
sys.excepthook = catch_exceptions


if __name__ == "__main__":
    ui_util.kill_same_script()

    app = QApplication(sys.argv)

    src_file = sys.argv[1] if len(sys.argv) > 1 else ''
    mywindow = MainWindow(None, src_file)
    mywindow.show()
    app.exec_()