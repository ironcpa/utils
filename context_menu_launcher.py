import sys
import os
import win32api

import common_util as co
import file_util
import find_file
import db_util


if __name__ == '__main__':
    print('context_menu_launcher', sys.argv[1], sys.argv[2])

    command = sys.argv[1]
    if command == 'format':
        file_util.rename_files(sys.argv[2])
    elif command == 'collect':
        print(sys.argv[2])
        path = sys.argv[2]
        disk_name = None
        if len(path) == 3:
            disk_name = win32api.GetVolumeInformation(os.path.splitdrive(path)[0])
        print('disk', disk_name)
        db = db_util.DB()
        if disk_name and co.is_disk_online(disk_name):
            db.delete_by_disk(disk_name)
            fileinfos = find_file.find_file(path, '')
            db.update_product_w_fileinfos(fileinfos)
        else:
            db.delete_by_dir(path)
            fileinfos = find_file.find_file(path, '')
            db.update_product_w_fileinfos(fileinfos)


