import os
import sys
import psutil

from PyQt5.QtWidgets import QMessageBox
from send2trash import send2trash


def delete_path(widget, path):
    ok = QMessageBox.question(widget, 'alert', 'Sure to delete?', QMessageBox.Yes, QMessageBox.No)
    if ok == QMessageBox.Yes:
        return send2trash(path) is None
    return False


def kill_same_script():
    for p in psutil.process_iter():
        if 'python' in p.name() and os.path.basename(p.cmdline()[1]) == os.path.basename(sys.argv[0]):
            if os.getpid() != p.pid:
                p.kill()


def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)
