# Deployment Guide for BringYourAI.net

BringYourAI.net is Michael Chambers' live resume and AI systems portfolio. The repository can still be served as static HTML for preview, but the live Aria prototype requires a small Node.js backend so the browser never receives the OpenAI API key.

## Deployment Model

- **Site type:** static HTML/CSS plus a minimal Node.js API endpoint.
- **Preferred server root:** `/srv/www/bringyourai.net`.
- **Source of truth:** GitHub repository `caosos/bringyourai.net`.
- **Backend endpoint:** `POST /api/aria-chat`.
- **Runtime secrets:** `OPENAI_API_KEY` must exist only in the server environment.
- **No persistent services:** no database, auth service, analytics, visitor memory, admin panel, or autonomous action system is required for this prototype.
- **Abuse protection:** `/api/aria-chat` has a simple in-memory per-IP rate limit for prototype abuse control. It is not persistent visitor memory.
- **Public serving scope:** the Node server serves only `index.html`, `aria.html`, `projects.html`, and files placed under public asset directories such as `assets/`, `images/`, `css/`, or `js/`. Repository docs, deployment notes, source modules, dotfiles, and private/config-style files are not intended website content.
- **Private data:** do not place secrets, private notes, internal incident history, private conversation logs, or unredacted credentials in the web root.

## Runtime Configuration

Required:

```bash
cd /srv/www/bringyourai.net
export OPENAI_API_KEY="sk-your-openai-api-key"
```

Optional:

```bash
cd /srv/www/bringyourai.net
export ARIA_OPENAI_MODEL="gpt-4.1-mini"
export PORT=3000
```

Use a server-side environment manager such as systemd environment files, a deployment secret store, or shell exports. Never hardcode secrets in HTML, JavaScript, Markdown, or committed files.

## Local Safe Run

```bash
cd /srv/www/bringyourai.net
npm run check
set -a
source .env
set +a
npm start
```

Then open:

```text
http://localhost:3000/aria.html
```

To verify the endpoint shape without storing data:

```bash
cd /srv/www/bringyourai.net
curl -sS -X POST http://localhost:3000/api/aria-chat \
  -H 'content-type: application/json' \
  -d '{"message":"What is CAOS?"}'
```

## Server Prerequisites

The server should have:

- Linux host with shell access.
- Node.js 18 or newer.
- `nginx` installed if reverse proxying.
- `git` installed.
- DNS control for `bringyourai.net` and optional `www.bringyourai.net`.
- TLS certificate provider such as Let's Encrypt/Certbot or another managed certificate process.

Example package installation on Ubuntu/Debian:

```bash
cd /srv/www
sudo apt update
sudo apt install -y nginx git nodejs npm
```

## Initial Deployment

```bash
cd /srv/www
sudo mkdir -p /srv/www/bringyourai.net
sudo chown -R "$USER":"$USER" /srv/www/bringyourai.net
git clone https://github.com/caosos/bringyourai.net.git /srv/www/bringyourai.net
cd /srv/www/bringyourai.net
npm run check
```

Set safe read permissions for nginx and keep environment files private:

```bash
cd /srv/www/bringyourai.net
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
chmod 600 .env 2>/dev/null || true
```

## Nginx Reverse Proxy

For the Aria backend prototype, nginx should proxy traffic to the Node process instead of only serving static files. The example static config may need to be adapted so `/api/aria-chat` reaches the Node server.

Minimal proxy location example:

```nginx
location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

After changing nginx:

```bash
cd /srv/www/bringyourai.net
sudo nginx -t
sudo systemctl reload nginx
```

## Updating the Live Site

```bash
cd /srv/www/bringyourai.net
git fetch origin
git status
git pull --ff-only origin main
npm run check
sudo systemctl restart bringyourai  # if a systemd service is used
sudo nginx -t
sudo systemctl reload nginx
```

Before pulling updates, make sure there are no local-only changes on the server. Any site change should be committed to GitHub first.

## Prototype Safety Rules

- Do not expose `OPENAI_API_KEY` or any model credentials to the browser.
- Do not add private memory, hidden visitor tracking, analytics, auth, admin views, support logs, raw conversation history, or database persistence without a separate explicit design pass.
- Do not retrieve from private conversations or unpublished operational notes.
- Keep Aria's answers concise, public-safe, and framed around Michael's resume / AI systems portfolio.
