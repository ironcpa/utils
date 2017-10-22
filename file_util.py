# -*- coding: utf-8 -*-
import os
import shutil

MIN_BRAND_LEN = 2


def make_valid_product_name(src_name):
    num_pos = -1
    for i, c in enumerate(src_name):
        if i + 1 > MIN_BRAND_LEN and c.isdigit():
            num_pos = i
            break
    # sp = [x.isdigit() for x in s].index(True)

    brand = src_name[0:num_pos]
    number_n_other = src_name[num_pos:]

    print(src_name, num_pos, brand, number_n_other)

    if brand.endswith('-'):
        return brand + number_n_other
    else:
        return brand + '-' + number_n_other


def remove_date_prefix(src_name):
    if len(src_name) < 4:
        return

    if not src_name[:4].isdigit():
        return

    # check month
    has_date_prefix = False
    month = int(src_name[:2])
    day = int(src_name[2:4])
    if month <= 12 and day <= 31:
        has_date_prefix = True

    # call remove substring

    return ''


def rename_files(path):
    #remove_str = "[Thz.la]"
    remove_strs = ["[Thz.la]",
                   "[thz.la]",
                   "21bt.net-"
                   "1203-javbo.net_",
                   "0814",
                   "1018",
                   "1019",
                   "1020",
                   ]
    for root, dirs, files in os.walk(path):
        for f in files:
            os.chdir(root)

            print('file',f)
            for rs in remove_strs:
                if f.find(rs) >= 0:
                    removed_name = f.replace(rs, "")
                    print(removed_name, "<-", f)

                    formatted_name = make_valid_product_name(removed_name)

                    os.rename(f, formatted_name)

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
    valid_name = make_valid_product_name("aaa111")
    print(valid_name)

    test_dir = './test_area'
    copy_sample_to_test_area(test_dir)

    rename_files(test_dir)
