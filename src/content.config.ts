import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// 双语文本：西语（墨西哥）为默认，英语为第二语言
const i18nText = z.object({
  es: z.string(),
  en: z.string(),
});

// 一级 / 二级 / 三级分类
const categories = defineCollection({
  loader: glob({ pattern: '**/*.yml', base: './src/content/categories' }),
  schema: z.object({
    name: i18nText,
    level: z.union([z.literal(1), z.literal(2), z.literal(3)]),
    parent: z.string().optional(),
    order: z.number().default(99),
    summary: i18nText.optional(),
    icon: z.string().optional(),
  }),
});

// 产品：挂在三级分类下
const products = defineCollection({
  loader: glob({ pattern: '**/*.yml', base: './src/content/products' }),
  schema: z.object({
    model: z.string(),
    name: i18nText,
    series: i18nText.optional(),
    category: z.string(),
    subcategory: z.string().optional(),
    platform: z.string().optional(),
    image: z.string().optional(),
    order: z.number().default(99),
    eol: z.boolean().default(false),
  }),
});

// manual：产品手册、指南、数据表等
const manual = defineCollection({
  loader: glob({ pattern: '**/*.yml', base: './src/content/manual' }),
  schema: z.object({
    title: i18nText,
    // 手册清单：Datasheet / User Guide / Wiring Diagram / Certification
    // Firmware 与 Video 走独立集合，不在这里
    docType: z.enum(['datasheet', 'user-guide', 'wiring-diagram', 'certification']),
    products: z.array(z.string()),
    version: z.string().optional(),
    date: z.coerce.date(),
    fileEs: z.string().optional(),
    fileEn: z.string().optional(),
    externalUrl: z.string().optional(),
    summary: i18nText.optional(),
  }),
});

// firmware：固件包与工具，文件托管在 GitHub Releases
const firmware = defineCollection({
  loader: glob({ pattern: '**/*.yml', base: './src/content/firmware' }),
  schema: z.object({
    version: z.string(),
    products: z.array(z.string()),
    date: z.coerce.date(),
    releaseNotes: i18nText.optional(),
    fileSize: z.string().optional(),
    checksum: z.string().optional(),
    downloadUrl: z.string(),
    mandatory: z.boolean().default(false),
    type: z.enum(['firmware', 'tool']).default('firmware'),
  }),
});

// video：视频教程，本地 mp4 或外部链接
const video = defineCollection({
  loader: glob({ pattern: '**/*.yml', base: './src/content/video' }),
  schema: z.object({
    title: i18nText,
    products: z.array(z.string()),
    date: z.coerce.date(),
    duration: z.string().optional(),
    cover: z.string().optional(),
    url: z.string(),
    external: z.boolean().default(true),
    summary: i18nText.optional(),
  }),
});

export const collections = { categories, products, manual, firmware, video };
