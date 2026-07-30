import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// public/ 下的文件会被原样拷到 dist/，其中 reading_data.json 由 export_stats.py 生成，
// _headers 是 Cloudflare Pages 的缓存配置。
export default defineConfig({
  plugins: [react()],
});
