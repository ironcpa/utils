import sys
import file_util
import find_file
import db_util


if __name__ == '__main__':
    print('context_menu_launcher', sys.argv[1], sys.argv[2])

    command = sys.argv[1]
    if command == 'format':
        file_util.rename_files(sys.argv[2])
    elif command == 'collect':
        fileinfos = find_file.find_file(sys.argv[2], '')
        db = db_util.DB()
        db.update_product_w_fileinfos(fileinfos)

