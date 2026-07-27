import os
import re
import sqlite3
import datetime
import pandas as pd
import numpy as np

DB_PATH = 'statistics.sqlite3'
README_PATH = 'README.md'

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

def generate_koreader_stats(conn):
    """提取 KOReader 深度阅读数据并生成 Markdown 仪表盘"""
    page_stats = pd.read_sql_query("SELECT id_book, page, start_time, duration FROM page_stat_data ORDER BY start_time", conn)
    books_df = pd.read_sql_query("SELECT id, title, authors, highlights, pages, total_read_time, total_read_pages FROM book WHERE total_read_time > 0", conn)

    if page_stats.empty:
        return "<!-- READ_STATS_START -->\n暂无阅读数据\n<!-- READ_STATS_END -->"

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

    # 3. 连续打卡与活跃天数
    page_stats['dt'] = pd.to_datetime(page_stats['start_time'], unit='s')
    page_stats['date'] = page_stats['dt'].dt.date
    unique_dates = sorted(page_stats['date'].unique())

    start_date_str = unique_dates[0].strftime("%Y-%m-%d") if unique_dates else "N/A"
    end_date_str = unique_dates[-1].strftime("%Y-%m-%d") if unique_dates else "N/A"
    total_calendar_days = (unique_dates[-1] - unique_dates[0]).days + 1 if len(unique_dates) > 1 else len(unique_dates)
    active_days = len(unique_dates)
    active_ratio = round((active_days / total_calendar_days) * 100, 1) if total_calendar_days > 0 else 0

    curr_streak, max_streak = calculate_streaks(unique_dates)

    # 4. 阅读会话分析 (间隔 > 10 分钟算新会话)
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

    # 6. Top 投入图书 & 进度与 ETA 预测
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

    top_rows = []
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for idx, (_, r) in enumerate(merged_top.head(5).iterrows()):
        clean_title = r['title'].split('（')[0].split('(')[0].strip()
        if len(clean_title) > 22:
            clean_title = clean_title[:20] + "..."
        time_str = f"{r['duration'] / 3600.0:.1f}h" if r['duration'] >= 3600 else f"{int(r['duration'] // 60)}m"
        
        progress_str = f"{r['progress_pct']:.1f}%"
        eta_str = f"已读完" if r['progress_pct'] >= 100 else f"约还需 {r['eta_hours']}h"
        
        top_rows.append(f"| {medals[idx]} | **{clean_title}** | {time_str} | {progress_str} | {eta_str} | {int(r['highlights'])} 处 |")

    top_books_table = "\n".join(top_rows)

    # 7. 最近阅读动态
    last_record = page_stats.sort_values(by='start_time', ascending=False).iloc[0]
    last_book_row = books_df[books_df['id'] == last_record['id_book']].iloc[0]
    last_book_title = last_book_row['title'].split('（')[0].split('(')[0].strip()
    
    last_time = (datetime.datetime.fromtimestamp(last_record['start_time'], datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    update_date_str = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")

    # 组合为 Markdown 看板
    stats_markdown = f"""<!-- READ_STATS_START -->
### 📖 KOReader 阅读深度看板

> 📅 **统计周期**：`{start_date_str}` ~ `{end_date_str}` （追踪共 {total_calendar_days} 天） | ⏱️ **更新时间**：`{update_date_str}`

#### 📊 核心阅读指标 (Overall Statistics)

| 统计指标 (Metric) | 数值 (Value) | KOReader 统计说明 |
| :--- | :---: | :--- |
| ⏱️ **总阅读时长** | **{total_hrs} 小时** ({total_mins} 分钟) | `SUM(duration)` 真实有效阅读时长 |
| 📄 **总翻页数量** | **{total_pages:,} 页** | `COUNT(*)` 累积翻页日志条目 |
| 🎯 **阅读会话次数** | **{total_sessions} 次** (最长 **{max_session_min} 分钟**) | 平均单次 **{avg_session_min} 分钟** |
| 📚 **在读/已图书目** | **{total_books} 本** | `total_read_time > 0` 活跃图书 |
| ⚡ **平均阅读速度** | **{avg_speed_pph} 页/小时** ({avg_sec_per_page} 秒/页) | KOReader `PPH` 翻页效率 |
| 🔥 **阅读打卡 Streak** | **{curr_streak} 天** (历史最长: **{max_streak} 天**) | 连续阅读打卡天数 |
| 🌙 **夜猫子指数** | **{night_ratio}%** (00:00-06:00 时段) | 🏷️ 资深夜猫子读者 |
| ✏️ **划线与高亮总数** | **{total_highlights} 处** | `SUM(highlights)` 笔记总数 |

#### 🏆 核心研读图书进度与读完预估 (Progress & ETA)

| 排名 | 图书名称 | 阅读时长 | 当前进度 | 剩余预计 | 划线/标注 |
| :---: | :--- | :---: | :---: | :---: | :---: |
{top_books_table}

#### ⌛ 最近阅读动态
最近阅读：《**{last_book_title}**》 （时间：`{last_time}`）
<!-- READ_STATS_END -->"""

    return stats_markdown

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

    conn = sqlite3.connect(DB_PATH)
    update_readme(conn)
    conn.close()

if __name__ == '__main__':
    main()