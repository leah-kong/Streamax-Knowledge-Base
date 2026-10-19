import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// 双语文本：西语（墨西哥）为默认，英语为第二语言。
// 后台（Sveltia CMS）可能把双语字段保存成普通字符串，这里对象/字符串都接受，
// 由 translated() 统一取值 —— 避免非技术人员在后台改内容导致整站构建失败。
const i18nText = z.union([
  z.object({
    es: z.string().optional(),
    en: z.string().optional(),
  }),
  z.string(),
]);

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
    // 手动指定的关联产品（产品 id / slug 或 model 均可）；产品页只展示此处手动挂接的产品，
    // 不再自动同分类关联。清空即不显示任何关联产品，由编辑在 CMS 中手动添加。
    related: z.array(z.string()).optional(),
    // 内嵌资源（物理嵌套）：产品页 manual/firmware/video 的真源，站点直接从这里读取。
    // 不再依赖独立的 manual/firmware/video 集合。
    manuals: z
      .array(
        z.object({
          title: i18nText,
          docType: z.enum(['datasheet', 'user-guide', 'wiring-diagram', 'certification']),
          version: z.string().optional(),
          date: z.coerce.date(),
          fileEs: z.string().optional(),
          fileEn: z.string().optional(),
          externalUrl: z.string().optional(),
          summary: i18nText.optional(),
        })
      )
      .optional(),
    firmware: z
      .array(
        z.object({
          version: z.string(),
          date: z.coerce.date(),
          type: z.enum(['firmware', 'tool']).default('firmware'),
          fileSize: z.string().optional(),
          checksum: z.string().optional(),
          downloadUrl: z.string().optional(),
          releaseNotes: i18nText.optional(),
          mandatory: z.boolean().default(false),
        })
      )
      .optional(),
    videos: z
      .array(
        z.object({
          title: z.string(),
          date: z.coerce.date(),
          duration: z.string().optional(),
          url: z.string(),
          external: z.boolean().default(true),
          cover: z.string().optional(),
          summary: z.string().optional(),
        })
      )
      .optional(),
  }),
});

// 注：manual / firmware / video 已物理嵌套进每个产品的内嵌列表（见 products.manuals / .firmware / .videos），
// 不再作为独立集合存在。站点资源全部从产品内嵌列表读取，独立目录 src/content/{manual,firmware,video} 已删除。

export const collections = { categories, products };
