# -*-coding:utf-8-*-

import os
import shutil
import subprocess

import common_util as co
import file_util
import ui_util


def get_clip_infos(clip_dir, filename, include_sample_clip = False):
    sample_prefix = 'sample_' if include_sample_clip else ''
    return [(clip_dir + x, file_util.get_file_size(clip_dir + x)) for x in os.listdir(clip_dir)
                                                    if x.startswith('{}clip_{}'.format(sample_prefix, filename))]


def get_clip_paths(clip_dir, filename):
    return [clip_dir + x for x in os.listdir(clip_dir)
            if x.startswith('clip_{}'.format(file_util.get_product_no(filename)))]


def create_clip(src_path, start_time, end_time, out_clip_path):
    command = 'ffmpeg -i "{}" -ss {} -to {} -c copy "{}" -y'.format(src_path, co.to_time_form(start_time),
                                                                    co.to_time_form(end_time), out_clip_path)
    print(command)
    subprocess.Popen(command)


def merge_file_path(src_path):
    pno = file_util.get_product_no(os.path.basename(src_path))
    merged_file_name = os.path.dirname(src_path) + os.path.sep + pno + '_con' + os.path.basename(src_path).replace(pno, '')
    return merged_file_name


def merge_all_clips(merged_file_path, clip_paths, is_async = False):
    if len(clip_paths) < 1:
        return

    if len(clip_paths) == 1:
        # shutil.move(clip_paths[0], merged_file)
        shutil.copy(clip_paths[0], merged_file_path)
        return merged_file_path

    tmp_list_file_name = 'tmp_list.txt'
    with open(tmp_list_file_name, 'w') as tmp_list_file:
        for p in clip_paths:
            tmp_list_file.write("file '{}'\n".format(p))

    cmd = 'ffmpeg -f concat -safe 0 -i {} -c copy "{}" -y'.format(tmp_list_file_name, merged_file_path)
    if is_async:
        subprocess.Popen(cmd)
    else:
        subprocess.check_output(cmd)
    os.remove(tmp_list_file_name)

    return merged_file_path


def capture(src_path, time_form, recap_tag, out_dir):
    # based on pot player capture format
    out_path = '{}\\{}_{}_{}.000.jpg'.format(out_dir, os.path.basename(src_path), recap_tag, time_form.replace(':', ''))
    cmd = 'ffmpeg -ss {} -i "{}" -vframes 1 -q:v 2 "{}" -y'.format(time_form, src_path, out_path)
    print(cmd)
    subprocess.Popen(cmd)