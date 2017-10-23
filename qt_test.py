import sys
import os
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from find_file import *
import subprocess

form_class = uic.loadUiType("./resource/mainwindow.ui")[0]
column_def = {'dir' : 0, 'open' : 1, 'del' : 2, 'path' : 3 }


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_search.clicked.connect(self.on_search_clicked)
        self.btn_select_src_dir.clicked.connect(lambda state: self.on_select_dir_clicked(False))
        self.btn_select_tgt_dir.clicked.connect(lambda state: self.on_select_dir_clicked(True))

        self.tbl_search_result.setRowCount(5)
        self.tbl_search_result.setColumnCount(5)
        self.tbl_search_result.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def update_result(self, files):
        for row, f in enumerate(files):
            btn_open_dir = QPushButton(self.tbl_search_result)
            btn_open_dir.setText('folder'.format(row))
            btn_open_dir.clicked.connect(lambda state, x=row: self.on_open_dir_clicked(x))
            self.tbl_search_result.setCellWidget(row, column_def['dir'], btn_open_dir)
            btn_open_file = QPushButton(self.tbl_search_result)
            btn_open_file.setText('open'.format(row))
            btn_open_file.clicked.connect(lambda state, x=row: self.on_open_file_clicked(x))
            self.tbl_search_result.setCellWidget(row, column_def['open'], btn_open_file)

            btn_delete_file = QPushButton(self.tbl_search_result)
            btn_delete_file.setText('delete')
            self.tbl_search_result.setCellWidget(row, column_def['del'], btn_delete_file)

            item = QTableWidgetItem(f)
            self.tbl_search_result.setItem(row, column_def['path'], item)

        self.tbl_search_result.resizeColumnsToContents()
        self.tbl_search_result.resizeRowsToContents()

    def on_search_clicked(self):
        target_dir = 'c:\\__devroot\\utils\\sample_data'
        results = find_file(target_dir, 'juy(.*)012')
        print(results)
        self.update_result(results)

    def on_select_dir_clicked(self, is_target):
        path = QFileDialog.getExistingDirectory(self, "select directory")
        print('select file : ', path)
        if path and os.path.isdir(path):
            if is_target:
                self.txt_selected_tgt_dir.setText(path)
            else:
                self.txt_selected_src_dir.setText(path)

    def on_open_dir_clicked(self, row):
        print(row)
        path = self.tbl_search_result.item(row, column_def['path']).text()
        subprocess.Popen('explorer /select,"{}"'.format(path))

    def on_open_file_clicked(self, row):
        path = self.tbl_search_result.item(row, column_def['path']).text()
        subprocess.Popen('explorer "{}"'.format(path))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()

    # target_dir = 'c:\\__devroot\\utils\\sample_data'
    # command = 'explorer "{}"'.format(target_dir)
    # print(command)
    # subprocess.Popen(command)
    # # subprocess.Popen('explorer "c:\\__devroot"')
