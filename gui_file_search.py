# -*-coding:utf-8-*-

import common_util as cu
import ui_util
import db_util
from find_file import *
from db_util import DB
from widgets import *

column_def = {'checkbox': 0, 'dir': 1, 'open': 2, 'del': 3, 'capture': 4, 'clip': 5, 'copy name': 6, 'size': 7, 'path': 8}


class MainWindow(UtilWindow):
    search_req = pyqtSignal(str, str)
    collect_req = pyqtSignal(str, str)
    stop_req = pyqtSignal()

    def __init__(self, src_dir, src_file):
        super().__init__('file_search')

        self.db = db_util.DB()

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
        self.btn_stop.clicked.connect(lambda: self.search_worker.on_stop_req())  # called from main thread
        self.btn_clear_result.clicked.connect(self.on_clear_result)
        self.btn_collect_db.clicked.connect(self.on_coll_data_clicked)

        self.setting_ui.apply_req.connect(self.apply_curr_settings)

        self.model = QtGui.QStandardItemModel(0, len(column_def))
        self.tbl_search_result.setModel(self.model)

        self.load_ini_file()

        if src_dir:
            self.flc_src_dir.set_path(src_dir)

        self.db = DB()

        self.load_settings()

        if src_file:
            base = os.path.basename(src_file)
            product_no = file_util.get_product_no(os.path.splitext(base)[0])
            drive = src_file[:2] + os.path.sep
            self.txt_search_text.setText(product_no)
            self.flc_src_dir.set_path(drive)
            self.start_search(product_no, drive)

    def setup_ui(self):
        self.setGeometry(0, 0, 1024, 760)

        root_layout = QVBoxLayout()
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(root_layout)

        self.txt_search_text = LabeledLineEdit('search text', '', 200)
        self.flc_src_dir = FileChooser(True, 'source dir', 200)
        self.flc_tgt_dir = FileChooser(True, 'target dir', 200)

        self.btn_search_dir = QPushButton('search dir')
        self.btn_search_all_drives = QPushButton('search all drives')
        self.btn_collect_db = QPushButton('collect db')

        self.tbl_search_result = QTableView()

        self.btn_stop = QPushButton('stop')
        self.btn_clear_result = QPushButton('clear result')

        buttongrid = QGridLayout()
        buttongrid.addWidget(self.txt_search_text, 0, 0)
        buttongrid.addWidget(self.flc_src_dir, 1, 0)

        file_button_group = QHBoxLayout()
        file_button_group.addWidget(self.btn_search_dir)
        file_button_group.addWidget(self.btn_search_all_drives)
        file_button_group.addWidget(self.btn_collect_db)
        buttongrid.addLayout(file_button_group, 2, 0)

        tbl_button_group = QHBoxLayout()
        tbl_button_group.addWidget(self.btn_stop)
        tbl_button_group.addWidget(self.btn_clear_result)

        root_layout.addLayout(buttongrid)
        root_layout.addWidget(self.tbl_search_result)
        root_layout.addLayout(tbl_button_group)

    def init_setting_ui(self):
        self.setting_ui = BaseSearchSettingUI(self)
        self.setting_ui.hide()

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()

        if key == Qt.Key_Return:
            self.on_search_dir_clicked()
        elif key == Qt.Key_Escape:
            ui_util.focus_to_text(self.txt_search_text)
        elif key == Qt.Key_S and mod == Qt.ControlModifier:
            self.setting_ui.show()
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
            src_dir = self.flc_src_dir.path()
            tgt_dir = self.flc_tgt_dir.path()

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
                    self.txt_search_text.set_text(key_val[1].rstrip())
                elif key_val[0] == 'last_src_dir':
                    self.flc_src_dir.set_path(key_val[1].rstrip())
                elif key_val[0] == 'last_tgt_dir':
                    self.flc_tgt_dir.set_path(key_val[1].rstrip())

    def start_search(self, text, src_dir=''):
        self.enable_req_buttons(False)
        self.search_req.emit(text, src_dir)

    def get_search_re_text(self):
        src_text = self.txt_search_text.text()
        return '(.*)'.join([x for x in src_text.split()])

    def on_search_dir_clicked(self):
        src_dir = self.flc_src_dir.path()
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
        self.db.insert_product_w_fileinfos(file_infos)
        self.enable_req_buttons(True)
        QMessageBox.information(self, 'info', 'collect finished : {}'.format(len(file_infos)))

    def on_open_dir_clicked(self):
        subprocess.Popen('explorer /select,"{}"'.format(self.get_selected_path(self.sender())))

    def on_open_file_clicked(self):
        subprocess.Popen('explorer "{}"'.format(self.get_selected_path(self.sender())))

    def on_del_file_clicked(self):
        row = self.get_table_row(self.sender())
        path = self.model.item(row, column_def['path']).text()
        if ui_util.delete_path(self, path):
            self.model.removeRow(row)
            self.db.delete_by_path(path)

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
            if ui_util.delete_path(src_path):
                self.model.removeRow(src_row)

                tgt_dir = os.path.dirname(tgt_path)
                new_tgt_path = os.path.join(tgt_dir, os.path.basename(src_path))

                os.rename(tgt_path, new_tgt_path)

                tgt_item.setText(new_tgt_path)
                self.release_all_checkbox()

                self.db.delete_by_path(src_path)
                '''todo: update product fields on db'''

    def release_all_checkbox(self):
        for r in range(self.model.rowCount()):
            self.tbl_search_result.indexWidget(self.model.index(r, column_def['checkbox'])).setChecked(False)

    def on_stop_clicked(self):
        self.stop_req.emit()

    def on_clear_result(self):
        self.model.clear()

    def on_coll_data_clicked(self):
        self.enable_req_buttons(False)

        src_dir = self.flc_src_dir.path()
        self.collect_req.emit('.', src_dir)

    def get_table_row(self, widget):
        return self.tbl_search_result.indexAt(widget.pos()).row()

    def get_selected_path(self, widget):
        row = self.get_table_row(widget)
        return self.model.item(row, column_def['path']).text()


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
            for extension in ('*.avi', '*.wmv', '*.mp4', '*.mpg', '*.asf', '*.mov', '*.mkv', '*.iso'):
                # for f in files:
                for f in fnmatch.filter(files, extension):
                    if not self.is_working:
                        return founds

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
                        founds.append(FileInfo(full_path.replace('/', '\\'), file_util.get_file_size(full_path), file_util.get_ctime(full_path)))  # for windows cmd call
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


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == "__main__":
    ui_util.kill_same_script()

    app = QApplication(sys.argv)

    src_type = sys.argv[1]
    src_dir, src_file = None, None
    if src_type == 'file':
        src_file = sys.argv[2]
    elif src_type == 'dir':
        src_dir = sys.argv[2]
    # src_path = file_util.get_cmd_path_arg(sys.argv[1]) if len(sys.argv) > 1 else ''
    mywindow = MainWindow(src_dir, src_file)
    mywindow.show()
    app.exec_()

    # target_dir = 'c:\\__devroot\\utils\\sample_data'
    # command = 'explorer "{}"'.format(target_dir)
    # print(command)
    # subprocess.Popen(command)
    # # subprocess.Popen('explorer "c:\\__devroot"')
