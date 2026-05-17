# Static Deployment Guide for BringYourAI.net

BringYourAI.net is Michael Chambers' live resume and AI systems portfolio. The broader **Bring Your AI** concept is demonstrated by placing Aria on the resume as a portfolio/resume experience, not by wiring a live backend chat service in this repository.

This guide prepares the site for a static server deployment. GitHub remains the source of truth, and the server should publish a checked-out or exported copy of the static files only.

## Deployment Model

- **Site type:** static HTML/CSS assets.
- **Preferred server root:** `/srv/www/bringyourai.net`.
- **Source of truth:** GitHub repository `caosos/bringyourai.net`.
- **Runtime services:** none required by this repository.
- **Backend logic:** intentionally excluded.
- **Aria chat:** presentation/demo layer only; do not wire live chat from this deployment guide.
- **Private data:** do not place secrets, private notes, internal incident history, or unredacted credentials in the web root.

## Files Published

The static deployment should publish only public site content, such as:

- `index.html`
- `projects.html`
- `aria.html`
- `README.md` if intentionally public
- `docs/` if intentionally public
- static assets added later, such as `assets/`, `images/`, or `css/`

Deployment helper files such as `DEPLOYMENT.md`, `nginx/`, and `scripts/` may remain in the repository, but they do not need to be served publicly.

## Server Prerequisites

The server should have:

- A Linux host with shell access.
- `nginx` installed.
- `git` installed.
- DNS control for `bringyourai.net` and optional `www.bringyourai.net`.
- A TLS certificate provider such as Let's Encrypt/Certbot or another managed certificate process.

Example package installation on Ubuntu/Debian:

```bash
cd /srv/www
sudo apt update
sudo apt install -y nginx git
```

## Initial Static Deployment

Create the preferred web root and clone the GitHub repository into it:

```bash
cd /srv/www
sudo mkdir -p /srv/www/bringyourai.net
sudo chown -R "$USER":"$USER" /srv/www/bringyourai.net
git clone https://github.com/caosos/bringyourai.net.git /srv/www/bringyourai.net
```

If the directory already exists and is empty, clone directly into it. If it already contains a previous deployment, back it up or confirm it is safe to replace before continuing.

Set safe read permissions for nginx:

```bash
cd /srv/www/bringyourai.net
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
```

## Nginx Configuration

An example nginx static-site configuration is provided at:

- `nginx/bringyourai.net.conf.example`

Install it as a site configuration:

```bash
cd /srv/www/bringyourai.net
sudo cp nginx/bringyourai.net.conf.example /etc/nginx/sites-available/bringyourai.net
sudo ln -s /etc/nginx/sites-available/bringyourai.net /etc/nginx/sites-enabled/bringyourai.net
sudo nginx -t
sudo systemctl reload nginx
```

If the default nginx site conflicts with this domain or port, disable it:

```bash
cd /etc/nginx/sites-enabled
sudo rm -f default
sudo nginx -t
sudo systemctl reload nginx
```

## DNS Checklist

Before enabling HTTPS, confirm DNS points at the server:

- `A` record for `bringyourai.net` points to the public IPv4 address.
- Optional `AAAA` record for `bringyourai.net` points to the public IPv6 address.
- `A` record for `www.bringyourai.net` points to the public IPv4 address, or `CNAME` points to `bringyourai.net`.
- Optional `AAAA` record for `www.bringyourai.net` points to the public IPv6 address.
- No private IP addresses, internal hostnames, or hidden infrastructure names are published.
- DNS has propagated before requesting certificates.

Useful checks:

```bash
cd /srv/www/bringyourai.net
dig bringyourai.net A
dig www.bringyourai.net A
```

## HTTPS Checklist

Use your preferred certificate process. With Certbot on Ubuntu/Debian, a typical nginx flow is:

```bash
cd /srv/www/bringyourai.net
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d bringyourai.net -d www.bringyourai.net
sudo nginx -t
sudo systemctl reload nginx
```

After certificate issuance:

- Confirm `https://bringyourai.net` loads the live resume / AI systems portfolio.
- Confirm `https://www.bringyourai.net` either loads the same site or redirects to the canonical host.
- Confirm HTTP redirects to HTTPS if Certbot or the nginx configuration enables it.
- Confirm certificate renewal is active.

Renewal check:

```bash
cd /srv/www/bringyourai.net
sudo certbot renew --dry-run
```

## Updating the Live Site

Because GitHub is the source of truth, update the server by pulling the intended branch or tag from GitHub.

Basic update flow:

```bash
cd /srv/www/bringyourai.net
git fetch origin
git status
git pull --ff-only origin main
sudo nginx -t
sudo systemctl reload nginx
```

If using the optional helper script from this repository:

```bash
cd /srv/www/bringyourai.net
./scripts/deploy-static.sh
```

Before pulling updates, make sure there are no local-only changes on the server. Any site change should be committed to GitHub first.

## Rollback Steps

Roll back by checking out a known good commit from GitHub. Replace `<GOOD_COMMIT_SHA>` with a public commit hash from the repository history.

```bash
cd /srv/www/bringyourai.net
git fetch origin
git checkout <GOOD_COMMIT_SHA>
sudo nginx -t
sudo systemctl reload nginx
```

To return to the main branch later:

```bash
cd /srv/www/bringyourai.net
git checkout main
git pull --ff-only origin main
sudo nginx -t
sudo systemctl reload nginx
```

For a release-style workflow, prefer deploying signed or reviewed tags:

```bash
cd /srv/www/bringyourai.net
git fetch --tags origin
git checkout <RELEASE_TAG>
sudo nginx -t
sudo systemctl reload nginx
```

## Static-Site Safety Rules

- Do not add server-side application code to this deployment.
- Do not configure a private API endpoint for Aria from this repository.
- Do not commit `.env` files, API keys, credentials, private server IPs, or internal incident notes.
- Do not expose private/internal history in public pages or public deployment notes.
- Keep BringYourAI.net framed as Michael's live resume and AI systems portfolio.
- Keep the broader Bring Your AI concept framed as the idea demonstrated by putting Aria on the resume.

## Verification Checklist

After deployment or update:

```bash
cd /srv/www/bringyourai.net
curl -I http://bringyourai.net
curl -I https://bringyourai.net
curl -I https://bringyourai.net/projects.html
curl -I https://bringyourai.net/aria.html
```

Confirm manually in a browser:

- Homepage loads cleanly.
- Projects page loads cleanly.
- Aria page loads as a static portfolio/resume demonstration.
- Navigation links work.
- No private data appears in rendered pages.
- No backend endpoint is required for the public experience.
