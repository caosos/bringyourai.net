import { ARIA_PUBLIC_CONTEXT, ARIA_SYSTEM_INSTRUCTIONS } from './publicContext.mjs';

const OPENAI_RESPONSES_URL = 'https://api.openai.com/v1/responses';
const DEFAULT_MODEL = 'gpt-4.1-mini';
const MAX_MESSAGE_LENGTH = 1000;
const MAX_OUTPUT_TOKENS = 220;
const OPENAI_TIMEOUT_MS = 15000;
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX_REQUESTS = 12;
const rateLimitBuckets = new Map();

export function jsonResponse(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff'
  });
  res.end(body);
}

export async function readJsonBody(req, limitBytes = 8192) {
  let raw = '';
  for await (const chunk of req) {
    raw += chunk;
    if (Buffer.byteLength(raw) > limitBytes) {
      const error = new Error('Request body is too large.');
      error.statusCode = 413;
      throw error;
    }
  }

  try {
    return raw ? JSON.parse(raw) : {};
  } catch {
    const error = new Error('Request body must be valid JSON.');
    error.statusCode = 400;
    throw error;
  }
}

function validateMessage(value) {
  if (typeof value !== 'string') {
    const error = new Error('Message must be a string.');
    error.statusCode = 400;
    throw error;
  }

  const message = value.trim();
  if (!message) {
    const error = new Error('Message is required.');
    error.statusCode = 400;
    throw error;
  }

  if (message.length > MAX_MESSAGE_LENGTH) {
    const error = new Error(`Message must be ${MAX_MESSAGE_LENGTH} characters or fewer.`);
    error.statusCode = 400;
    throw error;
  }

  return message;
}

function extractOutputText(data) {
  if (typeof data?.output_text === 'string' && data.output_text.trim()) {
    return data.output_text.trim();
  }

  const chunks = [];
  for (const item of data?.output ?? []) {
    for (const content of item?.content ?? []) {
      if (typeof content?.text === 'string') chunks.push(content.text);
    }
  }

  return chunks.join('\n').trim();
}

function normalizeIp(ip) {
  return ip || 'unknown';
}

function pruneRateLimitBuckets(now) {
  for (const [ip, bucket] of rateLimitBuckets.entries()) {
    if (now - bucket.windowStart > RATE_LIMIT_WINDOW_MS * 2) {
      rateLimitBuckets.delete(ip);
    }
  }
}

export function enforceRateLimit(ip) {
  const now = Date.now();
  const key = normalizeIp(ip);
  let bucket = rateLimitBuckets.get(key);

  if (!bucket || now - bucket.windowStart >= RATE_LIMIT_WINDOW_MS) {
    bucket = { count: 0, windowStart: now };
    rateLimitBuckets.set(key, bucket);
    pruneRateLimitBuckets(now);
  }

  bucket.count += 1;
  if (bucket.count > RATE_LIMIT_MAX_REQUESTS) {
    const error = new Error('Too many Aria requests. Please wait a minute and try again.');
    error.statusCode = 429;
    throw error;
  }
}

export async function createAriaReply(message, env = process.env) {
  const apiKey = env.OPENAI_API_KEY;
  if (!apiKey) {
    const error = new Error('Aria is not configured yet. Set OPENAI_API_KEY on the server to enable live replies.');
    error.statusCode = 503;
    throw error;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), Number(env.ARIA_OPENAI_TIMEOUT_MS || OPENAI_TIMEOUT_MS));

  let response;
  try {
    response = await fetch(OPENAI_RESPONSES_URL, {
      method: 'POST',
      signal: controller.signal,
      headers: {
        authorization: `Bearer ${apiKey}`,
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: env.ARIA_OPENAI_MODEL || DEFAULT_MODEL,
        instructions: ARIA_SYSTEM_INSTRUCTIONS,
        input: [
          {
            role: 'user',
            content: [
              {
                type: 'input_text',
                text: `Approved public context for this single response only:\n${ARIA_PUBLIC_CONTEXT}\n\nVisitor message:\n${message}`
              }
            ]
          }
        ],
        max_output_tokens: MAX_OUTPUT_TOKENS,
        temperature: 0.3,
        store: false
      })
    });
  } catch (error) {
    const publicError = new Error(
      error.name === 'AbortError'
        ? 'Aria timed out while contacting the model. Please try again shortly.'
        : 'The live Aria model call failed. Please try again shortly.'
    );
    publicError.statusCode = error.name === 'AbortError' ? 504 : 502;
    throw publicError;
  } finally {
    clearTimeout(timeout);
  }

  if (!response.ok) {
    const error = new Error('The live Aria model call failed. Please try again shortly.');
    error.statusCode = 502;
    throw error;
  }

  const data = await response.json();
  const reply = extractOutputText(data);
  if (!reply) {
    const error = new Error('Aria returned an empty response. Please try again.');
    error.statusCode = 502;
    throw error;
  }

  return reply;
}

export async function handleAriaChat(req, res, options = {}) {
  if (req.method !== 'POST') {
    res.writeHead(405, { allow: 'POST' });
    res.end();
    return;
  }

  try {
    enforceRateLimit(options.ip);
    const body = await readJsonBody(req);
    const message = validateMessage(body.message);
    const reply = await createAriaReply(message);
    jsonResponse(res, 200, { reply });
  } catch (error) {
    jsonResponse(res, error.statusCode || 500, {
      error: error.statusCode ? error.message : 'Aria is temporarily unavailable.'
    });
  }
}
