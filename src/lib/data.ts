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

export async function getManualByProduct(productId: string) {
  const all = await getCollection('manual');
  return all
    .filter((m) => m.data.products.includes(productId))
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

export async function getFirmwareByProduct(productId: string) {
  const all = await getCollection('firmware');
  return all
    .filter((f) => f.data.products.includes(productId))
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

export async function getVideoByProduct(productId: string) {
  const all = await getCollection('video');
  return all
    .filter((v) => v.data.products.includes(productId))
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
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
