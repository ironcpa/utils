# -*-coding:utf-8-*-

import subprocess
import sys

from PyQt5 import uic, QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from send2trash import send2trash

from find_file import *
import gui_ffmpeg

# form_class = uic.loadUiType("./resource/mainwindow.ui")[0]
form_class = uic.loadUiType("C:/__devroot/utils/resource/mainwindow.ui")[0]
column_def = {'checkbox': 0, 'dir': 1, 'open': 2, 'del': 3, 'clip': 4, 'copy name': 5, 'path': 6}


class MainWindow(QMainWindow, form_class):
    search_start_req = pyqtSignal(str, str)
    search_stop_req = pyqtSignal()

    def __init__(self, src_dir):
        super().__init__()
        self.setupUi(self)

        self.thread = QThread()
        self.thread.start()

        self.search_worker = SearchWorker()
        self.search_worker.moveToThread(self.thread)
        self.search_worker.finished.connect(self.on_search_finished)

        self.search_start_req.connect(self.search_worker.search)
        self.search_stop_req.connect(self.search_worker.stop)

        self.btn_search_dir.clicked.connect(self.on_search_dir_clicked)
        self.btn_search_all_drives.clicked.connect(self.on_search_all_drives_clicked)
        self.btn_select_src_dir.clicked.connect(lambda state: self.on_select_dir_clicked(False))
        self.btn_select_tgt_dir.clicked.connect(lambda state: self.on_select_dir_clicked(True))
        # self.btn_stop.clicked.connect(self.on_stop_clicked)       # it'll be called from worker's thread : so can't be stopped
        self.btn_stop.clicked.connect(lambda: self.search_worker.stop())  # called from main thread
        self.btn_clear_result.clicked.connect(self.on_clear_result)
        self.btn_coll_data.clicked.connect(self.on_coll_data_clicked)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.tbl_search_result.setModel(self.model)

        self.load_ini_file()

        if src_dir is not '':
            self.txt_selected_src_dir.setText(src_dir)

    def update_result(self, files):
        self.model.clear()
        for row, f in enumerate(files):
            print(row, f)

            self.model.setItem(self.model.rowCount(), column_def['path'], QtGui.QStandardItem(f))

            chk_box = QCheckBox(self.tbl_search_result)
            chk_box.setText('')
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['checkbox']), chk_box)

            btn_open_dir = QPushButton()
            btn_open_dir.setText('folder')
            btn_open_dir.clicked.connect(self.on_open_dir_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['dir']), btn_open_dir)

            btn_open_file = QPushButton()
            btn_open_file.setText('open')
            btn_open_file.clicked.connect(self.on_open_file_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['open']), btn_open_file)

            btn_delete_file = QPushButton()
            btn_delete_file.setText('delete')
            btn_delete_file.clicked.connect(self.on_del_file_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['del']), btn_delete_file)

            btn_open_ffmpeg = QPushButton()
            btn_open_ffmpeg.setText('clip')
            btn_open_ffmpeg.clicked.connect(self.on_open_ffmpeg_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['clip']), btn_open_ffmpeg)

            btn_copy_name = QPushButton()
            btn_copy_name.setText('copy name')
            btn_copy_name.clicked.connect(self.on_copy_name_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['copy name']), btn_copy_name)

        self.tbl_search_result.resizeColumnsToContents()
        self.tbl_search_result.resizeRowsToContents()

        self.update_ini_file()

    def update_ini_file(self):
        # with open('search.ini', 'w') as f:
        with open('C:/__devroot/utils/search.ini', 'w') as f:
            search_text = self.txt_search_text.text()
            src_dir = self.txt_selected_src_dir.text()
            tgt_dir = self.txt_selected_tgt_dir.text()

            f.write('last_search_text={}\n'.format(search_text))
            f.write('last_src_dir={}\n'.format(src_dir))
            f.write('last_tgt_dir={}\n'.format(tgt_dir))

    def load_ini_file(self):
        # ini_name = 'search.ini'
        ini_name = 'C:/__devroot/utils/search.ini'
        if not os.path.exists(ini_name):
            return

        with open(ini_name, 'r') as f:
            for line in iter(f):
                key_val = line.split('=')
                if key_val[0] == 'last_search_text':
                    self.txt_search_text.setText(key_val[1].rstrip())
                elif key_val[0] == 'last_src_dir':
                    self.txt_selected_src_dir.setText(key_val[1].rstrip())
                elif key_val[0] == 'last_tgt_dir':
                    self.txt_selected_tgt_dir.setText(key_val[1].rstrip())

    def start_search(self, text, src_dir=''):
        self.btn_search_dir.setEnabled(False)
        self.btn_search_all_drives.setEnabled(False)
        # self.search_worker.search(text, src_dir)
        self.search_start_req.emit(text, src_dir)

    def on_search_dir_clicked(self):
        # # target_dir = 'c:\\__devroot\\utils\\sample_data'
        # src_dir = self.txt_selected_src_dir.text()
        # search_text = self.txt_search_text.text()
        # # results = find_file(target_dir, 'juy(.*)012')
        # results = find_file(src_dir, search_text)
        # print(results)
        # self.update_result(results)

        src_dir = self.txt_selected_src_dir.text()
        search_text = self.txt_search_text.text()
        self.start_search(search_text, src_dir)

    def on_search_all_drives_clicked(self):
        # search_text = self.txt_search_text.text()
        # results = find_file_in_all_drives(search_text)
        # print(results)
        # self.update_result(results)

        search_text = self.txt_search_text.text()
        self.start_search(search_text, '')

    def on_search_finished(self):
        self.update_result(self.search_worker.search_results)
        self.btn_search_dir.setEnabled(True)
        self.btn_search_all_drives.setEnabled(True)
        QMessageBox.information(self, 'info', 'complete results={}'.format(len(self.search_worker.search_results)))

    def on_select_dir_clicked(self, is_target):
        path = QFileDialog.getExistingDirectory(self, "select directory")
        print('select file : ', path)
        if path and os.path.isdir(path):
            if is_target:
                self.txt_selected_tgt_dir.setText(path)
            else:
                self.txt_selected_src_dir.setText(path)

    def on_open_dir_clicked(self):
        subprocess.Popen('explorer /select,"{}"'.format(self.get_selected_path(self.sender())))

    def on_open_file_clicked(self):
        subprocess.Popen('explorer "{}"'.format(self.get_selected_path(self.sender())))

    def on_del_file_clicked(self):
        row = self.get_table_row(self.sender())
        ok = QMessageBox.question(self, 'alert', 'Sure to delete?', QMessageBox.Yes, QMessageBox.No)
        if ok == QMessageBox.Yes:
            path = self.tbl_search_result.item(row, column_def['path']).text()
            send2trash(path)

    def on_open_ffmpeg_clicked(self):
        w = gui_ffmpeg.MainWindow(self.get_selected_path(self.sender()))
        w.show()

    def on_copy_name_clicked(self):
        path_col = column_def['path']

        src_path = ''
        tgt_path = self.get_selected_path(self.sender())
        row = self.get_table_row(self.sender())
        src_row = -1
        tgt_item = self.model.item(row, path_col)

        for r in range(self.model.rowCount()):
            chkbox = self.tbl_search_result.indexWidget(self.model.index(r, column_def['checkbox']))
            if r != row and chkbox is not None and chkbox.isChecked():
                src_path = self.model.item(r, path_col).text()
                src_row = r
                break

        if src_path != '' and src_row >= 0:
            if self.delete_path(src_path):
                self.model.removeRow(src_row)
                os.rename(tgt_path, src_path)
                tgt_item.setText(src_path)

    def on_stop_clicked(self):
        print('stop clicked')
        self.search_stop_req.emit()

    def on_clear_result(self):
        self.tbl_search_result.clear()

    def on_coll_data_clicked(self):
        print('collect src dir data recursively and insert to db')

    def get_table_row(self, widget):
        return self.tbl_search_result.indexAt(widget.pos()).row()

    def get_selected_path(self, widget):
        row = self.get_table_row(widget)
        return self.model.item(row, column_def['path']).text()

    def delete_path(self, path):
        reply = QMessageBox.question(self, 'alert', 'Sure to delete?', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return send2trash(path) is None


class SearchWorker(QObject):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.is_working = False
        self.search_text = ''
        self.src_dir = None
        self.search_results = []

    def search(self, text, src_dir=None):
        self.search_text = text
        self.src_dir = src_dir
        self.is_working = True
        self.search_results = []

        # if self.src_dir is None:
        if self.src_dir == '':
            self.search_results = self.find_file_in_all_drives(self.search_text)
        else:
            self.search_results = self.find_file(self.src_dir, self.search_text)

        self.is_working = False
        self.finished.emit()

    def stop(self):
        print('worker.stop')
        self.is_working = False

    def find_file(self, root_folder, file_name, ignore_path=None):
        founds = []
        rex = re.compile(file_name, re.IGNORECASE)
        print(root_folder)
        for root, dirs, files in os.walk(root_folder):
            # for thread stop
            if not self.is_working:
                break

            for extension in ('*.avi', '*.wmv', '*.mp4', '*.mpg', '*.asf', '*.mov', '*.mkv', '*.iso'):
                # for f in files:
                for f in fnmatch.filter(files, extension):
                    result = rex.search(f)
                    if result:
                        full_path = os.path.join(root, f)
                        # ignore path patterns
                        if not (ignore_path is None) and (ignore_path in full_path):
                            print('ignore path ' + ignore_path)
                            continue
                        if r"C:\Users\hjchoi\Documents" in full_path:  # downloading torrent
                            print('ignore ' + full_path)
                            continue
                        if r"C:\Windows\Sys" in full_path:  # why some files found in system folders?
                            print('ignore system ' + full_path)
                            continue
                        if full_path.endswith(SYMLINK_SUFFIX):
                            print('ignore symlink file ' + full_path)
                            continue
                        founds.append(full_path.replace('/', '\\')) # for windows cmd call
                        print(full_path + ", size=" + format(os.path.getsize(full_path) / 1000, ','))
        return founds

    def find_file_in_all_drives(self, file_name, ignore_path=None):
        print('search : ' + file_name)
        all_founds = []
        for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
            # for thread stop
            if not self.is_working:
                break
            all_founds.extend(self.find_file(drive, file_name, ignore_path))
        print('found results : ' + str(len(all_founds)))
        return all_founds


def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)

old_hook = sys.excepthook
sys.excepthook = catch_exceptions

if __name__ == "__main__":
    app = QApplication(sys.argv)

    src_path = ''
    print('arg', sys.argv)
    # if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        src_path = sys.argv[1]
    mywindow = MainWindow(src_path)
    mywindow.show()
    app.exec_()

    # target_dir = 'c:\\__devroot\\utils\\sample_data'
    # command = 'explorer "{}"'.format(target_dir)
    # print(command)
    # subprocess.Popen(command)
    # # subprocess.Popen('explorer "c:\\__devroot"')
