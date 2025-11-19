from openai import OpenAI
import requests
from ratelimit import limits, sleep_and_retry
import json
import yaml
import time
import os

confs={}
with open('../NBot/config.yaml', 'r') as file:
    confs = yaml.load(file, Loader=yaml.FullLoader)

def writerl(filepath,data):
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return None
    except Exception as e:
        return None

@sleep_and_retry    # 当达到限制时自动等待
@limits(calls=3, period=1)
def wzry_get_official(reqtype,userid=-1, roleid=0,gameseq=-1,gameSvrId=-1,relaySvrId=-1,pvptype=-1):
    roleid=str(roleid)
    userid=str(userid)
    headers = {
        "Host": "kohcamp.qq.com",
        "istrpcrequest": "true",
        "cchannelid": "10035044",
        "cclientversioncode": "2047937708",
        "cclientversionname": "9.104.0903",
        "ccurrentgameid": "20001",
        "cgameid": "20001",
        "cgzip": "1",
        "cisarm64": "true",
        "crand": '1758455866028',
        "csupportarm64": "true",
        "csystem": "android",
        "csystemversioncode": "32",
        "csystemversionname": "12",
        "cpuhardware": "HONOR",
        "encodeparam": confs["wzry"]["encodeparam"],
        "gameareaid": "1",
        "gameid": "20001",
        "gameopenid": confs["wzry"]["gameopenid"],
        "gameroleid": confs["wzry"]["gameroleid"],
        "gameserverid": "1533",
        "gameusersex": "1",
        "openid": confs["wzry"]["openid"],
        "tinkerid": confs["wzry"]["tinkerid"],
        "token": confs["wzry"]["token"],
        "userid": confs["wzry"]["userid"],
        "content-encrypt": "",
        "accept-encrypt": "",
        "noencrypt": "1",
        "x-client-proto": "https",
        "x-log-uid": confs["wzry"]["x-log-uid"],
        "kohdimgender": "2",
        "content-type": "application/json; charset=UTF-8",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/4.9.1",
        "traceparent": confs["wzry"]["traceparent"]
    }

    btldetail_data = {
        "recommendPrivacy": 0,
        "gameSvr": gameSvrId,
        "gameSeq": gameseq,
        "targetRoleId": roleid,
        "relaySvr": relaySvrId,
        "battleType": int(pvptype)
    }
    print(btldetail_data)
    btlist_data = {
        "lastTime": 0,
        "recommendPrivacy": 0,
        "apiVersion": 5,
        "friendRoleId": roleid,
        "isMultiGame": 1,
        "friendUserId": userid,
        "option": 0
    }
    profile_data = {
        "resVersion": 3,
        "recommendPrivacy": 0,
        "apiVersion": 2,
        "targetUserId": userid,
        "targetRoleId": roleid,
        "itsMe": False
    }
    season_data = {
        "recommendPrivacy": 0,
        "roleId": roleid
    }
    heropower_data = {
        "recommendPrivacy": 0,
        "targetUserId":userid,
        "targetRoleId":roleid
    }
    match reqtype:
        case "btldetail":
            url=btldetail_url
            data=btldetail_data
        case "btlist":
            url=btlist_url
            data=btlist_data
        case "profile":
            url=profile_url
            data=profile_data
        case "season":
            url=season_url
            data=season_data
        case "heropower":
            url=heropower_url
            data=heropower_data
    retry_time=3
    while(retry_time):
        response = requests.post(url, headers=headers, json=data)
        # print(response.text)
        res=response.json().get("data",{})
        if res: break
        retry_time-=1
    if (not retry_time): raise Exception(str("王者荣耀数据源错误"))
    return res


def file_exist(file_path):
    return os.path.exists(file_path)
def retry_until_true(func, timeout=1, *args, **kwargs):
    """
    重试函数直到返回True或超时
    :param func: 要重试的函数
    :param timeout: 超时时间（秒）
    :param args, kwargs: 函数的参数
    :return: 最终结果
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = func(*args, **kwargs)
        if result:
            return result
        time.sleep(0.01)  # 短暂休眠，避免CPU占用过高
    
    # 超时后最后尝试一次
    return func(*args, **kwargs)