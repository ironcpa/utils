# -*-coding:utf-8-*-

import os
import sys
import win32api
import subprocess

from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

import ui_util
from db_util import DB

form_class = uic.loadUiType("C:/__devroot/utils/resource/gui_db_search.ui")[0]
column_def = {'no': 0, 'disk': 1, 'size': 2, 'date': 3, 'rate': 4, 'desc': 5, 'open': 6, 'dir': 7, 'tool':8 ,'del file': 9, 'del db': 10, 'location': 11}


class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.btn_search.clicked.connect(self.search_db)
        self.btn_filter.clicked.connect(self.filter_result)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.model.setHorizontalHeaderLabels([*column_def])
        self.tbl_result.setModel(self.model)

        self.product_filter_model = QtCore.QSortFilterProxyModel()
        self.product_filter_model.setSourceModel(self.model)
        self.product_filter_model.setFilterKeyColumn(column_def['no'])

        self.db = DB()

        ui_util.load_settings(self, 'db_search')

    def closeEvent(self, e: QtGui.QCloseEvent):
        ui_util.save_settings(self, 'db_search')

        e.accept()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        if key == Qt.Key_Return:
            self.search_db()
        elif key == Qt.Key_Escape:
            ui_util.focus_to_text(self.txt_search)
        else:
            event.ignore()

    def get_search_text(self):
        return self.txt_search.text()

    def is_and_checked(self):
        return self.chk_is_and_condition.isChecked()

    def get_table_row(self, widget):
        return self.tbl_result.indexAt(widget.pos()).row()

    def get_text_on_table_widget(self, widget, col):
        row = self.get_table_row(widget)
        return self.model.item(row, col).text()

    def get_drive(self, disk_label):
        for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
            if disk_label == win32api.GetVolumeInformation(drive)[0]:
                return drive
        return None

    def is_disk_online(self, disk):
        return self.get_drive(disk) is not None

    def search_db(self):
        self.model.removeRows(0, self.model.rowCount())

        products = self.db.search(self.get_search_text(), self.is_and_checked())

        for p in products:
            row = self.model.rowCount()
            is_disk_online = self.is_disk_online(p.disk_name)

            # self.model.setItem(row, column_def['no'], QtGui.QStandardItem(p.product_no[:15] + '...' if len(p.product_no) > 10 else p.product_no))
            self.model.setItem(row, column_def['no'], QtGui.QStandardItem(p.product_no))
            disk_item = QtGui.QStandardItem(p.disk_name)
            if is_disk_online:
                disk_item.setBackground(QtGui.QBrush(Qt.yellow))
            self.model.setItem(row, column_def['disk'], disk_item)
            self.model.setItem(row, column_def['rate'], QtGui.QStandardItem(p.rate))
            self.model.setItem(row, column_def['desc'], QtGui.QStandardItem(p.desc))
            self.model.setItem(row, column_def['location'], QtGui.QStandardItem(p.location))
            size_item = QtGui.QStandardItem(p.size)
            size_item.setTextAlignment(Qt.AlignRight)
            self.model.setItem(row, column_def['size'], size_item)
            self.model.setItem(row, column_def['date'], QtGui.QStandardItem(p.cdate))

            if is_disk_online:
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['open'], 'open', None, 60, self.on_result_open_file_clciekd)
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['dir'], 'dir', None, 60, self.on_result_open_dir_clciekd)
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['tool'], 'tool', None, 60, self.on_result_open_tool_clciekd)
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['del file'], 'del file', None, 100, self.on_result_del_file_clicked)
            ui_util.add_button_on_tableview(self.tbl_result, row, column_def['del db'], 'del db', None, 80, self.on_result_delete_row_clicked)

        self.tbl_result.resizeColumnsToContents()
        self.tbl_result.resizeRowsToContents()
        self.tbl_result.setColumnWidth(0, 150)
        # self.tbl_result.scrollToBottom()

    def filter_result(self):
        self.product_filter_model.setFilterRegExp(self.get_search_text())

    def get_path_on_row(self, widget):
        disk_label = self.get_text_on_table_widget(widget, column_def['disk'])
        curr_drive = self.get_drive(disk_label)
        if curr_drive is None:
            return

        path = curr_drive[0] + ':' + os.path.splitdrive(self.get_text_on_table_widget(widget, column_def['location']))[1]
        return path

    def on_result_open_file_clciekd(self):
        ui_util.open_path(self.get_path_on_row(self.sender()))

    def on_result_open_dir_clciekd(self):
        ui_util.open_path_dir(self.get_path_on_row(self.sender()))

    def on_result_open_tool_clciekd(self):
        command = 'pythonw c:/__devroot/utils/gui_capture_tool.py "{}"'.format(self.get_path_on_row(self.sender()))
        subprocess.Popen(command)

    def on_result_del_file_clicked(self):
        ui_util.delete_path(self, self.get_path_on_row(self.sender()))

    def on_result_delete_row_clicked(self):
        pass


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec_()