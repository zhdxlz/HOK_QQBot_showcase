from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.templating import Jinja2Templates

import redis
import os
import json
import sys
import logging
import datetime
import secrets
import yaml
import time
from redis import ConnectionPool

from utils import wzry_get_official
from utils import writerl,file_exist,retry_until_true

# 引入变量
variables_to_import = ["userlist","idname"]
with open("../NBot/variables_static.json", 'r', encoding='utf-8') as file:
    data = json.load(file)
for var_name in variables_to_import:
    if var_name in data:
        globals()[var_name] = data[var_name]
templates = Jinja2Templates(directory="templates")
# 引入Redis变量
nginx_path=str(os.environ.get('NGINX_HTML'))
redis_path=str(os.environ.get('REDIS_CONF'))
with open(redis_path, 'r', encoding='utf-8') as file:
    varia = json.load(file)
globals().update(varia)

# 初始化fastapi与redis
app = FastAPI()
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,password=REDIS_PASSWORD)
r_liked_btl = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_LIKED_BTL,password=REDIS_PASSWORD)
share_pool=ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_SHARE_POOL,password=REDIS_PASSWORD)
r_share_pool=redis.Redis(connection_pool=share_pool)
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "err_expired.html",
        {"request": request},
        status_code=404
    )

@app.get("/btlist", response_class=HTMLResponse)
async def show_btlist(request:Request,key: str):
    # raise HTTPException(
    #     status_code=404,
    #     detail={"template": "404_a.html", "context": {"message": ""}}
    # )
    today_date=datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        text_content = json.loads(r.get(key).decode('utf-8'))
        local_path=os.path.join(nginx_path,"wzry_history",text_content["filename"]+".json")
        if (not file_exist(local_path)): raise Exception("File not exists.")
    except Exception as e:
        return templates.TemplateResponse(
            "err_expired.html",{"request": request,}
        )
    return templates.TemplateResponse(
        "AllBattleList.html",
        {
            "request": request,
            "filename": os.path.join("wzry_history",text_content["filename"]+".json"),
            "time": text_content["time"],
            "caller": text_content["caller"],
        }
    )
@app.get("/btlperson", response_class=HTMLResponse)
async def show_btlperson(request:Request,key: str):
    today_date=datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        text_content = json.loads(r.get(key).decode('utf-8'))
        local_path=os.path.join(nginx_path,"wzry_history",text_content["filename"]+".json")
        if (not file_exist(local_path)): raise Exception("File not exists.")
    except Exception as e:
        return templates.TemplateResponse(
            "err_expired.html",{"request": request,}
        )
    return templates.TemplateResponse(
        "SingleBattleList.html",
        {
            "request": request,
            # "userfiles":{"a":os.path.join("wzry_history","ed5db8f34da0d8e8.json")},
            "filename": os.path.join("wzry_history",text_content["filename"]+".json"),
            "key": key,
        }
    )
@app.get("/btldetail", response_class=HTMLResponse)
async def show_btldetail(request:Request,key: str):
    today_date=datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        text_content = json.loads(r.get(key).decode('utf-8'))
        local_path=os.path.join(nginx_path,"wzry_history",text_content["filename"]+".json")
        if (not file_exist(local_path)): raise Exception("File not exists.")
    except Exception as e:
        return templates.TemplateResponse(
            "err_expired.html",{"request": request,}
        )
    return templates.TemplateResponse(
        "BattleDetail.html",
        {
            "request": request,
            # "userfiles":{"a":os.path.join("wzry_history","ed5db8f34da0d8e8.json")},
            "filename": os.path.join("wzry_history",text_content["filename"]+".json"),
            "key": key,
        }
    )
@app.get("/jump-btlperson", response_class=HTMLResponse)
async def jump_btlperson(request:Request,userid: str,roleid: str,key:str):
    if (not r.exists(key)):
        return templates.TemplateResponse(
            "err_illegal.html",{"request": request,"message":"key失效"}
        )
    try:
        profile_res=wzry_get_official(reqtype="profile",userid=userid,roleid=roleid)
        btlist_res=wzry_get_official(reqtype="btlist",userid=userid,roleid=roleid)
    except Exception as e:
        return templates.TemplateResponse(
            "err_illegal.html",{"request": request,"message":"网络参数错误"}
        )
    res={"btlist":btlist_res,"profile":profile_res}
    file_name=secrets.token_hex(8)+".json"
    save_path=os.path.join(nginx_path,"wzry_history", file_name)
    writerl(save_path,res)
    return templates.TemplateResponse(
        "SingleBattleList.html",
        {
            "request": request,
            # "userfiles":{"a":os.path.join("wzry_history","ed5db8f34da0d8e8.json")},
            "filename": os.path.join("wzry_history",file_name),
            "key":key,
        }
    )
@app.get("/jump-btldetail", response_class=HTMLResponse)
async def jump_btldetail(request:Request,gameSvr: str,gameSeq: str,targetRoleId: str, relaySvr: str,battleType:str,key:str):
    if (not r.exists(key)):
        return templates.TemplateResponse(
            "err_illegal.html",{"request": request,"message":"key失效"}
        )
    try:
        res=wzry_get_official(reqtype="btldetail",gameseq=gameSeq,gameSvrId=gameSvr,relaySvrId=relaySvr,roleid=int(targetRoleId),pvptype=battleType)
    except Exception as e:
        return templates.TemplateResponse(
            "err_illegal.html",{"request": request,"message":"网络错误或id错误"}
        )
    file_name=secrets.token_hex(8)+".json"
    save_path=os.path.join(nginx_path,"wzry_history", file_name)
    writerl(save_path,res)
    return templates.TemplateResponse(
        "BattleDetail.html",
        {
            "request": request,
            # "userfiles":{"a":os.path.join("wzry_history","ed5db8f34da0d8e8.json")},
            "filename": os.path.join("wzry_history",file_name),
            "key":key,
            "gameSeq":gameSeq,
            "gameSvr":gameSvr,
            "relaySvr":relaySvr,
            "targetRoleId":targetRoleId,
            "battleType":battleType,
        }
    )
@app.get("/like-btldetail", response_class=HTMLResponse)
async def like_btldetail(request:Request,gameSeq: str,key:str):
    if (not r.exists(key)):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"key失效",
                "error_code": "LIKE_FAILED"
            }
        )
    happen_time=int(time.time())
    if (r_liked_btl.exists(gameSeq)):
        result=r_liked_btl.delete(gameSeq) 
        success_data={
            "success": True,
            "message": "取消收藏成功",
            "data": {
                "battle_id": gameSeq,
                "timestamp": happen_time
            }
        }
    else:
        r_liked_btl.set(gameSeq,happen_time)
        success_data={
            "success": True,
            "message": "收藏成功",
            "data": {
                "battle_id": gameSeq,
                "timestamp": happen_time
            }
        }
    return JSONResponse(success_data)
@app.get("/share-btldetail", response_class=HTMLResponse)
async def share_btldetail(request:Request,gameSvr: str,gameSeq: str,targetRoleId: str, relaySvr: str,battleType:str,key:str):
    if (not r.exists(key)):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"key失效",
                "error_code": "LIKE_FAILED"
            }
        )
    params={
        "gameSvrId":gameSvr,
        "gameseq":gameSeq,
        "roleid":targetRoleId,
        "relaySvrId":relaySvr,
        "pvptype":battleType
    }
    try:
        json_params = json.dumps(params)
        result = r_share_pool.lpush("Shared_queue", json_params)
        current_length = r_share_pool.llen("Shared_queue")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "数据库操作失败",
                "error_code": "DB_OPERATION_ERROR"
            }
        )
    
    happen_time=int(time.time())
    success_data={
        "success": True,
        "message": "分享成功",
        "data": {
            "battle_id": gameSeq,
            "timestamp": happen_time
        }
    }
    return JSONResponse(success_data)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)