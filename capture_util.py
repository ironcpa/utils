# -*-coding:utf-8-*-

import sys
import os
import subprocess
import asyncio

import ui_util
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


def future_call(src_path, clip_dir, captures, header=''):
    """for async call stub"""
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(async_create_clips_from_captures(loop, src_path, clip_dir, captures, header))
    loop.close()

    return result


async def async_create_clips_from_captures(async_loop, src_path, clip_dir, captures, prefix=''):
    """async test"""
    times = [cu.get_time(f) for f in captures]
    futures = [asyncio.ensure_future(create_clip_from_capture(async_loop, clip_dir, src_path, times[i - 1], t, prefix))
               for i, t in enumerate(times) if i % 2 == 1]
    result = await asyncio.gather(*futures)
    print(result)
    return result


async def create_clip_from_capture(async_loop, out_dir, src_path, start_time, end_time, prefix):
    """async test"""
    src_dir, src_name, src_ext = cu.split_path(src_path)

    start_pad = START_TIME_PAD if int(start_time) > 0 else 0
    start_time = '{:06d}'.format(int(start_time) - start_pad)
    out_file = '{}clip_{}_{}_{}{}'.format(prefix, src_name, start_time, end_time, src_ext)
    out_clip_path = os.path.join(out_dir, out_file)

    # ffmpeg_util.create_clip(src_path, start_time, end_time, out_clip_path)
    command = 'ffmpeg -i "{}" -ss {} -to {} -c copy "{}" -y'.format(src_path, cu.to_time_form(start_time),
                                                                    cu.to_time_form(end_time), out_clip_path)
    print(command)
    try:
        # subprocess.check_output(command, stderr=subprocess.STDOUT)
        await async_loop.run_in_executor(None, subprocess.check_output, command)
        return start_time, True, None
    except subprocess.CalledProcessError as e:
        return start_time, False, e


old_hook = sys.excepthook
sys.excepthook = ui_util.catch_exceptions


if __name__ == '__main__':
    src_path = 'C:/__devroot/utils/sample_data/2017-18 NBA 10, 25 휴스턴 VS 필라델피아.mp4'
    cap_dir = 'c:/__potplayer_caputure_for_clip'
    clip_dir = 'c:/__clips'
    create_clips_from_captures(src_path, cap_dir, clip_dir, [])
