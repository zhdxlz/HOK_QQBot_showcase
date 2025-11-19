
from .zutil import *
from .zstatic import *
from . import zdynamic as dmc

    
def manual_dump():
    from .ztime import time_sul
    from .zfunc import wzry_data
    from .zfile import writerl

    dump_date=time_sul().strftime("%Y-%m-%d") # 因为提早了5分钟，所以时间就是在导出的日期
    log_message("DUMPBEGIN "+dump_date+".json")
    # try:
    gameinfo = [wzry_data(key,userlist[key],os.path.join("history", "personal", dump_date, str(userlist[key]) + ".json")) for key in userlist] # dump -- 每个人
    # except Exception as e:
    #     return str(e)
    filename=os.path.join("history",dump_date+".json")
    writerl(filename,gameinfo)
    log_message("DUMPEND "+dump_date+".json")
    return None

def recover_last():
    from .ztime import time_r_delta
    from .zfunc import wzry_data
    from .zfile import writerl

    dump_date=time_r_delta(1).strftime("%Y-%m-%d") # 因为提早了5分钟，所以时间就是在导出的日期
    log_message("DUMPBEGIN "+dump_date+".json")
    # try:
    gameinfo = [wzry_data(key,userlist[key],os.path.join("history", "personal", dump_date, str(userlist[key]) + ".json")) for key in userlist] # dump -- 每个人
    # except Exception as e:
    #     return str(e)
    filename=os.path.join("history",dump_date+".json")
    writerl(filename,gameinfo)
    log_message("DUMPEND "+dump_date+".json")
    return None

