# -*-coding:utf-8-*-

import sys
import os
import subprocess

from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import capture_util
import ui_util
import file_util
import ffmpeg_util
import gui_clip_tool

form_class = uic.loadUiType('C:/__devroot/utils/resource/gui_capture_tool.ui')[0]
cap_col_def = {'seq':0, 'time': 1, 'duration': 2, 'dir':3, 'open':4, 'del': 5, 'file':6}


class MainWindow(QMainWindow, form_class):
    def __init__(self, src_path):
        super().__init__()
        self.setupUi(self)

        self.lbl_src_path.setText(src_path)

        self.btn_open_src.clicked.connect(self.open_src_path)
        self.btn_open_cap_dir.clicked.connect(self.open_cap_dir)
        self.btn_open_clip_dir.clicked.connect(self.open_clip_dir)

        self.btn_select_cap_dir.clicked.connect(lambda state: self.open_dir_dialog(self.txt_selected_cap_dir))
        self.btn_select_clip_dir.clicked.connect(lambda state: self.open_dir_dialog(self.txt_selected_cap_dir))

        self.btn_make_clips.clicked.connect(self.make_clips)
        self.btn_merge.clicked.connect(self.make_direct_merge)
        self.btn_open_clip_tool.clicked.connect(self.open_clip_tool)

        self.btn_del_all.clicked.connect(self.del_all_capture_files)
        self.btn_recapture.clicked.connect(self.recapture_all)

        self.cap_model = QtGui.QStandardItemModel(0, len(cap_col_def))
        self.tbl_caps.setModel(self.cap_model)

        #init setting
        self.txt_selected_cap_dir.setText('c:/__potplayer_capture_for_clip')
        self.txt_selected_clip_dir.setText('c:/__clips')

        self.load_rel_caps()

        self.txt_sync_time.setText(str(5))

        self.chk_auto_sync.setChecked(True)
        self.chk_auto_sync.stateChanged.connect(self.auto_sync_changed)

        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.load_rel_caps)
        if self.sync_on():
            self.sync_timer.start(self.sync_miliseconds())

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier and key == Qt.Key_C:
            ui_util.copy_to_clipboard(self.src_product_no())
        else:
            event.ignore()

    def src_path(self):
        return self.lbl_src_path.text()

    def src_product_no(self):
        _, fname = os.path.split(os.path.splitext(self.src_path())[0])
        return file_util.get_product_no(fname)

    def cap_dir(self):
        return self.txt_selected_cap_dir.text()

    def clip_dir(self):
        return self.txt_selected_clip_dir.text()

    def sync_on(self):
        return self.chk_auto_sync.isChecked()

    def sync_miliseconds(self):
        return int(self.txt_sync_time.text()) * 1000

    def open_dir_dialog(self, widget):
        ui_util.open_dir_dialog(self, widget)

    def get_table_row(self, widget):
        return self.tbl_caps.indexAt(widget.pos()).row()

    def load_rel_caps(self):
        self.cap_model.clear()

        # fname으로 찾는 옵션 고려
        rel_cap_paths = [os.path.join(self.cap_dir(), x) for x in os.listdir(self.cap_dir()) if x.startswith(self.src_product_no())]
        for c in rel_cap_paths:
            self.add_cap_result(c)

        self.show_total_time()

    def show_total_time(self):
        total_time = 0
        for r in range(self.cap_model.rowCount()):
            du_item = self.cap_model.item(r, cap_col_def['duration'])
            total_time += capture_util.to_second(du_item.text()) if du_item is not None else 0
        self.lbl_total_time.setText('total time : {}'.format(capture_util.second_to_time_from((total_time))))

    def open_src_path(self):
        ui_util.open_path(self.src_path())

    def open_cap_dir(self):
        ui_util.open_path(self.cap_dir())

    def open_clip_dir(self):
        ui_util.open_path(self.clip_dir())

    def make_clips(self):
        capture_util.create_clips_from_captures(self.src_path(), self.cap_dir(), self.clip_dir(), False)

    def make_direct_merge(self):
        src_filename = os.path.splitext(os.path.basename(self.src_path()))[0]
        merged_name = ffmpeg_util.merge_all_clips(self.src_path(), ffmpeg_util.get_clip_paths('c:\\__clips\\', src_filename))
        QMessageBox.information(self, 'job', 'merge complete : {}'.format(merged_name))

    def open_clip_tool(self):
        command = 'pythonw c:/__devroot/utils/gui_clip_tool.py "{}"'.format(self.src_path())
        subprocess.Popen(command)

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
        self.cap_model.setItem(row, cap_col_def['time'], time_item)

        if row % 2 == 1:
            duration = capture_util.get_duration_in_time_form(self.cap_model.item(row-1, cap_col_def['time']).text(), time)
            duration_item = QtGui.QStandardItem(str(duration))
            duration_item.setFont(font)
            self.cap_model.setItem(row - 1, cap_col_def['duration'], duration_item)
            self.set_duration_color(capture_util.to_second(duration), duration_item)
        else:
            seq_item = QtGui.QStandardItem(str(row // 2 + 1))
            seq_item.setFont(font)
            self.cap_model.setItem(row, cap_col_def['seq'], seq_item)

        file_item = QtGui.QStandardItem(os.path.basename(cap_path))
        file_item.setData(cap_path)
        file_item.setFont(font)
        self.cap_model.setItem(row, cap_col_def['file'], file_item)

        btn_font = font
        btn_font.setPointSize(14)
        ui_util.add_button_on_tableview(self.tbl_caps, row, cap_col_def['dir'], 'dir', btn_font, 60, self.on_item_dir_file_clicked)
        ui_util.add_button_on_tableview(self.tbl_caps, row, cap_col_def['open'], 'open', btn_font, 70, self.on_item_open_file_clicked)
        ui_util.add_button_on_tableview(self.tbl_caps, row, cap_col_def['del'], 'del', btn_font, 60, self.on_item_del_file_clicked)

        self.tbl_caps.resizeColumnsToContents()
        self.tbl_caps.resizeRowsToContents()
        self.tbl_caps.scrollToBottom()

    def set_duration_color(self, play_time, item):
        if play_time > 10 * 60:
            item.setBackground(QtGui.QBrush(Qt.red))
            item.setForeground(QtGui.QBrush(Qt.white))
        elif play_time > 5 * 60:
            item.setBackground(QtGui.QBrush(Qt.green))
        elif play_time > 2 * 60:
            item.setBackground(QtGui.QBrush(Qt.yellow))

    def del_all_capture_files(self):
        ok = QMessageBox.question(self, 'alert', 'Sure to delete all?', QMessageBox.Yes, QMessageBox.No)
        if ok == QMessageBox.Yes:
            for r in range(self.cap_model.rowCount()):
                path = self.cap_model.item(r, cap_col_def['file']).data()
                ui_util.send2trash(path)
        self.load_rel_caps()

    def recapture_all(self):
        if self.cap_model.rowCount() == 0:
            return

        o_start = capture_util.to_second(self.cap_model.item(0, cap_col_def['time']).text())
        n_start = capture_util.to_second(self.txt_new_start_time.text().replace(' ', ''))
        offset_sec = n_start - o_start

        if o_start + offset_sec < 0:
            QMessageBox.warning(self, 'warning', 'start time is under zero')
            return

        ok = QMessageBox.question(self, 'alert', 'Sure to delete all old captures?', QMessageBox.Yes, QMessageBox.No)
        if ok != QMessageBox.Yes:
            return

        for r in range(self.cap_model.rowCount()):
            o_time = self.cap_model.item(r, cap_col_def['time']).text()
            n_time = capture_util.second_to_time_from(capture_util.to_second(o_time) + offset_sec)
            ui_util.send2trash(self.cap_model.item(r, cap_col_def['file']).data())
            ffmpeg_util.capture(self.src_path(), n_time, 'recap', self.cap_dir())

        self.load_rel_caps()

    def get_path_on_widget(self, widget):
        return self.cap_model.item(self.get_table_row(widget), cap_col_def['file']).data()

    def on_item_dir_file_clicked(self):
        ui_util.open_path_dir(self.get_path_on_widget(self.sender()))

    def on_item_open_file_clicked(self):
        ui_util.open_path(self.get_path_on_widget(self.sender()))

    def on_item_del_file_clicked(self):
        row = self.get_table_row(self.sender())
        if ui_util.delete_path(self, self.get_path_on_widget(self.sender())):
            self.cap_model.removeRow(row)


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == "__main__":
    ui_util.kill_same_script()

    app = QApplication(sys.argv)

    src_path = sys.argv[1]
    window = MainWindow(src_path)
    window.show()
    app.exec_()
