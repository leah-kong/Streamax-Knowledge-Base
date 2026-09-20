# Despliegue en Cloudflare Pages

Guía para mover el sitio de GitHub Pages a **Cloudflare Pages** (CDN global, HTTPS
gratuito, despliegue automático desde GitHub). El código ya soporta este modo: basta
con construir con `SITE_URL` + `BASE_PATH=/` (modo 3 en `astro.config.mjs`).

## Por qué Cloudflare Pages
- CDN global rápido (resuelve la lentitud de GitHub Pages en algunas regiones).
- HTTPS por defecto y cabeceras de seguridad — sin servidor, sin base de datos.
- Gratis para sitios estáticos. Despliegue automático en cada `git push` a `main`.
- `/admin` (Sveltia CMS) y `/assets/*` (logo, etc.) se sirven igual que en local.

## 1. Crear el proyecto en Cloudflare
1. Ir a https://dash.cloudflare.com/ → **Workers & Pages** → **Create** → **Pages**.
2. Elegir **Connect to Git** → autorizar GitHub → seleccionar `leah-kong/Streamax-Knowledge-Base`.
3. Configuración de build:
   - **Framework preset**: `Astro` (o dejar en *None* y poner los comandos manuales).
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Node.js version**: 22 (en *Settings → Build & deployments → Build system* o vía `package.json` `engines`).
4. **Variables de entorno** (en *Settings → Environment variables*, para todas las ramas):
   - `SITE_URL` = `https://<tu-proyecto>.pages.dev` (o tu dominio propio, ver paso 3)
   - `BASE_PATH` = `/`
5. Guardar y **Save and Deploy**. La primera compilación tarda ~1–2 min.

> El `postbuild` de `package.json` ejecuta `pagefind` sobre `dist/`, así que el buscador
> estático se genera solo en cada despliegue. No se necesita `wrangler.toml`.

## 2. Verificar
- Abrir la URL `https://<tu-proyecto>.pages.dev`.
- `curl -I https://<...>/assets/streamax-logo.png` → `200`.
- Entrar a un producto → pestaña **Videos**: los enlaces de YouTube se incrustan como
  reproductor; los manuales con `externalUrl` de Google Drive muestran el botón **Abrir**.
- `/admin` → iniciar sesión con GitHub y crear/editar contenido; al guardar se hace
  `git commit` y Cloudflare re-despliega solo.

## 3. Dominio propio (opcional)
1. En el proyecto Pages → **Custom domains** → añadir `kb.tudominio.com`.
2. Cloudflare da los registros DNS/NS; al activarlo, el `SITE_URL` se toma solo de
   `CF_PAGES_URL` (o se sobreescribe con la variable `SITE_URL` en *Settings →
   Environment variables*). `BASE_PATH` siempre es `/` en Cloudflare.
3. No hace falta tocar `astro.config.mjs`: el build detecta `CF_PAGES=true` automáticamente.

## 4. Desactivar GitHub Pages (opcional)
Si antes usabas GitHub Pages, puedes apagarlo en el repo → *Settings → Pages* (elegir
*Deploy from a branch* → None) para no tener dos sitios. El workflow `.github/workflows/deploy.yml`
puede quedar o eliminarse; no afecta a Cloudflare, que lee el repo directamente.

## 5. El logo de la empresa ya está en el sitio
El logotipo Streamax (`public/assets/streamax-logo.png`) ya está en la cabecera de **todas**
las páginas (esquina superior izquierda), añadido en el commit `c6f3df1`. Como Cloudflare
construye la misma rama `main`, el logo aparece solo, sin pasos extra. Verificación rápida
tras el despliegue:

```bash
curl -I https://<tu-proyecto>.pages.dev/assets/streamax-logo.png   # -> 200
```

Si se quisiera el logo también en el pie de página o como favicon, se añade en
`src/layouts/BaseLayout.astro` (mismo archivo de imagen).

## 6. Construcción local (mismo resultado)
```bash
SITE_URL=https://<tu-proyecto>.pages.dev BASE_PATH=/ npm run build
# dist/ listo para previsualizar con: npx serve dist
```
