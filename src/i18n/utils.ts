import { ui, defaultLang } from './ui';

export type Lang = keyof typeof ui;

// 站点 base：
//   '/'                          → 部署在域名根目录
//   '/Streamax-Knowledge-Base/'  → GitHub Pages 项目页
//   './'                         → 离线 file:// 分发
const BASE: string = import.meta.env.BASE_URL ?? '/';
const OFFLINE = BASE === './';

// 去掉路径里的 base 前缀，得到"站点内相对路径"（如 /en/category/truck/）
function stripBase(p: string): string {
  if (OFFLINE || BASE === '/') return p;
  const b = BASE.replace(/\/+$/, '');
  if (p === b || p === `${b}/`) return '/';
  if (p.startsWith(`${b}/`)) return p.slice(b.length);
  return p;
}

// 给站内相对路径补上 base 前缀
function withBase(p: string): string {
  if (OFFLINE || BASE === '/') return p;
  return BASE.replace(/\/+$/, '') + (p.startsWith('/') ? p : `/${p}`);
}

// 站内资源（如 /docs/xxx.pdf）也要带 base，否则会打到域名根目录导致 404
export function siteAsset(url: string): string {
  if (!url) return url;
  // 外链、mailto、锚点、相对路径保持原样
  if (/^(https?:|mailto:|tel:|data:|#)/.test(url) || url.startsWith('./') || url.startsWith('../')) {
    return url;
  }
  return withBase(url);
}

export function getLangFromUrl(url: URL): Lang {
  const segment = stripBase(url.pathname).split('/')[1];
  return segment === 'en' ? 'en' : 'es';
}

export function useTranslations(lang: Lang) {
  return function t(key: string): string {
    const table = ui[lang] as Record<string, string>;
    const fallback = ui[defaultLang] as Record<string, string>;
    return table[key] ?? fallback[key] ?? key;
  };
}

// 西语为默认语言、不带前缀；英语统一加 /en 前缀
export function localizedPath(lang: Lang, path: string): string {
  const clean = path === '/' ? '' : path.startsWith('/') ? path : `/${path}`;
  let p = lang === 'en' ? `/en${clean}` : clean;
  if (p.endsWith('/')) p = p.slice(0, -1);
  if (OFFLINE) return `.${p === '' ? '/index' : p}.html`;
  // 首页必须带尾斜杠，否则拼锚点会变成 /base#xxx
  if (p === '') return BASE.endsWith('/') ? BASE : `${BASE}/`;
  return `${withBase(p)}/`;
}

// 生成另一侧语言的对应路径
export function switchLangPath(currentLang: Lang, pathname: string): string {
  const target: Lang = currentLang === 'es' ? 'en' : 'es';
  const normalized = stripBase(pathname)
    .replace(/\/+$/, '')
    .replace(/\.html$/, '')
    .replace(/^\/index$/, '');
  let p: string;
  if (target === 'en') {
    p = `/en${normalized}`;
  } else {
    p = normalized.replace(/^\/en(\/|$)/, '/');
  }
  if (p.endsWith('/')) p = p.slice(0, -1);
  if (OFFLINE) return `.${p === '' ? '/index' : p}.html`;
  if (p === '' || p === '/') return BASE.endsWith('/') ? BASE : `${BASE}/`;
  return `${withBase(p)}/`;
}

export function formatDate(date: Date, lang: Lang): string {
  return new Intl.DateTimeFormat(lang === 'es' ? 'es-MX' : 'en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(date);
}

// 取双语字段在当前语言下的值
export function translated(
  value: { es?: string; en?: string } | string | undefined | null,
  lang: Lang
): string {
  if (!value) return '';
  // 后台可能把双语字段存成普通字符串，此时两种语言都显示它
  if (typeof value === 'string') return value;
  return value[lang] ?? value.es ?? value.en ?? '';
}
