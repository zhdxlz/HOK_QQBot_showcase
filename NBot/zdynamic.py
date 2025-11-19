
from .zutil import *

# 引入程序动态变量
with open('variables_dynamic.json', 'r', encoding='utf-8') as file:
    varia = json.load(file)
globals().update(varia)