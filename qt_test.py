import sys
import os
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from find_file import *
import subprocess

# form_class = uic.loadUiType("./resource/mainwindow.ui")[0]
form_class = uic.loadUiType("C:/__devroot/utils/resource/mainwindow.ui")[0]
column_def = {'dir': 0, 'open': 1, 'del': 2, 'path': 3}


class MyWindow(QMainWindow, form_class):
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

        self.tbl_search_result.setRowCount(10)
        self.tbl_search_result.setColumnCount(5)
        self.tbl_search_result.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.load_ini_file()

        if src_dir is not '':
            self.txt_selected_src_dir.setText(src_dir)

    def update_result(self, files):
        self.tbl_search_result.clear()
        for row, f in enumerate(files):
            print(row, f)
            btn_open_dir = QPushButton(self.tbl_search_result)
            btn_open_dir.setText('folder({}'.format(row))
            btn_open_dir.clicked.connect(lambda state, x=row: self.on_open_dir_clicked(x))
            self.tbl_search_result.setCellWidget(row, column_def['dir'], btn_open_dir)
            btn_open_file = QPushButton(self.tbl_search_result)
            btn_open_file.setText('open')
            btn_open_file.clicked.connect(lambda state, x=row: self.on_open_file_clicked(x))
            self.tbl_search_result.setCellWidget(row, column_def['open'], btn_open_file)

            btn_delete_file = QPushButton(self.tbl_search_result)
            btn_delete_file.setText('delete')
            self.tbl_search_result.setCellWidget(row, column_def['del'], btn_delete_file)

            item = QTableWidgetItem(f)
            self.tbl_search_result.setItem(row, column_def['path'], item)

        self.tbl_search_result.setRowCount(len(files))
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

    def on_open_dir_clicked(self, row):
        print(row)
        path = self.tbl_search_result.item(row, column_def['path']).text()
        subprocess.Popen('explorer /select,"{}"'.format(path))

    def on_open_file_clicked(self, row):
        path = self.tbl_search_result.item(row, column_def['path']).text()
        subprocess.Popen('explorer "{}"'.format(path))

    def on_stop_clicked(self):
        print('stop clicked')
        self.search_stop_req.emit()


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
                print('is not working')
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
                        founds.append(full_path)
                        print(full_path + ", size=" + format(os.path.getsize(full_path) / 1000, ','))
        return founds

    def find_file_in_all_drives(self, file_name, ignore_path=None):
        print('search : ' + file_name)
        all_founds = []
        for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
            all_founds.extend(self.find_file(drive, file_name, ignore_path))
        print('found results : ' + str(len(all_founds)))
        return all_founds


if __name__ == "__main__":
    app = QApplication(sys.argv)

    src_path = ''
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        src_path = sys.argv[1]
    mywindow = MyWindow(src_path)
    mywindow.show()
    app.exec_()

    # target_dir = 'c:\\__devroot\\utils\\sample_data'
    # command = 'explorer "{}"'.format(target_dir)
    # print(command)
    # subprocess.Popen(command)
    # # subprocess.Popen('explorer "c:\\__devroot"')
