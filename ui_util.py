from PyQt5.QtWidgets import QMessageBox
from send2trash import send2trash


def delete_path(path):
    return send2trash(path) is None
