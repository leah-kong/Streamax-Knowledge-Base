import { getCollection, getEntry, type CollectionEntry } from 'astro:content';

// 内嵌资源条目形状（与 products 集合 schema 中的 manuals/firmware/videos 对应）
export interface ManualItem {
  title: any;
  docType: 'datasheet' | 'user-guide' | 'wiring-diagram' | 'certification';
  version?: string;
  date: Date;
  fileEs?: string;
  fileEn?: string;
  externalUrl?: string;
  summary?: any;
}
export interface FirmwareItem {
  version: string;
  date: Date;
  type?: 'firmware' | 'tool';
  fileSize?: string;
  checksum?: string;
  downloadUrl?: string;
  releaseNotes?: any;
  mandatory?: boolean;
}
export interface VideoItem {
  title: string;
  date: Date;
  duration?: string;
  url: string;
  external?: boolean;
  cover?: string;
  summary?: string;
}
// 前端组件统一消费 { data: T } 形状，因此组件代码无需改动
export interface ResourceEntry<T> {
  data: T;
}
export type VideoEntry = ResourceEntry<VideoItem>;

function embed<T>(items?: T[]): ResourceEntry<T>[] {
  return (items ?? []).map((item) => ({ data: item }));
}

export async function getCategoriesByLevel(level: 1 | 2 | 3, parent?: string) {
  const all = await getCollection('categories');
  return all
    .filter((c) => c.data.level === level && (parent ? c.data.parent === parent : true))
    .sort((a, b) => a.data.order - b.data.order);
}

export async function getCategory(id: string) {
  return getEntry('categories', id);
}

export async function getProducts() {
  const all = await getCollection('products');
  return all.sort((a, b) => a.data.model.localeCompare(b.data.model));
}

export async function getProductsByCategory(categoryId: string) {
  const all = await getProducts();
  return all.filter((p) => p.data.category === categoryId);
}

export async function getProductsBySubcategory(categoryId: string, subcategoryId: string) {
  return (await getProductsByCategory(categoryId)).filter(
    (p) => p.data.subcategory === subcategoryId
  );
}

export async function getProductsByPlatform(categoryId: string, platformId: string) {
  return (await getProductsByCategory(categoryId)).filter(
    (p) => p.data.platform === platformId
  );
}

// 资源已物理嵌套进每个产品（products.manuals / .firmware / .videos），
// 站点只从产品内嵌列表读取，不再依赖独立的 manual/firmware/video 集合。
export async function getManualByProduct(productId: string): Promise<ResourceEntry<ManualItem>[]> {
  const product = await getEntry('products', productId);
  return embed(product?.data.manuals as ManualItem[] | undefined);
}

export async function getFirmwareByProduct(productId: string): Promise<ResourceEntry<FirmwareItem>[]> {
  const product = await getEntry('products', productId);
  return embed(product?.data.firmware as FirmwareItem[] | undefined);
}

export async function getVideoByProduct(productId: string): Promise<ResourceEntry<VideoItem>[]> {
  const product = await getEntry('products', productId);
  return embed(product?.data.videos as VideoItem[] | undefined);
}

async function allManuals(): Promise<ResourceEntry<ManualItem>[]> {
  const products = await getCollection('products');
  return products.flatMap((p) => embed(p.data.manuals as ManualItem[] | undefined));
}
async function allFirmware(): Promise<ResourceEntry<FirmwareItem>[]> {
  const products = await getCollection('products');
  return products.flatMap((p) => embed(p.data.firmware as FirmwareItem[] | undefined));
}
async function allVideos(): Promise<ResourceEntry<VideoItem>[]> {
  const products = await getCollection('products');
  return products.flatMap((p) => embed(p.data.videos as VideoItem[] | undefined));
}

export async function getRecentManual(limit = 6): Promise<ResourceEntry<ManualItem>[]> {
  return (await allManuals())
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .slice(0, limit);
}
export async function getRecentFirmware(limit = 5): Promise<ResourceEntry<FirmwareItem>[]> {
  return (await allFirmware())
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .slice(0, limit);
}
export async function getRecentVideo(limit = 4): Promise<ResourceEntry<VideoItem>[]> {
  return (await allVideos())
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .slice(0, limit);
}

// 给 VideosView：聚合所有产品内嵌视频，按 (title|url) 去重，
// 回链其关联产品与一级分类（用于筛选）。
export interface VideoViewItem {
  video: ResourceEntry<VideoItem>;
  products: CollectionEntry<'products'>[];
  catIds: string[];
}
export async function getAllVideos(): Promise<VideoViewItem[]> {
  const products = await getCollection('products');
  const bySig = new Map<string, VideoViewItem>();
  for (const p of products) {
    const vids = (p.data.videos as VideoItem[] | undefined) ?? [];
    for (const v of vids) {
      const sig = `${v.title} ${v.url}`;
      let item = bySig.get(sig);
      if (!item) {
        item = { video: { data: v }, products: [], catIds: [] };
        bySig.set(sig, item);
      }
      if (!item.products.some((x) => x.id === p.id)) {
        item.products.push(p);
        const cat = p.data.category;
        if (cat && !item.catIds.includes(cat)) item.catIds.push(cat);
      }
    }
  }
  return [...bySig.values()].sort(
    (a, b) => b.video.data.date.valueOf() - a.video.data.date.valueOf()
  );
}

export const DOC_TYPES = [
  'datasheet',
  'qsg',
  'deployment',
  'user-guide',
  'admin-guide',
  'compatibility',
  'white-paper',
  'api',
  'other',
] as const;
