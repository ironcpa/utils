import sys
import os
import win32api

import common_util as co
import file_util
import find_file
import db_util


def collect_files_to_db(disk_name, path):
    print('disk', disk_name)
    db = db_util.DB()
    if disk_name and co.is_disk_online(disk_name):
        db.delete_by_disk(disk_name)
        fileinfos = find_file.find_file(path, '')
        db.insert_product_w_fileinfos(fileinfos)
    else:
        db.delete_by_dir(path)
        fileinfos = find_file.find_file(path, '')
        db.insert_product_w_fileinfos(fileinfos)


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        print('context_menu_launcher', sys.argv[1], sys.argv[2])
    else:
        print('context_menu_launcher', sys.argv[1])

    command = sys.argv[1]
    if command == 'format':
        file_util.rename_files(sys.argv[2])
    elif command == 'collect':
        if len(sys.argv) == 2:
            # collect from all drive
            for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
                if drive.startswith('C:'):
                    continue
                disk_name = win32api.GetVolumeInformation(drive)[0]
                print(disk_name, drive)
                collect_files_to_db(disk_name, drive)
        else:
            path = sys.argv[2]
            disk_name = None
            if len(path) <= 3: # drive root
                disk_name = win32api.GetVolumeInformation(os.path.splitdrive(path)[0] + os.path.sep)
                path = path + os.path.sep
            collect_files_to_db(disk_name, path)

