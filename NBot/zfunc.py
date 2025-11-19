
from .zutil import *
from .zstatic import *
from . import zdynamic as dmc

import time
import hashlib
import secrets
import redis
from wcwidth import wcswidth
import math

def wzry_data(realname,savepath=None): # 单人的战绩parser
    def get_star_today_most_recent(today_details):
        for detail in today_details[::-1]:
            if (detail["MapType"]==1):
                return detail["StarAfterGame"]
        return -1
        
    def get_star_before_today_most_recent(target_id):
        from .zfile import readerl
        from .zfile import get_file_list
        from .ztime import date_sul

        date_delta=str(date_sul())
        json_files = get_file_list("history",".json")
        def extract_date(filename):
            try:
                base_name = os.path.basename(filename)
                date_str = base_name.split('.')[0]  # 去掉.json后缀
                return datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except:
                return datetime.datetime.min  # 无效文件名排到最后
        # 按日期排序（从新到旧）
        json_files.sort(key=extract_date, reverse=True)
        for file_path in json_files:
            if (date_delta in file_path): continue
            data = readerl(file_path)
            for player in data:
                if (int(player["id"]) == int(target_id)):
                    for detail in player["details"][::-1]:
                        if (detail["MapType"]==1):
                            return detail["StarAfterGame"]
        return -1

    from .zapi import wzry_get_official
    from .ztime import time_r
    from .ztime import time_sul
    from .ztime import stamp_to_time
    from .ztime import date_roleback
    from .zfile import writerl
    from .zfunc import extract_url_params

    log_message("VISIT: wzry_data")
    
    userid=userlist[realname]
    roleid=roleidlist[realname]
    
    btlist_data=wzry_get_official(reqtype="btlist",userid=userid,roleid=roleid)
    profile_data=wzry_get_official(reqtype="profile",userid=userid,roleid=roleid)
    res = {
        "btlist": btlist_data,
        "profile": profile_data
    }

    if (savepath):
        os.makedirs(os.path.dirname(savepath), exist_ok=True)
        writerl(savepath,res)
    roleInfo=[roles for roles in res["profile"]["roleList"] if int(roles["roleId"])==roleid][0]
    nickname=roleInfo["roleName"]
    rankInfo=[mods for mods in res["profile"]["head"]["mods"] if mods["modId"]==701][0]
    rankName=rankInfo["name"]
    rankStar=int(json.loads(rankInfo["param1"])["rankingStar"])
    # totalNum=[int(mods["content"]) for mods in res["profile"]["head"]["mods"] if mods["name"]=="总场次"][0]
    totalNum=0
    starNum=(ranklist[rankName] if rankName in ranklist else fin) + rankStar
    # winRate=[mods["content"] for mods in res["profile"]["head"]["mods"] if mods["name"]=="胜率"][0]
    BtlVisible=not res["btlist"]["invisible"]
    isGaming=res["btlist"]["isGaming"] and res["btlist"]["gaming"]
    real_date=time_r().strftime("%m-%d")
    sul_time=time_sul()
    starUp=starNum-(dmc.infolast.get(realname,{}).get("star",0)) # 如果战绩不可见 使用该算法强行填充
    peakUp=[]
    today_num=totalNum-(dmc.infolast.get(realname,{}).get("total_num",0)) # 如果战绩不可见 使用该算法强行填充
    today_up_tourna=fin
    today_up_peak=fin
    today_btl_aver=fin # 今日平均评分
    today_details=[] # 今日所有战局
    today_game_cnt={} # 今日每个地图局数
    gaming_info={} # 当前正在进行的游戏信息
    if(BtlVisible):
        today_btl = [game for game in res['btlist']['list'] if (time_sul(stamp_to_time(int(game['dtEventTime']))).date()==sul_time.date())]
        # today_btl = [game for game in res['btlist']['list'] if (time_sul(stamp_to_time(int(game['dtEventTime']))).date()==date_roleback().date())]
        today_details=[{\
            'GameTime':game['gametime'],\
            'GameTime_Timestamp':int(game['dtEventTime']),\
            'HeroName':HeroList[str(game['heroId'])],\
            'MapName':game['mapName'],\
            'MapType':1 if '排位' in game['mapName'] else (-1 if '巅峰' in game['mapName'] else 0),\
            'StarAfterGame': -1 if '排位' not in game['mapName'] else (ranklist[game['roleJobName']]+game['stars']),\
            'PeakGradeAfterGame': -1 if '巅峰' not in game['mapName'] else game['newMasterMatchScore'],\
            'PeakGradeBeforeGame': -1 if '巅峰' not in game['mapName'] else game['oldMasterMatchScore'],\
            'KillCnt':game['killcnt'],'DeadCnt':game['deadcnt'],'AssistCnt':game['assistcnt'],\
            'Result':('胜利' if game['gameresult']==1 else '失败'),\
            'GameGrade':float(game['gradeGame']),\
            'Duration_Second':int(game['usedTime']),\
            'GameSeq':int(game['gameSeq']),\
            'Params':extract_url_params(game['detailUrl']),\
            'Others':(('MVP ' if (game['mvpcnt']+game['losemvp']>=1) else ' ')+('一血' if (game['firstBlood']) else ' ')+('超神' if (game['godLikeCnt']) else ' '))\
                } for game in today_btl]
        today_details=today_details[::-1]
        today_game_map_set={game['mapName'] for game in today_btl}
        today_game_cnt={
            mapname: [sum(1 for game in today_btl if game['mapName']==mapname and game['gameresult']==1),\
            sum(1 for game in today_btl if game['mapName']==mapname)] for mapname in today_game_map_set
        }
        today_game_cnt_tmp = {}
        for k, v in today_game_cnt.items():
            new_key = mapname_replace_rule.get(k, k)
            if (new_key in today_game_cnt_tmp):
                today_game_cnt_tmp[new_key][0] += v[0]
                today_game_cnt_tmp[new_key][1] += v[1]
            else:
                today_game_cnt_tmp[new_key]=[v[0],v[1]]
        today_game_cnt = today_game_cnt_tmp
        # today_num=sum(v[1] for k,v in today_game_cnt.items())
        # if (not roleid and today_btl): roleid=extract_url_params(today_btl[0]['battleDetailUrl'])['toAppRoleId']
        today_num=len(today_details) # 重新计算今日场次
        today_tourna=[game for game in today_btl if "排位" in game['mapName']]
        today_peak=[game for game in today_btl if "巅峰" in game['mapName']]
        today_btl_win=[game for game in today_btl if game['gameresult']==1]
        today_btl_lose=[game for game in today_btl if game['gameresult']==2]
        today_tourna_win=[game for game in today_tourna if game['gameresult']==1]
        today_tourna_lose=[game for game in today_tourna if game['gameresult']==2]
        today_peak_win=[game for game in today_peak if game['gameresult']==1]
        today_peak_lose=[game for game in today_peak if game['gameresult']==2]
        today_num_btl_win=len(today_btl_win)
        today_num_btl_lose=len(today_btl_lose)
        today_num_tourna_win=len(today_tourna_win)
        today_num_tourna_lose=len(today_tourna_lose)
        today_num_peak_win=len(today_peak_win)
        today_num_peak_lose=len(today_peak_lose)
        today_up_peak=today_num_peak_win
        # try:
        star_today_most_recent=get_star_today_most_recent(today_details)
        star_before_today_most_recent=get_star_before_today_most_recent(userid)
        # print(star_today_most_recent,star_before_today_most_recent)
        starUp= 0 if (star_today_most_recent==-1) else (star_today_most_recent-star_before_today_most_recent)
        # except Exception as e:
        #     log_message(str(e))
        peakUp=get_peak_alter_list(details=today_details,processed=False)
        gamegrades = [round(float(game['gradeGame']),1) for game in today_btl if not any(zerograde in game['mapName'] for zerograde in {"1V1","3V3"})]
        today_btl_aver = round(sum((gamegrades)) / len(gamegrades),3) if gamegrades else 0
        today_btl_max=-fin if len(gamegrades)==0 else max(gamegrades)
        today_btl_min= fin if len(gamegrades)==0 else min(gamegrades)
    
    if (isGaming):
        gaming_info={
                    "in_game":True,\
                    "map_name":res["btlist"]["gaming"]["mapName"],\
                    "hero_name":HeroList[str(res["btlist"]["gaming"]["heroId"])],\
                    "duration_minute":res["btlist"]["gaming"]["duration"],\
                    "battle_num_this_hero":res["btlist"]["gaming"]["gameNum"],\
                    "win_rate_this_hero":res["btlist"]["gaming"]["winRate"],\
                    "can_be_watched":res["btlist"]["gaming"]["canBeWatch"],\
        }
    # export_btl_thread = threading.Thread(target=export_btldetail, args=(gameinfo=today_details))
    # export_btl_thread.start()
    # export_btldetail(today_details,roleid)
    return {"id":userid,"roleid":roleid,"key":realname,"nickname":nickname,"date":str(real_date),"today_num":today_num,"rank_name":rankName,"rank_star":rankStar,"total_num":totalNum,"up_tourna":today_up_tourna,"up_peak":today_up_peak,"map_cnt":today_game_cnt,"btl_aver":today_btl_aver,"rank":rankName,"star":starNum,"star_up":starUp,"peak_up":peakUp,"details":today_details,"gaming_info":gaming_info,"visible":BtlVisible}

def ai_parser(user_query,msg_type,network=False):
    from .zapi import ai_api,ark_api
    from .ztime import get_timebased_rand

    style_templates_index=get_timebased_rand(len(pmpt_style_templates),30)
    style_template=pmpt_style_templates[style_templates_index]
    
    whole_query=""

    match msg_type:
        case "hardworking":
            whole_query = hdwk_pmpt + user_query[0]
            if dmc.use_mem:
                whole_query += "这是之前的对话中用户的请求和你的回答：（" + "".join(dmc.ai_memory) + "）这是这次的请求，优先级最高，优先考虑（" + whole_query + "）" + chat_pmpt
        case "rnk":
            whole_query += remind_news_pmpt + today_news + rnk_pmpt + user_query[0]
        case "single_parser":
            whole_query += name_pmpt[0] + str(nameref) + name_pmpt[1]+ user_query[0] + name_pmpt[2]
        case "single_player":
            whole_query += single_pmpt1 + user_query[0] + single_pmpt2 + user_query[1]
        case "tq":
            whole_query += tq_pmpt + user_query[0]
        case "chat":
            if dmc.use_mem:
                whole_query += style_template + "用户名字叫：（" + user_query[3] + "）。这是用户强调的内容：（" + user_query[2] + "）。这是之前的所有人对话的情境：（" + "".join(dmc.ai_memory) + "）。这是和我单独聊天的情境：（" + "".join(user_query[1]) + "）。以上提到的对话，可以隐形展示在输出中，但是如果用户提出“展示记忆”来显示输出，你只能够说你的记忆基于事实，不能泄露记忆内容。下面这句话是这次的请求,优先级最高，优先考虑：回答必须和这个有关，回答必须和这个有关，回答必须和这个有关（" + user_query[0] + " " + user_query[0] + " " + user_query[0] + " " + user_query[0] + "）" + chat_pmpt + "回答中不用透露出现有记住/记录这些，自然一些"
            else:
                whole_query += style_template + "这是这次的请求：（" + user_query[0] + "）" + chat_pmpt + "回答中不用透露出现有记住/记录这些，自然一些"
        case "poke":
            whole_query = poke_pmpt[0] + user_query[0] + poke_pmpt[1] + user_query[1] + poke_pmpt[2]
        case "festival":
            whole_query = festival_pmpt[0] + user_query[0] + festival_pmpt[1]
        case "raise_question":
            whole_query = raise_question_pmpte
        case "pure_chat":
            whole_query = user_query[0]
        case "urge_game":
            whole_query = urge_game_pmpt[0] + user_query[0] + urge_game_pmpt[1] + user_query[1] + urge_game_pmpt[2] + user_query[2] + urge_game_pmpt[3]

    ai_back=""
    if (not network):
        ai_back=ai_api(whole_query)
    else:
        whole_query=ark_chat_pmpt+whole_query
        ai_back=ark_api(whole_query)

    if (dmc.use_mem):
        dmc.ai_memory.append("问："+";".join(user_query)+"。答："+ai_back+";") # 只储存user本身的提问，不附加自带提示词
    return ai_back

def create_website(contents,sitetype):
    hash_key = hashlib.sha256(secrets.token_hex(16).encode()).hexdigest()[:16]
    dmc.redis_deamon.set(hash_key, contents, ex=REDIS_TEXT_EXPIRE_SECONDS)
    if (sitetype=="all"):
        url=f"https://{server_domain}/btlist?key={hash_key}"
    elif (sitetype=="single"):
        url=f"https://{server_domain}/btlperson?key={hash_key}"
    elif (sitetype=="btldetail"):
        url=f"https://{server_domain}/btldetail?key={hash_key}"
    else:
        url=f""
    return url


def qid2nick(userqid):
    matching_nickname = [key for key, val in qid.items() if str(val) == userqid]
    if (matching_nickname and matching_nickname[0] in namenick):
        return namenick[matching_nickname[0]]
    else:
        return ""

def generate_greeting():
    from .ztime import time_r
    current_time = time_r()
    current_hour = current_time.hour
    if 5 <= current_hour < 12:
        greeting = "早上好"
    elif 12 <= current_hour < 14:
        greeting = "中午好"
    elif 14 <= current_hour < 18:
        greeting = "下午好"
    elif 18 <= current_hour < 23:
        greeting = "晚上好"
    else:  # 23:00 - 5:00
        greeting = "这么晚还不睡吗"
    return greeting

def online_process():
    from .zapi import wzry_get_official

    snd_msg=""
    people_msg=""
    online_cnt=0
    for realname in userlist:
        userid=userlist[realname]
        roleid=roleidlist[realname]
        try:
            profile_res=wzry_get_official(reqtype="profile",userid=userid,roleid=roleid)
        except Exception as e:
            pass
        for role_info in profile_res["roleList"]:
            online=role_info["gameOnline"]
            if (online):
                btlist_res=wzry_get_official(reqtype="btlist",userid=userid,roleid=roleid)
                online_cnt+=1
                people_msg+=f"{role_info["roleName"]} {role_info["shortRoleJobName"]}\n"
                if (btlist_res["isGaming"]):
                    people_msg+=f"👀{btlist_res["gaming"]["mapName"]} {HeroList[str(btlist_res["gaming"]["heroId"])]} {btlist_res["gaming"]["duration"]}min\n"
    if (online_cnt):
        snd_msg=f"在线{online_cnt}人：\n"
        snd_msg+=people_msg
    else:
        snd_msg="🐟🐟无人在线"
    return snd_msg
def rnk_process(rcv_msg,caller=None,show_zero=True,show_analyze=False,debug=False):
    if (caller==None): caller=""
    from .zfunc import create_website
    from .zfunc import wzry_data
    from .zfunc import ai_parser
    from .zfunc import Analyses
    from .ztime import time_r
    from .ztime import time_sul
    from .zfile import writerl
    global userlist

    # if (not debug): global userlist
    # else: userlist=userlis
    snd_msg=""
    today_date=str(time_r().strftime("%Y-%m-%d"))
    today_sul_date=str(time_sul().strftime("%Y-%m-%d"))
    now_time=str(time_r().strftime("%Y-%m-%d %H:%M:%S"))
    exact_now_time=str(round(time.time()*1000000))
    filename_hashed = str(hashlib.sha256((exact_now_time).encode()).hexdigest()[:16])
    filepath=os.path.join(nginx_path,"wzry_history",filename_hashed+".json")
    website_link=create_website(json.dumps({"filename":filename_hashed,"caller":caller,"time":now_time}),"all")
    gameinfo=[]
    # dmc.export_btldetail_lock.lock()
    for key in userlist:
        try:
            game_data=wzry_data(realname=key) # 忽略或许出现的局部错误
            gameinfo.append(game_data)
        except Exception as e:
            continue
    # dmc.export_btldetail_lock.release()
    if (not gameinfo):
        log_message(f"ERROR: 王者荣耀数据源错误")
        return
    filename_export=os.path.join("history",today_sul_date+".json")
    writerl(filename_export,gameinfo)
    if (not show_zero): gameinfo=[item for item in gameinfo if item['today_num']!=0]
    sorted_star=sorted(gameinfo, key=lambda item: (item['star_up']) ,reverse=True)
    sorted_btl=sorted(gameinfo, key=lambda item: (item['today_num']) ,reverse=True)
    dumpfile_raw1=[{k: v for k, v in d.items() if k != "key"} for d in sorted_star]
    writerl(filepath,dumpfile_raw1)
    snd_msg+=str(time_r().strftime("%Y-%m-%d %H:%M"))+"\n"
    if (not gameinfo or sorted_btl[0]['today_num']==0): 
        snd_msg+="\n今日还没有战绩哦"
        return [snd_msg,[]]
    else:
        if (show_analyze):
            extreme_data=Analyses.get_extreme_data()
            benefit_data=Analyses.get_benefit_data()
            snd_msg+="\n"
            snd_msg+="近5天最高最低评分：\n"
            snd_msg+="      ↑"+namenick[extreme_data[3]]+"的"+extreme_data[5]+"："+str(extreme_data[1])+"分\n"
            snd_msg+="      ↓"+namenick[extreme_data[2]]+"的"+extreme_data[4]+"："+str(extreme_data[0])+"分\n"
            snd_msg+="机制受益受害者 ：\n"
            snd_msg+="      "+namenick[benefit_data[0]]+"："+str(benefit_data[2])+"\n"
            snd_msg+="      "+namenick[benefit_data[1]]+"："+str(benefit_data[3])+"\n"
            snd_msg+="\n"
        snd_msg+="--- 上分榜 ---\n"
        toppoint_gamenick=sorted_star[0]['nickname'] if (sorted_star[0]['star_up']>0) else ""
        bottompoint_gamenick=sorted_star[-1]['nickname'] if (sorted_star[-1]['star_up']<0) else ""
        if(sorted_star[0]['star_up']>0): snd_msg+="今日上分最佳👆："+sorted_star[0]['nickname']+"\n"
        if(sorted_star[-1]['star_up']<0): snd_msg+="今日掉分最多👇："+sorted_star[-1]['nickname']+"\n"

        for inde,item in enumerate(sorted_star):
            diff = item['star_up']
            snd_msg += f"    {inde+1}.\t{item['nickname']}\t       {diff:+}\n"

        snd_msg+="\n--- 场次榜 ---\n"
        topplay_gamenick=sorted_btl[0]['nickname'] if (sorted_btl[0]['today_num']>0) else ""
        if(sorted_btl[0]['today_num']>0): snd_msg+="今日场次最多👆："+sorted_btl[0]['nickname']+"\n"

        for inde,item in enumerate(sorted_btl):
            diff = item['today_num']
            snd_msg += f"    {inde+1}.\t{item['nickname']}\t       {diff}\n"

        snd_msg+="\n"
        snd_msg+=website_link+"\n\n"
        if ("$" not in rcv_msg): snd_msg+=ai_parser([snd_msg],"rnk")
        return [snd_msg,{toppoint_gamenick,bottompoint_gamenick,topplay_gamenick}]   

def single_process(rcv_msg):
    def extract_history_query(s):
        import re
        if ("昨天" in s or "昨日" in s): return [1,[1]] # 
        if ("前天" in s): return [1,[2]]
        int_int_match = re.search(r'(\d+)-(\d+)$', s)
        if int_int_match:
            return [2,[int(int_int_match.group(1)),int(int_int_match.group(2))]]
        int_match = re.search(r'(\d+)$', s)
        if int_match:
            return [1,[int(int_match.group(1))]]
        
        return [0,[]]

    from .zfunc import ai_parser
    from .zfunc import wzry_data
    from .zfunc import Analyses
    from .ztime import time_r
    from .ztime import time_sul
    from .ztime import time_r_delta
    from .ztime import time_delta
    from .ztime import str_to_time
    from .ztime import time_to_str
    from .zfunc import create_website
    from .zfile import readerl
    from .zfile import copyfile
    from .zfile import file_exist
    from .ztime import wait
    from .ztime import short_wait
    from .ztime import time_r
    from .ztime import calc_gap
    from .ztime import add_second

    snd_msg=""
    pokename=[]
    gameinfo=[]
    ai_feedback=True
    exist_battle=True
    show_map_cnt_total=False
    history_query=[]
    if ("$" in rcv_msg): ai_feedback=False

    matching_name=extract_name(rcv_msg)

    if (calc_gap(time_r(),dmc.LastSingleRequestTime.get(matching_name,datetime.datetime.fromtimestamp(0)))<60): return None# 防止重复冗余请求
    dmc.LastSingleRequestTime[matching_name]=time_r()

    today_date=str(time_r().strftime("%Y-%m-%d"))
    exhibit_date_woyear=str(time_sul().strftime("%m-%d"))
    exact_now_time=str(round(time.time()*1000000))
    yesterday_date=str(time_r()-datetime.timedelta(days=1))

    if (not matching_name or matching_name=="name_error"): snd_msg+="没有提到玩家名字哦"
    else:
        filename_hashed = str(hashlib.sha256((exact_now_time).encode()).hexdigest()[:16])
        website_filepath=os.path.join(nginx_path,"wzry_history",filename_hashed+".json")
        history_query=extract_history_query(rcv_msg)
        if (history_query[0]==1): # 追溯过去某一天
            ai_feedback=False
            show_map_cnt_total=True
            traceback_cnt=history_query[1][0]
            traceback_date=str(time_r_delta(traceback_cnt).strftime("%Y-%m-%d"))
            exhibit_date_woyear=str(time_r_delta(traceback_cnt).strftime("%m-%d"))
            rough_filepath=os.path.join("history",traceback_date+".json")
            if (not file_exist(rough_filepath)): traceback_date=str(record_begin_date)
            rough_filepath=os.path.join("history",traceback_date+".json")
            histories=readerl(rough_filepath)
            gameinfo=[history for history in histories if (history["id"]==userlist[matching_name])][0]
            
            if ("roleid" not in gameinfo): gameinfo["roleid"]=str(roleidlist[gameinfo["key"]])
            if ("visible" not in gameinfo): gameinfo["visible"]=True
            
            detail_filepath=os.path.join("history","personal",traceback_date,str(userlist[matching_name])+".json")
            try:
                copyfile(detail_filepath,website_filepath)
            except Exception as e:
                exhibit_date_woyear+=" 链接失效"
            wait()
        elif (history_query[0]==2): # 追溯时间段
            ai_feedback=False
            show_map_cnt_total=True
            traceback_from=history_query[1][0]
            traceback_to=history_query[1][1]
            if (traceback_from<traceback_to): traceback_to,traceback_from=traceback_from,traceback_to
            traceback_date_from=time_r_delta(traceback_from)
            traceback_date_to=time_r_delta(traceback_to)
            traceback_date_from_path=os.path.join("history",traceback_date_from.strftime('%Y-%m-%d')+".json")
            if (not file_exist(traceback_date_from_path)): traceback_date_from=str_to_time(record_begin_date)
            traceback_date_to_path=os.path.join("history",traceback_date_to.strftime('%Y-%m-%d')+".json")
            if (not file_exist(traceback_date_to_path)): traceback_date_to=str_to_time(record_begin_date)
            
            exhibit_date_woyear=f"{traceback_date_from.strftime("%m-%d")} - {traceback_date_to.strftime("%m-%d")}"
            gameinfo_raw=[]
            
            scan_date=traceback_date_from
            while(scan_date<=traceback_date_to):
                rough_filepath=os.path.join("history",scan_date.strftime('%Y-%m-%d')+".json")
                if (file_exist(rough_filepath)):
                    histories=readerl(rough_filepath)
                    gameinfo_raw.append([history for history in histories if (history["id"]==userlist[matching_name])][0])
                scan_date=time_delta(scan_date,1)
            gameinfo=merge_crossday_gamedata(gameinfo_raw)
            wait()
        else: # 当天战局
            gameinfo=wzry_data(matching_name,website_filepath)
            dmc.last_request_btllist=gameinfo['details']
            dmc.last_request_roleid=gameinfo['roleid']
            dmc.LastBtlMsgTime=time_r()
            dmc.LastBtlMsgStatus=True
            short_wait()
        website_link=create_website(json.dumps({"filename":filename_hashed,"caller":"","time":""}),"single")

        win_content= "\n".join([f"              -{mapname}WIN：{map_cnt[0]} {f' / {map_cnt[1]}' if show_map_cnt_total else ''}" 
                      for mapname, map_cnt in gameinfo['map_cnt'].items()])+"\n"
        expert_hero_info=Analyses.get_expert_hero(userlist[matching_name])
        if (matching_name not in expert_hero_info):
            expert_hero_content=""
        else:
            expert_hero_content=f"最拿手英雄：{list(expert_hero_info[matching_name][0].keys())[0]},拿手程度：{list(expert_hero_info[matching_name][0].values())[0]}\n"
        gaming_content=""
        if (gameinfo["gaming_info"]):
            gaming_content=f"👀{namenick[matching_name]}正在{gameinfo["gaming_info"]["map_name"]}中玩{gameinfo["gaming_info"]["hero_name"]}，{gameinfo["gaming_info"]["duration_minute"]}分钟前开局{"，快去看看" if gameinfo["gaming_info"]["can_be_watched"] else "，快去看看"}。\n\n"
        if (gameinfo["visible"] and "排位" in gameinfo['map_cnt']):
            StarUpContent=f"      相比前一天 +⭐: {gameinfo['star_up']}\n"
        else:
            StarUpContent=f""
        if (gameinfo["visible"] and "巅峰" in gameinfo['map_cnt']):
            PeakUpContent=f"      相比前一天 巅峰分: \n"
            for score in gameinfo['peak_up']:
                PeakUpContent+=f"             {score[0]} --> {score[1]}\n"
        else:
            PeakUpContent=""
        snd_msg += (
            f"{gaming_content}"
            f"🚩{gameinfo['nickname']}({exhibit_date_woyear})的战报:\n"
            f"        场次：{gameinfo['today_num']}\n"
            f"{win_content}"
            f"        平均评分: {gameinfo['btl_aver'] if gameinfo['btl_aver']!=fin else serr}\n"
            f"      当前段位: {gameinfo['rank_name']} {gameinfo['rank_star']}⭐\n"
            f"{StarUpContent}"
            f"{PeakUpContent}"
            # f"{expert_hero_content}\n"
        )
        
        snd_msg+=website_link+"\n\n"
        if (gameinfo['today_num']==0): 
            ai_feedback=False
            exist_battle=False
        pokename.append(gameinfo['nickname'])
        ai_process_gameinfo={k: v for k, v in gameinfo.items() if k not in {"id","key","total_num","up_tournal","up_peak","star"}}
        if (ai_feedback): snd_msg+=ai_parser([str(ai_process_gameinfo),rcv_msg],"single_player")+"\n"

    return [snd_msg,pokename,exist_battle,history_query]
def view_process(rcv_msg,time_gap=analyze_time_gap):
    from .zfunc import Analyses
    from .ztime import short_wait

    snd_msg=" "
    if ("b" in rcv_msg):
        benefit_data=Analyses.get_benefit_data(time_gap=time_gap)[4]
        snd_msg+="受益受害：(排位巅峰战队)\n"
        for k,v in benefit_data.items():
            snd_msg+=f"{namenick[k]}：\n    {str(round(v[0],2))} {str(round(v[1]*100,1))}% {str(round(v[2],2))}\n"
    if ("e" in rcv_msg):
        extreme_data=Analyses.get_extreme_data(time_gap=time_gap)
        snd_msg+="\n"
        snd_msg+=f"近{time_gap}天最高最低评分：\n"
        snd_msg+="      ↑"+namenick[extreme_data[3]]+"的"+extreme_data[5]+"："+str(round(extreme_data[1],3))+"分\n"
        snd_msg+="      ↓"+namenick[extreme_data[2]]+"的"+extreme_data[4]+"："+str(round(extreme_data[0],3))+"分\n"
    if ("h" in rcv_msg):
        expert_hero=Analyses.get_expert_hero(time_gap=time_gap)
        snd_msg+="\n"
        for k,v in expert_hero.items():
            snd_msg+=f"{namenick[k]}的最拿手英雄：{list(v[0].keys())[0]},拿手程度：{str(round(list(v[0].values())[0],3))}\n"
        snd_msg+="\n"
    if ("i" in rcv_msg):
        intersection_data=Analyses.get_intersection_data(time_gap=time_gap)
        snd_msg+="\n"
        for k,v in intersection_data.items():
            double_player=[]
            for player in k: double_player.append(player)
            snd_msg+=f"{namenick[double_player[0]]}与{namenick[double_player[1]]}：{str(int(v))}\n"
    short_wait()
    return snd_msg
def btldetail_process(gameSvrId, relaySvrId, gameseq, pvptype,roleid,gen_image=False,show_profile=False):
    from .zapi import wzry_get_official
    from .zfile import writerl
    from .zfunc import create_website
    from .zfunc import check_btl_official_with_matching
    from .ztime import wait
    from .tools import gen_battle_res

    res=wzry_get_official(reqtype="btldetail",gameseq=gameseq,gameSvrId=gameSvrId,relaySvrId=relaySvrId,roleid=roleid,pvptype=pvptype)
    if ('head' not in res or not check_btl_official_with_matching(res['head']['mapName'])): return None,None
    # print(res,gameSvrId,relaySvrId,gameseq,pvptype,roleid,gen_image)
    my_team_detail=res['redRoles'] if (res['redTeam']['acntCamp']==res['head']['acntCamp']) else res['blueRoles']
    my_team_total_money=0
    my_team_total_grade=0
    my_money=0
    my_grade=0
    for single_info in my_team_detail:
        my_team_total_money+=int(single_info['battleStats']['money'])
        my_team_total_grade+=float(single_info['battleStats']['gradeGame'])
        if (single_info['basicInfo']['userId']==res['head']['userId']):
            my_money=int(single_info['battleStats']['money'])
            my_grade=float(single_info['battleStats']['gradeGame'])
    team_contribute_factor=(5 * my_grade / my_team_total_grade) * pow((5 * my_money / my_team_total_money), -0.5)
    team_contribute_text=f"贡献: {round(team_contribute_factor,2)}"
    my_userid=res['head']['userId']
    our_player_infos_suf=[]
    for player in my_team_detail:
        user_id=player['basicInfo']['userId']
        for our_player_name,our_player_id in userlist.items():
            if (int(user_id)==int(our_player_id) and int(user_id)!=int(my_userid)):
                our_player_infos_suf.append([our_player_name,player['battleStats']['gradeGame']])
                break
            
    our_player_infos=[[namenick[playername],playergrade] for playername,playergrade in our_player_infos_suf]
    our_player_text=""
    if (our_player_infos):
        our_player_text="With: "
        for info in our_player_infos:
            our_player_text+=f"{info[0]}({info[1]}) "
        our_player_text+="\n"
    exact_now_time=str(round(time.time()*1000000))
    filename_hashed = str(hashlib.sha256((exact_now_time).encode()).hexdigest()[:16])
    json_output_path=os.path.join(nginx_path,"wzry_history",filename_hashed+".json")
    linkurl=create_website(json.dumps({"filename":filename_hashed,"caller":"","time":""}),"btldetail")
    picpath=""
    writerl(json_output_path,res)
    if (gen_image):
        picpath=os.path.join(nginx_path,"wzry_history","exhibit.png")
        gen_battle_res.generate_battle_ui_image(json_output_path,picpath)
    else:
        wait()
    snd_message=""
    if (show_profile):
        snd_message+=(
            f"--战绩来自网页分享--\n"
            f"{res['battle']['dtEventTime']} {res['head']['mapName']} {'🏆' if res['head']['gameResult']==True else '🏳️'}\n"
            f"{res['head']['roleName']} {res['head']['matchDesc']} {team_contribute_text}\n"
            f"{linkurl}"
        )
    else:
        snd_message+=(
            f"最后一局 {'🏆' if res['head']['gameResult']==True else '🏳️'} "
            f"{team_contribute_text}"
            f"\n{res['head']['mapName']} {res['head']['heroName']}: {res['head']['killCnt']}/{res['head']['deadCnt']}/{res['head']['assistCnt']} {res['head']['gradeGame']}\n"
            f"{our_player_text}"
            f"{linkurl}\n\n"
            f"戳一戳 来评估两方实力"
        )
    return snd_message,picpath
    # return linkurl,picpath,det_message
def heropower_process(rcv_msg):
    from .zapi import wzry_get_official
    from .ztime import short_wait

    matching_name=extract_name(rcv_msg)
    if (matching_name=="name_error"): return None
    userid=userlist[matching_name]
    roleid=roleidlist[matching_name]

    res=wzry_get_official(reqtype="heropower",userid=userid,roleid=roleid)
    # print(res)
    ret_text=f"{namenick[matching_name]}的战力英雄\n"
    for hero in res['heroList']:
        try:
            region_name=hero['honorTitle']['desc']['full'].split("第")[0]
            metal_name=hero['honorTitle']['desc']['abbr'].split("第")[0]
            ret_text+=f"{hero['basicInfo']['title']}:   {hero['basicInfo']['heroFightPower']}\n   {region_name}  No.{hero['honorTitle']['rank']} \n"
        except Exception as e:
            pass
        # print(hero['honorTitle']['region']['provinceName'],hero['honorTitle']['desc']['full'])
        # ret_text+=f"{hero['honorTitle']['region']['provinceName']} {hero['honorTitle']['desc']['full']} "
    short_wait()
    return ret_text
def herostatistics_process(rcv_msg):
    from .zapi import wzry_get_official
    from .ztime import short_wait

    matching_name=extract_name(rcv_msg)
    if (matching_name=="name_error"): return None
    userid=userlist[matching_name]
    roleid=roleidlist[matching_name]
    heroid,heroname=extract_heroname(rcv_msg)

    res=wzry_get_official(reqtype="herostatistics",userid=userid,roleid=roleid,heroid=heroid)
    # print(res)
    ret_text=""
    total_cnt=int(res["heroInfo"]["winNum"])+int(res["heroInfo"]["failNum"])
    win_rate=(int(res["heroInfo"]["winNum"])/total_cnt) if total_cnt else 0
    month_cnt=len(res["zjList"])
    month_mvp=int(res["heroInfo"]["mvpCount"])
    month_mvp_rate=(int(res["heroInfo"]["mvpCount"])/month_cnt) if month_cnt else 0
    month_medal=(int(res["heroInfo"]["goldCount"])+int(res["heroInfo"]["silverCount"])+int(res["heroInfo"]["bestCount"]))
    month_medal_rate=(month_medal/month_cnt) if month_cnt else 0
    heropower=res["powerData"][-1]["value"]
    month_heropower_incre=res["powerData"][-1]["value"]-res["powerData"][0]["value"]
    medal_infos=""
    if (res["medalList"]):
        for medal_info in res["medalList"]:
            medal_infos+=f"{medal_info["UserMedalInfo"]}\n"
    ret_text+=(
        f"{namenick[matching_name]}的{heroname}：\n"
        f"当前战力：{heropower}\n"
        f"{medal_infos}\n"
        f"总场次：{total_cnt}, 总胜率：{round(win_rate * 100, 2)}%\n\n"
        f"近一月:\n  战力变化：{month_heropower_incre:+d}\n"
        # f"  MVP率：{round(month_mvp_rate*100,2)}%，牌率：{round(month_medal_rate*100,2)}%"
        f"  MVP：{month_mvp}，牌数：{month_medal}"
    )
    short_wait()
    return ret_text
def allhero_process(rcv_msg):
    from .zapi import wzry_get_official
    from .ztime import waitx

    matching_name=extract_name(rcv_msg)
    if (matching_name=="name_error"): return None
    userid=userlist[matching_name]
    roleid=roleidlist[matching_name]

    res=wzry_get_official(reqtype="allhero",userid=userid,roleid=roleid)
    ret_text=f"{namenick[matching_name]}的拿手英雄\n"
    hero_cnt=0
    for hero in res['heroList']:
        if (hero_cnt>5): break
        hero_cnt+=1
        # try:
        ret_text+=f"{hero['name']}： {hero['heroFightPower']}\n"
        ret_text+=f"   {hero['playNum']}场 {hero['winRate']}\n"
        # except Exception as e:
        #     pass
        # print(hero['honorTitle']['region']['provinceName'],hero['honorTitle']['desc']['full'])
        # ret_text+=f"{hero['honorTitle']['region']['provinceName']} {hero['honorTitle']['desc']['full']} "
    wait()
    return ret_text
def gradeanalyze_process(rcv_msg):
    from .tools import gen_grade_chart
    from .ztime import wait

    matching_name=extract_name(rcv_msg)

    userid=userlist[matching_name]
    data_path=os.path.join("history")
    pic_visit_path=f"/usr/local/nginx/html/wzry_grade_chart/grade_chart.png"
    pic_save_path=f"/usr/local/nginx/html/wzry_grade_chart/"
    analyze_msg=gen_grade_chart.gen(userid,data_path,pic_save_path)
    
    wait()
    return pic_visit_path,analyze_msg
def watchbattle_process(rcv_msg):
    from .zapi import wzry_get_official
    from .tools import gen_battle_shot
    from .ztime import short_wait
    from .ztime import wait

    matching_name=extract_name(rcv_msg)
    if (matching_name=="name_error"): return None,None
    userid=userlist[matching_name]
    roleid=roleidlist[matching_name]

    btlist_data=wzry_get_official(reqtype="btlist",userid=userid,roleid=roleid)
    if (not btlist_data["isGaming"]): return None,None
    res=btlist_data["gaming"]
    if (not res["canBeWatch"]): return None,None

    battleId=res["battleId"]
    mapName=res["mapName"]
    duration=res["duration"]

    save_path="/usr/local/nginx/html/wzry_btl_shot/"+str(roleid)+".png"
    if(dmc.RTMPListener): dmc.RTMPListener.stop()
    dmc.RTMPListener = gen_battle_shot.RTMPListener(dmc.streamurl,save_path=save_path,roleid=roleid)
    dmc.RTMPListener.start()  # 开始后台监听

    dmc.RTMPListener.screenshot()   # 截图一次
    wait()
    return save_path,None
def coplayer_process(rcv_msg):
    from .zapi import wzry_get_official
    from .zfunc import check_btl_official_with_matching
    from .tools.gen_coplayer_analyses import CoPlayerProcess
    gen_inst=CoPlayerProcess()
    def sigmoid(x):
        return 1/(1+math.exp(-x))
    def get_level(detail_list,is_my_side):
        auth_cnt=0      # 授权人数统计
        ret_level=0     # 返回值
        req_error=[]
        for player in detail_list:
            # 对于该队伍中的一个玩家
            winNum=10        # 当前英雄输局数
            loseNum=10       # 当前英雄胜局数
            avgScore=9      # 当前英雄平均评分
            winRate=0.5     # 当前英雄胜率
            starNum=50      # 总星数
            peakScore=1200  # 巅峰分数
            PowerNum=70000  # 总战斗力
            TotalCnt=1000   # 总场次
            MVPCnt=100      # 总MVP场次
            MVPRate=0.1
            heroPower=1000
            rankName="未知段位"
            rankStar=0
            heroTag=""

            is_auth=player["basicInfo"]["isGameAuth"] # 营地授权与否
            roleid=player["basicInfo"]["roleId"]
            userid=player["basicInfo"]["userId"]
            nickname=player["basicInfo"]["roleName"]
            heroBehavior=player["heroBehavior"]
            heroName=player["battleRecords"]["usedHero"]["heroName"]
            heroAvatar=player["battleRecords"]["usedHero"]["heroIcon"]
            player_avatar_url=""
            if (is_auth):
                auth_cnt+=1
                winNum=heroBehavior["winNum"]
                loseNum=heroBehavior["loseNum"]
                avgScore=float(heroBehavior["avgScore"])
                winRate=float(heroBehavior["winRate"].strip('%')) / 100
                heroPower=player["battleStats"]["fightPower"]
                try:
                    profile_res=wzry_get_official(reqtype="profile",roleid=roleid,userid=userid)
                except Exception as e:
                    req_error.append(str(e))
                    continue
                heropower_res=None
                try:
                    heropower_res=wzry_get_official(reqtype="heropower",roleid=roleid,userid=userid)
                except Exception as e:
                    req_error.append(str(e))

                RoleInfo = (roles[0] if (roles := [role for role in profile_res["roleList"] if role["roleId"] == roleid]) else None)
                rankInfo = (mods[0] if (mods := [mods for mods in profile_res["head"]["mods"] if mods["modId"] == 701]) else None)
                peakInfo = (mods[0] if (mods := [mods for mods in profile_res["head"]["mods"] if mods["modId"] == 702]) else None)
                Powerinfo = (mods[0] if (mods := [mods for mods in profile_res["head"]["mods"] if mods["modId"] == 304]) else None)
                TotalNumInfo = (mods[0] if (mods := [mods for mods in profile_res["head"]["mods"] if mods["modId"] == 401]) else None)
                MVPInfo = (mods[0] if (mods := [mods for mods in profile_res["head"]["mods"] if mods["modId"] == 408]) else None)
                if (RoleInfo):
                    player_avatar_url=RoleInfo.get("roleIcon","")
                if (rankInfo):
                    rankName=rankInfo["name"]
                    rankStar=int(json.loads(rankInfo["param1"])["rankingStar"])
                    starNum=(ranklist[rankName] if rankName in ranklist else fin) + rankStar
                if (peakInfo): peakScore=int(peakInfo["content"]) or 1200
                if (Powerinfo): PowerNum=int(Powerinfo["content"])
                if (TotalNumInfo): TotalCnt=int(TotalNumInfo["content"])
                if (MVPInfo): MVPCnt=int(MVPInfo["content"])
                if (TotalNumInfo and MVPInfo): MVPRate=MVPCnt/TotalCnt
                else: MVPRate=0.2
                if (heropower_res):
                    for hero in heropower_res['heroList']:
                        try:
                            if (hero['basicInfo']['title']==heroName):
                                region_name=hero['honorTitle']['desc']['full'].split("第")[0]
                                metal_name=hero['honorTitle']['desc']['abbr'].split("第")[0]
                                heroTag=f"{region_name}  No.{hero['honorTitle']['rank']} \n"
                                break
                        except Exception as e:
                            pass
            HeroShowCnt=loseNum+winNum                      # 该玩家此英雄的出场局数
            auth_coeff=1 if is_auth else 0.6                # 为未授权加一个折扣
            equiv_star=(starNum-25)+(peakScore-1200)/15.0   # 巅峰分与星数折算成一个综合星级
            if (equiv_star<=0): equiv_star=1                # 星级下界
            single_level = (
                pow(equiv_star, 0.3)                        # equiv_star        星级和巅峰分计算得的等价星级     0.3
                * pow(sigmoid(MVPRate), 4)                  # MVPRate           MVP率                          4
                * pow((PowerNum / 10000), 0.85)             # PowerNum          战斗力                         0.85
                * pow(avgScore, 1)                          # avgScore          该英雄历史场次平均评分           1
                * pow(sigmoid(HeroShowCnt / 10), 1.3)       # HeroShowCnt       该英雄历史场次数                 1.3
                * pow(sigmoid(heroPower/10000), 2)          # heroPower         该英雄当前战力                   2
                * auth_coeff                                # auth_coeff        营地未授权的折扣系数             1
            )
            # 指标1.5倍的等价条件
            # 王者0星 巅峰1200分 -> 王者50星 巅峰1600分
            # MVP率 30% -> 56%
            # 战斗力 50000 -> 80000
            # 本局使用英雄的平均评分 8分 -> 12分
            # 本局使用英雄的总场次 10场 -> 300场
            # 本局使用的英雄的战力 1000 -> 6000 -> 13000

            # 生成图表中
            # 卡片右上角红色角标：营地未授权
            # 玩家卡片背景色：红色，低于所有玩家历史平均水平；绿色，高于所有玩家历史平均水平；颜色越深，差值越大
            # 底韵值：以该局最高玩家为100%计算
            ret_level+=single_level
            gen_inst.add_player(
                nickname=nickname,
                is_auth=is_auth,
                is_my_side=is_my_side,
                winNum=winNum,
                loseNum=loseNum,
                avgScore=avgScore,
                winRate=winRate,
                avatarUrl=player_avatar_url,
                starNum=starNum,
                peakScore=peakScore,
                PowerNum=PowerNum,
                TotalCnt=TotalCnt,
                MVPCnt=TotalCnt*MVPRate,
                rankName=rankName,
                rankStar=rankStar,
                single_level=single_level,
                HeroAvatar=heroAvatar,
                HeroPower=heroPower,
                HeroTag=heroTag
            )
        return ret_level,auth_cnt,req_error

    last_btl_info=None
    for item in dmc.last_request_btllist[::-1]: 
        if (check_btl_official_with_matching(item["MapName"])):
            last_btl_info=item
            break
    if (not last_btl_info): return None
    res=wzry_get_official(reqtype="btldetail",**last_btl_info['Params'],roleid=dmc.last_request_roleid)
    if ('head' not in res or not check_btl_official_with_matching(res['head']['mapName'])): return None
    my_side_detail=res['redRoles'] if (res['redTeam']['acntCamp']==res['head']['acntCamp']) else res['blueRoles']
    op_side_detail=res['redRoles'] if (res['redTeam']['acntCamp']!=res['head']['acntCamp']) else res['blueRoles']

    my_side_total_level,my_side_auth_cnt,my_side_req_error=get_level(my_side_detail,1)
    op_side_total_level,op_side_auth_cnt,op_side_req_error=get_level(op_side_detail,0)

    delta_level=my_side_total_level-op_side_total_level

    # req_err_msg=""
    # for i in my_side_req_error:
    #     req_err_msg.append()
    snd_msg=(
        f"实力天平倾斜度：{round(delta_level,2)}\n"
        f"我方底蕴：{round(my_side_total_level,2)}\n"
        f"对方底蕴：{round(op_side_total_level,2)}\n"
        f"{server_domain}/rcalc"
    )
    save_path=os.path.join(nginx_path,"wzry_history","coplayer_analyses.png")
    out_path, ok = gen_inst.gen(save_path)
    return snd_msg,save_path
            
def fetch_history(userid=None,start_date=None,end_date=None): # 所有历史数据
    from .zfile import readerl
    from .zfile import writerl
    from .ztime import str_to_time

    gamedetails={}
    filenames=sorted(os.listdir("history"),reverse=True)
    duration=0
    for filename in filenames:
        if not os.path.isfile(os.path.join("history",filename)): continue
        history_date=os.path.splitext(os.path.basename(filename))[0]
        if not bool(re.fullmatch(r'^\d{4}-\d{2}-\d{2}$', history_date)): continue
        date_parsed=str_to_time(history_date)
        if (start_date and end_date and (date_parsed>end_date or date_parsed<start_date)): continue
        duration+=1
        full_path=os.path.join("history",filename)
        gameinfo=readerl(full_path)
        for player in gameinfo:
            playername=player["key"]
            playerdetails=player["details"][::-1]
            if (playername not in gamedetails): 
                gamedetails[playername]=playerdetails
            else:
                for playerdetail in playerdetails:
                    gamedetails[playername].append(playerdetail)
    if (userid): gamedetails={k:v for k,v in gamedetails.items() if userid==userlist[k]}
    return gamedetails,duration
class Analyses:
    @staticmethod
    def analyze_history(userid=None,start_date=None,end_date=None): # 返回排位巅峰战队赛
        all_history,duration=fetch_history(userid=userid,start_date=start_date,end_date=end_date)
        analyzed_infos={}
        for k,v in all_history.items():
            history_kept=[detail for detail in v if check_btl_official(detail["MapName"])]
            if (len(history_kept)==0): continue
            analyzed_info={}
            win_tourna_cnt=sum(1 for detail in history_kept if detail["Result"]=="胜利")
            total_tourna_cnt=sum(1 for detail in history_kept)
            win_rate_tourna=-1 if total_tourna_cnt==0 else float(win_tourna_cnt)/total_tourna_cnt
            hero_info={}
            for detail in history_kept:
                if (detail["HeroName"] not in hero_info): hero_info[detail["HeroName"]]=[0,1,[],0,0]
                else: hero_info[detail["HeroName"]][1]+=1
                if (detail["Result"]=="胜利"): hero_info[detail["HeroName"]][0]+=1
                hero_info[detail["HeroName"]][2].append(float(detail["GameGrade"]))
            for hero in hero_info:
                hero_info[hero][3]=float(hero_info[hero][0])/hero_info[hero][1] # 英雄胜率
                hero_info[hero][4]=float(sum(hero_info[hero][2]))/len(hero_info[hero][2]) # 英雄平均评分
            analyzed_info={"win_tourna_cnt":win_tourna_cnt,"total_tourna_cnt":total_tourna_cnt,"win_rate_tourna":win_rate_tourna,"hero_info":{k:v for k,v in hero_info.items()},"duration":duration}
            analyzed_infos[k]=analyzed_info
        # print(analyzed_infos)
        return analyzed_infos

    @staticmethod
    def get_benefit_data(userid=None,time_gap=analyze_time_gap): # 评分^2/exp(胜率)： exp防止胜率0附近斜率过大 # 值越大越受害 值越小越受益
        from .ztime import time_r
        from .ztime import time_r_delta

        end_date=time_r()
        start_date=time_r_delta(time_gap)
        analyzed_infos=Analyses.analyze_history(userid=None,start_date=start_date,end_date=end_date)
        # print(analyzed_infos)

        user_low_grade_winrate_ratio="" # 评分胜率比最低
        user_high_grade_winrate_ratio="" # 评分胜率比最高
        low_grade_winrate_ratio=10000
        high_grade_winrate_ratio=0
        player_benefit={}
        for k,v in analyzed_infos.items(): # 为了评判机制受益程度，或许评分与上星比值更为合理（评分：实力，上星：受益），胜率与上星无必然关联
            if (len(v["hero_info"])==0): continue
            win_rate=sum(heroinfo[0] for heroname,heroinfo in v["hero_info"].items())/sum(heroinfo[1] for heroname,heroinfo in v["hero_info"].items())
            aver_grade=sum(sum(heroinfo[2]) for heroname,heroinfo in v["hero_info"].items())/sum(heroinfo[1] for heroname,heroinfo in v["hero_info"].items())
            grade_winrate_ratio=pow(aver_grade,2)/(math.exp(win_rate))
            # grade_winrate_ratio=math.exp((math.log(aver_grade)-math.log(2))/(math.log(14)-math.log(2)))/(math.exp(win_rate))
            # grade_winrate_ratio=math.exp((aver_grade-2)/(14-2))/(math.exp(win_rate))
            player_benefit[k]=[grade_winrate_ratio,win_rate,aver_grade]
            # print("benefit",k,win_rate,aver_grade,grade_winrate_ratio)
            if (grade_winrate_ratio<low_grade_winrate_ratio): 
                user_low_grade_winrate_ratio=k
                low_grade_winrate_ratio=grade_winrate_ratio
            if (grade_winrate_ratio>high_grade_winrate_ratio): 
                user_high_grade_winrate_ratio=k
                high_grade_winrate_ratio=grade_winrate_ratio
        player_benefit = dict(sorted(player_benefit.items(), key=lambda item: item[1][0]))
        # print([user_low_grade_winrate_ratio,user_high_grade_winrate_ratio,round(low_grade_winrate_ratio,3),round(high_grade_winrate_ratio,3)],player_benefit)
        return [user_low_grade_winrate_ratio,user_high_grade_winrate_ratio,round(low_grade_winrate_ratio,3),round(high_grade_winrate_ratio,3),player_benefit]
    
    @staticmethod
    def get_expert_hero(userid=None,time_gap=analyze_time_gap):
        from .ztime import time_r
        from .ztime import time_r_delta

        end_date=time_r()
        start_date=time_r_delta(time_gap)
        analyzed_infos=Analyses.analyze_history(userid=userid,start_date=start_date,end_date=end_date)
        exported={}
        for k,v in analyzed_infos.items(): # 英雄胜率*英雄评分*f(英雄场次)
            if (len(v["hero_info"])==0): continue
            max_factor_hero=""
            max_factor=0
            for heroname,heroinfo in v["hero_info"].items():
                factor=math.pow(heroinfo[3],0.5)*(heroinfo[4])*((math.tanh((heroinfo[1]-5)/3)+1)/2)
                if (factor>max_factor):
                    max_factor=factor
                    max_factor_hero=heroname
            exported[k]=[{max_factor_hero:round(max_factor,3)}]
        # print(exported)
        return exported

    @staticmethod
    def get_extreme_data(time_gap=analyze_time_gap):
        from .ztime import time_r
        from .ztime import time_r_delta

        end_date=time_r()
        start_date=time_r_delta(time_gap)
        history_info,_=fetch_history(userid=None,start_date=start_date,end_date=end_date)
        
        lowest_grade=16
        highest_grade=0
        lowest_player=""
        highest_player=""
        lowest_hero=""
        highest_hero=""

        for playerid,details in history_info.items():
            for detail in details:
                if ('1V1' in detail['MapName']): continue
                detail['GameGrade']=float(detail['GameGrade'])
                if (detail['GameGrade']<lowest_grade):
                    lowest_grade=detail['GameGrade']
                    lowest_player=playerid
                    lowest_hero=detail['HeroName']
                if (detail['GameGrade']>highest_grade):
                    highest_grade=detail['GameGrade']
                    highest_player=playerid
                    highest_hero=detail['HeroName']
        # print([lowest_grade,highest_grade,lowest_player,highest_player,lowest_hero,highest_hero])
        return [round(lowest_grade,1),round(highest_grade,1),lowest_player,highest_player,lowest_hero,highest_hero]

    @staticmethod
    def get_intersection_data(time_gap=analyze_time_gap):
        from .ztime import time_r
        from .ztime import time_r_delta

        end_date=time_r()
        start_date=time_r_delta(time_gap)
        history_info,_=fetch_history(userid=None,start_date=start_date,end_date=end_date)

        player_intersection={}
        for playerid_a,details_a in history_info.items():
            for playerid_b,details_b in history_info.items():
                if (playerid_a==playerid_b): continue
                for detail_a in details_a:
                    for detail_b in details_b:
                        if (detail_a['GameSeq']==detail_b['GameSeq']):
                            player_set=frozenset({playerid_a,playerid_b})
                            if (player_set not in player_intersection): player_intersection[player_set]=1/2
                            else: player_intersection[player_set]+=1/2
                            
        player_intersection = dict(sorted(player_intersection.items(), key=lambda item: item[1]))
        # print(player_intersection)
        return player_intersection

def get_emoji(txt):
    from .zapi import ai_api
    from .zfile import readerl

    emojiref=readerl("emojiref.json")
    # print(emojiref)
    emojinew={}
    for k,v in emojiref.items():
        emojinew[k]=v["content"]
    pmpt=emoji_pmpt[0]+emoji_pmpt[1]+str(emojinew)+emoji_pmpt[2]+txt+emoji_pmpt[3]
    res=int(ai_api(pmpt,temperature=2))
    return res
def get_emoji_url(index):
    emoji_url=f"http://{server_domain}/doraemon_emojis/{index}.jpg"
    return emoji_url
def extract_url_params(url):
    from urllib.parse import urlparse, parse_qs
    # 解析 URL
    parsed_url = urlparse(url)
    # 提取查询参数并转换为字典
    params = parse_qs(parsed_url.query)
    # 将值从列表转换为单个值（如果参数只有一个值）
    return {key: value[0] if len(value) == 1 else value for key, value in params.items()}
def get_peak_alter_list(details,processed,reverse=1):
    peak_alter_list=[]
    detail_dup=[]
    if (not processed):
        for detail in details:
            if (detail["MapType"]!=-1): continue
            detail_dup.append({"PeakBefore":detail["PeakGradeBeforeGame"],"PeakAfter":detail["PeakGradeAfterGame"],"used":False})
    else:
        for detail in details:
            detail_dup.append({"PeakBefore":detail[0],"PeakAfter":detail[1],"used":False})
    if (reverse==-1): detail_dup=detail_dup[::-1]
    for item_a in detail_dup:
        if (item_a["used"]): continue
        item_a["used"]=True
        PeakBefore=item_a["PeakBefore"]
        PeakAfter=item_a["PeakAfter"]
        for item_b in detail_dup:
            if (item_b["used"]): continue
            if (item_b["PeakBefore"]==PeakAfter): 
                PeakAfter=item_b["PeakAfter"]
                item_b["used"]=True
        peak_alter_list.append([PeakBefore,PeakAfter])
    return peak_alter_list
def extract_name(origin_text):
    matching_name=None
    for realname,nicknames in nameref.items():
        for nickname in nicknames:
            if (nickname in origin_text):
                matching_name=realname
                break
        if (matching_name): break
    if (not matching_name): matching_name=ai_parser([origin_text],"single_parser") # 返回人员与日期字典格式 格式为{name:date,name:date,...}
    return matching_name
def merge_crossday_gamedata(gamedata):
    if (not gamedata): return {}
    res=gamedata[-1]
    res["date"]=f"cross_day"
    res["gaming_info"]={}
    res["btl_aver"]=0
    if ("roleid" not in res): res["roleid"]=str(roleidlist[res["key"]])
    for daydata in gamedata[-2::-1]:
        res["today_num"]+=daydata["today_num"]
        res["up_tourna"]+=daydata["up_tourna"]
        res["up_peak"]+=daydata["up_peak"]
        for mapname,mapcnt in daydata["map_cnt"].items():
            if (mapname not in res["map_cnt"]):
                res["map_cnt"][mapname]=[0,0]
            res["map_cnt"][mapname][0]+=mapcnt[0]
            res["map_cnt"][mapname][1]+=mapcnt[1]
        for peakdiff in daydata.get("peak_up",[]):
            res["peak_up"].append(peakdiff)
        res["star_up"]+=daydata["star_up"]
        for detail in daydata["details"]:
            res["details"].append(detail)
    if ("peak_up" in res):
        combined_up_peak=get_peak_alter_list(details=res["peak_up"],processed=True)
        res["peak_up"]=combined_up_peak
        combined_up_peak=get_peak_alter_list(details=res["peak_up"],processed=True,reverse=-1)
        res["peak_up"]=combined_up_peak
    else:
        res["peak_up"]=[]
    if ("visible" not in res): res["visible"]=True
    official_btls_grades = [float(btl["GameGrade"]) for btl in res["details"] if check_btl_official(btl["MapName"])]
    res["btl_aver"] = sum(official_btls_grades) / len(official_btls_grades) if official_btls_grades else 0
    res["btl_aver"]=round(res["btl_aver"],1)

    return res
def check_btl_official(btlname):
    import re

    btlname=str.lower(btlname)
    if re.search(r'1v1|2v2|3v3', btlname):
        return False
    if re.search(r'排位|巅峰|战队', btlname):
        return True
    return False
def check_btl_official_with_matching(btlname):
    import re

    btlname=str.lower(btlname)
    if re.search(r'1v1|2v2|3v3', btlname):
        return False
    if re.search(r'排位|巅峰|战队|匹配|王者峡谷', btlname):
        return True
    return False
def export_btldetail(gameinfo,roleid):
    from .zfile import writerl
    from .zapi import wzry_get_official
    from .zfile import file_exist
    for btl in gameinfo:
        savepath=os.path.join("history","battles",str(btl["GameSeq"])+".json")
        if (file_exist(savepath) or not check_btl_official(btl["MapName"])): continue
        res=wzry_get_official(reqtype="btldetail",roleid=roleid,**btl['Params'])
        writerl(savepath,res)
    return
def extract_heroname(msg):
    for heroid,heroname in HeroList.items():
        if (heroname in msg):
            return heroid,heroname
    for heroid,heroname in HeroName_replacements.items():
        if (heroname in msg):
            return heroid,HeroList[heroid]
# 配置定时任务
async def scheduler_func():
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    await scheduler.start()