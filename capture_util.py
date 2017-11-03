# -*-coding:utf-8-*-

import os
import subprocess

import file_util


def get_time(cap_path):
    # need to have validation
    return cap_path[-14:][:6]


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


def create_clips_from_captures(src_path, cap_dir, clip_dir, sort_by_time):
    src_dir, src_file = os.path.split(src_path)
    src_name, src_ext = os.path.splitext(src_file)
    cap_ext = '.jpg'

    product_no = file_util.get_product_no(src_name)
    captures = [os.path.join(cap_dir, x) for x in os.listdir(cap_dir) if x.startswith(product_no) and x.endswith(cap_ext)]
    if sort_by_time:
        captures = sorted(filter(os.path.isfile, captures), key=os.path.getmtime)
    print(captures)
    for c in captures:
        print(c)
    times = [get_time(f) for f in captures]
    print(times)

    ffmpeg_cmd = 'ffmpeg -i "{}" -ss {} -to {} -c copy "{}" -y'
    for i, t in enumerate(times):
        if i % 2 == 1:
            start_time = '{:06d}'.format(int(times[i - 1]) - 1)
            end_time = t
            out_file = 'clip_{}_{}_{}{}'.format(src_name, start_time, end_time, src_ext)
            out_clip_path = os.path.join(clip_dir, out_file)

            command = ffmpeg_cmd.format(src_path, to_time_form(start_time), to_time_form(end_time), out_clip_path)
            print(command)
            subprocess.Popen(command.format(src_path, times[i - 1], t, out_clip_path))
            # subprocess.check_output(command.format(src_path, times[i - 1], t, out_clip_path))


if __name__ == '__main__':
    src_path = 'C:/__devroot/utils/sample_data/2017-18 NBA 10, 25 휴스턴 VS 필라델피아.mp4'
    cap_dir = 'c:/__potplayer_caputure_for_clip'
    clip_dir = 'c:/__clips'
    create_clips_from_captures(src_path, cap_dir, clip_dir, False)
