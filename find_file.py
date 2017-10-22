#-*-coding:utf-8-*-

import os
import re
import win32api
import win32ui
import fnmatch
import stat
from symlink import *
import subprocess

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
        
def find_file(root_folder, file_name, ignore_path = None):
    founds = []
    rex = re.compile(file_name, re.IGNORECASE)
    print( root_folder)
    for root, dirs, files in os.walk(root_folder):
        for extension in ('*.avi', '*.wmv', '*.mp4', '*.mpg', '*.asf', '*.mov', '*.mkv', '*.iso'):
            #for f in files:
            for f in fnmatch.filter(files, extension):
                result = rex.search(f)
                if result:
                    full_path = os.path.join(root, f)
                    #ignore path patterns
                    if not (ignore_path is None) and (ignore_path in full_path):
                        print('ignore path ' + ignore_path)
                        continue
                    if r"C:\Users\hjchoi\Documents" in full_path:   # downloading torrent
                        print('ignore ' + full_path)
                        continue
                    if r"C:\Windows\Sys" in full_path:      # why some files found in system folders? 
                        print('ignore system ' + full_path)
                        continue
                    if full_path.endswith(SYMLINK_SUFFIX):
                        print('ignore symlink file ' + full_path)
                        continue
                    founds.append(full_path)
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


#===================================================
# run
#===================================================
'''
todo
-wakaba_kana 고화질
-mitsui hikaru 점검
harumiya suzu 전편
tomoka akari 점검
kono madoka 전편 - 넓은몸
'''
search_text = 'vicd(.*)362'
#search_text = '(.*)75'
dest_dir = r'C:\__vid_temps\__find_1018' + '\\'

#remove_dup_files_in_dest(search_text, dest_dir)
#find_file_in_all_drives( search_text )
#find_file('c:\\', "star(.*)752")
#move_files(search_text, dest_dir)
create_symlinks(search_text, dest_dir)

#symlink(r'xxxx', r'yyyy')
#xcopy('test_file.wmv', 'test_filder')
#create_dir_if_not_exists(dest_dir)

win32ui.MessageBox("Script End", "Python", 4096)
