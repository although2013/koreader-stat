"""自建服务器：接收 KOReader 插件上传的 statistics.sqlite3，生成 reading_data.json 并出前端页面。

复用仓库根目录的 export_stats.py 里的解析逻辑，避免维护两套统计口径。
"""

import os
import sqlite3
import sys
import time
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

# export_stats.py 在仓库根目录，server/ 是其子目录，需要把根目录加进 sys.path 才能 import。
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import export_stats  # noqa: E402  (必须在 sys.path 处理之后 import)

DATA_DIR = Path(os.environ.get('DATA_DIR', str(Path(__file__).resolve().parent / 'data')))
DB_PATH = DATA_DIR / 'statistics.sqlite3'
JSON_PATH = DATA_DIR / 'reading_data.json'
DIST_DIR = Path(os.environ.get('DIST_DIR', str(REPO_ROOT / 'dist')))

UPLOAD_TOKEN = os.environ.get('UPLOAD_TOKEN')
MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', '50'))

# SQLite 文件头魔数，用于校验上传内容确实是数据库而不是垃圾文件。
SQLITE_MAGIC = b'SQLite format 3\x00'

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024


def _check_auth():
    if not UPLOAD_TOKEN:
        # 没配置 Token 就拒绝所有上传，而不是"裸奔"接受任何人上传。
        abort(500, description='UPLOAD_TOKEN 未配置，服务器拒绝接受上传')
    if request.headers.get('Authorization') != f'Bearer {UPLOAD_TOKEN}':
        abort(401, description='Token 无效')


@app.post('/api/upload')
def upload():
    _check_auth()

    file = request.files.get('database')
    if file is None:
        abort(400, description='缺少 database 文件字段')

    payload = file.read()
    if payload[:16] != SQLITE_MAGIC:
        abort(400, description='上传的文件不是有效的 SQLite 数据库')

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_bytes(payload)

    conn = sqlite3.connect(str(DB_PATH))
    try:
        export_stats.generate_web_json(conn, json_output_path=str(JSON_PATH))
    finally:
        conn.close()

    return jsonify(ok=True, updatedAt=int(time.time()))


@app.get('/reading_data.json')
def reading_data():
    if not JSON_PATH.exists():
        abort(404, description='尚无阅读数据，请先用 KOReader 插件上传一次 statistics.sqlite3')
    return send_from_directory(DATA_DIR, JSON_PATH.name)


@app.get('/healthz')
def healthz():
    return jsonify(ok=True)


@app.get('/', defaults={'path': ''})
@app.get('/<path:path>')
def serve_frontend(path):
    if not DIST_DIR.exists():
        abort(500, description=f'前端构建产物不存在: {DIST_DIR}，请先执行 npm run build')

    target = DIST_DIR / path
    if path and target.is_file():
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, 'index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')))
