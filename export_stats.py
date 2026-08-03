import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

DB_PATH = 'statistics.sqlite3'
JSON_OUTPUT_PATH = 'public/reading_data.json'  # Cloudflare Pages 静态资源目录

# ⚙️ 时区的唯一定义处：改这一个数字，Python 与前端的日界线会一起跟着变
#    （前端不硬编码时区，而是读 JSON 里的 period.tzOffsetHours）
# 日期与小时口径都以此为准，不依赖运行环境的本地时区，否则同一份 DB
# 在本机 +9 与 GitHub Actions UTC 上会算出不同结果。
TZ_OFFSET_HOURS = 9  # Asia/Tokyo
TZ = timezone(timedelta(hours=TZ_OFFSET_HOURS))
SQLITE_TZ_MODIFIER = f'{TZ_OFFSET_HOURS:+d} hours'  # 供 SQLite datetime() 使用

SESSION_GAP_SEC = 600  # 间隔超过 10 分钟即视为新的阅读会话


def to_local_datetime(epoch_series):
    """Unix 时间戳 -> 目标时区的 naive datetime，便于直接取 .dt.date / .dt.hour"""
    return (
        pd.to_datetime(epoch_series, unit='s', utc=True)
        .dt.tz_convert(TZ)
        .dt.tz_localize(None)
    )


def split_sessions(df):
    """按「间隔 > 10 分钟或换书」切分会话，返回每个会话的时长（分钟）"""
    if df.empty:
        return pd.Series(dtype='float64')

    df = df.sort_values('start_time')
    gap = df['start_time'] - (df['start_time'].shift(1) + df['duration'].shift(1))
    new_session = (gap > SESSION_GAP_SEC) | (df['id_book'] != df['id_book'].shift(1))
    return df.groupby(new_session.cumsum())['duration'].sum() / 60.0


def build_metrics(df, label, days):
    """计算一个时间切片的指标组。df 需已带 date / hour 列（统一时区口径）"""
    total_sec = int(df['duration'].sum())
    # KOReader's page count is based on distinct pages. Re-visiting a page should
    # add reading time but not inflate the number of pages read.
    total_pages = len(df.drop_duplicates(subset=['id_book', 'page']))
    total_hrs = total_sec / 3600.0
    sessions = split_sessions(df)
    night_sec = int(df.loc[df['hour'] < 6, 'duration'].sum()) if total_pages else 0

    return {
        "label": label,
        "days": days,
        "daysWithReading": int(df['date'].nunique()),
        "totalHours": round(total_hrs, 1),
        "totalMinutes": int(total_sec // 60),
        "totalPages": total_pages,
        "totalSessions": int(len(sessions)),
        "avgSessionMin": round(float(sessions.mean()), 1) if len(sessions) else 0.0,
        "maxSessionMin": round(float(sessions.max()), 1) if len(sessions) else 0.0,
        "activeBooks": int(df['id_book'].nunique()),
        "avgSpeedPph": round(total_pages / total_hrs, 1) if total_sec > 0 else 0.0,
        "avgSecPerPage": round(total_sec / total_pages, 1) if total_pages > 0 else 0.0,
        "nightOwlRatio": round(night_sec / total_sec * 100, 1) if total_sec > 0 else 0.0,
        "avgDailyMin": round((total_sec / 60.0) / days, 1) if days > 0 else 0.0,
    }


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

def get_daily_heatmap(cursor):
    """提取过去 365 天每天的阅读时长（分钟），使用 KOReader 的 page_stat_data 表"""
    one_year_ago = (datetime.now(TZ) - timedelta(days=365)).strftime('%Y-%m-%d')

    # 日界线用固定偏移，不用 'localtime'（后者跟运行环境走，CI 与本机会不一致）
    query = f"""
        SELECT
            date(start_time, 'unixepoch', '{SQLITE_TZ_MODIFIER}') as read_date,
            SUM(duration) / 60.0 as minutes
        FROM page_stat_data
        WHERE date(start_time, 'unixepoch', '{SQLITE_TZ_MODIFIER}') >= ?
        GROUP BY read_date
        ORDER BY read_date ASC
    """

    cursor.execute(query, (one_year_ago,))
    rows = cursor.fetchall()
    
    # 转为字典 {"2026-01-01": 45.5, ...}
    heatmap_data = {row[0]: round(row[1], 1) for row in rows if row[0]}
    return heatmap_data

def generate_web_json(conn, json_output_path=JSON_OUTPUT_PATH):
    """从 SQLite 提取并清洗数据，生成 Cloudflare Pages 所需的结构化 JSON

    json_output_path 可传入以复用本函数（例如 server/app.py 在收到设备
    上传的数据库后，直接调用本函数生成到服务器自己的数据目录，而不是
    仓库里 GitHub Actions 用的 public/ 目录）。
    """
    # 🌟 1. 修复：建立游标对象，供 get_daily_heatmap 使用
    cursor = conn.cursor()

    page_stats = pd.read_sql_query("SELECT id_book, page, start_time, duration FROM page_stat_data ORDER BY start_time", conn)
    books_df = pd.read_sql_query("SELECT id, title, authors, highlights, pages, total_read_time, total_read_pages FROM book WHERE total_read_time > 0", conn)

    if page_stats.empty:
        print("⚠️ 数据库中没有找到阅读记录。")
        return

    # 1. 统一时区的时间列：后续所有 date / hour 口径都基于它
    page_stats['dt'] = to_local_datetime(page_stats['start_time'])
    page_stats['date'] = page_stats['dt'].dt.date
    page_stats['hour'] = page_stats['dt'].dt.hour

    # 2. 划线与书目（book 表只有累计值，无时间戳，因此无法按周期拆分）
    total_highlights = int(books_df['highlights'].sum()) if not books_df.empty else 0
    total_books = len(books_df)

    # 3. 日期打卡
    unique_dates = sorted(page_stats['date'].unique())
    start_date_str = unique_dates[0].strftime("%Y-%m-%d") if unique_dates else "N/A"
    end_date_str = unique_dates[-1].strftime("%Y-%m-%d") if unique_dates else "N/A"
    total_calendar_days = (unique_dates[-1] - unique_dates[0]).days + 1 if len(unique_dates) > 1 else len(unique_dates)
    curr_streak, max_streak = calculate_streaks(unique_dates)

    # 4. 三档周期切片：总计 / 本周（最近 7 天滚动）/ 当天
    today_local = datetime.now(TZ).date()
    week_start = today_local - timedelta(days=6)  # 含今天在内共 7 天
    last_logged_date = unique_dates[-1]           # 「当天」以最后有记录的一天为准

    week_df = page_stats[page_stats['date'] >= week_start]
    today_df = page_stats[page_stats['date'] == last_logged_date]
    previous_date = last_logged_date - timedelta(days=1)
    previous_day_df = page_stats[page_stats['date'] == previous_date]

    metrics = {
        "all": build_metrics(page_stats, f"{start_date_str} ~ {end_date_str}", total_calendar_days),
        "week": build_metrics(week_df, f"{week_start:%m-%d} ~ {today_local:%m-%d}", 7),
        "today": build_metrics(today_df, f"{last_logged_date:%m-%d}", 1),
    }
    # Streak 是跨周期概念，三档共用同一个全局值；划线只有总计口径
    for block in metrics.values():
        block["currentStreak"] = curr_streak
        block["maxStreak"] = max_streak
    metrics["all"]["totalHighlights"] = total_highlights
    metrics["all"]["activeBooks"] = total_books  # 总计沿用「全库有阅读时长的书」口径
    metrics["week"]["start"] = week_start.strftime("%Y-%m-%d")
    metrics["week"]["end"] = today_local.strftime("%Y-%m-%d")
    metrics["today"]["date"] = last_logged_date.strftime("%Y-%m-%d")
    # Provide the previous calendar day for the daily comparison badges.
    metrics["today"]["previousDay"] = build_metrics(previous_day_df, f"{previous_date:%m-%d}", 1)
    metrics["today"]["previousDay"]["date"] = previous_date.strftime("%Y-%m-%d")

    # 5. 生成 24 小时阅读时长分布数据
    hourly_duration = page_stats.groupby('hour')['duration'].sum() / 3600.0
    time_distribution = [
        {"hour": f"{h:02d}:00", "hours": round(hourly_duration.get(h, 0.0), 2)}
        for h in range(24)
    ]

    # Calendar events: one entry per book and local calendar day.  Keeping this
    # compact daily representation lets the web UI join consecutive dates into
    # Google-Calendar-style bars without exposing every individual page event.
    calendar_df = (
        page_stats.groupby(['date', 'id_book'])['duration']
        .sum()
        .reset_index()
    )
    book_titles = books_df.set_index('id')['title'].to_dict()
    calendar_entries = [
        {
            "date": row['date'].strftime('%Y-%m-%d'),
            "bookId": int(row['id_book']),
            "title": str(book_titles.get(row['id_book'], 'Unknown book')).split('(')[0].strip(),
            "minutes": round(float(row['duration']) / 60.0, 1),
        }
        for _, row in calendar_df.iterrows()
    ]

    # 6. 图书进度 & ETA 预测 & 划线密度诊断
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
        
        # 🌟 计算划线密度与诊断模式
        hrs = r['duration'] / 3600.0
        highlight_density = round(r['highlights'] / hrs, 1) if hrs > 0 else 0.0
        if highlight_density >= 5.0:
            reading_mode = "💡 干货研读"
        elif highlight_density >= 1.5:
            reading_mode = "📝 随手记"
        else:
            reading_mode = "🌊 纯沉浸"

        books_list.append({
            "rank": idx + 1,
            "medal": medals[idx] if idx < 5 else f"{idx+1}",
            "title": clean_title,
            "duration": time_str,
            "hours": round(hrs, 2),
            "progress": round(r['progress_pct'], 1),
            "eta": eta_str,
            "highlights": int(r['highlights']),
            "highlightDensity": highlight_density,  # 划线密度
            "readingMode": reading_mode,            # 阅读模式 Tag
            "status": "finished" if r['progress_pct'] >= 100 else "reading"
        })
    
    # 🌟 最近 7 天阅读数据（与「本周」Tab 同一口径，直接复用上面的切片）
    recent_7days_df = week_df

    # 1. 每日阅读时长 (分钟) 柱状图数据
    daily_7days = (
        recent_7days_df.groupby('date')['duration'].sum() / 60.0
    ).reindex(
        [week_start + timedelta(days=i) for i in range(7)],
        fill_value=0
    )

    recent_7days_chart = [
        {
            "day": d.strftime("%m-%d"),
            "minutes": round(mins, 1)
        }
        for d, mins in daily_7days.items()
    ]

    # 2. 7 天主攻图书 Top 3
    recent_7days_books = (
        recent_7days_df.groupby('id_book')['duration'].sum()
        .reset_index()
        .sort_values(by='duration', ascending=False)
        .head(3)
    )
    
    top_7days_books = []
    for _, row in recent_7days_books.iterrows():
        book_match = books_df[books_df['id'] == row['id_book']]
        if not book_match.empty:
            title = book_match.iloc[0]['title'].split('（')[0].split('(')[0].strip()
            top_7days_books.append({
                "title": title,
                "hours": round(row['duration'] / 3600.0, 1)
            })

    

    # 7. 最近动态
    last_record = page_stats.sort_values(by='start_time', ascending=False).iloc[0]
    last_book_row = books_df[books_df['id'] == last_record['id_book']].iloc[0]
    last_book_title = last_book_row['title'].split('（')[0].split('(')[0].strip()
    last_time = datetime.fromtimestamp(int(last_record['start_time']), TZ).strftime("%Y-%m-%d %H:%M")
    update_date_str = datetime.now(TZ).strftime("%Y-%m-%d")

    # 8. 组装 JSON 对象
    # overall 是 metrics.all 的旧版别名，保留以兼容尚未更新的前端缓存
    overall = {key: metrics["all"][key] for key in (
        "totalHours", "totalMinutes", "totalPages", "totalSessions", "maxSessionMin",
        "avgSessionMin", "activeBooks", "avgSpeedPph", "avgSecPerPage",
        "currentStreak", "maxStreak", "nightOwlRatio", "totalHighlights",
    )}

    web_data = {
        "period": {
            "start": start_date_str,
            "end": end_date_str,
            "totalDays": total_calendar_days,
            "updatedAt": update_date_str,
            "timezone": f"UTC{TZ_OFFSET_HOURS:+d}",   # 展示用
            "tzOffsetHours": TZ_OFFSET_HOURS          # 前端据此切分日界线
        },
        "overall": overall,
        "metrics": metrics,
        "heatmap": get_daily_heatmap(cursor), # 传入正确的 cursor
        "recent": {
            "title": last_book_title,
            "time": last_time
        },
        "timeDistribution": time_distribution,
        "books": books_list,
        "calendarEntries": calendar_entries,
    }

    # 将 7 天数据写入 web_data 字典（汇总值直接取 metrics.week，保证与「本周」Tab 一致）
    web_data["last7Days"] = {
        "totalHours": metrics["week"]["totalHours"],
        "avgDailyMin": metrics["week"]["avgDailyMin"],
        "chart": recent_7days_chart,
        "topBooks": top_7days_books
    }

    # 保存文件
    output_dir = os.path.dirname(json_output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(json_output_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)

    return web_data

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ 错误: 未找到数据库文件 {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    generate_web_json(conn)
    conn.close()

if __name__ == '__main__':
    main()
