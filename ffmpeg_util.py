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


def create_clip_command(src_path, start_time, end_time, out_clip_path, is_reencode=False):
    start_time_form = co.to_time_form(start_time)
    end_time_form = co.to_time_form(end_time)
    command = ''
    if is_reencode:
        command = 'ffmpeg -i "{}" -ss {} -to {} {} -y'.format(src_path, start_time_form, end_time_form, out_clip_path)
    else:
        command = 'ffmpeg -i "{}" -ss {} -to {} -c copy {} -y'.format(src_path, start_time_form, end_time_form,
                                                                      out_clip_path)
    print(command)
    return command


def create_clip(src_path, start_time, end_time, out_clip_path):
    subprocess.Popen(create_clip_command(src_path, start_time, end_time, out_clip_path))


def create_clip_for_refactor(src_path, start_time, end_time, out_clip_path, is_reencode=False, is_async_call=False):
    """asyncio call 적용 위한 임시 테스트 인터페이스"""
    command = create_clip_command(src_path, start_time, end_time, out_clip_path, is_reencode)

    if is_async_call:
        subprocess.Popen(command)
        return True, None
    else:
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
            # self.remove_old_same_result(out_clip_path)
            # self.add_clip_result(out_clip_path, file_util.get_file_size(out_clip_path))
            # self.show_total_clip_size()
            return True, None
        except subprocess.CalledProcessError as e:
            return False, e


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