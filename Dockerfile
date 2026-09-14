# ---- 构建阶段：Node 构建静态站 + Pagefind 索引 ----
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json ./
RUN npm install --no-audit --no-fund

COPY . .

# 正式上线时传入：docker build --build-arg SITE_URL=https://kb.example.com --build-arg BASE_PATH=/
ARG SITE_URL=https://example.com
ARG BASE_PATH=/
ENV SITE_URL=$SITE_URL
ENV BASE_PATH=$BASE_PATH

RUN npx astro build && npx pagefind --site dist --output-subdir search

# ---- 运行阶段：Nginx 托管静态文件 ----
FROM nginx:alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
