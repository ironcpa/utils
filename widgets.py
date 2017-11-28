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
        self.setting_ui.set_font_size(ui_util.load_settings(self, self.app_name, 'font_size', 20))

        self.apply_curr_settings()

    def apply_curr_settings(self):
        """currently only font size"""
        self.setStyleSheet('font: ' + self.setting_ui.font_size() + 'pt')

    def save_settings(self):
        ui_util.save_settings(self, self.app_name, 'pos', self.pos())
        ui_util.save_settings(self, self.app_name, 'size', self.size())
        ui_util.save_settings(self, self.app_name, 'font_size', self.setting_ui.font_size())


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

        self.label = QLabel()
        self.lineedit = QLineEdit()
        settingLayout.addWidget(self.label)
        settingLayout.addWidget(self.lineedit)

        self.setLayout(settingLayout)

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

    def __init__(self, is_dir=False, label='', label_w=0):
        super().__init__()

        self.is_dir = is_dir

        self.init_ui(label, label_w)

        self.btn_show_dialog.clicked.connect(self.on_show_dialog_clicked)

    def init_ui(self, label, label_w):
        lbl_title = None
        if label is not '':
            lbl_title = QLabel(label)
        if label_w > 0:
            lbl_title.setFixedWidth(label_w)
        self.txt_path = QLineEdit()
        self.btn_show_dialog = QPushButton('...')

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


class BaseSearchSettingUI(QWidget, Settings):
    apply_req = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)

        self.setup_ui()

    def show(self):
        super().show()

        self.txt_font_size.setFocus()

    def setup_ui(self):
        self.setGeometry(0, 0, 400, 300)

        self.gridlayout = QGridLayout()
        self.setLayout(self.gridlayout)

        self.buttonlayout = QHBoxLayout()
        self.buttonlayout.setContentsMargins(0, 0, 0, 0)
        self.gridlayout.addLayout(self.buttonlayout, 1, 0)
        self.gridlayout.setColumnStretch(1, 2)

        self.btn_apply = QPushButton('apply')
        self.buttonlayout.addWidget(self.btn_apply)

        self.add_setting_ui('font size')

        self.btn_apply.clicked.connect(self.apply_req)

    def add_setting_ui(self, name):
        self.txt_font_size = QLineEdit()
        self.gridlayout.addWidget(QLabel(name), 0, 0)
        self.gridlayout.addWidget(self.txt_font_size, 0, 1)

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
        self.txt_font_size.setText(str(value))

    def font_size(self):
        return self.txt_font_size.text()


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setup_ui()

    def setup_ui(self):
        self.setLayout(QGridLayout())

        db_setting = BaseSearchSettingUI(self)
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
