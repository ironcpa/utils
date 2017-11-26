import os
import sys
import psutil
import subprocess

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QApplication, QPushButton, QCheckBox
from PyQt5.QtCore import QSettings, QPoint
from send2trash import send2trash

import file_util


def open_path_dir(path):
    cmd = 'explorer /select,"{}"'.format(path.replace('/', '\\'))
    print(cmd)
    subprocess.Popen(cmd)


def open_path(path):
    cmd = 'explorer "{}"'.format(path.replace('/', '\\'))
    print(cmd)
    subprocess.Popen(cmd)


def delete_path(widget, path, yes=False):
    ok = QMessageBox.No
    if yes:
        ok = QMessageBox.Yes
    else:
        ok = QMessageBox.question(widget, 'alert', 'Sure to delete?', QMessageBox.Yes, QMessageBox.No)
    if ok == QMessageBox.Yes:
        return send2trash(path) is None
    return False


def open_dir_dialog(widget, txt_widget):
    path = QFileDialog.getExistingDirectory(widget, "select directory")
    if path and os.path.isdir(path):
        txt_widget.setText(path)


def kill_same_script():
    for p in psutil.process_iter():
        if 'python' in p.name() and os.path.basename(p.cmdline()[1]) == os.path.basename(sys.argv[0]):
            if os.getpid() != p.pid:
                p.kill()


def copy_to_clipboard(text):
    QApplication.clipboard().setText(text)


def focus_to_text(lineedit):
    lineedit.setFocus()
    lineedit.select_all()


def add_button_on_tableview(tableview, row, col, label, font, width, slot):
    button = QPushButton()
    button.setFocusPolicy(Qt.NoFocus)
    button.setText(label)
    button.setFixedWidth(width)
    if font is not None:
        button.setFont(font)
    button.clicked.connect(slot)
    tableview.setIndexWidget(tableview.model().index(row, col), button)


def add_checkbox_on_tableview(tableview, row, col, label, width, slot):
    checkbox = QCheckBox()
    checkbox.setFocusPolicy(Qt.NoFocus)
    checkbox.setText(label)
    checkbox.setFixedWidth(width)
    checkbox.stateChanged.connect(slot)
    tableview.setIndexWidget(tableview.model().index(row, col), checkbox)


def load_settings(self, app_name):
    self.settings = QSettings('hjchoi', 'util')
    self.move(self.settings.value(app_name + '_pos', QPoint(0, 0)))


def save_settings(self, app_name):
    self.settings.setValue(app_name + '_pos', self.pos())


def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)
