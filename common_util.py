# -*-coding:utf-8-*-

import win32api
from defines import *


def better_filename(self, product):
    p = product
    return '{}_{}_{}'.format(p.p_no, p.desc.replace(' ', '_'), p.rate)


def get_time(capture_path):
    # need to have validation
    return capture_path[-14:][:6]


def to_time_form(time_str):
    # assumption : time's like '102030'
    return ':'.join(time_str[i:i + 2] for i in range(0, len(time_str), 2))


def second_to_time_from(seconds):
    h = seconds // (60 * 60)
    seconds -= h * 60 * 60
    m = seconds // 60
    seconds -= m * 60
    s = seconds
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)


def to_second(time_form):
    # str_time's like '10:20:30'
    h = int(time_form[0:2])
    m = int(time_form[3:5])
    s = int(time_form[6:8])
    return h * 60 * 60 + m * 60 + s


def get_duration(start_time, end_time):
    return to_second(end_time) - to_second(start_time)


def get_duration_in_time_form(start_time, end_time):
    return second_to_time_from(get_duration(start_time, end_time))


def get_drive(disk_label):
    for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
        if disk_label == win32api.GetVolumeInformation(drive)[0]:
            return drive
    return None


def is_disk_online(disk):
    return get_drive(disk) is not None


def conv_fileinfo_to_product(file_info):
    path = file_info.path

    drive_volume = win32api.GetVolumeInformation(os.path.splitdrive(path)[0] + '/')
    filename = os.path.basename(path)

    name_only = os.path.splitext(filename)[0]
    tokens = name_only.split('_')

    product_no = tokens[0]
    rate = tokens[-1] if tokens[-1] != product_no and tokens[-1].startswith('xx') else ''
    desc = ' '.join(tokens[1:]).replace(rate, '') if len(tokens) > 1 else ''
    disk_name = drive_volume[0]
    location = path

    return Product(None, product_no, desc, rate, disk_name, location, file_info.size, file_info.cdate)


def conv_path_to_product(path, id = None):
    size = file_util.get_file_size(path)
    cdate = file_util.get_ctime(path)
    return modify_product(conv_fileinfo_to_product(FileInfo(path, size, cdate)), id = id)


def modify_product(org_product, id = None, product_no = None, desc = None, rate = None, disk_name = None, location = None, size = None, cdate = None):
    return Product(
        id if id else org_product.id,
        product_no if product_no else org_product.product_no,
        desc if desc else org_product.desc,
        rate if rate else org_product.rate,
        disk_name if disk_name else org_product.disk_name,
        location if location else org_product.location,
        size if size else org_product.size,
        cdate if cdate else org_product.cdate
    )
