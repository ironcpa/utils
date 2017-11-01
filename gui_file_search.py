# -*-coding:utf-8-*-

import subprocess
import sys
import win32api

from PyQt5 import uic, QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from send2trash import send2trash

import ui_util
from find_file import *
import gui_clip_tool
from db_util import DB, Product

# form_class = uic.loadUiType("./resource/gui_file_search.ui")[0]
form_class = uic.loadUiType("C:/__devroot/utils/resource/gui_file_search.ui")[0]
column_def = {'checkbox': 0, 'dir': 1, 'open': 2, 'del': 3, 'capture': 4, 'clip': 5, 'copy name': 6, 'size': 7, 'path': 8}


class MainWindow(QMainWindow, form_class):
    search_req = pyqtSignal(str, str)
    collect_req = pyqtSignal(str, str)
    stop_req = pyqtSignal()

    def __init__(self, src_dir):
        super().__init__()
        self.setupUi(self)

        self.thread = QThread()
        self.thread.start()

        self.search_worker = SearchWorker()
        self.search_worker.moveToThread(self.thread)
        self.search_worker.search_finished.connect(self.on_search_finished)
        self.search_worker.collect_finished.connect(self.on_collect_finished)

        self.search_req.connect(self.search_worker.on_search_req)
        self.collect_req.connect(self.search_worker.on_collect_req);
        self.stop_req.connect(self.search_worker.on_stop_req)

        self.btn_search_dir.clicked.connect(self.on_search_dir_clicked)
        self.btn_search_all_drives.clicked.connect(self.on_search_all_drives_clicked)
        self.btn_select_src_dir.clicked.connect(lambda state: self.on_select_dir_clicked(False))
        self.btn_select_tgt_dir.clicked.connect(lambda state: self.on_select_dir_clicked(True))
        # self.btn_stop.clicked.connect(self.on_stop_clicked)       # it'll be called from worker's thread : so can't be stopped
        self.btn_stop.clicked.connect(lambda: self.search_worker.on_stop_req())  # called from main thread
        self.btn_clear_result.clicked.connect(self.on_clear_result)
        self.btn_coll_data.clicked.connect(self.on_coll_data_clicked)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.tbl_search_result.setModel(self.model)

        self.load_ini_file()

        if src_dir is not '':
            self.txt_selected_src_dir.setText(src_dir)

        self.db = DB()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return:
            self.on_search_dir_clicked()
        elif key == Qt.Key_Escape:
            ui_util.focus_to_txt(self.txt_search_text)
        else:
            event.ignore()

    def update_result(self, file_infos):
        self.model.clear()
        for fi in file_infos:
            path = fi.path
            size = fi.size
            row = self.model.rowCount()

            size_item = QtGui.QStandardItem(size)
            size_item.setTextAlignment(Qt.AlignRight)
            self.model.setItem(row, column_def['size'], size_item)
            self.model.setItem(row, column_def['path'], QtGui.QStandardItem(path))

            chk_box = QCheckBox(self.tbl_search_result)
            chk_box.setText('')
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['checkbox']), chk_box)

            btn_w = 60

            btn_open_dir = QPushButton()
            btn_open_dir.setText('folder')
            btn_open_dir.setFixedWidth(btn_w)
            btn_open_dir.clicked.connect(self.on_open_dir_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['dir']), btn_open_dir)

            btn_open_file = QPushButton()
            btn_open_file.setText('open')
            btn_open_file.setFixedWidth(btn_w)
            btn_open_file.clicked.connect(self.on_open_file_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['open']), btn_open_file)

            btn_delete_file = QPushButton()
            btn_delete_file.setText('delete')
            btn_delete_file.setFixedWidth(btn_w)
            btn_delete_file.clicked.connect(self.on_del_file_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['del']), btn_delete_file)

            btn_open_capture_tool = QPushButton()
            btn_open_capture_tool.setText('capture')
            btn_open_capture_tool.setFixedWidth(btn_w + 20)
            btn_open_capture_tool.clicked.connect(self.on_open_capture_tool_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['capture']), btn_open_capture_tool)

            btn_open_clip_tool = QPushButton()
            btn_open_clip_tool.setText('clip')
            btn_open_clip_tool.setFixedWidth(btn_w)
            btn_open_clip_tool.clicked.connect(self.on_open_clip_tool_clicked)
            self.tbl_search_result.setIndexWidget(self.model.index(row, column_def['clip']), btn_open_clip_tool)

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
        self.enable_req_buttons(False)
        self.search_req.emit(text, src_dir)

    def get_search_re_text(self):
        src_text = self.txt_search_text.text()
        return '(.*)'.join([x for x in src_text.split()])

    def on_search_dir_clicked(self):
        src_dir = self.txt_selected_src_dir.text()
        self.start_search(self.get_search_re_text(), src_dir)

    def on_search_all_drives_clicked(self):
        self.start_search(self.get_search_re_text(), '')

    def enable_req_buttons(self, t):
        self.btn_search_dir.setEnabled(t)
        self.btn_search_all_drives.setEnabled(t)

    def on_search_finished(self):
        self.update_result(self.search_worker.search_results)
        self.enable_req_buttons(True)
        QMessageBox.information(self, 'info', 'complete results={}'.format(len(self.search_worker.search_results)))

    def on_collect_finished(self):
        file_infos = self.search_worker.search_results
        for fi in file_infos:
            # prod_id, actor, desc, rating, location, tags = self.parse_filename(f)
            parsed = self.parse_filename(fi)
            # for p in parsed:
            # print('p_id={}, desc={}, rate={}, disk={}, loc={}'.format(*parsed))
            self.db.update_product(parsed)
        self.enable_req_buttons(True)

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
        path = self.model.item(row, column_def['path']).text()
        if ui_util.delete_path(self, path):
            self.model.removeRow(row)

    def on_open_capture_tool_clicked(self):
        command = 'pythonw c:/__devroot/utils/gui_capture_tool.py "{}"'.format(self.get_selected_path(self.sender()))
        # this is not call on pycharm debug mode : don't know why, os.command(command) is fine but has pyqt -> pyqt problem
        subprocess.Popen(command)

    def on_open_clip_tool_clicked(self):
        # command = 'pythonw gui_clip_tool.py "{}"'.format(self.get_selected_path(self.sender()))
        # os.system(command)
        command = 'pythonw c:/__devroot/utils/gui_clip_tool.py "{}"'.format(self.get_selected_path(self.sender()))
        subprocess.Popen(command)

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

                tgt_dir = os.path.dirname(tgt_path)
                new_tgt_path = os.path.join(tgt_dir, os.path.basename(src_path))

                os.rename(tgt_path, new_tgt_path)

                tgt_item.setText(new_tgt_path)
                self.release_all_checkbox()

    def release_all_checkbox(self):
        for r in range(self.model.rowCount()):
            self.tbl_search_result.indexWidget(self.model.index(r, column_def['checkbox'])).setChecked(False)

    def on_stop_clicked(self):
        self.stop_req.emit()

    def on_clear_result(self):
        self.model.clear()

    def on_coll_data_clicked(self):
        self.enable_req_buttons(False)

        src_dir = self.txt_selected_src_dir.text()
        self.collect_req.emit('.', src_dir)

    def parse_filename(self, file_info):
        path = file_info.path

        drive_volume = win32api.GetVolumeInformation(os.path.splitdrive(path)[0] + '/')
        filename = os.path.basename(path)

        name_only = os.path.splitext(filename)[0]
        tokens = name_only.split('_')

        product_no = tokens[0]
        rate = tokens[-1] if tokens[-1] != product_no and tokens[-1].startswith('xx') else ''
        desc = ' '.join(tokens[1:]).replace(rate, '') if len(tokens) > 1 else ''
        disk_name = drive_volume[0]
        location = path

        return Product(product_no, desc, rate, disk_name, location, file_info.size)

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
    search_finished = pyqtSignal()
    collect_finished = pyqtSignal()

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

    def on_search_req(self, text, src_dir=None):
        self.search(text, src_dir)
        self.search_finished.emit()

    def on_collect_req(self, text, src_dir=None):
        self.search(text, src_dir)
        self.collect_finished.emit()

    def on_stop_req(self):
        print('worker.stop')
        self.is_working = False

    def find_file(self, root_folder, file_name, ignore_path=None):
        founds = []
        rex = re.compile(file_name, re.IGNORECASE)
        # print(root_folder)
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
                        founds.append(FileInfo(full_path.replace('/', '\\'), format(os.path.getsize(full_path) / 1000, ',')))  # for windows cmd call
                        # print(full_path + ", size=" + format(os.path.getsize(full_path) / 1000, ','))
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
