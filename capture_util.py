# -*-coding:utf-8-*-

import os
import subprocess

sort_by_time = False
src_path = 'D:/새 폴더 (4)/post-407.mp4'
src_dir, src_file = os.path.split(src_path)
src_name, src_ext = os.path.splitext(src_file)
cap_dir = 'c:/__potplayer_caputure_for_clip'
cap_ext = '.jpg'
clip_dir = 'c:/__clips'

captures = [os.path.join(cap_dir, x) for x in os.listdir(cap_dir) if x.startswith(src_file) and x.endswith(cap_ext)]
if sort_by_time:
    captures = sorted(filter(os.path.isfile, captures), key=os.path.getmtime)
print(captures)
for c in captures:
    print(c)
times = [f[-14:][:6] for f in captures]
print(times)

commandf = 'ffmpeg -i "{}" -ss {} -to {} -c copy "{}" -y'
for i, t in enumerate(times):
    if i % 2 == 1:
        start_time = '{:06d}'.format(int(times[i-1]) - 1)
        end_time = t
        out_file = 'clip_{}_{}_{}{}'.format(src_name, start_time, end_time, src_ext)
        out_clip_path = os.path.join(clip_dir, out_file)

        start_form = ':'.join(start_time[i:i+2] for i in range(0, len(start_time), 2))
        end_form = ':'.join(end_time[i:i+2] for i in range(0, len(end_time), 2))
        command = commandf.format(src_path, start_form, end_form, out_clip_path)
        print(command)
        subprocess.Popen(command.format(src_path, times[i-1], t, out_clip_path))
