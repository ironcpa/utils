# -*-coding:utf-8-*-

import collections


Product = collections.namedtuple('Product', ['product_no', 'desc', 'rate', 'disk_name', 'location', 'size', 'cdate'])


def better_filename(self, product):
    p = product
    return '{}_{}_{}'.format(p.p_no, p.desc.replace(' ', '_'), p.rate)


def get_time(capture_path):
    # need to have validation
    return capture_path[-14:][:6]


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
