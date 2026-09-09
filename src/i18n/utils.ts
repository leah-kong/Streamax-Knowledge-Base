import { ui, defaultLang } from './ui';

export type Lang = keyof typeof ui;

export function getLangFromUrl(url: URL): Lang {
  const segment = url.pathname.split('/')[1];
  return segment === 'en' ? 'en' : 'es';
}

export function useTranslations(lang: Lang) {
  return function t(key: string): string {
    const table = ui[lang] as Record<string, string>;
    const fallback = ui[defaultLang] as Record<string, string>;
    return table[key] ?? fallback[key] ?? key;
  };
}

// 离线模式（base 为 './'）下链接必须相对且带 .html，否则 file:// 打不开
const BASE: string = import.meta.env.BASE_URL ?? '/';
const OFFLINE = BASE === './';

// 西语为默认语言、不带前缀；英语统一加 /en 前缀
export function localizedPath(lang: Lang, path: string): string {
  const clean = path === '/' ? '' : path.startsWith('/') ? path : `/${path}`;
  let p = lang === 'en' ? `/en${clean}` : clean;
  if (p.endsWith('/')) p = p.slice(0, -1);
  if (p === '') p = '/index';
  return OFFLINE ? `.${p}.html` : p === '/index' ? '/' : `${p}/`;
}

// 生成另一侧语言的对应路径
export function switchLangPath(currentLang: Lang, pathname: string): string {
  const target: Lang = currentLang === 'es' ? 'en' : 'es';
  const normalized = pathname.replace(/\/+$/, '').replace(/\.html$/, '').replace(/^\/index$/, '');
  let p: string;
  if (target === 'en') {
    p = `/en${normalized}`;
  } else {
    p = normalized.replace(/^\/en(\/|$)/, '/');
  }
  if (p.endsWith('/')) p = p.slice(0, -1);
  return OFFLINE ? `.${p === '' ? '/index' : p}.html` : p === '' ? '/' : `${p}/`;
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
  value: { es?: string; en?: string } | undefined | null,
  lang: Lang
): string {
  if (!value) return '';
  return value[lang] ?? value.es ?? value.en ?? '';
}
