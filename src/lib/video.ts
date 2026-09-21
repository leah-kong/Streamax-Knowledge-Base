// 把 YouTube 观看/短链/you.be/embed 链接，以及直接粘贴的 <iframe> 嵌入代码，
// 统一转成可嵌入的 embed 地址；非 YouTube 返回 null。
// 集中放在这里，产品页、首页、分类页共用同一套转换逻辑。
export function youtubeEmbed(url: string): string | null {
  if (!url) return null;
  // 兼容直接粘贴 YouTube 的 <iframe> 嵌入代码：先抽出 src 属性
  let input = url;
  if (/<iframe/i.test(input)) {
    const src = input.match(/src=["']([^"']+)["']/i);
    if (src) input = src[1];
  }
  const m = input.match(
    /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{11})/
  );
  return m ? `https://www.youtube.com/embed/${m[1]}` : null;
}

// 返回给用户点击外链的“观看页”地址（watch?v=），比 embed 更友好；
// 若不是 YouTube 链接则返回 null，调用方回退到原始 url。
export function youtubeWatch(url: string): string | null {
  const emb = youtubeEmbed(url);
  return emb ? emb.replace('/embed/', '/watch?v=') : null;
}
