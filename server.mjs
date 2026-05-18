import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { handleAriaChat } from './src/aria/handler.mjs';

const root = fileURLToPath(new URL('.', import.meta.url));
const port = Number(process.env.PORT || 3000);
const publicPages = new Set(['index.html', 'aria.html', 'projects.html']);
const publicAssetRoots = new Set(['assets', 'images', 'css', 'js']);

const mimeTypes = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.svg', 'image/svg+xml'],
  ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'],
  ['.jpeg', 'image/jpeg'],
  ['.webp', 'image/webp'],
  ['.gif', 'image/gif'],
  ['.ico', 'image/x-icon'],
  ['.woff', 'font/woff'],
  ['.woff2', 'font/woff2']
]);

function getClientIp(req) {
  const forwardedFor = req.headers['x-forwarded-for'];
  if (typeof forwardedFor === 'string' && forwardedFor.trim()) {
    return forwardedFor.split(',')[0].trim();
  }

  return req.socket.remoteAddress || 'unknown';
}

function decodePathname(pathname) {
  try {
    return decodeURIComponent(pathname);
  } catch {
    return null;
  }
}

function isPublicStaticPath(relativePath, segments) {
  if (publicPages.has(relativePath)) return true;
  return segments.length > 1 && publicAssetRoots.has(segments[0]);
}

function resolveStaticPath(pathname) {
  const decodedPath = decodePathname(pathname);
  if (!decodedPath) return null;

  const cleanPath = normalize(decodedPath).replace(/^([/\\])+/, '');
  const relativePath = cleanPath === '' ? 'index.html' : cleanPath;
  const segments = relativePath.split(/[\\/]+/);

  if (segments.some(segment => !segment || segment === '..' || segment.startsWith('.'))) return null;
  if (/\.(?:env|ini|log|sql|bak|old|orig|swp|md|mjs)$/i.test(relativePath)) return null;
  if (!isPublicStaticPath(relativePath, segments)) return null;

  const fullPath = join(root, relativePath);
  if (!fullPath.startsWith(root)) return null;
  return fullPath;
}

async function serveStatic(req, res, pathname) {
  const filePath = resolveStaticPath(pathname);
  if (!filePath) {
    res.writeHead(403, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('Forbidden');
    return;
  }

  try {
    const fileStat = await stat(filePath);
    if (!fileStat.isFile()) throw new Error('Not a file');

    res.writeHead(200, {
      'content-type': mimeTypes.get(extname(filePath)) || 'application/octet-stream',
      'x-content-type-options': 'nosniff'
    });

    if (req.method === 'HEAD') {
      res.end();
      return;
    }

    createReadStream(filePath).pipe(res);
  } catch {
    res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('Not found');
  }
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);

  if (url.pathname === '/api/aria-chat') {
    await handleAriaChat(req, res, { ip: getClientIp(req) });
    return;
  }

  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, { allow: 'GET, HEAD, POST' });
    res.end();
    return;
  }

  await serveStatic(req, res, url.pathname);
});

server.listen(port, () => {
  console.log(`BringYourAI.net listening at http://localhost:${port}`);
});
