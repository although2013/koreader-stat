# 📚 我的 KOReader 电子书阅读记录


## 🖥️ 自建服务器（KOReader 插件直传）

除了「Dropbox + GitHub Actions 定时拉取」这条链路，仓库里还提供了一条可以自己部署的实时链路：KOReader 插件把 `statistics.sqlite3` 直接上传到你自己的服务器，服务器解析后直接出网页。两条链路互不影响，按需选用。

### 1. 部署服务器

```bash
export UPLOAD_TOKEN=<自己生成一个足够长的随机字符串>
docker compose up -d --build
```

服务器启动后：
- `http://<你的服务器>:5000/` — 阅读数据仪表盘（跟现有前端一致）
- `POST /api/upload` — 插件上传数据库的接口，需要 `Authorization: Bearer <UPLOAD_TOKEN>`

数据持久化在 Docker volume `koreader_stat_data` 里（`statistics.sqlite3` + `reading_data.json`）。

建议在服务器前面挂反向代理（如 Caddy/Nginx）开 HTTPS，避免 Token 和阅读数据以明文 HTTP 传输。

### 2. 安装 KOReader 插件

把 [koreader-plugin/readingstat.koplugin](koreader-plugin/readingstat.koplugin) 整个文件夹拷贝到设备的 `koreader/plugins/` 目录下，重启 KOReader。

在 KOReader 里：菜单 → **更多工具 (More tools)** → **Reading stat uploader** → **Server settings**，填入服务器地址（如 `https://your-domain.com`）和上面设置的 `UPLOAD_TOKEN`。之后点 **Upload now** 即可手动同步一次。

菜单里还有一个可勾选项 **Upload when closing a book (only if Wi-Fi is already connected)**：勾上之后，每次关闭一本书时，如果设备**当前已经连着 Wi-Fi**（不会主动帮你打开 Wi-Fi、也不等待联网），就会静默上传一次；没联网、没配置服务器地址/Token 时会自动跳过，不会弹窗打扰。上传失败仍会弹提示。

> 如果上传报错，或者关书时卡顿明显，看 KOReader 日志（`crash.log`）里 `[ReadingStat]` 开头的记录；关书时的上传是同步阻塞的，服务器很慢会导致关书界面短暂卡顿。

## 📝 个人简介 / 其他说明
这里可以写你自己的其他 Markdown 内容，不会被自动化脚本覆盖...