from PyQt5.QtWidgets import QMessageBox
from send2trash import send2trash


def delete_path(widget, path):
    ok = QMessageBox.question(widget, 'alert', 'Sure to delete?', QMessageBox.Yes, QMessageBox.No)
    if ok == QMessageBox.Yes:
        return send2trash(path) is None
    return False
