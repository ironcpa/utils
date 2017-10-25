#-*-coding:utf-8-*-

import subprocess
import sys
import os

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

form_class = uic.loadUiType("C:/__devroot/utils/resource/gui_ffmpeg_main.ui")[0]


class MainWindow(QMainWindow, form_class):
    def __init__(self, src_path):
        super().__init__()
        self.setupUi(self)

        self.lbl_src_file.setText(src_path)

        src_name_only, src_ext = os.path.splitext(os.path.basename(src_path))
        clip_name = 'clip_' + src_name_only
        self.txt_clip_name.setText(clip_name + '_{}_{}' + src_ext)

        self.btn_encode.clicked.connect(self.on_encode_clicked)

    def on_encode_clicked(self):
        start_time = self.txt_start_time.text().replace(' ', '')
        end_time = self.txt_end_time.text().replace(' ', '')

        src_file = self.lbl_src_file.text()
        clip_file_form = self.txt_clip_name.text()
        clip_file_full = clip_file_form.format(start_time.replace(':', ''), end_time.replace(':', ''))

        # no reencoding : copy all settings
        # command = 'ffmpeg -i "{}" -ss {} -t {} -vcodec copy -acodec copy {}'.format(src_file, start_time, end_time, clip_file)
        command = 'ffmpeg -i "{}" -ss {} -to {} -c copy {} -y'.format(src_file, start_time, end_time, clip_file_full)
        # reencoding : if no reencoding result has glitch on start
        # command = 'ffmpeg -i "{}" -ss {} -to {} {} -y'.format(src_file, start_time, end_time, clip_file_full)
        print(command)

        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
            QMessageBox.information(self, 'info', 'encoding complete')
            # self.close()
        except subprocess.CalledProcessError as e:
            print(e)
            QMessageBox.critical(self, 'error', 'encoding failed\n{}'.format(err))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    src_file = sys.argv[1] if len(sys.argv) > 1 else ''
    mywindow = MainWindow(src_file)
    mywindow.show()
    app.exec_()
