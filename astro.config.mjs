import { defineConfig } from 'astro/config';

// TODO: 部署到 GitHub Pages 后，把 site 改成你的仓库地址
// 若仓库名为 my-kb，则 site: 'https://<用户名>.github.io', base: '/my-kb'
// 若使用自定义域名且仓库名为 <用户名>.github.io，则 base: '/'
// 两种构建模式：
//  1) 部署到 GitHub Pages   → npm run build                  base '/'，链接 /category/truck/
//  2) 离线分发（双击即看）  → OFFLINE=1 npm run build        base './'，链接 ./category/truck.html
const offline = process.env.OFFLINE === '1';

export default defineConfig({
  site: 'https://leah-kong.github.io',
  base: offline ? './' : '/Streamax-Knowledge-Base',
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
