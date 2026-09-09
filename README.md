# Base de conocimientos / Knowledge base

静态知识库站点，架构参考产品支持中心。**无登录模块**，固件与文档对所有人公开下载。

- 框架：Astro（静态输出）
- 语言：西语（墨西哥）为默认、根路径无前缀；英语在 `/en/` 下
- 后台：Sveltia CMS，挂在 `/admin`，内容写回 Git
- 二进制资产：GitHub Releases（不进 Git 仓库）
- 搜索：Pagefind（构建后生成索引，零后端）

## 目录结构

```
src/
  content/
    categories/   分类（level 1/2/3，用 parent 串成树）
    products/     产品，通过 category / subcategory / platform 归属分类
    manual/       手册与文档（datasheet / qsg / deployment / user-guide ...）
    firmware/     固件包与工具（版本号、校验码、更新日志、下载直链）
    video/        视频（外链或本地文件）
  components/     HomeView / CategoryView / ProductView
  layouts/        BaseLayout（导航、搜索、语言切换、页脚）
  i18n/           语言字典与工具函数
  pages/
    index.astro           西语首页
    en/index.astro        英语首页
    category/[id]         分类页
    product/[id]          产品详情页
    search                搜索结果页
public/
  admin/          Sveltia CMS（index.html + config.yml）
  docs/           放 PDF 手册（小文件；大文件建议放 Releases）
```

## 替换成你自己的产品目录

`src/content/` 下现在全是**占位示例**（车载录像机 / 摄像头 / 显示器），需要整体替换：

1. 编辑 `src/content/categories/*.yml`：一级分类 `level: 1`，二级 `level: 2` 且 `parent: <一级 id>`，三级 `level: 3`
2. 编辑 `src/content/products/*.yml`：`model` 是型号，`category` / `subcategory` / `platform` 填对应分类的文件名（不含 .yml）
3. 编辑 `src/content/manual|firmware|video/*.yml`：`products` 数组里填产品的文件名 id

文件名即 id，例如 `x5-ai.yml` 的 id 是 `x5-ai`。

## 本地开发

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # 输出到 dist/，并生成 Pagefind 索引
```

## 部署到 GitHub Pages

1. 把本目录推到 GitHub 仓库
2. 修改 `astro.config.mjs` 的 `site`：
   - 仓库名 `<user>.github.io` → `site: 'https://<user>.github.io'`, `base: '/'`
   - 其他仓库名 → `site: 'https://<user>.github.io'`, `base: '/<仓库名>'`
3. 修改 `public/admin/config.yml` 的 `repo: <owner>/<仓库名>`
4. 仓库 Settings → Pages → Source 选 **GitHub Actions**
5. 推到 `main` 分支，Actions 自动构建发布

## 后台使用

访问 `https://<你的域名>/admin`，用 GitHub 账号登录即可编辑内容。保存后 Sveltia 会提交到仓库，Actions 自动重新构建，约 1–2 分钟后线上生效。

> 编辑者的 GitHub 登录只用于后台，站点前台仍然完全匿名、无登录入口。

## 上传固件与视频

不要把大文件提交进 Git。推荐做法：

1. 在 GitHub 仓库创建 Release（tag 例如 `fw-x5-ai-2.4.0`），把固件包作为 asset 上传
2. 复制 asset 的下载直链
3. 在后台 Firmware 条目里把链接填进 `downloadUrl`

视频同理，或用 YouTube / Vimeo 外链填进 `url` 并把 `external` 设为 true。
