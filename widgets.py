import os
import sys
from abc import ABC, abstractmethod

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import ui_util


class UtilWindow(QMainWindow):
    def __init__(self, app_name, parent = None):
        super().__init__(parent)

        self.app_name = app_name
        self.setting_ui = None

        self.setup_ui()
        self.init_setting_ui()

    @abstractmethod
    def setup_ui(self):
        pass

    @abstractmethod
    def init_setting_ui(self):
        pass

    def closeEvent(self, e: QtGui.QCloseEvent):
        self.save_settings()

        e.accept()

    def load_settings(self):
        self.move(ui_util.load_settings(self, self.app_name, 'pos', QPoint(0, 0)))
        self.resize(ui_util.load_settings(self, self.app_name, 'size', QSize(1280, 768)))
        self.setting_ui.set_font_size(ui_util.load_settings(self, self.app_name, 'font size', 20))

        self.apply_curr_settings()

    def apply_curr_settings(self):
        """currently only font size"""
        self.setStyleSheet('font: ' + self.setting_ui.font_size() + 'pt')

    def save_settings(self):
        ui_util.save_settings(self, self.app_name, 'pos', self.pos())
        ui_util.save_settings(self, self.app_name, 'size', self.size())
        ui_util.save_settings(self, self.app_name, 'font size', self.setting_ui.font_size())


class TabledUtilWindow(UtilWindow):
    def __init__(self, app_name, parent=None):
        self._default_table = None
        super().__init__(app_name, parent)

    @abstractmethod
    def setup_ui(self):
        pass

    def set_default_table(self, tableview):
        self._default_table = tableview

    def init_setting_ui(self):
        self.setting_ui = TableBaseSettingUI(self)
        self.setting_ui.hide()

    def apply_curr_settings(self):
        super().apply_curr_settings()
        self._default_table.setStyleSheet('font: ' + self.setting_ui.table_font_size() + 'pt')

    def load_settings(self):
        self.setting_ui.set_table_font_size(ui_util.load_settings(self, self.app_name, 'table font size', 20))
        super().load_settings()

    def save_settings(self):
        super().save_settings()
        ui_util.save_settings(self, self.app_name, 'table font size', self.setting_ui.table_font_size())


class LabeledLineEdit(QWidget):
    return_pressed = pyqtSignal(str)

    def __init__(self, label_text='', edit_text='', label_w=0, txt_w=0):
        super().__init__()

        self.init_ui()

        self.label.setText(label_text)
        if label_w > 0:
            self.label.setFixedWidth(label_w)
        if txt_w > 0:
            self.lineedit.setFixedWidth(txt_w)
        self.lineedit.setText(str(edit_text))

        self.lineedit.returnPressed.connect(lambda: self.return_pressed.emit(self.lineedit.text()))

    def init_ui(self):
        settingLayout = QHBoxLayout()
        settingLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(settingLayout)

        self.label = QLabel()
        self.lineedit = QLineEdit()
        settingLayout.addWidget(self.label)
        settingLayout.addWidget(self.lineedit)

    def text(self):
        return self.lineedit.text()

    def set_text(self, text):
        self.lineedit.setText(str(text))

    def setFocus(self):
        super(LabeledLineEdit, self).setFocus()
        self.lineedit.setFocus()

    def select_all(self):
        self.lineedit.selectAll()

    def set_input_mask(self, mask):
        self.lineedit.setInputMask(mask)


class TitledLabel(QWidget):
    def __init__(self, title='', text='', title_w=0, text_w=0):
        super().__init__()

        self.init_ui()

        self.lbl_title.setText(title)
        if title_w > 0:
            self.lbl_title.setFixedWidth(title_w)
        if text_w > 0:
            self.lbl_text.setFixedWidth(text_w)
        self.lbl_text.setText(str(text))

    def init_ui(self):
        settingLayout = QHBoxLayout()
        settingLayout.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel()
        self.lbl_text = QLabel()
        settingLayout.addWidget(self.lbl_title)
        settingLayout.addWidget(self.lbl_text)

        self.setLayout(settingLayout)

    def text(self):
        return self.lbl_text.text()

    def set_text(self, text):
        self.lbl_text.setText(str(text))


class FileChooser(QWidget):
    clicked = pyqtSignal()

    def __init__(self, is_dir=False, label='', label_w=0, button_w=0):
        super().__init__()

        self.is_dir = is_dir

        self.init_ui(label, label_w, button_w)

        self.btn_show_dialog.clicked.connect(self.on_show_dialog_clicked)

    def init_ui(self, label, label_w, button_w):
        lbl_title = None
        if label is not '':
            lbl_title = QLabel(label)
        self.txt_path = QLineEdit()
        self.btn_show_dialog = QPushButton('...')
        if label_w > 0:
            lbl_title.setFixedWidth(label_w)
        if button_w > 0:
            self.btn_show_dialog.setFixedWidth(button_w)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        if lbl_title:
            layout.addWidget(lbl_title)
        layout.addWidget(self.txt_path)
        layout.addWidget(self.btn_show_dialog)

        self.setLayout(layout)

    def on_show_dialog_clicked(self):
        if self.is_dir:
            path = QFileDialog.getExistingDirectory(self, "select directory")
            if path and os.path.isdir(path):
                self.txt_path.setText(path)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "select file")
            if path and os.path.exists(path):
                self.txt_path.setText(path)

    def set_path(self, path):
        self.txt_path.setText(path)

    def path(self):
        return self.txt_path.text()


class SearchViewDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

        self.color_curr_highlight = Qt.green

    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QModelIndex):
        if index.row() == self.parent().currentIndex().row():
            painter.fillRect(option.rect, self.color_curr_highlight)
        elif self.parent().indexWidget(index.model().index(index.row(), 10)).isChecked():
            painter.fillRect(option.rect, Qt.red)

        super(SearchViewDelegate, self).paint(painter, option, index)


class SearchView(QTableView):
    def __init__(self):
        super().__init__()
        self.setItemDelegate(SearchViewDelegate(self))

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        key = e.key()
        mod = e.modifiers()
        if key == Qt.Key_C and mod == Qt.ControlModifier:
            e.ignore()
        else:
            super(SearchView, self).keyPressEvent(e)

    def currentChanged(self, current: QModelIndex, previous: QModelIndex):
        for c in range(self.model().columnCount()):
            self.update(self.model().index(previous.row(), c))
        for c in range(self.model().columnCount()):
            self.update(self.model().index(current.row(), c))
        super().currentChanged(current, previous)


class NameEditor(QWidget):
    edit_finished = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.input_name = ''

        self.setup_ui()
        self.init_signal_slots()

    def setup_ui(self):
        self.setGeometry(0, 0, 800, 100)

        self.setStyleSheet('background-color: cyan; font:40pt')

        layout = QHBoxLayout()

        self.txt_name = QLineEdit(self.input_name)
        layout.addWidget(self.txt_name)

        self.setLayout(layout)

    def init_signal_slots(self):
        self.txt_name.returnPressed.connect(lambda: self.edit_finished.emit(self.txt_name.text()))

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        key = e.key()
        if key == Qt.Key_Return:
            e.accept()
        elif key == Qt.Key_Escape:
            self.hide()
            self.closed.emit()

    def open_editor(self, name):
        self.set_name(name)
        self.set_position()
        self.txt_name.setFocus()
        self.show()

    def set_position(self):
        self.setFixedWidth(self.parent().width() - 20)
        self.move((self.parent().width() - self.width()) // 2, (self.parent().height() - self.height()) // 2)

    def set_name(self, name):
        self.input_name = name
        self.txt_name.setText(name)


class Settings():
    @abstractmethod
    def set_font_size(self, value):
        pass

    @abstractmethod
    def font_size(self):
        pass


class BaseSettingUI(QWidget, Settings):
    apply_req = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)

        self.setup_ui()

    def show(self):
        super().show()

        self.default_setting_lineedit.setFocus()

    def setup_ui(self):
        self.setGeometry(0, 0, 400, 300)

        base_layout = QVBoxLayout()
        self.setLayout(base_layout)

        self.setting_group = QGridLayout()
        base_layout.addLayout(self.setting_group)

        self.buttonlayout = QHBoxLayout()
        self.buttonlayout.setContentsMargins(0, 0, 0, 0)
        base_layout.addLayout(self.buttonlayout)

        self.btn_apply = QPushButton('apply')
        self.buttonlayout.addWidget(self.btn_apply)

        self.setting_lineedits = {}
        self.add_setting_ui('font size')
        self.default_setting_lineedit = self.setting_lineedits['font size']

        self.btn_apply.clicked.connect(self.apply_req)

    def add_setting_ui(self, name, default=0):
        lineedit = QLineEdit(str(default))
        row = len(self.setting_lineedits)
        self.setting_lineedits[name] = lineedit
        self.setting_group.addWidget(QLabel(name), row, 0)
        self.setting_group.addWidget(lineedit, row, 1)

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        key = e.key()
        if key == Qt.Key_Return:
            self.apply_req.emit()
        elif key == Qt.Key_Escape:
            self.hide()
            self.closed.emit()

    def paintEvent(self, e: QtGui.QPaintEvent):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), Qt.lightGray)
        painter.end()
        super().paintEvent(e)

    def set_font_size(self, value):
        self.setting_lineedits['font size'].setText(str(value))

    def font_size(self):
        return self.setting_lineedits['font size'].text()


class TableBaseSettingUI(BaseSettingUI):
    def __init__(self, parent):
        super().__init__(parent)

    def setup_ui(self):
        super().setup_ui()

        self.add_setting_ui('table font size', 10)

    def set_table_font_size(self, value):
        self.setting_lineedits['table font size'].setText(str(value))

    def table_font_size(self):
        return self.setting_lineedits['table font size'].text()


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setup_ui()

    def setup_ui(self):
        self.setLayout(QGridLayout())

        db_setting = BaseSettingUI(self)
        self.layout().addWidget(db_setting, 0, 0)


def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)


if __name__ == '__main__':
    old_hook = sys.excepthook
    sys.excepthook = catch_exceptions

    app = QApplication(sys.argv)

    test_window = TestWindow()
    test_window.show()
    app.exec_()
