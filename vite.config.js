import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/*
 * 把构建出的 CSS 内联进 HTML。
 * CSS 的 <link> 是阻塞渲染的：浏览器必须拿到它才能首次绘制。
 * 这份 CSS 只有 4KB(gzip)，内联省掉一整跳请求；代价是它不再被单独缓存，
 * 但入口 HTML 本来就是 no-cache，每次都要取，等于没有额外代价。
 */
function inlineCss() {
  return {
    name: 'inline-css',
    apply: 'build',
    enforce: 'post',
    transformIndexHtml: {
      order: 'post',
      handler(html, ctx) {
        if (!ctx.bundle) return html;

        for (const [key, asset] of Object.entries(ctx.bundle)) {
          if (!key.endsWith('.css') || asset.type !== 'asset') continue;
          const css = asset.source.toString();
          const linkPattern = new RegExp(`<link[^>]+href="[^"]*${asset.fileName.split('/').pop()}"[^>]*>`);
          if (!linkPattern.test(html)) continue;
          html = html.replace(linkPattern, `<style>${css}</style>`);
          delete ctx.bundle[key]; // 已内联，不必再产出独立文件
        }
        return html;
      },
    },
  };
}

// public/ 下的文件会被原样拷到 dist/，其中 reading_data.json 由 export_stats.py 生成，
// _headers 是 Cloudflare 的缓存配置。
export default defineConfig({
  plugins: [react(), inlineCss()],
});
