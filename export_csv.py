import os
import re
import sqlite3
import datetime
import pandas as pd
import numpy as np

DB_PATH = 'statistics.sqlite3'
OUTPUT_DIR = 'data_csv'
README_PATH = 'README.md'

def calculate_streaks(dates):
    """计算 KOReader 风格的连续打卡天数 (Streak)"""
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
    
    # 计算截至最近一次阅读的连续天数
    curr_streak = 1
    for i in range(len(sorted_dates)-2, -1, -1):
        if (sorted_dates[i+1] - sorted_dates[i]).days == 1:
            curr_streak += 1
        else:
            break
    return curr_streak, max_streak

def get_advanced_stats(conn):
    page_stats = pd.read_sql_query("SELECT id_book, page, start_time, duration FROM page_stat_data ORDER BY start_time", conn)
    books_df = pd.read_sql_query("SELECT id, title, pages, highlights FROM book WHERE total_read_time > 0", conn)
    
    if page_stats.empty:
        return {}

    # 1. 阅读会话分析 (间隔 > 10 分钟算新会话)
    page_stats['gap'] = page_stats['start_time'] - (page_stats['start_time'].shift(1) + page_stats['duration'].shift(1))
    page_stats['new_session'] = (page_stats['gap'] > 600) | (page_stats['id_book'] != page_stats['id_book'].shift(1))
    page_stats['session_id'] = page_stats['new_session'].cumsum()
    
    sessions = page_stats.groupby('session_id')['duration'].sum() / 60.0 # 分钟
    total_sessions = len(sessions)
    avg_session_min = round(sessions.mean(), 1)
    max_session_min = round(sessions.max(), 1)

    # 2. 夜猫子指数 (00:00 - 06:00 时段比例)
    page_stats['hour'] = pd.to_datetime(page_stats['start_time'], unit='s').dt.hour
    night_sec = page_stats[page_stats['hour'].isin([0, 1, 2, 3, 4, 5])]['duration'].sum()
    night_ratio = round((night_sec / page_stats['duration'].sum()) * 100, 1)

    # 3. 各书进度与 ETA 计算
    progress_df = page_stats.groupby('id_book').agg(
        max_page=('page', 'max'),
        logged_pages=('page', 'count'),
        total_sec=('duration', 'sum')
    ).reset_index()

    merged = pd.merge(books_df, progress_df, left_on='id', right_on='id_book')
    merged['progress_pct'] = np.minimum(100.0, (merged['max_page'] / merged['pages']) * 100)
    merged['sec_per_page'] = merged['total_sec'] / merged['logged_pages']
    merged['remaining_pages'] = np.maximum(0, merged['pages'] - merged['max_page'])
    merged['eta_hours'] = round((merged['remaining_pages'] * merged['sec_per_page']) / 3600.0, 1)

    return {
        'total_sessions': total_sessions,
        'avg_session_min': avg_session_min,
        'max_session_min': max_session_min,
        'night_ratio': night_ratio,
        'book_progress': merged.sort_values(by='total_sec', ascending=False)
    }

def update_readme(conn):
    """更新 README.md"""
    stats_markdown = generate_koreader_stats(conn)

    if not os.path.exists(README_PATH):
        content = f"# 我的阅读记录\n\n{stats_markdown}\n"
    else:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r"<!-- READ_STATS_START -->.*?<!-- READ_STATS_END -->"
        if re.search(pattern, content, flags=re.DOTALL):
            content = re.sub(pattern, stats_markdown, content, flags=re.DOTALL)
        else:
            content = f"{stats_markdown}\n\n" + content

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("✅ README.md 仪表盘更新成功！")

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ 错误: 未找到数据库文件 {DB_PATH}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 导出表为 CSV
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        df = pd.read_sql_query(f"SELECT * FROM `{table}`", conn)
        df.to_csv(os.path.join(OUTPUT_DIR, f"{table}.csv"), index=False, encoding='utf-8-sig')

    # 2. 导出视图为 CSV
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
    views = [row[0] for row in cursor.fetchall()]
    for view in views:
        df = pd.read_sql_query(f"SELECT * FROM `{view}`", conn)
        df.to_csv(os.path.join(OUTPUT_DIR, f"{view}_view.csv"), index=False, encoding='utf-8-sig')

    print("✅ 所有 CSV 文件导出完成！")

    # 3. 自动更新 README 页面
    update_readme(conn)
    conn.close()

if __name__ == '__main__':
    main()
