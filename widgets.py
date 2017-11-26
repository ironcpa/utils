import os

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class LabeledLineEdit(QWidget):
    return_pressed = pyqtSignal(str)

    def __init__(self, label_text = '', edit_text = ''):
        super().__init__()
        self.init_ui()

        self.label.setText(label_text)
        self.lineedit.setText(str(edit_text))

        self.lineedit.returnPressed.connect(lambda: self.return_pressed.emit(self.lineedit.text()))

    def init_ui(self):
        settingLayout = QHBoxLayout()
        settingLayout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel('cell width')
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


class FileChooser(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

        self.btn_show_dialog.clicked.connect(self.on_show_dialog_clicked)

    def init_ui(self):
        self.txt_path = QLineEdit()
        self.btn_show_dialog = QPushButton('...')

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.txt_path)
        layout.addWidget(self.btn_show_dialog)

        self.setLayout(layout)

    def on_show_dialog_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "select file")
        print(path)
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
        else:
            super().keyPressEvent(e)

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
