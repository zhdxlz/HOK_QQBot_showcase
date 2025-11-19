
from .zutil import *

from .config import Config
from nonebot.plugin import PluginMetadata
from nonebot import get_plugin_config
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.util import timezone
import redis
from redis import ConnectionPool

# NONEBOT配置 
__plugin_meta__ = PluginMetadata(
    name="Qbot",
    description="",
    usage="",
    config=Config,
)
config = get_plugin_config(Config)

# logging配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler("QBOT.log")]
)

# 引入Redis配置
nginx_path=str(os.environ.get('NGINX_HTML')) # 依赖环境变量
redis_path=str(os.environ.get('REDIS_CONF'))
with open(redis_path, 'r', encoding='utf-8') as file:
    varia = json.load(file)
globals().update(varia)
redis_deamon = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,password=REDIS_PASSWORD)
redis_deamon_liked_btl = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_LIKED_BTL,password=REDIS_PASSWORD)
redis_deamon_share_btl = redis.Redis(connection_pool=ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_SHARE_POOL,password=REDIS_PASSWORD))
# 引入程序配置
confs={}
with open('config.yaml', 'r') as file:
    confs = yaml.load(file, Loader=yaml.FullLoader)

# 引入程序静态变量
with open('variables_static.json', 'r', encoding='utf-8') as file:
    varia = json.load(file)
for heroid,heroname in varia["HeroList"].items():
    varia["HeroNames"].append(heroname)
for heroid,heroname in varia["HeroName_replacements"].items():
    varia["HeroNames"].append(heroname)
globals().update(varia)