#-*-coding:utf-8-*-

import re
import fnmatch
import stat
from symlink import *
import subprocess

from defines import *
import file_util


def get_file_size(file):
    file.seek(0, 2)
    size = file.tell()
    return size


def xcopy(src, dst):
    #os.system('xcopy "%s" "%s"' % (src, dst))

    #subprocess.call(['xcopy', src, dst])

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.call(['xcopy', src, dst], startupinfo=si)


def remove_file(path):
    os.chmod(path, stat.S_IWRITE)
    os.remove(path)


def create_dir_if_not_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)
        print('create new dir : {}'.format(path))


EXTENSIONS = ('*.avi', '*.wmv', '*.mp4', '*.mpg', '*.asf', '*.mov', '*.mkv', '*.iso')


def is_ignore_dir(path, ignore_path):
    if not (ignore_path is None) and (ignore_path in path):
        print('ignore path ' + ignore_path)
        return True
    if r"C:\Users\hjchoi\Documents" in path:  # downloading torrent
        print('ignore ' + path)
        return True
    if r"C:\Windows\Sys" in path:  # why some files found in system folders?
        print('ignore system ' + path)
        return True
    if path.endswith(SYMLINK_SUFFIX):
        print('ignore symlink file ' + path)
        return True
    return False


def find_file(root_folder, file_name, ignore_path = None):
    founds = []
    rex = re.compile(file_name, re.IGNORECASE)
    print( root_folder)
    for root, dirs, files in os.walk(root_folder):
        for ext in EXTENSIONS:
            #for f in files:
            for f in fnmatch.filter(files, ext):
                result = rex.search(f)
                if result:
                    full_path = os.path.join(root, f)
                    #ignore path patterns
                    if is_ignore_dir(full_path, ignore_path):
                        continue
                    # if not (ignore_path is None) and (ignore_path in full_path):
                    #     print('ignore path ' + ignore_path)
                    #     continue
                    # if r"C:\Users\hjchoi\Documents" in full_path:   # downloading torrent
                    #     print('ignore ' + full_path)
                    #     continue
                    # if r"C:\Windows\Sys" in full_path:      # why some files found in system folders?
                    #     print('ignore system ' + full_path)
                    #     continue
                    # if full_path.endswith(SYMLINK_SUFFIX):
                    #     print('ignore symlink file ' + full_path)
                    #     continue
                    founds.append(FileInfo(full_path.replace('/', '\\'), file_util.get_file_size(full_path),
                                           file_util.get_ctime(full_path)))  # for windows cmd call
                    # founds.append(full_path)
                    print(full_path + ", size=" + format(os.path.getsize(full_path) / 1000, ','))
    return founds


def find_file_in_all_drives(file_name, ignore_path = None):
    print( 'search : ' + file_name)
    all_founds = []
    for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
        all_founds.extend(find_file(drive, file_name, ignore_path))
    print('found results : ' + str(len(all_founds)))
    return all_founds


def move_files(search_text, dest_dir):
    if not dest_dir.endswith('\\'):
        print('dest dir needs to be ends with \\')
        return

    create_dir_if_not_exists(dest_dir)

    founds = find_file_in_all_drives(search_text, dest_dir)
    job_counter = 0
    
    for file_path in founds:
        if dest_dir in file_path:
            print(file_path + ' is dest dir file. pass')
            continue
        file_name = os.path.basename(file_path)
        dest_path = dest_dir + file_name
        print('move : ' + file_name )
        if not os.path.isfile(dest_path):
            #print('\tdummy call copy : ' + file_path)
            xcopy(file_path, dest_dir)
            print('\t' + file_path + ' copied')
            if os.path.isfile(dest_path):
                print('\t' + dest_path + ' copied and delete source file')
                remove_file(file_path)
        else:
            print('\t' + dest_path + 'is already exists')
        job_counter = job_counter + 1
        print('{}/{} completed'.format(job_counter, len(founds)))


def remove_dup_files_in_dest(file_name, dest_dir):
    founds = find_file_in_all_drives(file_name, dest_dir)

    for path in founds:
        dest_path = dest_dir + os.path.basename(path)
        if os.path.isfile(dest_path):
            print('call remove ' + path)
            remove_file(path)


def create_symlinks(search_text, dest_dir):
    founds = find_file_in_all_drives(search_text)

    create_dir_if_not_exists(dest_dir)
    
    print('founds : ' + str(len(founds)))
    for file_path in founds:
        if dest_dir in file_path:
            continue    #pass if search file is in dest dir
        link_name = os.path.basename(file_path) + SYMLINK_SUFFIX
        link_path = os.path.join(dest_dir, link_name)
        if os.path.isfile(link_path):
            continue    #pass if already exists
        print('link path : ' + link_path)
        symlink(file_path, link_path)


if __name__ == '__main__':
    # search_text = 'vicd(.*)362'
    # # search_text = '(.*)75'
    # dest_dir = r'C:\__vid_temps\__find_1018' + '\\'
    #
    # # remove_dup_files_in_dest(search_text, dest_dir)
    # # find_file_in_all_drives( search_text )
    # # find_file('c:\\', "star(.*)752")
    # # move_files(search_text, dest_dir)
    # # create_symlinks(search_text, dest_dir)
    #
    # # symlink(r'xxxx', r'yyyy')
    # # xcopy('test_file.wmv', 'test_filder')
    # # create_dir_if_not_exists(dest_dir)
    #
    # # results = find_file('c:\\__devroot\\utils\\sample_data\\', 'aaa')
    # results = find_file('c:\\__devroot\\utils\\sample_data\\', '*')
    # print(results)
    #
    # # win32ui.MessageBox("Script End", "Python", 4096)

    root_dir = 'C:\\__devroot\\utils'
    exclude_dir = ['.git', '.idea']
    visits = 0
    for root, dirs, files in os.walk(root_dir):
        visits += 1
        # if '.git' in root:
        #     continue
        dirs[:] = [d for d in dirs if not any(exc in d for exc in exclude_dir)]
        print(str(visits), root)
        # print(str(visits), root, dirs, files)