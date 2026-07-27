import os
import re
import sqlite3
import datetime
import pandas as pd

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

def generate_koreader_stats(conn):
    """提取 KOReader 原生风格的丰富统计数据"""
    page_stats = pd.read_sql_query("SELECT id_book, page, start_time, duration FROM page_stat_data", conn)
    books_df = pd.read_sql_query("SELECT id, title, authors, highlights, pages, total_read_time, total_read_pages FROM book WHERE total_read_time > 0", conn)

    if page_stats.empty:
        return "<!-- READ_STATS_START -->\n暂无阅读数据\n<!-- READ_STATS_END -->"

    # 1. 基础汇总数据
    total_sec = page_stats['duration'].sum()
    total_hrs = round(total_sec / 3600.0, 1)
    total_mins = int(total_sec // 60)
    total_pages = len(page_stats)

    # 2. 速度指标 (PPH & SPM)
    avg_speed_pph = round(total_pages / (total_sec / 3600.0), 1) if total_sec > 0 else 0
    avg_sec_per_page = round(total_sec / total_pages, 1) if total_pages > 0 else 0
    total_highlights = int(books_df['highlights'].sum()) if not books_df.empty else 0
    total_books = len(books_df)

    # 3. 连续阅读打卡与活跃度 (Streaks & Active Days)
    page_stats['dt'] = pd.to_datetime(page_stats['start_time'], unit='s')
    page_stats['date'] = page_stats['dt'].dt.date
    unique_dates = sorted(page_stats['date'].unique())

    start_date_str = unique_dates[0].strftime("%Y-%m-%d") if unique_dates else "N/A"
    end_date_str = unique_dates[-1].strftime("%Y-%m-%d") if unique_dates else "N/A"
    total_calendar_days = (unique_dates[-1] - unique_dates[0]).days + 1 if len(unique_dates) > 1 else len(unique_dates)
    active_days = len(unique_dates)
    active_ratio = round((active_days / total_calendar_days) * 100, 1) if total_calendar_days > 0 else 0

    curr_streak, max_streak = calculate_streaks(unique_dates)

    # 4. Top 3 投入时长最多图书 (Most Read Books)
    book_stats = page_stats.groupby('id_book').agg(
        duration=('duration', 'sum'),
        logged_pages=('page', 'count')
    ).reset_index()

    merged_top = pd.merge(books_df, book_stats, left_on='id', right_on='id_book', how='inner')
    merged_top = merged_top.sort_values(by='duration', ascending=False).head(3)

    top_rows = []
    medals = ["🥇", "🥈", "🥉"]
    for idx, (_, r) in enumerate(merged_top.iterrows()):
        clean_title = r['title'].split('（')[0].split('(')[0].strip()
        if len(clean_title) > 22:
            clean_title = clean_title[:20] + "..."
        time_str = f"{r['duration'] / 3600.0:.1f} 小时" if r['duration'] >= 3600 else f"{int(r['duration'] // 60)} 分钟"
        top_rows.append(f"| {medals[idx]} | **{clean_title}** | {time_str} | {int(r['logged_pages'])} 页 | {int(r['highlights'])} 处 |")

    top_books_table = "\n".join(top_rows)

    # 5. 最近阅读动态
    last_record = page_stats.sort_values(by='start_time', ascending=False).iloc[0]
    last_book_row = books_df[books_df['id'] == last_record['id_book']].iloc[0]
    last_book_title = last_book_row['title'].split('（')[0].split('(')[0].strip()
    
    # 转换时间为 UTC+8
    last_time = (datetime.datetime.fromtimestamp(last_record['start_time'], datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    update_date_str = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")

    # 组合为漂亮的 Markdown 看板
    stats_markdown = f"""<!-- READ_STATS_START -->
### 📖 KOReader 阅读统计看板

> 📅 **统计周期**：`{start_date_str}` ~ `{end_date_str}` （追踪共 {total_calendar_days} 天） | ⏱️ **数据更新**：`{update_date_str}`

#### 📊 核心阅读指标 (Overall Statistics)

| 统计指标 (Metric) | 数值 (Value) | KOReader 统计说明 |
| :--- | :---: | :--- |
| ⏱️ **总阅读时长** | **{total_hrs} 小时** ({total_mins} 分钟) | `SUM(duration)` 真实有效阅读时长 |
| 📄 **总翻页数量** | **{total_pages:,} 页** | `COUNT(*)` 累积翻页日志条目 |
| 📚 **在读/已图书目** | **{total_books} 本** | `total_read_time > 0` 活跃图书 |
| ⚡ **平均阅读速度** | **{avg_speed_pph} 页/小时** ({avg_sec_per_page} 秒/页) | KOReader 原生 `PPH` 翻页效率 |
| 🔥 **阅读打卡 Streak** | **{curr_streak} 天** (历史最长: **{max_streak} 天**) | 连续阅读打卡天数计算 |
| 📅 **阅读天数活跃率** | **{active_days} / {total_calendar_days} 天** (**{active_ratio}%**) | 有阅读记录的天数比例 |
| ✏️ **划线与高亮总数** | **{total_highlights} 处** | `SUM(highlights)` 笔记与标注汇总 |

#### 🏆 投入时长 Top 3 图书 (Most Read Books)

| 排名 | 图书名称 | 阅读时长 | 累计页数 | 划线/标注 |
| :---: | :--- | :---: | :---: | :---: |
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
