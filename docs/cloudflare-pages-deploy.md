# Despliegue en Cloudflare Pages

Guía para mover el sitio de GitHub Pages a **Cloudflare Pages** (CDN global, HTTPS
gratuito, despliegue automático desde GitHub). El código ya soporta este modo: basta
con construir con `SITE_URL` + `BASE_PATH=/` (modo 3 en `astro.config.mjs`).

> **Método activo en este repo:** el despliegue lo hace GitHub Actions con
> `.github/workflows/deploy-cloudflare.yml` (acción oficial `cloudflare/wrangler-action@v4`,
> comando `pages deploy dist --project-name=streamax-kb`). No hace falta "Connect to Git"
> en el panel de Cloudflare: el workflow se autentica con el API Token. Basta con añadir
> dos *repository secrets* (paso 0) y luego re-ejecutar el workflow o hacer `push` a `main`.
> (El antiguo `cloudflare/pages-action` ya no existe en GitHub y se reemplazó por este.)

## 0. Secrets de GitHub (obligatorio antes del primer despliegue)
En el repo → **Settings → Secrets and variables → Actions → New repository secret**, añade dos:
- `CLOUDFLARE_API_TOKEN` → token de API de Cloudflare (permiso: *Account → Cloudflare Pages → Edit*).
  ⚠️ Nunca se pega un token real en el chat; si se filtró, créalo de nuevo en
  dash.cloudflare.com → My Profile → API Tokens.
- `CLOUDFLARE_ACCOUNT_ID` → el "Account ID" de Cloudflare (~32 caracteres hex, se ve en la
  barra lateral derecha del panel; **NO** es tu correo de login).
Con eso el workflow ya puede autenticarse; no requiere conectar Git en el dashboard.
Tras añadirlos, ve a la pestaña **Actions** → el workflow "Deploy to Cloudflare Pages" →
**Re-run all jobs** (o simplemente haz `push` a `main`).

## Por qué Cloudflare Pages
- CDN global rápido (resuelve la lentitud de GitHub Pages en algunas regiones).
- HTTPS por defecto y cabeceras de seguridad — sin servidor, sin base de datos.
- Gratis para sitios estáticos. Despliegue automático en cada `git push` a `main`.
- `/admin` (Sveltia CMS) y `/assets/*` (logo, etc.) se sirven igual que en local.

## 1. Crear el proyecto en Cloudflare (paso a paso)

> Requisitos: una cuenta gratuita en Cloudflare (registrarse en cloudflare.com) y que el
> repo `leah-kong/Streamax-Knowledge-Base` sea accesible (es público, así que basta con
> autorizar a Cloudflare a leerlo).

1. Abrir **https://dash.cloudflare.com/** e iniciar sesión.
2. En el menú lateral izquierdo, pulsar **Workers & Pages**.
3. Arriba a la derecha, pulsar el botón **Create** (o **Create application**).
4. En la pestaña **Pages**, pulsar **Create a project** (o directamente **Connect to Git**).
5. Elegir la tarjeta **Connect to Git** (NO "Direct upload").
6. **Conectar GitHub**: aparece una ventana de GitHub. Si ya autorizaste Cloudflare antes,
   salta al paso 7. Si no:
   - Pulsar **Connect GitHub** → iniciar sesión en GitHub si hace falta.
   - GitHub pedirá autorizar a "Cloudflare Pages"; pulsar **Authorize Cloudflare Pages**.
   - (Opcional) elegir si dar acceso a todos los repos o solo a
     `Streamax-Knowledge-Base`; se recomienda "Only select repositories" → marcar el nuestro.
7. En **Select a repository**, buscar / hacer clic en **`Streamax-Knowledge-Base`**
   (debajo del usuario `leah-kong`).
8. Pulsar **Begin setup**.
9. Pantalla **Build settings** — rellenar exactamente:
   - **Project name**: `streamax-kb` (o el que quieras; define el subdominio `.pages.dev`).
   - **Production branch**: `main`.
   - **Framework preset**: dejar en **None** (lo ponemos manual para asegurar pagefind).
   - **Build command**: `npm run build`  ← importante: `run build`, no solo `astro build`,
     porque el `postbuild` de package.json genera el índice de búsqueda (pagefind).
   - **Build output directory**: `dist`
   - **Root directory**: dejar en `/` (raíz del repo).
   - **Node.js version**: `22` (en *Settings → Build & deployments → Build system* o vía
     `package.json` `engines`; Astro 5 lo necesita).
10. **Variables de entorno**: ninguna obligatoria. El `astro.config.mjs` ya detecta
    `CF_PAGES=true` y usa `BASE_PATH=/` + `SITE_URL=CF_PAGES_URL` solo. (Si más adelante
    usas dominio propio, aquí pondrías `SITE_URL=https://kb.tudominio.com`.)
11. Pulsar **Save and Deploy**. La primera compilación tarda ~1–2 min; se ve el log en vivo.

> El `postbuild` de `package.json` ejecuta `pagefind` sobre `dist/`, así que el buscador
> estático se genera solo en cada despliegue. No se necesita `wrangler.toml`.

## 2. Verificar
- Al terminar, Cloudflare muestra **Visit your site** con la URL
  `https://streamax-kb.pages.dev` (o el nombre que hayas puesto). Pulsarla.
- En la página: el logotipo Streamax arriba a la izquierda (cabecera de todas las páginas).
- Entrar a cualquier producto → pestaña **Videos**: los enlaces de YouTube se incrustan como
  reproductor; los manuales con `externalUrl` de Google Drive muestran el botón **Abrir**.
- Probar el buscador (lupa / barra de búsqueda): debe devolver resultados.
- (Opcional, desde terminal) `curl -I https://streamax-kb.pages.dev/assets/streamax-logo.png`
  → debe responder `200`.
- `/admin` → iniciar sesión con GitHub y crear/editar contenido; al guardar se hace
  `git commit` y Cloudflare re-despliega solo.

## 2b. Despliegues siguientes (automático)
Una vez creado, **cada `git push` a `main` re-despliega solo** (Cloudflare vigila el repo).
No hace falta volver al panel salvo para dominio propio o ajustes.

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
