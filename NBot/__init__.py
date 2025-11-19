
import threading
import redis

from .zutil import * # 引入通用库
from .zstatic import * # 引入静态变量
from . import zdynamic as dmc # 引入动态变量

from .zapi import * # API处理（王者荣耀、deepseek）
from .zevent import * # QQBot事件（接收、发送、戳一戳、定时）
from .zfile import * # 文件IO
from .zfunc import * # 辅助函数
from .zscheduler import * # 定时事件
from .ztime import * # 时间获取

# 加载昨日数据
load_yesterday(1) 
init_fetch_news()
# 启动定时任务 
scheduler_thread = threading.Thread(target=scheduler_func)
scheduler_thread.daemon = True
scheduler_thread.start()

redis_path=str(os.environ.get('REDIS_CONF'))
with open(redis_path, 'r', encoding='utf-8') as file:
    varia = json.load(file)
globals().update(varia)
dmc.redis_deamon= redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,password=REDIS_PASSWORD)
dmc.export_btldetail_lock=threading.Lock()
dmc.LastBtlMsgTime=str_to_time("2025-01-01 00:00:00")
dmc.LastBtlMsgCoolDownTime=str_to_time("2025-01-01 00:00:00")
# web_shared_btls_processor()
if __name__=="__main__":
    pass