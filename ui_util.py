import os
import sys
import psutil
import subprocess

import PyQt5
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QApplication, QPushButton, QCheckBox
from PyQt5.QtCore import QSettings, QPoint
from send2trash import send2trash

import file_util


def load_settings(self, app_name, key, default):
    self.settings = QSettings('hjchoi', app_name)
    # return self.settings.value(app_name + '_' + key, default)
    return self.settings.value(key, default)

    # self.setting_ui.set_font_size(self.settings.value(app_name + '_font_size', 20))


def save_settings(self, app_name, key, value):
    # self.settings.setValue(app_name + '_' + key, value)
    self.settings.setValue(key, value)


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


def add_button_on_tableview(tableview, row, col, label, font, width, slot=None):
    button = QPushButton()
    button.setFocusPolicy(Qt.NoFocus)
    button.setText(label)
    if font is not None:
        button.setFont(font)
    # button.setFixedWidth(width)
    # button.setFixedWidth(button.fontMetrics().boundingRect(label).width() + 24)
    if slot:
        button.clicked.connect(slot)
    tableview.setIndexWidget(tableview.model().index(row, col), button)


def add_checkbox_on_tableview(tableview, row, col, label, width, slot=None, is_checked=False):
    checkbox = QCheckBox()
    if width > 0:
        checkbox.setStyleSheet('QCheckBox::indicator {width: ' + str(width) + 'px; height: ' + str(width) + 'px;}')
    checkbox.setFocusPolicy(Qt.NoFocus)
    checkbox.setText(label)
    checkbox.setFixedWidth(width)
    if slot:
        checkbox.stateChanged.connect(slot)
    checkbox.setChecked(is_checked)
    tableview.setIndexWidget(tableview.model().index(row, col), checkbox)


def show_messagebox(title, text, *buttons):
    msgbox = QMessageBox()
    msgbox.setWindowTitle(title)
    msgbox.setText(text)
    msgbox.addButton(QPushButton('OK'), QMessageBox.YesRole)
    msgbox.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)

    for btn in buttons:
        msgbox.addButton(btn, QMessageBox.NoRole)

    return msgbox.exec_()


def show_create_clip_result(parent, result):
    if result:
        succ, fail = 0, 0
        for r in result:
            if r[1]:
                succ += 1
            else:
                fail += 1
        QMessageBox.information(parent, 'result', '{} completed, {} failed'.format(succ, fail))


def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)
