#!/usr/bin/env bash
set -euo pipefail

SITE_ROOT="${SITE_ROOT:-/srv/www/bringyourai.net}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

cd "$SITE_ROOT"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Refusing to deploy: local changes exist in $SITE_ROOT." >&2
  echo "Commit changes to GitHub first, or reset the server checkout to a known public commit." >&2
  exit 1
fi

git fetch "$REMOTE"
git pull --ff-only "$REMOTE" "$BRANCH"

if command -v nginx >/dev/null 2>&1; then
  sudo nginx -t
  sudo systemctl reload nginx
else
  echo "nginx not found; pulled static site only." >&2
fi
