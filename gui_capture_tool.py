# -*-coding:utf-8-*-

import sys
import os
import subprocess

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from widgets import *
import common_util as co
import capture_util
import ui_util
import file_util
import ffmpeg_util

cap_col_def = {'seq':0, 'time': 1, 'duration': 2, 'dir':3, 'open':4, 'del': 5, 'file':6}


class MainWindow(UtilWindow):
    def __init__(self, src_path):
        super().__init__('capture_tool')

        self.flc_src_path.set_path(src_path)

        self.btn_open_src.clicked.connect(self.open_src_path)
        self.btn_open_cap_dir.clicked.connect(self.open_cap_dir)
        self.btn_open_clip_dir.clicked.connect(self.open_clip_dir)

        self.btn_make_clips.clicked.connect(self.make_clips_from_model)
        self.btn_make_sample_clips.clicked.connect(lambda: self.make_clips_from_model('sample_'))
        self.btn_merge_clips.clicked.connect(self.make_direct_merge)
        self.btn_open_clip_tool.clicked.connect(self.open_clip_tool)

        self.btn_del_all.clicked.connect(self.del_all_capture_files)
        self.btn_recapture.clicked.connect(self.recapture_all)

        self.setting_ui.apply_req.connect(self.apply_curr_settings)

        self.cap_model = QtGui.QStandardItemModel(0, len(cap_col_def))
        self.tbl_caps.setModel(self.cap_model)

        self.flc_capture_dir.set_path('c:/__potplayer_capture_for_clip')
        self.flc_clip_dir.set_path('c:/__clips')

        self.load_rel_caps()

        self.txt_sync_time.setText(str(5))

        self.chk_auto_sync.setChecked(True)
        self.chk_auto_sync.stateChanged.connect(self.auto_sync_changed)

        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.load_rel_caps)
        if self.sync_on():
            self.sync_timer.start(self.sync_miliseconds())

        self.load_settings()

    def setup_ui(self):
        self.setGeometry(0, 0, 1024, 760)

        # self.lbl_src_path = QLabel()
        self.flc_src_path = FileChooser(False, 'source file', 200, 60)
        self.btn_open_src = QPushButton('open')
        self.flc_capture_dir = FileChooser(True, 'capture dir', 200, 60)
        self.btn_open_cap_dir = QPushButton('open')
        self.flc_clip_dir = FileChooser(True, 'clip dir', 200, 60)
        self.btn_open_clip_dir = QPushButton('open')
        self.chk_auto_sync = QCheckBox('auto sync')
        self.txt_sync_time = QLineEdit()
        self.txt_sync_time.setFixedWidth(60)
        self.btn_make_clips = QPushButton('make clips')
        self.btn_merge_clips = QPushButton('merge clips')
        self.btn_open_clip_tool = QPushButton('open clip tool')
        self.lbl_total_time = QLabel('total time : 0')
        self.btn_make_sample_clips = QPushButton('make sample clips')
        self.btn_del_all = QPushButton('delete all')
        self.txt_offset_time = LabeledLineEdit('offset time', '', 200, 250)
        self.txt_offset_time.set_input_mask('x00 : 00 : 00')
        self.txt_offset_time.set_text('+00 : 00 : 00')
        self.btn_recapture = QPushButton('recapture')
        self.tbl_caps = QTableView()

        self.setCentralWidget(QWidget())

        base_layout = QVBoxLayout()
        self.centralWidget().setLayout(base_layout)

        file_group = QGridLayout()
        file_group.addWidget(self.flc_src_path, 0, 0)
        file_group.addWidget(self.btn_open_src, 0, 4)
        file_group.addWidget(self.flc_capture_dir, 1, 0)
        file_group.addWidget(self.btn_open_cap_dir, 1, 4)
        file_group.addWidget(self.flc_clip_dir, 2, 0)
        file_group.addWidget(self.btn_open_clip_dir, 2, 4)
        base_layout.addLayout(file_group)

        clip_group = QHBoxLayout()
        clip_group.addWidget(self.btn_make_clips)
        clip_group.addWidget(self.btn_make_sample_clips)
        clip_group.addWidget(self.btn_merge_clips)
        clip_group.addWidget(self.btn_open_clip_tool)
        base_layout.addLayout(clip_group)

        offset_clip_group = QGridLayout()
        offset_clip_group.setColumnStretch(2, 3)
        offset_clip_group.addWidget(self.txt_offset_time, 0, 0)
        offset_clip_group.addWidget(self.btn_recapture, 0, 1)
        base_layout.addLayout(offset_clip_group)

        table_button_group = QGridLayout()
        table_button_group.setColumnStretch(4, 1)
        table_button_group.addWidget(self.lbl_total_time, 0, 0)
        table_button_group.addWidget(self.btn_del_all, 0, 1)
        table_button_group.addWidget(self.chk_auto_sync, 0, 2)
        table_button_group.addWidget(self.txt_sync_time, 0, 3)
        base_layout.addLayout(table_button_group)

        base_layout.addLayout(clip_group)
        base_layout.addWidget(self.tbl_caps)

    def init_setting_ui(self):
        self.setting_ui = BaseSearchSettingUI(self)
        self.setting_ui.hide()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        mod = QApplication.keyboardModifiers()
        if mod == Qt.ControlModifier and key == Qt.Key_C:
            ui_util.copy_to_clipboard(self.src_product_no())
        elif key == Qt.Key_S and mod == Qt.ControlModifier:
            self.setting_ui.show()
        else:
            event.ignore()

    def src_path(self):
        return self.flc_src_path.path()

    def src_product_no(self):
        _, fname = os.path.split(os.path.splitext(self.src_path())[0])
        return file_util.get_product_no(fname)

    def cap_dir(self):
        return self.flc_capture_dir.path()

    def clip_dir(self):
        return self.flc_clip_dir.path()

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
            total_time += co.to_second(du_item.text()) if du_item is not None else 0
        self.lbl_total_time.setText('total time : {}'.format(co.second_to_time_from((total_time))))

    def open_src_path(self):
        ui_util.open_path(self.src_path())

    def open_cap_dir(self):
        ui_util.open_path(self.cap_dir())

    def open_clip_dir(self):
        ui_util.open_path(self.clip_dir())

    def make_clips_from_files(self):
        src_dir, src_file = os.path.split(self.src_path())
        src_name, src_ext = os.path.splitext(src_file)
        cap_ext = '.jpg'

        product_no = file_util.get_product_no(src_name)
        captures = [os.path.join(self.cap_dir(), x) for x in os.listdir(self.cap_dir())
                                    if x.startswith(product_no) and x.endswith(cap_ext)]

        capture_util.create_clips_from_captures(self.src_path(), self.cap_dir(), self.clip_dir(), captures)

    def make_clips_from_model(self, out_prefix=''):
        captures = [self.cap_model.item(r, cap_col_def['file']).data() for r in range(self.cap_model.rowCount())]
        # capture_util.create_clips_from_captures(self.src_path(), self.cap_dir(), self.clip_dir(), captures)
        result = capture_util.future_call(self.src_path(), self.clip_dir(), captures, out_prefix)

        succ, fail = 0, 0
        for r in result:
            if r[1]:
                succ += 1
            else:
                fail += 1
        QMessageBox.information(self, 'result', '{} completed, {} failed'.format(succ, fail))

    # def make_sample_clips_from_model(self):
    #     captures = [self.cap_model.item(r, cap_col_def['file']).data() for r in range(self.cap_model.rowCount())]
    #     capture_util.create_clips_from_captures(self.src_path(), self.cap_dir(), self.clip_dir(), captures, 'sample_')

    def make_direct_merge(self):
        src_filename = os.path.splitext(os.path.basename(self.src_path()))[0]
        clip_paths = ffmpeg_util.get_clip_paths('c:\\__clips\\', src_filename)
        merged_path = ffmpeg_util.merge_all_clips(self.src_path(), clip_paths)
        for p in clip_paths:
            ui_util.delete_path(self, p, True)
        ui_util.delete_path(self, self.src_path(), True)
        QMessageBox.information(self, 'info', 'merge complete : {}'.format(merged_path))

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

        time = co.to_time_form(co.get_time(cap_path))
        time_item = QtGui.QStandardItem(time)
        font = time_item.font()
        font.setPointSize(20)
        time_item.setFont(font)
        self.cap_model.setItem(row, cap_col_def['time'], time_item)

        if row % 2 == 1:
            duration = co.get_duration_in_time_form(self.cap_model.item(row - 1, cap_col_def['time']).text(), time)
            duration_item = QtGui.QStandardItem(str(duration))
            duration_item.setFont(font)
            self.cap_model.setItem(row - 1, cap_col_def['duration'], duration_item)
            self.set_duration_color(co.to_second(duration), duration_item)
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

        offset_str = self.txt_offset_time.text().replace(' ', '')
        offset_sec = co.to_second(offset_str[1:])

        if offset_str[0] != '+' and offset_str[0] != '-':
            QMessageBox.warning(self, 'warning', 'offset seconds need to start with "+" or "-"')
            return

        if offset_str[0] == '-':
            offset_sec *= -1

        ok = QMessageBox.question(self, 'alert', 'Sure to delete all old captures?', QMessageBox.Yes, QMessageBox.No)
        if ok != QMessageBox.Yes:
            return

        for r in range(self.cap_model.rowCount()):
            o_time = self.cap_model.item(r, cap_col_def['time']).text()
            n_time = co.second_to_time_from(co.to_second(o_time) + offset_sec)
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
