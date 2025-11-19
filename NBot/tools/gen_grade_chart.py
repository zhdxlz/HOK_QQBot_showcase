import json
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import re
from ..zfunc import check_btl_official

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def load_json_files(folder_path):
    """加载文件夹中的所有JSON文件"""
    data_by_date = {}
    json_files = [f for f in os.listdir(folder_path) 
                  if f.endswith('.json') and not f.startswith('BEGIN_TEMPLATE')]
    
    for filename in json_files:
        date_str = filename.replace('.json', '')
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"跳过无效日期格式的文件: {filename}")
            continue
            
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data_by_date[date_obj] = data
        except Exception as e:
            print(f"读取文件 {filename} 时出错: {e}")
    
    return data_by_date

def extract_game_scores(player_data):
    """提取单个玩家的所有游戏评分和时间戳"""
    if not player_data.get('details'):
        return []
    
    game_scores = []
    for detail in player_data['details']:
        map_name = detail.get('MapName', '')
        game_grade = detail.get('GameGrade')
        timestamp = detail.get('GameTime_Timestamp')
        
        if check_btl_official(map_name) and game_grade is not None and timestamp is not None:
            try:
                score = float(game_grade)
                game_time = datetime.fromtimestamp(timestamp)
                game_scores.append((game_time, score))
            except (ValueError, TypeError):
                continue
    
    return sorted(game_scores, key=lambda x: x[0])

def detect_performance_anomalies(timestamps, scores, min_games_threshold=10):
    """检测表现异常情况"""
    if len(scores) < min_games_threshold:
        return False, [], "游戏场次不足，无法进行表现检测"
    
    # 计算统计指标
    overall_avg = np.mean(scores)
    overall_std = np.std(scores)
    
    # 设置阈值
    high_threshold = overall_avg + 0.8 * overall_std
    excellent_threshold = overall_avg + 1.5 * overall_std
    low_threshold = overall_avg - 0.8 * overall_std
    poor_threshold = overall_avg - 1.5 * overall_std
    
    # 时间窗口分析
    anomaly_periods = []
    window_hours = 6
    i = 0
    
    while i < len(timestamps):
        window_start = timestamps[i]
        window_end = window_start + timedelta(hours=window_hours)
        
        # 获取窗口内的游戏
        window_games = []
        j = i
        while j < len(timestamps) and timestamps[j] <= window_end:
            window_games.append((timestamps[j], scores[j]))
            j += 1
        
        if len(window_games) >= 3:
            window_scores = [game[1] for game in window_games]
            window_avg = np.mean(window_scores)
            window_std = np.std(window_scores) if len(window_scores) > 1 else 0
            
            # 高分异常检测
            conditions_met = 0
            reasons = []
            
            if window_avg > high_threshold:
                conditions_met += 2
                reasons.append("水平表现异常稳定")
            
            excellent_games = sum(1 for score in window_scores if score > max(8.5, excellent_threshold))
            if excellent_games >= len(window_scores) * 0.6:
                conditions_met += 1
                reasons.append("发挥超常稳定")
            
            if len(window_scores) > 3 and window_std < overall_std * 0.6:
                conditions_met += 1
                reasons.append("表现一致性异常")
            
            if len(window_games) >= 8:
                conditions_met += 1
                reasons.append("游戏频率异常")
            
            low_score_games = sum(1 for score in window_scores if score < overall_avg - 0.5 * overall_std)
            if low_score_games == 0 and len(window_scores) >= 5:
                conditions_met += 1
                reasons.append("失误率异常偏低")
            
            # 低分异常检测
            low_conditions = 0
            low_reasons = []
            
            if window_avg < low_threshold:
                low_conditions += 2
                low_reasons.append("状态明显低迷")
            
            poor_games = sum(1 for score in window_scores if score < max(4.0, poor_threshold))
            if poor_games >= len(window_scores) * 0.5:
                low_conditions += 1
                low_reasons.append("发挥严重失常")
            
            # 连续失误检测
            consecutive_low = 0
            max_consecutive_low = 0
            for score in window_scores:
                if score < overall_avg - 0.3 * overall_std:
                    consecutive_low += 1
                    max_consecutive_low = max(max_consecutive_low, consecutive_low)
                else:
                    consecutive_low = 0
            
            if max_consecutive_low >= 3:
                low_conditions += 1
                low_reasons.append("连续表现不佳")
            
            # 记录异常时段
            if conditions_met >= 3:
                anomaly_periods.append({
                    'start_time': window_start,
                    'end_time': window_games[-1][0],
                    'games': window_games,
                    'avg_score': window_avg,
                    'conditions': conditions_met,
                    'reasons': reasons,
                    'type': 'high'
                })
            elif low_conditions >= 2:
                anomaly_periods.append({
                    'start_time': window_start,
                    'end_time': window_games[-1][0],
                    'games': window_games,
                    'avg_score': window_avg,
                    'conditions': low_conditions,
                    'reasons': low_reasons,
                    'type': 'low'
                })
        
        i += max(1, len(window_games) // 2)
    
    # 合并相近时段
    merged_periods = []
    for period in anomaly_periods:
        if not merged_periods:
            merged_periods.append(period)
        else:
            last_period = merged_periods[-1]
            if ((period['start_time'] - last_period['end_time']).total_seconds() < 7200 
                and period['type'] == last_period['type']):
                last_period['end_time'] = period['end_time']
                last_period['games'].extend(period['games'])
                last_period['avg_score'] = np.mean([g[1] for g in last_period['games']])
                last_period['conditions'] = max(last_period['conditions'], period['conditions'])
                last_period['reasons'].extend(period['reasons'])
            else:
                merged_periods.append(period)
    
    # 生成分析结果
    has_anomalies = len(merged_periods) > 0
    if has_anomalies:
        high_anomalies = [p for p in merged_periods if p['type'] == 'high']
        low_anomalies = [p for p in merged_periods if p['type'] == 'low']
        
        analysis_parts = []
        if high_anomalies:
            total_high_games = sum(len(p['games']) for p in high_anomalies)
            analysis_parts.append(f"发现{len(high_anomalies)}个超常发挥时段({total_high_games}场)")
        
        if low_anomalies:
            total_low_games = sum(len(p['games']) for p in low_anomalies)
            analysis_parts.append(f"{len(low_anomalies)}个状态低迷时段({total_low_games}场)")
        
        analysis = "表现波动分析: " + "、".join(analysis_parts)
    else:
        analysis = "表现相对稳定，未发现显著异常时段"
    
    return has_anomalies, merged_periods, analysis

def create_stats_text(data, anomaly_periods):
    """创建统计信息文本"""
    high_anomalies = [p for p in anomaly_periods if p['type'] == 'high']
    low_anomalies = [p for p in anomaly_periods if p['type'] == 'low']
    
    time_span = data['timestamps'][-1] - data['timestamps'][0]
    days_span = time_span.days + 1
    
    min_score = min(data['scores'])
    max_score = max(data['scores'])
    avg_all = np.mean(data['scores'])
    std_score = np.std(data['scores'])
    
    stats_lines = [
        # "═══ 数据统计 ═══",
        # f"游戏场次：{len(data['scores']):>4} 场",
        # f"时间跨度：{days_span:>4} 天",
        # f"最高评分：{max_score:>6.2f}",
        # f"最低评分：{min_score:>6.2f}",
        # f"平均评分：{avg_all:>6.2f}",
        # f"标准差值：{std_score:>6.2f}",
        # "",
        "═══ 表现分析 ═══"
    ]
    
    # 确定状态和颜色
    if high_anomalies and low_anomalies:
        performance_status = "波动较大"
        box_color = 'wheat'
        stats_lines.append(f"状态评估：{performance_status}")
        total_high_games = sum(len(p['games']) for p in high_anomalies)
        stats_lines.append(f"超常局数：{total_high_games} 场")
        total_low_games = sum(len(p['games']) for p in low_anomalies)
        stats_lines.append(f"低迷局数：{total_low_games} 场")
    elif high_anomalies:
        performance_status = "表现突出"
        box_color = 'lightyellow'
        stats_lines.append(f"状态评估：{performance_status}")
        total_high_games = sum(len(p['games']) for p in high_anomalies)
        stats_lines.append(f"超常局数：{total_high_games} 场")
        high_percentage = (total_high_games / len(data['scores'])) * 100
        stats_lines.append(f"占总比例：{high_percentage:.1f}%")
    elif low_anomalies:
        performance_status = "需要调整"
        box_color = 'lightcyan'
        stats_lines.append(f"状态评估：{performance_status}")
        total_low_games = sum(len(p['games']) for p in low_anomalies)
        stats_lines.append(f"低迷局数：{total_low_games} 场")
        low_percentage = (total_low_games / len(data['scores'])) * 100
        stats_lines.append(f"占总比例：{low_percentage:.1f}%")
    else:
        performance_status = "表现平稳"
        box_color = 'lightblue'
        stats_lines.append(f"状态评估：{performance_status}")
        stats_lines.append("各项指标正常")
    
    return "\n".join(stats_lines), box_color

def plot_anomaly_periods(anomaly_periods):
    """绘制异常时段标记"""
    if not anomaly_periods:
        return
    
    high_label_added = False
    low_label_added = False
    
    for period in anomaly_periods:
        period_timestamps = [game[0] for game in period['games']]
        period_scores = [game[1] for game in period['games']]
        
        if period['type'] == 'high':
            plt.scatter(period_timestamps, period_scores, color='red', s=60, marker='*',
                       zorder=5, label='超常发挥' if not high_label_added else "")
            high_label_added = True
            if len(period_timestamps) > 1:
                plt.axvspan(period['start_time'], period['end_time'],
                          alpha=0.15, color='red', zorder=1)
        else:
            plt.scatter(period_timestamps, period_scores, color='blue', s=60, marker='v',
                       zorder=5, label='状态低迷' if not low_label_added else "")
            low_label_added = True
            if len(period_timestamps) > 1:
                plt.axvspan(period['start_time'], period['end_time'],
                          alpha=0.15, color='blue', zorder=1)

def generate_player_chart(player_id, data):
    """为单个玩家生成图表"""
    plt.figure(figsize=(16, 8))
    
    # 绘制主图
    plt.plot(data['timestamps'], data['scores'], marker='o', linewidth=1.5, markersize=4, alpha=0.8)
    
    # 设置标题和标签
    plt.title(f"{data['nickname']} - 评分时间线", fontsize=20, fontweight='bold')
    plt.xlabel('时间', fontsize=12)
    plt.ylabel('游戏评分', fontsize=12)
    
    # 设置时间格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    if len(data['timestamps']) > 50:
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(data['timestamps'])//30)))
    else:
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(data['timestamps'])//10)))
    plt.xticks(rotation=45)
    
    # 添加网格
    plt.grid(True, alpha=0.3)
    
    # 设置Y轴范围
    min_score = min(data['scores'])
    max_score = max(data['scores'])
    y_range = max_score - min_score
    y_padding = max(0.5, y_range * 0.1)
    plt.ylim(max(0, min_score - y_padding), max_score + y_padding)
    
    # 异常检测和标记
    has_anomalies, anomaly_periods, performance_analysis = detect_performance_anomalies(data['timestamps'], data['scores'])
    plot_anomaly_periods(anomaly_periods)
    
    # 添加平均线
    avg_all = np.mean(data['scores'])
    plt.axhline(y=avg_all, color='r', linestyle='--', alpha=0.7, label=f'总体平均: {avg_all:.2f}')
    
    # 创建统计信息
    stats_text, box_color = create_stats_text(data, anomaly_periods)
    
    # 调整布局并添加统计信息
    plt.subplots_adjust(right=0.78)
    try:
        plt.text(1.02, 0.5, stats_text, transform=plt.gca().transAxes,
                fontsize=10, verticalalignment='center', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.6', facecolor=box_color, alpha=0.9, edgecolor='gray'),
                fontfamily='sans-serif')
    except:
        plt.text(1.02, 0.5, stats_text, transform=plt.gca().transAxes,
                fontsize=10, verticalalignment='center', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.6', facecolor=box_color, alpha=0.9, edgecolor='gray'))
    
    # 添加图例
    plt.legend(loc='upper left')
    plt.tight_layout()
    
    return anomaly_periods

def generate_player_charts(data_by_date, output_folder,id):
    """为每个玩家生成时间-评分图表"""
    # if not os.path.exists(output_folder):
    #     os.makedirs(output_folder)
    
    # 收集所有玩家数据
    player_data = defaultdict(lambda: {'timestamps': [], 'scores': [], 'nickname': ''})
    
    for date in sorted(data_by_date.keys()):
        for player in data_by_date[date]:
            player_id = player.get('id')
            if player_id is None or player_id!=id:
                continue
            
            game_scores = extract_game_scores(player)
            for game_time, score in game_scores:
                player_data[player_id]['timestamps'].append(game_time)
                player_data[player_id]['scores'].append(score)
                player_data[player_id]['nickname'] = player.get('nickname', f'Player_{player_id}')
    
    # 为每个玩家生成图表
    for player_id, data in player_data.items():
        if (player_id!=id): continue
        if len(data['timestamps']) == 0:
            print(f"玩家 {data['nickname']} (ID: {player_id}) 没有有效数据，跳过")
            continue
        
        anomaly_periods = generate_player_chart(player_id, data)
        
        # 保存图表
        safe_nickname = data['nickname'].replace('/', '_').replace('\\', '_')
        # safe_filename = f"player_{player_id}_{safe_nickname}.png"
        safe_filename = f"grade_chart.png"
        output_path = os.path.join(output_folder, safe_filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

def gen(id,folder_path,pic_path):
    data_by_date = load_json_files(folder_path)
    generate_player_charts(data_by_date,pic_path,id)
    return ""