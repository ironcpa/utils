import os
import subprocess

import file_util


def get_clip_infos(clip_dir, filename):
    return [(clip_dir + x, file_util.get_file_size(clip_dir + x)) for x in os.listdir(clip_dir)
                                                    if x.startswith('clip_{}'.format(filename))]


def get_clip_paths(clip_dir, filename):
    return [clip_dir + x for x in os.listdir(clip_dir)
            if x.startswith('clip_{}'.format(file_util.get_product_no(filename)))]


def merge_all_clips(src_path, clip_paths, is_async = False):
    if len(clip_paths) < 1:
        return

    tmp_list_file_name = 'tmp_list.txt'
    with open(tmp_list_file_name, 'w') as tmp_list_file:
        for p in clip_paths:
            tmp_list_file.write("file '{}'\n".format(p))
    merged_file = os.path.dirname(src_path) + '\\con_' + os.path.basename(src_path)

    command = 'ffmpeg -f concat -safe 0 -i {} -c copy "{}" -y'.format(tmp_list_file_name, merged_file)
    if is_async:
        subprocess.Popen(command)
    else:
        subprocess.check_output(command)
    os.remove(tmp_list_file_name)

    return merged_file
