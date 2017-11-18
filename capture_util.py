# -*-coding:utf-8-*-

import os
import subprocess

import common_util as cu
import ffmpeg_util

START_TIME_PAD = 1


def create_clips_from_captures(src_path, cap_dir, clip_dir, captures, header = ''):
    src_dir, src_file = os.path.split(src_path)
    src_name, src_ext = os.path.splitext(src_file)
    times = [cu.get_time(f) for f in captures]

    for i, t in enumerate(times):
        if i % 2 == 1:
            s = times[i - 1]
            start_pad = START_TIME_PAD if int(s) > 0 else 0
            start_time = '{:06d}'.format(int(s) - start_pad)
            end_time = t
            out_file = '{}clip_{}_{}_{}{}'.format(header, src_name, start_time, end_time, src_ext)
            out_clip_path = os.path.join(clip_dir, out_file)

            ffmpeg_util.create_clip(src_path, start_time, end_time, out_clip_path)


if __name__ == '__main__':
    src_path = 'C:/__devroot/utils/sample_data/2017-18 NBA 10, 25 휴스턴 VS 필라델피아.mp4'
    cap_dir = 'c:/__potplayer_caputure_for_clip'
    clip_dir = 'c:/__clips'
    create_clips_from_captures(src_path, cap_dir, clip_dir, [])
