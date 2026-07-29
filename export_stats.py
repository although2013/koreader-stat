import os
import json
import sqlite3
import datetime
import pandas as pd
import numpy as np

DB_PATH = 'statistics.sqlite3'
JSON_OUTPUT_PATH = 'public/reading_data.json'  # Cloudflare Pages 静态资源目录

def calculate_streaks(dates):
    """计算连续阅读打卡天数 (Streak)"""
    if not dates:
        return 0, 0
    sorted_dates = sorted(list(set(dates)))
    max_streak, temp_streak = 1, 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
            temp_streak += 1
        else:
            temp_streak = 1
        max_streak = max(max_streak, temp_streak)
    
    curr_streak = 1
    for i in range(len(sorted_dates)-2, -1, -1):
        if (sorted_dates[i+1] - sorted_dates[i]).days == 1:
            curr_streak += 1
        else:
            break
    return curr_streak, max_streak

def generate_web_json(conn):
    """从 SQLite 提取并清洗数据，生成 Cloudflare Pages 所需的结构化 JSON"""
    page_stats = pd.read_sql_query("SELECT id_book, page, start_time, duration FROM page_stat_data ORDER BY start_time", conn)
    books_df = pd.read_sql_query("SELECT id, title, authors, highlights, pages, total_read_time, total_read_pages FROM book WHERE total_read_time > 0", conn)

    if page_stats.empty:
        print("⚠️ 数据库中没有找到阅读记录。")
        return

    # 1. 基础汇总
    total_sec = page_stats['duration'].sum()
    total_hrs = round(total_sec / 3600.0, 1)
    total_mins = int(total_sec // 60)
    total_pages = len(page_stats)

    # 2. 速度与划线
    avg_speed_pph = round(total_pages / (total_sec / 3600.0), 1) if total_sec > 0 else 0
    avg_sec_per_page = round(total_sec / total_pages, 1) if total_pages > 0 else 0
    total_highlights = int(books_df['highlights'].sum()) if not books_df.empty else 0
    total_books = len(books_df)

    # 3. 日期打卡
    page_stats['dt'] = pd.to_datetime(page_stats['start_time'], unit='s')
    page_stats['date'] = page_stats['dt'].dt.date
    unique_dates = sorted(page_stats['date'].unique())

    start_date_str = unique_dates[0].strftime("%Y-%m-%d") if unique_dates else "N/A"
    end_date_str = unique_dates[-1].strftime("%Y-%m-%d") if unique_dates else "N/A"
    total_calendar_days = (unique_dates[-1] - unique_dates[0]).days + 1 if len(unique_dates) > 1 else len(unique_dates)
    curr_streak, max_streak = calculate_streaks(unique_dates)

    # 4. 会话分析 (>10分钟间隔算新会话)
    page_stats['gap'] = page_stats['start_time'] - (page_stats['start_time'].shift(1) + page_stats['duration'].shift(1))
    page_stats['new_session'] = (page_stats['gap'] > 600) | (page_stats['id_book'] != page_stats['id_book'].shift(1))
    page_stats['session_id'] = page_stats['new_session'].cumsum()
    sessions = page_stats.groupby('session_id')['duration'].sum() / 60.0
    total_sessions = len(sessions)
    avg_session_min = round(sessions.mean(), 1)
    max_session_min = round(sessions.max(), 1)

    # 5. 夜猫子指数 (00:00 - 06:00 时段比例)
    page_stats['hour'] = page_stats['dt'].dt.hour
    night_sec = page_stats[page_stats['hour'].isin([0, 1, 2, 3, 4, 5])]['duration'].sum()
    night_ratio = round((night_sec / total_sec) * 100, 1) if total_sec > 0 else 0

    # 5.1 生成 24 小时阅读时长分布数据（供 Recharts 面积图渲染）
    hourly_duration = page_stats.groupby('hour')['duration'].sum() / 3600.0
    time_distribution = [
        {"hour": f"{h:02d}:00", "hours": round(hourly_duration.get(h, 0.0), 2)}
        for h in range(24)
    ]

    # 6. 图书进度 & ETA 预测
    book_stats = page_stats.groupby('id_book').agg(
        duration=('duration', 'sum'),
        logged_pages=('page', 'count'),
        max_page=('page', 'max')
    ).reset_index()

    merged_top = pd.merge(books_df, book_stats, left_on='id', right_on='id_book', how='inner')
    merged_top['progress_pct'] = np.minimum(100.0, (merged_top['max_page'] / merged_top['pages']) * 100)
    merged_top['sec_per_page'] = merged_top['duration'] / merged_top['logged_pages']
    merged_top['remaining_pages'] = np.maximum(0, merged_top['pages'] - merged_top['max_page'])
    merged_top['eta_hours'] = round((merged_top['remaining_pages'] * merged_top['sec_per_page']) / 3600.0, 1)
    merged_top = merged_top.sort_values(by='duration', ascending=False)

    books_list = []
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for idx, (_, r) in enumerate(merged_top.head(10).iterrows()):
        clean_title = r['title'].split('（')[0].split('(')[0].strip()
        time_str = f"{r['duration'] / 3600.0:.1f}h" if r['duration'] >= 3600 else f"{int(r['duration'] // 60)}m"
        eta_str = "已完成" if r['progress_pct'] >= 100 else f"{r['eta_hours']}h"
        
        books_list.append({
            "rank": idx + 1,
            "medal": medals[idx] if idx < 5 else f"{idx+1}",
            "title": clean_title,
            "duration": time_str,
            "hours": round(r['duration'] / 3600.0, 2),
            "progress": round(r['progress_pct'], 1),
            "eta": eta_str,
            "highlights": int(r['highlights']),
            "status": "finished" if r['progress_pct'] >= 100 else "reading"
        })

    # 7. 最近动态
    last_record = page_stats.sort_values(by='start_time', ascending=False).iloc[0]
    last_book_row = books_df[books_df['id'] == last_record['id_book']].iloc[0]
    last_book_title = last_book_row['title'].split('（')[0].split('(')[0].strip()
    last_time = (datetime.datetime.fromtimestamp(last_record['start_time'], datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    update_date_str = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")

    # 组装最终网页使用的 JSON 对象
    web_data = {
        "period": {
            "start": start_date_str,
            "end": end_date_str,
            "totalDays": total_calendar_days,
            "updatedAt": update_date_str
        },
        "overall": {
            "totalHours": total_hrs,
            "totalMinutes": total_mins,
            "totalPages": total_pages,
            "totalSessions": total_sessions,
            "maxSessionMin": max_session_min,
            "avgSessionMin": avg_session_min,
            "activeBooks": total_books,
            "avgSpeedPph": avg_speed_pph,
            "avgSecPerPage": avg_sec_per_page,
            "currentStreak": curr_streak,
            "maxStreak": max_streak,
            "nightOwlRatio": night_ratio,
            "totalHighlights": total_highlights
        },
        "heatmap": get_daily_heatmap(cursor),
        "recent": {
            "title": last_book_title,
            "time": last_time
        },
        "timeDistribution": time_distribution,
        "books": books_list
    }

    # 保存文件
    os.makedirs(os.path.dirname(JSON_OUTPUT_PATH), exist_ok=True)
    with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 成功生成网页数据文件: {JSON_OUTPUT_PATH}")

def get_daily_heatmap(cursor):
    """提取过去 365 天每天的阅读时长（分钟）"""
    # 计算一年前的日期
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # 假设你的阅读记录表/日志表中有 timestamp 或 date 字段
    # 这里以 KOReader 的 page_stat / book_stat 按天 group by 为例：
    query = """
        SELECT 
            date(start_time, 'unixepoch', 'localtime') as read_date,
            SUM(duration) / 60 as minutes
        FROM user_book
        WHERE read_date >= ?
        GROUP BY read_date
        ORDER BY read_date ASC
    """
    
    cursor.execute(query, (one_year_ago,))
    rows = cursor.fetchall()
    
    # 转为字典 {"2026-01-01": 45, ...}
    heatmap_data = {row[0]: round(row[1], 1) for row in rows if row[0]}
    return heatmap_data

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ 错误: 未找到数据库文件 {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    generate_web_json(conn)
    conn.close()

if __name__ == '__main__':
    main()
