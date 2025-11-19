
from .zutil import *
from .zstatic import *
from . import zdynamic as dmc
from datetime import timedelta
from dateutil import parser

import time

def time_r(): # time_real
    time_real=datetime.datetime.now()
    return time_real
def date_r():
    date_real = datetime.datetime.now().strftime("%Y-%m-%d")
    return date_real
def time_r_delta(delta=0):
    time_real=time_r()
    time_back=time_real-timedelta(days=delta)
    return time_back
#别用默认参数列表
def time_sul(time_real=None): # time_stay_up_late 将凌晨对局算在前一天，以3:30为界，时间向前挪动(将3:30视作0:00)
    if (time_real==None):time_real=datetime.datetime.now()
    time_fake=time_real-datetime.timedelta(hours=bound_hour, minutes=bound_minute)
    return time_fake
def date_roleback(time_real=None): # time_stay_up_late 将凌晨对局算在前一天，以3:30为界，时间向前挪动(将3:30视作0:00)
    if (time_real==None):time_real=datetime.datetime.now()
    time_fake=time_real-datetime.timedelta(days=1)
    return time_fake
def date_sul(time_real=None): # time_stay_up_late 将凌晨对局算在前一天，以3:30为界，时间向前挪动(将3:30视作0:00)
    if (time_real==None):time_fake=time_sul()
    date_fake = time_fake.strftime("%Y-%m-%d")
    return date_fake
def stamp_to_time(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)
def str_to_time(time_str):
    time_datetime = parser.parse(time_str)
    return time_datetime
def time_to_str(time_datetime, format_str="%Y-%m-%d %H:%M:%S"):
    return time_datetime.strftime(format_str)
def time_delta(time_in,delta):
    return time_in+timedelta(days=delta)
def wait():
    delay_second=random.uniform(3,5)
    time.sleep(delay_second)
def short_wait():
    delay_second=random.uniform(0.5,1)
    time.sleep(delay_second)
def calc_gap(t1,t2):
    return abs((t1-t2).total_seconds())
def add_second(src,det):
    return src+timedelta(seconds=det)
def get_timebased_rand(n,rand_gap):
    """
    基于当前时间获取[0, n]内的随机整数，间隔一段时间变一次
    """
    time_now = time_r()
    time_seed = int(time_now.timestamp()) // (60*rand_gap)
    random.seed(time_seed)
    return random.randint(0, n-1) # 保证左闭右开
