import { defineConfig } from 'astro/config';

// 三种构建模式，全部由环境变量驱动；不传变量时保持 GitHub Pages 现状（不影响线上站点）：
//  1) GitHub Pages（默认）   → npm run build
//       site=https://leah-kong.github.io  base=/Streamax-Knowledge-Base
//  2) 离线分发（双击即看）   → OFFLINE=1 npm run build
//       base=./  输出 category/truck.html
//  3) 自有服务器（正式上线） → SITE_URL=https://kb.example.com BASE_PATH=/ npm run build
//       base=/   链接变为 /category/truck/，适配独立域名根路径
const offline = process.env.OFFLINE === '1';

// 正式站点地址与根路径；服务器上线时用环境变量注入，无需改代码
const SITE = process.env.SITE_URL || 'https://leah-kong.github.io';
const BASE = offline ? './' : (process.env.BASE_PATH ?? '/Streamax-Knowledge-Base');

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
