import { getCollection, getEntry } from 'astro:content';

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

// 资源（manual/firmware/video）通过 products 字段关联产品。
// 该字段可能存 slug（如 trucking-ds100）或 model（如 DS100）：
//   - 仓库里手写的条目多用 slug；
//   - /admin 的 relation 控件配置 value_field: model，存的是 model。
// 这里两种都兼容，避免 CMS 用 model 存储时资源不显示在产品页。
async function getResourcesByProduct<T extends { data: { products: string[]; date: Date } }>(
  items: T[],
  productId: string
): Promise<T[]> {
  const product = await getEntry('products', productId);
  const keys = new Set<string>([productId]);
  if (product) keys.add(product.data.model);
  return items
    .filter((it) => it.data.products.some((p) => keys.has(p)))
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

export async function getManualByProduct(productId: string) {
  return getResourcesByProduct(await getCollection('manual'), productId);
}

export async function getFirmwareByProduct(productId: string) {
  return getResourcesByProduct(await getCollection('firmware'), productId);
}

export async function getVideoByProduct(productId: string) {
  return getResourcesByProduct(await getCollection('video'), productId);
}

export async function getRecentManual(limit = 6) {
  const all = await getCollection('manual');
  return all
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .slice(0, limit);
}

export async function getRecentFirmware(limit = 5) {
  const all = await getCollection('firmware');
  return all
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .slice(0, limit);
}

export async function getRecentVideo(limit = 4) {
  const all = await getCollection('video');
  return all
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .slice(0, limit);
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
