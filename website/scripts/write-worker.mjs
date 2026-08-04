import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const serverDirectory = resolve('dist/server');
const worker = `/** Static Astro documentation worker for Sites. */
async function fetchAsset(request, env) {
  const response = await env.ASSETS.fetch(request);
  if (response.status !== 404 || !['GET', 'HEAD'].includes(request.method)) return response;

  const url = new URL(request.url);
  if (!url.pathname.includes('.') && !url.pathname.endsWith('/')) {
    url.pathname += '/';
    const redirected = await env.ASSETS.fetch(new Request(url, request));
    if (redirected.status !== 404) return redirected;
  }

  const fallbackUrl = new URL('/404.html', request.url);
  const fallback = await env.ASSETS.fetch(new Request(fallbackUrl, request));
  return new Response(request.method === 'HEAD' ? null : fallback.body, {
    status: 404,
    headers: fallback.headers,
  });
}

export default {
  async fetch(request, env) {
    return fetchAsset(request, env);
  },
};
`;

await mkdir(serverDirectory, { recursive: true });
await writeFile(resolve(serverDirectory, 'index.js'), worker);
console.log('Prepared the static documentation worker.');
