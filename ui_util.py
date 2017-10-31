import os
import sys
import psutil
import subprocess

from PyQt5.QtWidgets import QMessageBox, QFileDialog, QApplication
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


def delete_path(widget, path):
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


def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)


def copy_to_clipboard(text):
    QApplication.clipboard().setText(text)