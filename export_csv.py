import os
import re
import sqlite3
import datetime
import pandas as pd

DB_PATH = 'statistics.sqlite3'
OUTPUT_DIR = 'data_csv'
README_PATH = 'README.md'

def update_readme(conn):
    """提取核心统计数据并写入 README.md"""
    page_stats = pd.read_sql_query("SELECT duration FROM page_stat_data", conn)
    books_df = pd.read_sql_query("SELECT id FROM book WHERE total_read_time > 0", conn)
    
    # 计算核心指标
    total_seconds = page_stats['duration'].sum() if not page_stats.empty else 0
    total_hours = round(total_seconds / 3600.0, 1)
    total_pages = len(page_stats)
    total_books = len(books_df)
    
    # 获取更新日期 (UTC/北京时间)
    update_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
    date_str = update_time.strftime("%Y-%m-%d")

    # 构建几行简洁的 Markdown 统计小卡片
    stats_markdown = f"""<!-- READ_STATS_START -->
### 📊 KOReader 阅读实时简报

| ⏱️ 总阅读时长 | 📚 阅读书目 | 📖 总阅读页数 | 📅 最后更新 |
| :---: | :---: | :---: | :---: |
| **{total_hours} 小时** | **{total_books} 本** | **{total_pages} 页** | **{date_str}** |
<!-- READ_STATS_END -->"""

    # 读取并更新 README.md
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
        
    print("✅ README.md 统计数据已更新！")

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ 错误: 未找到数据库文件 {DB_PATH}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 导出所有表为 CSV
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        df = pd.read_sql_query(f"SELECT * FROM `{table}`", conn)
        df.to_csv(os.path.join(OUTPUT_DIR, f"{table}.csv"), index=False, encoding='utf-8-sig')

    # 2. 导出所有视图为 CSV
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
    views = [row[0] for row in cursor.fetchall()]
    for view in views:
        df = pd.read_sql_query(f"SELECT * FROM `{view}`", conn)
        df.to_csv(os.path.join(OUTPUT_DIR, f"{view}_view.csv"), index=False, encoding='utf-8-sig')

    print("✅ CSV 文件导出完成！")

    # 3. 更新 README.md 统计
    update_readme(conn)

    conn.close()

if __name__ == '__main__':
    main()
