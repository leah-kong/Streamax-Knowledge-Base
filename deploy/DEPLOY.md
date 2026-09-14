# 私有服务器部署手册

从 GitHub Pages 迁移到自有服务器（海外 / 免备案）的完整步骤。

## 0. 三种构建模式

| 模式 | 命令 | base | 用途 |
| --- | --- | --- | --- |
| GitHub Pages（默认） | `npm run build` | `/Streamax-Knowledge-Base` | 现在的线上站 |
| 离线分发 | `OFFLINE=1 npm run build` | `./` | 双击即看的 zip |
| 自有服务器 | `SITE_URL=https://kb.example.com BASE_PATH=/ npm run build` | `/` | 正式上线 |

关键：正式域名下 `base` 必须是 `/`，否则全站内链会 404。已通过环境变量驱动，无需改代码。

## 1. 服务器准备

1. 购买服务器（海外/香港，免备案），系统建议 Ubuntu 22.04。
2. 安全组放行 `22 / 80 / 443`。
3. 创建部署用户并配置 SSH 密钥登录，关闭密码登录：

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo mkdir -p /home/deploy/.ssh && sudo chmod 700 /home/deploy/.ssh
# 把本机公钥写入 /home/deploy/.ssh/authorized_keys，权限 600
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

4. 安装 Docker 与 rsync：

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo apt-get update && sudo apt-get install -y rsync
```

## 2. 方式 A：服务器上用 Docker 构建（最简单）

```bash
git clone <你的仓库地址> kb && cd kb
cp .env.example .env      # 改成正式域名
docker compose up -d --build
```

访问 `http://服务器IP/` 验证。更新时：

```bash
git pull && docker compose up -d --build
```

## 3. 方式 B：本地/CI 构建后 rsync 推送（推荐）

本地验证：

```bash
SITE_URL=https://kb.example.com BASE_PATH=/ npm run build
rsync -az --delete dist/ deploy@服务器IP:/var/www/kb/
```

或用 GitHub Actions（`.github/workflows/deploy-server.yml`，手动触发）。需在仓库
Settings → Secrets and variables → Actions 配置：

| Secret | 说明 |
| --- | --- |
| `DEPLOY_SSH_KEY` | 部署用私钥 |
| `DEPLOY_HOST` | 服务器 IP 或域名 |
| `DEPLOY_USER` | 部署用户（如 deploy） |
| `DEPLOY_PATH` | 目标目录（如 /var/www/kb） |

## 4. 方式 C：宿主 Nginx 直接托管（不用 Docker）

把 `deploy/nginx.conf` 拷到 `/etc/nginx/conf.d/kb.conf`，修改 `root` 指向 `/var/www/kb`，
然后 `sudo nginx -t && sudo systemctl reload nginx`。

## 5. HTTPS

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d kb.example.com
```

证书自动续期；也可用云厂商免费证书。

## 6. 大文件（固件 / 视频）

不要把大文件放进 Git。方案：
- 对象存储（COS / OSS / S3）+ CDN，页面里放直链或签名 URL；
- 或放在服务器 `/var/www/kb/downloads/`，Nginx 已配置 `Range` 支持断点续传。

## 7. 上线检查清单

- [ ] 全站内链自测（重点查 base 改 `/` 后的链接）
- [ ] 自定义 404 生效
- [ ] `robots.txt` 可访问；补 `sitemap` 后提交搜索引擎
- [ ] HTTPS 跳转 + HSTS
- [ ] 缓存策略：`/_astro/` 长缓存、HTML 不缓存
- [ ] Uptime 探活、Nginx 访问日志、访问统计
- [ ] 服务器配置与 Nginx 配置纳入版本管理；内容在 Git；对象存储开版本控制
