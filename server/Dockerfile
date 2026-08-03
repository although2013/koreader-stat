# 多阶段构建：先用 Node 构建前端静态产物，再拷进跑 Flask 的 Python 镜像。
FROM node:20-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js tailwind.config.js postcss.config.js ./
COPY src ./src
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY export_stats.py ./
COPY server/app.py server/app.py
COPY --from=frontend /app/dist ./dist

ENV DATA_DIR=/app/data
ENV DIST_DIR=/app/dist
VOLUME ["/app/data"]

EXPOSE 5000
CMD ["gunicorn", "--chdir", "server", "--bind", "0.0.0.0:5000", "app:app"]
