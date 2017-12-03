# -*-coding:utf-8-*-

import sys
import win32api
import subprocess

from PyQt5 import uic, QtGui, QtCore

import ui_util
import defines
import file_util
import common_util as cu
from db_util import DB
from widgets import *
from defines import ColumnDef, Product, FileInfo, DBException

column_def = ColumnDef(['no', 'disk', 'size', 'date', 'rate', 'desc', 'open', 'dir', 'tool', 'del file', 'chk', 'copy', 'del db', 'location'],
                       {'chk': ''})


class MainWindow(TabledUtilWindow):
    def __init__(self, search_text = None):
        super().__init__('db_search')

        self.search_stack = []

        self.btn_search.clicked.connect(self.search_db)
        self.btn_filter.clicked.connect(self.filter_result)
        self.btn_search_dup.clicked.connect(lambda: self.search_db(True))
        self.name_editor.edit_finished.connect(self.update_file_name_n_synk_db)
        self.name_editor.closed.connect(lambda: self.tbl_result.setFocus())
        self.setting_ui.apply_req.connect(self.apply_curr_settings)

        self.model = QtGui.QStandardItemModel(0, column_def.size())
        self.model.setHorizontalHeaderLabels(column_def.header_titles)
        self.tbl_result.setModel(self.model)

        self.product_filter_model = QtCore.QSortFilterProxyModel()
        self.product_filter_model.setSourceModel(self.model)

        self.db = DB()

        self.load_settings()

        if search_text:
            self.txt_search.set_text(search_text)
            self.search_db()

    def setup_ui(self):
        super().setup_ui()

        self.setGeometry(0, 0, 1000, 600)

        self.setCentralWidget(QWidget())
        base_layout = QVBoxLayout()
        self.centralWidget().setLayout(base_layout)

        all_control_group = QVBoxLayout()

        main_control_group = QHBoxLayout()
        self.txt_search = LabeledLineEdit('search text')
        self.chk_is_and_condition = QCheckBox('and')
        self.btn_search = QPushButton('start')
        self.btn_filter = QPushButton('filter')
        self.btn_search_dup = QPushButton('show dup result')
        main_control_group.addWidget(self.txt_search)
        main_control_group.addWidget(self.chk_is_and_condition)
        main_control_group.addWidget(self.btn_search)
        main_control_group.addWidget(self.btn_filter)
        main_control_group.addWidget(self.btn_search_dup)
        all_control_group.addLayout(main_control_group)

        filter_group = QGridLayout()
        filter_group.setColumnStretch(0, 4)
        self.txt_limit_filter = LabeledLineEdit('limit by')
        filter_group.addWidget(self.txt_limit_filter, 0, 0)
        self.txt_limit_count = LabeledLineEdit('count', 200, 120, 120)
        filter_group.addWidget(self.txt_limit_count, 0, 1)
        self.txt_order = LabeledLineEdit('order by')
        filter_group.addWidget(self.txt_order, 1, 0, 1, 2)
        all_control_group.addLayout(filter_group)

        base_layout.addLayout(all_control_group)

        self.tbl_result = SearchView()
        self.set_default_table(self.tbl_result)
        self.tbl_result.setSortingEnabled(True)
        base_layout.addWidget(self.tbl_result)

        self.name_editor = NameEditor(self)
        self.name_editor.hide()

    def init_setting_ui(self):
        super().init_setting_ui()
        self.setting_ui.closed.connect(lambda: self.tbl_result.setFocus())

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        mod = event.modifiers()
        if key == Qt.Key_Return:
            if mod == Qt.ControlModifier:
                self.search_db()
            elif mod == Qt.ShiftModifier:
                location_item = self.model.item(self.tbl_result.currentIndex().row(), column_def['location'])
                name_only = os.path.splitext(os.path.basename(location_item.text()))[0] if location_item else ''
                self.name_editor.open_editor(name_only)
            elif mod == Qt.ControlModifier | Qt.ShiftModifier:
                self.open_curr_row_dir(self.get_del_button_at(self.tbl_result.currentIndex().row()))
            else:
                self.open_curr_row_file(self.get_del_button_at(self.tbl_result.currentIndex().row()))
        elif key == Qt.Key_Tab and mod == Qt.ControlModifier:
            self.close()
        elif key == Qt.Key_Escape:
            ui_util.focus_to_text(self.txt_search)
        elif key == Qt.Key_D and mod == Qt.ControlModifier:
            self.open_curr_row_db_search()
        elif key == Qt.Key_F and mod == Qt.ControlModifier:
            self.open_curr_row_file_search()
        elif key == Qt.Key_Z and mod == Qt.ControlModifier:
            self.open_curr_row_capture_tool(self.get_del_button_at(self.tbl_result.currentIndex().row()))
        elif key == Qt.Key_Delete:
            self.del_curr_row_file(self.get_del_button_at(self.tbl_result.currentIndex().row()))
        elif key == Qt.Key_Left and mod == Qt.ControlModifier:
            self.set_prev_search_text()
        elif key == Qt.Key_C and mod == Qt.ControlModifier:
            self.turn_on_curr_checkbox()
            ui_util.copy_to_clipboard(self.get_pno_on_curr_row())
        elif key == Qt.Key_N and mod == Qt.ControlModifier:
            self.copy_curr_row_file_name_from_checked_row(self.get_widget_at(self.tbl_result.currentIndex().row(), column_def['chk']))
        elif key == Qt.Key_S and mod == Qt.ControlModifier:
            self.setting_ui.show()
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

    def get_data_on_table_widget(self, widget, col):
        row = self.get_table_row(widget)
        return self.model.item(row, col).data()

    def get_drive(self, disk_label):
        for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
            if disk_label == win32api.GetVolumeInformation(drive)[0]:
                return drive
        return None

    def is_disk_online(self, disk):
        return self.get_drive(disk) is not None

    def search_db(self, is_find_dub=False):
        self.model.removeRows(0, self.model.rowCount())

        products = []
        if is_find_dub:
            products = self.db.search_dup_list()
        else:
            search_tuple = (self.get_search_text(),
                            self.txt_limit_filter.text(),
                            self.txt_limit_count.text(),
                            self.txt_order.text(),
                            self.is_and_checked())
            self.search_stack.append(search_tuple)
            try:
                products = self.db.search(*search_tuple)
            except DBException as e:
                QMessageBox.warning(self, 'db', e.msg)

        for p in products:
            row = self.model.rowCount()
            is_disk_online = self.is_disk_online(p.disk_name)

            # self.model.setItem(row, column_def['no'], QtGui.QStandardItem(p.product_no[:15] + '...' if len(p.product_no) > 10 else p.product_no))
            no_item = QtGui.QStandardItem(p.product_no)
            no_item.setData(p)
            self.model.setItem(row, column_def['no'], no_item)
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

            ui_util.add_checkbox_on_tableview(self.tbl_result, row, column_def['chk'], '', 20, self.on_checkbox_changed)
            if is_disk_online:
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['open'], 'open', None, 60, self.on_result_open_file_clciekd)
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['dir'], 'dir', None, 60, self.on_result_open_dir_clciekd)
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['tool'], 'tool', None, 60, self.on_result_open_tool_clciekd)
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['del file'], 'del file', None, 100, self.on_result_del_file_clicked)
                ui_util.add_button_on_tableview(self.tbl_result, row, column_def['copy'], 'copy', None, 100, self.on_result_copy_name_clicked)
            ui_util.add_button_on_tableview(self.tbl_result, row, column_def['del db'], 'del db', None, 80, self.on_result_delete_row_clicked)

        self.arrange_table()

        self.tbl_result.setModel(self.model)
        self.tbl_result.setFocus()

    def arrange_table(self):
        self.tbl_result.resizeColumnsToContents()
        self.tbl_result.resizeRowsToContents()
        self.tbl_result.setColumnWidth(0, 150)
        self.tbl_result.setColumnWidth(column_def['desc'], 400)
        self.tbl_result.setColumnWidth(column_def['chk'], 20)
        # self.tbl_result.scrollToBottom()

    def filter_result(self):
        """only by p_no"""
        self.product_filter_model.setFilterKeyColumn(column_def['no'])
        self.product_filter_model.setFilterRegExp(self.get_search_text())
        self.tbl_result.setModel(self.product_filter_model)

    def get_path_on_row(self, widget):
        disk_label = self.get_text_on_table_widget(widget, column_def['disk'])
        curr_drive = self.get_drive(disk_label)
        if curr_drive is None:
            return

        path = curr_drive[0] + ':' + os.path.splitdrive(self.get_text_on_table_widget(widget, column_def['location']))[1]
        return path

    def get_path_on_curr_row(self):
        return self.model.item(self.tbl_result.currentIndex().row(), column_def['location']).text()

    def get_pno_on_row(self, widget):
        return self.get_text_on_table_widget(widget, column_def['no'])

    def get_pno_on_curr_row(self):
        return self.model.item(self.tbl_result.currentIndex().row(), column_def['no']).text()

    def on_result_open_file_clciekd(self):
        self.open_curr_row_file(self.sender())

    def on_result_open_dir_clciekd(self):
        self.open_curr_row_dir(self.sender())

    def on_result_open_tool_clciekd(self):
        self.open_curr_row_capture_tool(self.sender())

    def on_result_del_file_clicked(self):
        self.del_curr_row_file(self.sender())

    def on_checkbox_changed(self, state):
        if state:
            self.turn_off_other_checkboxes(self.sender())

    def on_result_copy_name_clicked(self):
        self.copy_curr_row_file_name_from_checked_row(self.sender())

    def on_result_delete_row_clicked(self):
        pass

    def get_del_button_at(self, row):
        return self.tbl_result.indexWidget(self.model.index(row, column_def['del file']))

    def get_widget_at(self, row, col):
        return self.tbl_result.indexWidget(self.model.index(row, col))

    def open_curr_row_file(self, widget):
        if not widget:
            return
        ui_util.open_path(self.get_path_on_row(widget))
        self.db.add_view_history(self.get_pno_on_row(widget))

    def open_curr_row_dir(self, widget):
        if not widget:
            return
        ui_util.open_path_dir(self.get_path_on_row(widget))

    def open_curr_row_capture_tool(self, widget):
        command = 'pythonw c:/__devroot/utils/gui_capture_tool.py "{}"'.format(self.get_path_on_row(widget))
        subprocess.Popen(command)

    def open_curr_row_db_search(self):
        command = 'pythonw c:/__devroot/utils/gui_db_search.py "{}"'.format(self.get_pno_on_curr_row())
        subprocess.Popen(command)

    def open_curr_row_file_search(self):
        '''not completed'''
        command = 'pythonw c:/__devroot/utils/gui_file_search.py "file" "{}"'.format(self.get_path_on_curr_row())
        subprocess.Popen(command)

    def del_curr_row_file(self, widget):
        if not widget:
            return
        s = self
        if ui_util.delete_path(s, s.get_path_on_row(widget)):
            if s.db.delete_product(s.get_data_on_table_widget(widget, column_def['no'])) == 1:
                s.model.removeRow(s.get_table_row(widget))

    def copy_curr_row_file_name_from_checked_row(self, widget):
        if not widget:
            return

        copy_src_path = ''
        copy_src_widget  = None
        for r in range(self.model.rowCount()):
            checkbox = self.tbl_result.indexWidget(self.model.index(r, column_def['chk']))
            if checkbox.isChecked():
                copy_src_path = self.model.item(r, column_def['location']).text()
                copy_src_widget = checkbox
                QMessageBox.information(self, 'debug', str(copy_src_path))
                break
        if not copy_src_path or copy_src_path == '':
            return

        target_path = self.get_path_on_row(widget)
        target_name = os.path.splitext(os.path.basename(target_path))[0]
        new_target_path = target_path.replace(target_name, os.path.splitext(os.path.basename(copy_src_path))[0])
        print('c_path : ' + copy_src_path)
        print('o_path : ' + target_path)
        print('n_path : ' + new_target_path)
        if copy_src_path != new_target_path and os.path.exists(new_target_path):
            QMessageBox.warning(self, 'failed', 'file already exists')
            return
        if not os.path.exists(target_path):
            QMessageBox.warning(self, 'failed', 'source or target path not exist. \nyou may run db collect and search again')
            return

        if os.path.exists(copy_src_path):
            self.del_curr_row_file(copy_src_widget)
        os.rename(target_path, new_target_path)

        '''db update'''
        cur_row = self.tbl_result.currentIndex().row()
        self.db.delete_by_path(copy_src_path)
        self.update_path_on_db_n_model(cur_row, new_target_path)

        QMessageBox.information(self, 'copied', 'copied :\n{}\n<- {}'.format(new_target_path, target_path))

    def turn_off_other_checkboxes(self, widget):
        for r in range(self.model.rowCount()):
            checkbox = self.tbl_result.indexWidget(self.model.index(r, column_def['chk']))
            if checkbox != widget and checkbox.isChecked():
                checkbox.setChecked(False)
        self.model.layoutChanged.emit()

    def turn_on_curr_checkbox(self):
        r = self.tbl_result.currentIndex().row()
        self.tbl_result.indexWidget(self.model.index(r, column_def['chk'])).setChecked(True)

    def set_prev_search_text(self):
        search_tuple = self.search_stack.pop()
        self.txt_search.set_text(search_tuple[0])
        self.chk_is_and_condition.setChecked(search_tuple[1])

        # self.search_db()

    def update_file_name_n_synk_db(self, name):
        cur_row = self.tbl_result.currentIndex().row()

        # on current
        target_path = self.model.item(cur_row, column_def['location']).text()
        o_dir = os.path.dirname(target_path)
        o_name, o_ext = os.path.splitext(os.path.basename(target_path))
        new_target_path = os.path.join(o_dir, name + o_ext)

        os.rename(target_path, new_target_path)

        # # update curr item
        # cur_product = self.model.item(cur_row, column_def['no']).data()
        # # update db
        # new_product = cu.conv_path_to_product(new_target_path, cur_product.id)
        # self.update_row(cur_row, new_product)
        # self.db.update_product(new_product)
        self.update_path_on_db_n_model(cur_row, new_target_path)

        QMessageBox.information(self, 'renamed', 'renamed :\n{}\n<- {}'.format(new_target_path, target_path))
        self.name_editor.hide()
        self.tbl_result.setFocus()

    def update_path_on_db_n_model(self, cur_row, new_path):
        # update curr item
        cur_product = self.model.item(cur_row, column_def['no']).data()
        # update db
        new_product = cu.conv_path_to_product(new_path, cur_product.id)
        self.update_row(cur_row, new_product)
        self.db.update_product(new_product)

    def update_row(self, row, product):
        self.model.item(row, column_def['no']).setText(product.product_no)
        self.model.item(row, column_def['no']).setData(product)
        self.model.item(row, column_def['disk']).setText(product.disk_name)
        self.model.item(row, column_def['rate']).setText(product.rate)
        self.model.item(row, column_def['desc']).setText(product.desc)
        self.model.item(row, column_def['location']).setText(product.location)
        self.model.item(row, column_def['size']).setText(product.size)
        self.model.item(row, column_def['date']).setText(product.cdate)


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions

if __name__ == '__main__':
    app = QApplication(sys.argv)

    search_text = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(search_text)
    window.show()
    app.exec_()