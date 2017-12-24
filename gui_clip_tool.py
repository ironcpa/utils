# -*-coding:utf-8-*-

import subprocess
import sys
import os
import re
import asyncio
import functools

from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from send2trash import send2trash

from defines import ColumnDef
from widgets import *
import common_util as cu
import ui_util
import file_util
import ffmpeg_util

column_def = ColumnDef(['chk', 'dir', 'open', 'del', 'reclip', 'copy setting', 'size', 'path'],
                       {'chk': ''})


class MainWindow(TabledUtilWindow):
    def __init__(self, parent, src_path):
        super().__init__('clip_tool', parent)

        self.flc_src_file.set_path(src_path)

        src_dir, src_name, src_ext = cu.split_path(src_path)
        clip_name = 'clip_' + src_name
        self.txt_clip_name.set_text('c:\\__clips\\' + clip_name + '_{}_{}' + src_ext)
        self.txt_merge_name.set_text(ffmpeg_util.merge_file_path(src_path))

        self.btn_encode.clicked.connect(self.on_encode_clicked)
        self.btn_encode_0_9_start_seconds.clicked.connect(self.on_encode_0_9_seconds_clicked)
        self.btn_merge_all_clips.clicked.connect(self.merge_all_clips)
        self.btn_dir_src.clicked.connect(self.on_dir_src_clicked)
        self.btn_open_src.clicked.connect(self.on_open_src_clicked)
        self.btn_del_src.clicked.connect(self.on_del_src_clicked)
        self.btn_to_start_time.clicked.connect(self.copy_end_to_start_time)
        self.btn_to_end_time.clicked.connect(self.copy_start_to_end_time)
        self.btn_reload.clicked.connect(self.load_rel_clips)
        self.btn_del_all.clicked.connect(self.delete_all_clips)

        self.setting_ui.apply_req.connect(self.apply_curr_settings)

        self.clip_model = QtGui.QStandardItemModel(0, len(column_def))
        self.clip_model.setHorizontalHeaderLabels(column_def.header_titles)
        self.tbl_clip_result.setModel(self.clip_model)

        self.load_settings()

        self.load_rel_clips()

    def setup_ui(self):
        self.setGeometry(0, 0, 1280, 768)

        col1_w = 150

        self.flc_src_file = FileChooser(False, 'file name')
        self.btn_reload = QPushButton('reload')
        self.btn_dir_src = QPushButton('src dir')
        self.btn_open_src = QPushButton('src open')
        self.btn_del_src = QPushButton('src delete')
        self.txt_start_time = FFMPEGTimeLineEdit('start', '', col1_w, col1_w)
        self.txt_start_time.set_input_mask('00 : 00 : 00')
        self.btn_to_end_time = QPushButton('E')
        self.chk_include_samples = QCheckBox('include samples')
        self.txt_end_time = FFMPEGTimeLineEdit('end', '', col1_w, col1_w)
        self.txt_end_time.set_input_mask('00 : 00 : 00')
        self.btn_to_start_time = QPushButton('S')
        self.txt_clip_name = LabeledLineEdit('clip name', '', col1_w)
        self.txt_merge_name = LabeledLineEdit('merge name', '', col1_w)
        self.btn_encode = QPushButton('encode')
        self.btn_encode_0_9_start_seconds = QPushButton('encode(0-9sec)')
        self.btn_merge_all_clips = QPushButton('merge all')
        self.chk_reencode = QCheckBox('re-encode?')
        self.lbl_clip_total_size = TitledLabel('total size:')
        self.btn_del_all = QPushButton('del all clips')
        self.tbl_clip_result = SearchView()
        self.tbl_clip_result.setSortingEnabled(True)
        self.set_default_table(self.tbl_clip_result)

        self.setCentralWidget(QWidget())
        base_layout = QVBoxLayout()
        self.centralWidget().setLayout(base_layout)

        base_layout.addWidget(self.flc_src_file)

        file_button_group = QHBoxLayout()
        file_button_group.addWidget(self.btn_dir_src)
        file_button_group.addWidget(self.btn_open_src)
        file_button_group.addWidget(self.btn_del_src)
        file_button_group.addWidget(self.btn_reload)
        file_button_group.addWidget(self.chk_include_samples)
        base_layout.addLayout(file_button_group)

        start_end_group = QGridLayout()
        start_end_group.setColumnStretch(5, 4)
        start_end_group.addWidget(self.txt_start_time, 0, 0)
        start_end_group.addWidget(self.btn_to_end_time, 0, 2)
        start_end_group.addWidget(self.txt_end_time, 1, 0)
        start_end_group.addWidget(self.btn_to_start_time, 1, 2)
        base_layout.addLayout(start_end_group)

        base_layout.addWidget(self.txt_clip_name)
        base_layout.addWidget(self.txt_merge_name)

        encode_group = QHBoxLayout()
        encode_group.addWidget(self.btn_encode)
        encode_group.addWidget(self.btn_encode_0_9_start_seconds)
        encode_group.addWidget(self.btn_merge_all_clips)
        encode_group.addWidget(self.chk_reencode)
        base_layout.addLayout(encode_group)

        table_button_group = QGridLayout()
        table_button_group.setColumnStretch(2, 3)
        table_button_group.addWidget(self.lbl_clip_total_size, 0, 0, 1, 2)
        table_button_group.addWidget(self.btn_del_all, 0, 5)
        base_layout.addLayout(table_button_group)

        base_layout.addWidget(self.tbl_clip_result)

    def src_path(self):
        return self.flc_src_file.path()

    def src_product_no(self):
        _, fname = os.path.split(os.path.splitext(self.src_path())[0])
        return file_util.get_product_no(fname)

    def load_rel_clips(self):
        dir, fname = os.path.split(os.path.splitext(self.src_path())[0])
        dir = '.' if dir == '' else dir
        clip_dir = 'c:\\__clips\\'
        pno = file_util.get_product_no(fname)

        self.clip_model.removeRows(0, self.clip_model.rowCount())
        for i in ffmpeg_util.get_clip_infos(clip_dir, pno, self.chk_include_samples.isChecked()):
            self.add_clip_result(i[0], i[1])
        self.show_total_clip_size()

    def delete_all_clips(self):
        ok = QMessageBox.question(self, 'alert', 'Sure to delete all?', QMessageBox.Yes, QMessageBox.No)
        if ok == QMessageBox.Yes:
            for r in range(self.clip_model.rowCount()):
                path = self.clip_model.item(r, column_def['path']).text()
                ui_util.send2trash(path)
        self.load_rel_clips()

    def show_total_clip_size(self):
        total = 0
        for r in range(self.clip_model.rowCount()):
            s = self.clip_model.item(r, column_def['size']).text()
            if len(s) > 0:
                total += int(s.split('.')[0].replace(',', ''))
        self.lbl_clip_total_size.set_text(format(total, ','))

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        mod = QApplication.keyboardModifiers()
        if key == Qt.Key_Return:
            self.on_encode_clicked()
        elif mod == Qt.ControlModifier and key == Qt.Key_C:
            ui_util.copy_to_clipboard(self.src_product_no())
        elif key == Qt.Key_S and mod == Qt.ControlModifier:
            self.setting_ui.show()
        else:
            event.ignore()

    def on_encode_clicked(self):
        start_time = self.txt_start_time.ffmpeg_time()
        end_time = self.txt_end_time.ffmpeg_time()
        clip_file_form = self.txt_clip_name.text()
        out_clip_path = clip_file_form.format(start_time, end_time)

        ok, err = self.create_clip(start_time, end_time, out_clip_path)
        if ok:
            QMessageBox.information(self, 'info', 'encoding complete')
            # self.close()
        else:
            print(err)
            QMessageBox.critical(self, 'error', 'encoding failed\n{}'.format(err))

    def on_encode_0_9_seconds_clicked(self):
        start_time = self.txt_start_time.ffmpeg_time()
        end_time = self.txt_end_time.ffmpeg_time()
        if len(start_time) < 6:
            QMessageBox.critical(self, 'error', 'no start time')
            return

        clip_file_form = self.txt_clip_name.text()
        loop = asyncio.new_event_loop()
        funcs = [self.async_create_clip(loop, start_time[0:-1], end_time, clip_file_form.format(start_time[0:-1] + str(s), end_time)) for s in range(10)]
        result = cu.asyncio_gatter_call(loop, funcs)
        ui_util.show_create_clip_result(self, result)

    def merge_all_clips(self):
        model_clip_paths = [self.clip_model.item(r, column_def['path']).text() for r in range(self.clip_model.rowCount())
                            if self.tbl_clip_result.indexWidget(self.clip_model.index(r, column_def['chk'])).isChecked()]
        merged_path = ffmpeg_util.merge_all_clips(self.txt_merge_name.text(), model_clip_paths)
        if self.is_condenced_merge_condition() \
                and QMessageBox.Yes == QMessageBox.question(self, 'alert', 'delete source & clips?', QMessageBox.Yes, QMessageBox.No):
            for p in model_clip_paths:
                ui_util.delete_path(self, p, True)
            ui_util.delete_path(self, self.src_path(), True)

        btn_open_merged = QPushButton('Open')
        btn_open_merged.clicked.connect(functools.partial(ui_util.open_path, merged_path))
        result = ui_util.show_messagebox('info', 'merge complete : {}'.format(merged_path), btn_open_merged)

    def is_condenced_merge_condition(self):
        src_dir, src_name, src_ext = cu.split_path(self.src_path())
        src_path_wo_ext = src_dir + os.path.sep + src_name
        return self.txt_merge_name.text().startswith(src_path_wo_ext) and '_con' in self.txt_merge_name.text()

    def on_dir_src_clicked(self):
        if os.path.exists(self.src_path()):
            ui_util.open_path_dir(self.src_path())
        else:
            # try to open dir
            src_dir, _, _ = cu.split_path(self.src_path())
            ui_util.open_path_dir(src_dir)

    def on_open_src_clicked(self):
        ui_util.open_path(self.src_path())

    def on_del_src_clicked(self):
        ui_util.delete_path(self, self.src_path())

    def copy_end_to_start_time(self):
        self.txt_start_time.set_text(self.txt_end_time.text())

    def copy_start_to_end_time(self):
        self.txt_end_time.set_text(self.txt_start_time.text())

    def create_clip(self, start_time, end_time, out_clip_path, is_async_call=False):
        src_path = self.flc_src_file.path()
        is_reencode = self.chk_reencode.isChecked()
        command = ffmpeg_util.create_clip_command(src_path, start_time, end_time, out_clip_path, is_reencode)
        if is_async_call:
            subprocess.Popen(command)
            return True, None
        else:
            try:
                subprocess.check_output(command, stderr=subprocess.STDOUT)
                self.remove_old_same_result(out_clip_path)
                self.add_clip_result(out_clip_path, file_util.get_file_size(out_clip_path))
                self.show_total_clip_size()
                return True, None
            except subprocess.CalledProcessError as e:
                return False, e

    async def async_create_clip(self, async_loop, start_time, end_time, out_clip_path):
        src_path = self.flc_src_file.path()
        is_reencode = self.chk_reencode.isChecked()
        command = ffmpeg_util.create_clip_command(src_path, start_time, end_time, out_clip_path, is_reencode)
        try:
            # subprocess.check_output(command, stderr=subprocess.STDOUT)
            await async_loop.run_in_executor(None, subprocess.check_output, command)
            self.remove_old_same_result(out_clip_path)
            self.add_clip_result(out_clip_path, file_util.get_file_size(out_clip_path))
            self.show_total_clip_size()
            return True, None
        except subprocess.CalledProcessError as e:
            return False, e

    def add_clip_result(self, path, size):
        row = self.clip_model.rowCount()

        size_item = QtGui.QStandardItem(size)
        size_item.setTextAlignment(Qt.AlignRight)
        self.clip_model.setItem(row, column_def['size'], size_item)
        self.clip_model.setItem(row, column_def['path'], QtGui.QStandardItem(path))

        ui_util.add_checkbox_on_tableview(self.tbl_clip_result, row, column_def['chk'], '', 20, None, True)
        ui_util.add_button_on_tableview(self.tbl_clip_result, row, column_def['dir'], 'dir', None, 0, self.on_item_open_dir_clicked)
        ui_util.add_button_on_tableview(self.tbl_clip_result, row, column_def['open'], 'open', None, 0, self.on_item_open_file_clicked)
        ui_util.add_button_on_tableview(self.tbl_clip_result, row, column_def['del'], 'del', None, 0, self.on_item_del_file_clicked)
        ui_util.add_button_on_tableview(self.tbl_clip_result, row, column_def['reclip'], 'reclip', None, 0, self.on_item_reclip_clicked)
        ui_util.add_button_on_tableview(self.tbl_clip_result, row, column_def['copy setting'], 'copy setting', None, 0, self.on_item_copy_setting)

        self.arrange_table()

    def arrange_table(self):
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
        if ui_util.delete_path(self, self.clip_model.item(row, column_def['path']).text()):
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

        ok, err = self.create_clip(start_time, end_time, out_clip_path)
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
            self.txt_start_time.set_text(time_form[0:6])
            self.txt_end_time.set_text(time_form[-6:])

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


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == "__main__":
    ui_util.kill_same_script()

    app = QApplication(sys.argv)

    src_file = sys.argv[1] if len(sys.argv) > 1 else ''
    mywindow = MainWindow(None, src_file)
    mywindow.show()
    app.exec_()