# -*- coding: utf-8 -*-
import os
import shutil
import datetime
import time


MIN_BRAND_LEN = 2
REMOVE_STRS = ["[Thz.la]",
               "[thz.la]",
               "[thz.tw]",
               "[HD]",
               "[FHD]",
               "21bt.net-",
               "-AV9.CC",
               "99BT工厂-",
               "www.u-15.info-",
               "www.youiv.net-",
               "3xplanet_",
               "206.108.51.3-",
               "206.108.51.2-",
               "5032.ifei.com.tw-",
               "avbtdown.com-",
               "www.av-9.cc-",
               "javfile.org_",
               "javbo.net_",
               "big-cup.tv-",
               "1203-javbo.net_",
               "youiv.net-",
              ]
REMOVE_STRS_3PLENET = ['{:03d}_'.format(x) + '3xplanet_' for x in range(1, 100)]
REMOVE_STRS.extend(REMOVE_STRS_3PLENET)

TIME_FORMAT = '%Y%m%d-%H%M%S'


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

    if src_name.endswith('4M'):
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

    brand = src_name[0:num_pos].lower()
    number_n_other = src_name[num_pos:]

    # 20171102
    if len(brand) > 0 and brand[0] == '-':
        brand = brand[1:]
    if number_n_other.endswith('FHD'):
        number_n_other = number_n_other[:-3]
    if number_n_other.endswith('MP4'):
        number_n_other = number_n_other[:-3]

    if brand.endswith('-'):
        return brand + number_n_other
    elif not number_n_other[0].isdigit():
        return brand + number_n_other
    else:
        return brand + '-' + number_n_other


def create_log_name(root_path):
    return os.path.join(root_path, 'rename_log_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.txt')


def backup_file_name(log_name, old_path, new_path):
    with open(log_name, 'a', encoding='utf-8') as f:
        f.write("{} <- {}\n".format(new_path, old_path))


def rename_files(path):
    log_name = create_log_name(path)

    for root, dirs, files in os.walk(path):
        for file_name in files:
            if file_name.startswith('rename_log'):
                continue

            name, ext = os.path.splitext(file_name)
            new_name = name

            if not ('1pon' in name and 'carib' in name):
                new_name = remove_date_prefix(new_name)
            new_name = remove_unused(new_name)
            new_name = make_valid_product_name(new_name)
            new_name += ext

            if new_name == file_name:
                continue

            o_path = os.path.join(root, file_name)
            n_path = os.path.join(root, new_name)
            print(new_name, '<-', file_name)
            os.rename(o_path, n_path)

            backup_file_name(log_name, o_path, n_path)

#rename_files("D:/새 폴더")


def get_product_no(formatted_name):
    name_only = os.path.splitext(formatted_name)[0]
    pos_under = name_only.find('_')
    return name_only[:pos_under] if pos_under > 0 else name_only


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


def get_file_size(full_path):
    return str(os.path.getsize(full_path) // 1000)
    # return format(os.path.getsize(full_path) // 1000, ',')


def get_ctime(full_path):
    return time.strftime(TIME_FORMAT, time.localtime(os.path.getctime(full_path)))


def is_drive(letter):
    return len(letter) == 2 and letter[0].isalpha() and letter[1] == ':'


def get_cmd_path_arg(arg):
    # os.path.join 이 cmd에서 C: 로 들어오는 루트 경로를 C:\\로 변환하지 못하는 문제 해결 
    # join('C:', os.sep) 로 되지만, 'C:\\aaa', os.sep 는 C: 가 나옴
    if is_drive(arg):
        return arg + os.sep
    elif os.path.isdir(arg):
        return arg
    return None


if __name__ == '__main__':
    file_name = "pppd-605FHD.mp4"
    name, ext = os.path.splitext(file_name)
    new_name = name
    # if not ('1pon' in file_name and 'carib' in file_name):
    #     new_name = remove_date_prefix(new_name)
    # new_name = remove_unused(new_name)
    new_name = make_valid_product_name(new_name) + ext
    print(new_name)

    # test_dir = './test_area'
    # # test_dir = 'c:/__devroot/util/test_area'
    # copy_sample_to_test_area(test_dir)
    #
    # rename_files(test_dir)
