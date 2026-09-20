import { defineConfig } from 'astro/config';

// 构建模式，全部由环境变量驱动；不传变量时保持 GitHub Pages 现状（不影响线上站点）：
//  1) GitHub Pages（默认）   → npm run build
//       site=https://leah-kong.github.io  base=/Streamax-Knowledge-Base
//  2) 离线分发（双击即看）   → OFFLINE=1 npm run build
//       base=./  输出 category/truck.html
//  3) 自有服务器 / Cloudflare Pages（正式上线，推荐） → SITE_URL=https://kb.example.com BASE_PATH=/ npm run build
//       base=/   链接变为 /category/truck/，适配独立域名根路径
//     Cloudflare Pages 连 GitHub 仓库后：Build command = `npm run build`，Output dir = `dist`。
//     Cloudflare 构建时会注入 CF_PAGES=true 与 CF_PAGES_URL，下面自动据此判定，无需手填环境变量。
//     pagefind 检索索引由 postbuild 自动生成；文档/视频外链（Google Drive / YouTube）无需改代码。

// Cloudflare Pages 在构建环境中自动设置 CF_PAGES=true；据此自动切到根路径模式
const isCloudflare = process.env.CF_PAGES === 'true' || process.env.CF_PAGES === '1';
const offline = process.env.OFFLINE === '1';

// 正式站点地址与根路径；Cloudflare / 自有服务器用环境变量注入，无需改代码
const SITE =
  process.env.SITE_URL ||
  (isCloudflare ? (process.env.CF_PAGES_URL ?? 'https://example.pages.dev') : 'https://leah-kong.github.io');
const BASE = offline
  ? './'
  : process.env.BASE_PATH ?? (isCloudflare ? '/' : '/Streamax-Knowledge-Base');

export default defineConfig({
  site: SITE,
  base: BASE,
  build: {
    // 离线模式输出 category/truck.html 而非 category/truck/index.html，
    // 因为 file:// 协议不会自动补 index.html
    format: offline ? 'file' : 'directory',
  },
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
