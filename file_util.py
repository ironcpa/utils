# -*- coding: utf-8 -*-
import os
import shutil
import datetime


MIN_BRAND_LEN = 2
REMOVE_STRS = ["[Thz.la]",
               "[thz.la]",
               "21bt.net-"
               "1203-javbo.net_",
               "0814",
               "1018",
               "1019",
               "1020",
              ]


def remove_unused(src_name):
    new_name = src_name
    for rs in REMOVE_STRS:
        if src_name.find(rs) >= 0:
            new_name = src_name.replace(rs, "")
    return new_name


def remove_date_prefix(src_name):
    if len(src_name) < 4:
        return src_name

    if not src_name[:4].isdigit():
        return src_name

    # check month
    has_date_prefix = False
    month = int(src_name[:2])
    day = int(src_name[2:4])
    if month <= 12 and day <= 31:
        has_date_prefix = True

    if has_date_prefix:
        return src_name[4:]
    else:
        return src_name


def make_valid_product_name(src_name):
    if src_name[0].isdigit():
        return src_name

    num_pos = -1
    for i, c in enumerate(src_name):
        if i + 1 > MIN_BRAND_LEN and c.isdigit():
            num_pos = i
            break

    brand = src_name[0:num_pos]
    number_n_other = src_name[num_pos:]

    if brand.endswith('-'):
        return brand + number_n_other
    else:
        return brand + '-' + number_n_other


def create_log_name(root_path):
    return os.path.join(root_path, 'log_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.txt')


def backup_file_name(log_name, old_path, new_path):
    with open(log_name, 'a') as f:
        f.write("{} <- {}\n".format(old_path, new_path))


def rename_files(path):
    log_name = create_log_name(path)

    for root, dirs, files in os.walk(path):
        for file_name in files:
            if file_name.startswith('log'):
                continue

            new_name = file_name

            new_name = remove_date_prefix(new_name)
            new_name = remove_unused(new_name)
            new_name = make_valid_product_name(new_name)

            if new_name == file_name:
                continue

            o_path = os.path.join(root, file_name)
            n_path = os.path.join(root, new_name)
            print(new_name, '<-', file_name)
            os.rename(o_path, n_path)

            backup_file_name(log_name, o_path, n_path)

#rename_files("D:/새 폴더")


def copy_sample_to_test_area(dst_dir):
    src_dir = './sample_data'

    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    src_files = os.listdir(src_dir)
    for fn in src_files:
        full_fn = os.path.join(src_dir, fn)
        if os.path.isfile(full_fn):
            shutil.copy(full_fn, dst_dir)


if __name__ == '__main__':
    valid_name = make_valid_product_name("1020dvdes012awefaw23242_한글_xx.txt")
    print(valid_name)

    test_dir = './test_area'
    # test_dir = 'c:/__devroot/util/test_area'
    copy_sample_to_test_area(test_dir)

    rename_files(test_dir)
