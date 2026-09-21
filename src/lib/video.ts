// 把 YouTube 观看/短链/you.be 链接转成可嵌入的 embed 地址；非 YouTube 返回 null。
// 集中放在这里，产品页与首页共用同一套转换逻辑。
export function youtubeEmbed(url: string): string | null {
  if (!url) return null;
  const m = url.match(
    /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{11})/
  );
  return m ? `https://www.youtube.com/embed/${m[1]}` : null;
}
