
from .zutil import *
from .zstatic import *
from . import zdynamic as dmc

import nonebot
from nonebot import get_plugin_config,require
from nonebot_plugin_apscheduler import scheduler
from nonebot.rule import to_me,Rule
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, Event, Message,MessageEvent,MessageSegment
from nonebot.adapters import MessageTemplate
from nonebot.adapters.onebot.v11.event import PokeNotifyEvent
from nonebot.plugin import on_message,on_notice,on_request,on_keyword,on_command,on_regex,on_fullmatch
require("nonebot_plugin_apscheduler")

async def judge_to_me(event)->bool:
    return event.get_plaintext().startswith("#") or event.get_plaintext().startswith("＃")
async def judge_herostatistics_query(event)->bool:
    rcv_msg=event.get_plaintext()
    if ("的" not in rcv_msg): return False
    if (len(rcv_msg)>=12): return False
    return True
async def judge_super(event)->bool:
    return str(confs["QQBot"]["super_qid"])==str(event.get_user_id())
async def judge_unsuper(event)->bool:
    return str(confs["QQBot"]["super_qid"])!=str(event.get_user_id())
async def check_repair(event)->bool:
    return dmc.repair
async def check_btl_request(event)->bool:
    return last_request_btllist!=[]
# EVENT
_group_poke = on_notice()
_repair=on_keyword({"##r"},rule=judge_super,priority=1, block=True)
_execute=on_keyword({"##e"},rule=judge_super,priority=1, block=True)
_test=on_keyword({"##t"},rule=judge_super,priority=1, block=True)
_update_local=on_keyword({"##u"},rule=judge_super,priority=1, block=True)
_forward=on_keyword({"##f"},rule=judge_super,priority=1, block=True)
_pure_chat=on_keyword({"##c"},rule=judge_super,priority=1, block=True)
_super_only = on_keyword({"##amnesia"},rule=judge_super,priority=1, block=True)
_all_only = on_keyword({"##memory"},rule=judge_super,priority=1, block=True)

_blocked=on_message(rule=Rule(judge_to_me,check_repair,judge_unsuper),priority=2, block=True)

_show_code=on_fullmatch("code",rule=judge_to_me,priority=3, block=True)
_empty_cache = on_keyword({"empty_cache"},rule=judge_to_me,priority=3, block=True)
_show_cache = on_keyword({"show_cache"},rule=judge_to_me,priority=3, block=True)
_forget_me=on_keyword({"清除记忆"},rule=judge_to_me,priority=3, block=True)
_manual=on_fullmatch("#帮助",rule=judge_to_me,priority=3, block=True)
_forever_mem=on_keyword({"记住"},rule=judge_to_me,priority=3, block=True)

_atall=on_fullmatch(tuple(atall_keywords),priority=4, block=True)
_rnk=on_keyword(set(rnk_keywords),rule=judge_to_me,priority=4, block=True)
_single=on_keyword(set(single_keywords),rule=judge_to_me,priority=4, block=True)
_btlview=on_keyword(set(btlview_keywords),rule=judge_to_me,priority=4, block=True)
_btldetail=on_keyword(set(btldetail_keywords),rule=judge_to_me,priority=4, block=True)
_heropower=on_keyword(set(heropower_keywords),rule=judge_to_me,priority=4, block=True)
_herostatistics=on_keyword(set(HeroNames),rule=Rule(judge_to_me,judge_herostatistics_query),priority=4, block=True)
_todayhero=on_keyword({"今日英雄"},rule=judge_to_me,priority=4, block=True)
# _allhero=on_keyword(set(allhero_keywords),rule=judge_to_me,priority=4, block=True)
_showonline=on_keyword({"在线"},rule=judge_to_me,priority=4, block=True)
_gradeanalyze=on_keyword({"分析"},rule=judge_to_me,priority=4, block=True)
_watchbattle=on_keyword({"ob"},rule=judge_to_me,priority=4, block=True)

_chat=on_message(rule=judge_to_me,priority=6, block=True)
# HANDLER
@_blocked.handle()
async def f_blocked(event):
    from .zfunc import qid2nick
    from .ztime import wait
    log_message("AT UNDER REPAIR")
    wait()
    await _blocked.finish(Message(f"🤖暂时离线，{qid2nick(event.get_user_id())}请稍等。"))

@_execute.handle()
async def f_execute(event):
    rcv_msg=event.get_plaintext().replace("##e","")
    from . import zapi
    from . import zevent
    from . import zfile
    from . import zfunc
    from . import zscheduler
    from . import ztime
    from . import zdebug
    # try:
    ret=str(eval(rcv_msg))
    # except Exception as e:
    #     ret=str(e)
    await _execute.finish(Message(ret))

@_update_local.handle()
async def f_update_local(event):
    # global confs
    with open('variables_dynamic.json', 'r', encoding='utf-8') as file:
        varia = json.load(file)
    vars(dmc).update(varia)
    # with open('config.yaml', 'r') as file:
    #     confs = yaml.load(file, Loader=yaml.FullLoader)
    load_yesterday(1)
    await _update_local.finish(Message("变量配置已更新"))

@_test.handle()
async def f_test(event):
    rcv_msg=event.get_plaintext()
    await _test.finish(Message(rcv_msg))

@_forward.handle()
async def f_forward(bot,event):
    log_message("FORWARD")
    bot = nonebot.get_bot(confs["QQBot"]["bot_qid"])
    snd_msg=event.get_plaintext().replace("##f","")
    log_message("SEND: "+snd_msg)
    await bot.send_group_msg(group_id=confs["QQBot"]["group_qid"], message=snd_msg)
@_pure_chat.handle()
async def f_pure_chat(bot,event):
    from .zfunc import ai_parser
    rcv_msg=event.get_plaintext()
    snd_msg=""
    try:
        snd_msg+=ai_parser([rcv_msg],"pure_chat")
    except Exception as e:
        await _pure_chat.send(str(e))
        return
    await _pure_chat.send(snd_msg)
@_repair.handle()
async def f_repair(bot,event):
    if (dmc.repair):
        log_message("REPAIR: 1->0")
        dmc.repair=False
        await _repair.finish(Message("关闭repair"))
    else:
        log_message("REPAIR: 0->1")
        dmc.repair=True
        await _repair.finish(Message("开启repair"))

@_show_code.handle()
async def f_show_code(bot,event):
    from .ztime import short_wait,wait
    wait()
    await _show_code.send(Message("Code on Github："))
    wait()
    await _show_code.send("https://github.com/zhdxlz/HOK_QQBot_showcase/")

@_group_poke.handle()
async def f_group_poke(bot, event):
    from .zfunc import qid2nick
    from .zfunc import ai_parser
    from .zfunc import get_emoji_url
    from .zfunc import coplayer_process
    from .ztime import short_wait,wait
    from .ztime import time_r
    from .ztime import str_to_time,time_to_str
    from .ztime import calc_gap
    from .zfile import file_exist
    from .ztime import add_second
    
    if isinstance(event, PokeNotifyEvent):
        if event.target_id == event.self_id: 
            if (not dmc.repair):
                if (dmc.RTMPStatus):
                    res=dmc.RTMPListener.screenshot()
                    wait()
                    pic_path="/usr/local/nginx/html/wzry_btl_shot/"+str(dmc.RTMPPlayer)+".png"
                    
                    if (res and file_exist(pic_path)): snd_msg = MessageSegment.image(pic_path)
                    else: snd_msg=MessageSegment.text("最快10秒ob一次")
                    await _group_poke.send(snd_msg)
                    return
                elif (dmc.LastBtlMsgStatus and calc_gap(time_r(),str_to_time(dmc.LastBtlMsgTime))<600):
                    dmc.LastBtlMsgStatus=False
                    dmc.LastBtlMsgCoolDownTime=time_to_str(add_second(time_r(),30))
                    try:
                        ret_msg=coplayer_process(**dmc.LastBtlParams,roleid=dmc.LastBtlRoleId)
                    except Exception as e: 
                        short_wait()
                        await _group_poke.send(str(e))
                        wait()
                        await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message=traceback.format_exc())
                        return
                    txt_msg,pic_path=ret_msg
                    snd_msg=MessageSegment.text(txt_msg)+MessageSegment.image(pic_path)
                    await _group_poke.send(snd_msg)
                    return
                elif (time_r()<str_to_time(dmc.LastBtlMsgCoolDownTime)):# 若两条戳一戳时间较近，防止误触发戳一戳消息，直接屏蔽
                    return
                else:
                    user_id = event.user_id
                    userqid=event.get_user_id()
                    try:
                        groupqid=event.group_id
                    except Exception as e:
                        groupqid=None

                    send_type=(random.random()>-1)
                    if send_type:
                        snd_msg=ai_parser([qid2nick(userqid),str(datetime.datetime.now())],"poke")
                    else:
                        pic_index=random.randint(1,emoji_amount+1)
                        emoji_url=get_emoji_url(pic_index)
                        snd_msg = MessageSegment.image(emoji_url)
                        wait()
                    await _group_poke.send(snd_msg)
                    return
                    # time.sleep(0.3)
                    # await bot.group_poke(group_id=groupqid, user_id=userqid)
            else:
                await f_blocked(event)
                return
                
@_empty_cache.handle()
async def f_empty_cache(event): # 清空全局记录和用户(自己的)记录
    from .ztime import short_wait
    log_message("CMD: EMPTY_CACHE")
    dmc.ai_memory.clear()
    userqid=event.get_user_id()
    file_path=os.path.join("chats",userqid+".json")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        pass
    short_wait()
    await _empty_cache.finish(Message("成功清空缓存"))

@_show_cache.handle()
async def f_show_cache(event):
    log_message("CMD: SHOW_CACHE")
    await _show_cache.finish(Message("缓存内容："+"".join(dmc.ai_memory)))

@_forget_me.handle()
async def f_forget_me(event): # 清空用户记录和用户(自己的)记忆
    log_message("CMD: EMPTY_ME")
    userqid=event.get_user_id()
    file_path=os.path.join("chats",userqid+".json")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        pass
    file_path=os.path.join("memory",userqid+".json")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        pass
    await _forget_me.finish(Message("成功清除记忆"))

@_forever_mem.handle()
async def f_forever_mem(event):
    from .zfile import mem_dumper
    from .zfunc import qid2nick
    from .ztime import short_wait
    log_message("CMD: FOREVER")
    userqid=event.get_user_id()
    rcv_msg=event.get_plaintext()
    mem_dumper(userqid,rcv_msg)
    snd_msg=rcv_msg.replace("记住", "").replace("我",qid2nick(userqid)).replace("不会","一定不会").replace("哦","").replace(","," ")
    short_wait()
    await _forever_mem.finish(Message("好的，我记住了哦："+snd_msg))

@_manual.handle()
async def f_manual(event):
    log_message("CMD: MANUAL")
    from .ztime import short_wait,wait
    wait()
    await _show_code.send(Message("Code on Github："))
    wait()
    await _show_code.send("https://github.com/zhdxlz/HOK_QQBot_showcase/")

@_super_only.handle()
async def f_super_only(event):
    log_message("CMD: AMNESIA")
    dmc.amnesia=True
    await _super_only.finish(Message("AMNESIA success"))

@_all_only.handle()
async def f_all_only(event):
    log_message("CMD: RECOVERY")
    dmc.amnesia=False
    await _all_only.finish(Message("RECOVERY success"))

@_atall.handle()
async def f_atall(bot,event):
    from .zfunc import ai_parser

    # at_msg=""
    # for name,id in qid.items():
    #     at_msg+=MessageSegment.at(str(id))
    # await _atall.send(at_msg)
    urge_msg=ai_parser([str(datetime.datetime.now()),str(namenick),dmc.today_news],"urge_game")
    await _atall.send(urge_msg)
    return
@_showonline.handle()
async def f_showonline(bot,event):
    from .zfunc import online_process
    snd_msg=online_process()
    await _showonline.send(snd_msg)
@_rnk.handle()
async def f_rnk(bot,event):
    from .zfunc import qid2nick
    from .zfunc import generate_greeting
    from .zfunc import rnk_process
    from .ztime import short_wait
    from .ztime import wait
    from .ztime import time_r
    from .ztime import calc_gap
    
    dmc.rank_query_late=datetime.datetime.now()
    rcv_msg=event.get_plaintext()
    debug="#" in rcv_msg
    log_message("VISIT: RANK_FUNCTION")
    # if (calc_gap(time_r(),dmc.LastAllRequestTime)<180): return # 防止重复冗余请求
    # dmc.LastAllRequestTime=time_r()
    userqid=event.get_user_id()
    try:
        groupqid=event.group_id
    except Exception as e:
        groupqid=None
    snd_msg=qid2nick(userqid)+" "+generate_greeting()+"\n"
    if (groupqid):
        short_wait()
        await bot.group_poke(group_id=groupqid, user_id=userqid)
    try:
        rnk_info=rnk_process(rcv_msg=rcv_msg,caller=qid2nick(userqid),show_zero=False,show_analyze=True,debug=debug)
        snd_msg+=rnk_info[0]
    except Exception as e:
        short_wait()
        await _rnk.send(str(e))
        wait()
        await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message=traceback.format_exc())
        return
    await _rnk.send(snd_msg)
    # if (groupqid):
    #     for poked in rnk_info[1]:
    #         if (poked!="" and poked in idname):
    #             await bot.group_poke(group_id=groupqid, user_id=qid[idname[poked]])
    return
@_single.handle()
async def f_single(bot,event):
    log_message("VISIT: SINGLEPLAYER_FUNCTION")
    from .zfunc import qid2nick
    from .zfunc import single_process
    from .zfunc import get_emoji
    from .zfunc import get_emoji_url
    from .zfunc import btldetail_process # 附带解析最后一局
    from .zfunc import check_btl_official_with_matching
    from .ztime import short_wait
    from .ztime import wait

    whether_emoji=(random.random()>1)
    userqid=event.get_user_id()
    rcv_msg=event.get_plaintext().replace("我",qid2nick(userqid))
    try:
        groupqid=event.group_id
    except Exception as e:
        groupqid=None
    if (groupqid):
        short_wait()
        await bot.group_poke(group_id=groupqid, user_id=userqid)
    try:
        sgl_info=single_process(rcv_msg)
    except Exception as e:
        short_wait()
        await _single.send(str(e))
        wait()
        await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message=traceback.format_exc())
        # await _single.send(traceback.format_exc())
        return
    if (not sgl_info): return
        
    await _single.send(sgl_info[0])
    
    if (whether_emoji):
        emoji_random=random.random()
        if (emoji_random<0.2): pic_index=random.randint(1,emoji_amount+1)
        else: pic_index=get_emoji(sgl_info[0])
    if (sgl_info[2] and whether_emoji):
        emoji_url=get_emoji_url(pic_index)
        emoji_data =  MessageSegment.image(emoji_url)
        await _single.send(emoji_data)

    if (sgl_info[3]): # 有合法的局
        last_btl_roleid=sgl_info[4]
        try:
            btl_info,picpath=btldetail_process(**sgl_info[3],roleid=last_btl_roleid,gen_image=True)
        except Exception as e:
            short_wait()
            await _single.send(str(e))
            wait()
            await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message=traceback.format_exc())
            # await _single.send(traceback.format_exc())
            return
        if (btl_info):
            snd_msg=MessageSegment.text(btl_info)+MessageSegment.image(picpath)
            await _single.send(snd_msg)

    # if (groupqid):
    #     for poked in sgl_info[1]:
    #         await bot.group_poke(group_id=groupqid, user_id=qid[idname[poked]])
        
    return
@_btlview.handle()
async def f_btlview(bot,event):
    def get_last_number_after_dash(text):
        last_dash = text.rfind('-')
        if last_dash != -1:
            after = text[last_dash + 1:]
            # 提取连续数字
            digits = ''.join(filter(str.isdigit, after))
            return int(digits) if digits else None
        return analyze_time_gap

    from .zfunc import view_process
    rcv_msg=event.get_plaintext()
    time_gap=get_last_number_after_dash(rcv_msg)
    snd_msg=view_process(rcv_msg=rcv_msg,time_gap=time_gap)
    await _btlview.send(snd_msg)
    return
@_btldetail.handle()
async def f_btldetail(bot,event):
    from .zfunc import btldetail_process
    last_btl_params=dmc.last_request_btllist[0]['Params']
    linkurl,picpath=btldetail_process(**last_btl_params)
    await _btldetail.send(linkurl)
@_heropower.handle()
async def f_heropower(bot,event):
    from .zfunc import heropower_process
    from .zfunc import qid2nick

    userqid=event.get_user_id()
    rcv_msg=event.get_plaintext().replace("我",qid2nick(userqid))
    
    snd_msg=heropower_process(rcv_msg)
    
    await _heropower.send(snd_msg)
@_herostatistics.handle()
async def f_herostatistics(bot,event):
    from .zfunc import herostatistics_process
    from .zfunc import qid2nick
    from .ztime import short_wait
    
    userqid=event.get_user_id()
    rcv_msg=event.get_plaintext().replace("我",qid2nick(userqid))
    
    snd_msg=herostatistics_process(rcv_msg)
    short_wait()
    await _heropower.send(snd_msg)
@_todayhero.handle()
async def f_todayhero(bot,event):
    from .zfunc import qid2realname
    from .zfunc import todayhero_process

    userqid=event.get_user_id()
    realname=qid2realname(userqid)
    rcv_msg=event.get_plaintext()
    if ("的" in rcv_msg): snd_msg="只能查询自己的今日英雄"
    else:
        ai_comment=False if ("$" in rcv_msg) else True
        ignore_limit=True if ("%" in rcv_msg) else False
        appoint_realname=True if ("~" in rcv_msg) else False
        if (appoint_realname):
            from .zfunc import extract_name
            matching_name=extract_name(rcv_msg)
            if (matching_name!="name_error"): 
                realname=matching_name
        hero_msg,play_reason,pic_path=todayhero_process(realname,ignore_limit,ai_comment)
        snd_msg=MessageSegment.text(hero_msg)+MessageSegment.image(pic_path)+MessageSegment.text(play_reason)

    await _todayhero.send(snd_msg)
    
# @_allhero.handle()
# async def f_allhero(bot,event):
#     from .zfunc import allhero_process
#     from .zfunc import qid2nick

#     userqid=event.get_user_id()
#     rcv_msg=event.get_plaintext().replace("我",qid2nick(userqid))
    
#     snd_msg=allhero_process(rcv_msg)
    
#     await _allhero.send(snd_msg)
@_gradeanalyze.handle()
async def f_gradeanalyze(bot,event):
    from .zfunc import gradeanalyze_process
    from .zfunc import qid2nick

    userqid=event.get_user_id()
    rcv_msg=event.get_plaintext().replace("我",qid2nick(userqid))
    
    img_url,analyze_msg=gradeanalyze_process(rcv_msg)
    # print(img_url)
    # await _gradeanalyze.send(MessageSegment.image(img_url)+MessageSegment.text(analyze_msg))
    await _gradeanalyze.send(MessageSegment.image(img_url))
@_watchbattle.handle()
async def f_watchbattle(bot,event):
    from .zfunc import watchbattle_process
    from .zfunc import qid2nick
    from .zfile import file_exist

    userqid=event.get_user_id()
    rcv_msg=event.get_plaintext().replace("我",qid2nick(userqid))
    
    img_url,analyze_msg=watchbattle_process(rcv_msg)
    # print(img_url)
    # await _gradeanalyze.send(MessageSegment.image(img_url)+MessageSegment.text(analyze_msg))
    if (file_exist(img_url)): await _gradeanalyze.send(MessageSegment.image(img_url))

@_chat.handle()
async def f_chat(bot,event):
    from .zfile import chats_loader
    from .zfile import chats_dumper
    from .zfile import mem_loader
    from .zfunc import qid2nick
    from .zfunc import ai_parser
    from .ztime import short_wait
    from .ztime import wait
    from .ztime import short_wait
    
    userqid=event.get_user_id()
    
    try:
        groupqid=event.group_id
    except Exception as e:
        groupqid=None
        
    if (groupqid):
        short_wait()
        await bot.group_poke(group_id=groupqid, user_id=userqid)
    my_temp_msg=chats_loader(userqid)
    perp_msg=mem_loader(userqid)
    rcv_msg=event.get_plaintext().replace("我",qid2nick(userqid))
    rcv_msg+=" "+(str(event.reply.message) if event.reply else "")+" "
    snd_msg=""
    ori_use_mem=dmc.use_mem

    network=False
    if ("&" in rcv_msg): network=True

    if ("nomem" in rcv_msg): 
        dmc.use_mem=False
    try:
        snd_msg+=ai_parser([rcv_msg,my_temp_msg,perp_msg,qid2nick(userqid)],"chat",network)
    except Exception as e:
        short_wait()
        await _rnk.send(str(e))
        wait()
        await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message=traceback.format_exc())
        return
    dmc.use_mem=ori_use_mem
    chats_dumper(userqid,rcv_msg,snd_msg)
    await _chat.send(snd_msg)
    return


@scheduler.scheduled_job("cron", hour=bound_hour, minute=bound_minute+5, second=00, id="load_yesterday") # 每日3:30定时加载昨日数据
def load_yesterday(imple_type=0):# 程序重启/定时任务
    from .ztime import time_sul
    from .zfile import readerl
    
    yesterday_date=(time_sul()-datetime.timedelta(days=1)).strftime("%Y-%m-%d") # 将真实时间减去boundary后的日期
    log_message("LOADLIST "+yesterday_date+".json")
    try:
        filename=os.path.join("history",yesterday_date+".json")
        gameinfo=readerl(filename)
        for item in gameinfo:
            dmc.infolast[item['key']]={}
            for key,value in item.items():
                dmc.infolast[item['key']][key]=value
    except Exception as e:
        return
    return

# @scheduler.scheduled_job("cron", hour=17, minute=24, second=10, id="dump_today") # 每日3:25定时导出当日数据（预留5分钟导出时间）
@scheduler.scheduled_job("cron", hour=bound_hour, minute=bound_minute-5, second=00, id="dump_today") # 每日3:25定时导出当日数据（预留5分钟导出时间）
async def dump_today():
    from .ztime import time_sul
    from .zfunc import wzry_data
    from .zfile import writerl
    import time

    # bot = nonebot.get_bot(confs["QQBot"]["bot_qid"])
    dump_date=time_sul().strftime("%Y-%m-%d") # 因为提早了5分钟，所以时间就是在导出的日期
    log_message("DUMPBEGIN "+dump_date+".json")
    gameinfo=[]
    # dmc.export_btldetail_lock.lock()
    for key in userlist:
        try:
            gameinfo.append(wzry_data(realname=key,savepath=os.path.join("history", "personal", dump_date, str(userlist[key]) + ".json"))) # dump -- 每个人
            time.sleep(0.3)
        except Exception as e:
            # await bot.send_group_msg(group_id=confs["QQBot"]["group_qid"], message=traceback.format_exc())
            continue
    # dmc.export_btldetail_lock.release()
    filename=os.path.join("history",dump_date+".json")
    writerl(filename,gameinfo)
    log_message("DUMPEND "+dump_date+".json")
    return

@scheduler.scheduled_job("cron", hour=23, minute=30,second=00, id="notify_msg")
async def notify_msg():
    from .zfunc import rnk_process
    from .ztime import wait

    log_message("NOTIFY"+str(datetime.date.today()))
    bot = nonebot.get_bot(confs["QQBot"]["bot_qid"])
    snd_msg="今日王者战报(每日23:30推送)：\n"
    try:
        snd_msg+=rnk_process(rcv_msg="",caller=None,show_zero=False,show_analyze=True)[0]
    except Exception as e:
        wait()
        await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message=traceback.format_exc())
        return
    log_message("SEND: "+snd_msg)
    await bot.send_group_msg(group_id=confs["QQBot"]["group_qid"], message=snd_msg)
# @scheduler.scheduled_job("cron", hour=10, minute=2,second=50, id="test_msg")
# async def test_msg():
#     bot = nonebot.get_bot(confs["QQBot"]["bot_qid"])
#     await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message="Test OK.")
# @scheduler.scheduled_job("cron", hour=9, minute=00,second=00, id="check_festival") # 每日9:00推送节日祝福
async def check_festival():
    from .ztime import time_r
    from .zfunc import ai_parser
    
    log_message("FESTIVAL")
    snd_msg=""
    bot = nonebot.get_bot(confs["QQBot"]["bot_qid"])
    today_date=time_r().strftime("%m-%d")
    ai_back=ai_parser([today_date],"festival")
    snd_msg=ai_back
    if (snd_msg!="NONE"):
        snd_msg="来自🤖的节日祝福：\n"+snd_msg
        log_message("SEND: "+snd_msg)
        await bot.send_group_msg(group_id=confs["QQBot"]["group_qid"], message=snd_msg)
@scheduler.scheduled_job("cron", hour=7, minute=00,second=00, id="fetch_news")  # 每日7点获取当日新闻，并入提示词
async def fetch_news():
    from .zapi import ark_api
    from .ztime import date_r
    from .zfile import file_exist
    from .zfile import readera
    from .zfile import writera
    log_message("FETCH_NEWS")

    current_date = date_r()
    news_dir = "news"
    file_path = os.path.join(news_dir, f"{current_date}.txt")
    
    if file_exist(file_path):
        dmc.today_news=readera(file_path)
    else:
        dmc.today_news = ark_api(fetch_news_pmpt)
        writera(file_path,dmc.today_news)
    return None

def init_fetch_news():
    from .zapi import ark_api
    from .ztime import date_r
    from .zfile import file_exist
    from .zfile import readera
    from .zfile import writera
    log_message("FETCH_NEWS")
    
    current_date = date_r()
    news_dir = "news"
    file_path = os.path.join(news_dir, f"{current_date}.txt")
    
    if file_exist(file_path):
        dmc.today_news=readera(file_path)
    else:
        dmc.today_news = ark_api(fetch_news_pmpt)
        writera(file_path,dmc.today_news)
    return None
def init_fetch_heroranklist():
    from .zapi import wzry_get_official
    from .ztime import date_r
    from .zfile import file_exist
    from .zfile import readerl
    from .zfile import writerl
    
    current_date = date_r()
    herorank_dir = "herorank"
    file_path = os.path.join(herorank_dir, f"{current_date}.json")
    
    if file_exist(file_path):
        dmc.herorank=readerl(file_path)
    else:
        for _,rankId in hero_ranklist_rankids.items():
            dmc.herorank[rankId]=wzry_get_official(reqtype="heroranklist",rankId=rankId,rankSegment=4)
        writerl(file_path,dmc.herorank)
    
    return None
@scheduler.scheduled_job("interval", seconds=3, id="web_shared_processor")
async def run_web_shared_btls_processor():
    from .zfunc import btldetail_process
    from .ztime import wait

    result=dmc.redis_deamon_share_btl.rpop("Shared_queue")
    if (not result): return
    bot = nonebot.get_bot(confs["QQBot"]["bot_qid"])
    params_json=result
    params=json.loads(params_json)

    btl_msg,pic_path=btldetail_process(**params,gen_image=True,show_profile=True)
    snd_msg = MessageSegment.text(btl_msg)+MessageSegment.image(pic_path)
    # await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message=snd_msg)
    await bot.send_group_msg(group_id=confs["QQBot"]["group_qid"], message=snd_msg)

    return 
@scheduler.scheduled_job("interval", seconds=3, id="web_analyze_processor")
async def run_web_analyze_btls_processor():
    from .zfunc import coplayer_process
    from .zfunc import btldetail_process
    from .ztime import wait

    result = dmc.redis_deamon_analyze_btl.rpop("Analyze_queue")
    if (not result): return
    bot = nonebot.get_bot(confs["QQBot"]["bot_qid"])
    params_json=result
    params=json.loads(params_json)

    btl_msg,pic_path=btldetail_process(**params,gen_image=True,show_profile=True,from_web=True)
    snd_msg = MessageSegment.text(btl_msg)+MessageSegment.image(pic_path)
    await bot.send_group_msg(group_id=confs["QQBot"]["group_qid"], message=snd_msg)

    btl_msg,pic_path=coplayer_process(**params,from_web=True)
    snd_msg = MessageSegment.text(btl_msg)+MessageSegment.image(pic_path)
    # await bot.send_private_msg(user_id=confs["QQBot"]["super_qid"], message=snd_msg)
    await bot.send_group_msg(group_id=confs["QQBot"]["group_qid"], message=snd_msg)

    return 
@scheduler.scheduled_job("interval", seconds=5, id="message_sender")
async def message_sender():
    result = dmc.MessageQueue.rpop("MessageQueue")
    if (not result): return
    bot = nonebot.get_bot(confs["QQBot"]["bot_qid"])
    msg_str=result
    msg_json=json.loads(msg_str)
    msg_type=msg_json.get("type",None)
    to_id=msg_json.get("toid",None)
    msg_content=msg_json.get("content",None)
    if (msg_type=="group"):
        await bot.send_group_msg(group_id=to_id, message=msg_content)
    if (msg_type=="private"):
        await bot.send_private_msg(user_id=to_id, message=msg_content)
    return
def add_msg(form,content):
    result=None
    msg_jsons=[]
    if (form=="group"):
        msg_jsons.append({"type":"group","toid":confs["QQBot"]["group_qid"],"content":content})
    if (form=="superid"):
        msg_jsons.append({"type":"private","toid":confs["QQBot"]["super_qid"],"content":content})
    if (form=="error"):
        msg_jsons.append({"type":"group","toid":confs["QQBot"]["group_qid"],"content":content[0]})
        msg_jsons.append({"type":"private","toid":confs["QQBot"]["super_qid"],"content":content[1]})
    for msg_json in msg_jsons:
        result = dmc.MessageQueue.lpush("MessageQueue", json.dumps(msg_jsons))
    return result