import { access, readFile, readdir, stat } from 'node:fs/promises';
import { join, resolve } from 'node:path';

const clientRoot = resolve('dist/client');
const serverEntry = resolve('dist/server/index.js');

async function walk(directory) {
	const output = [];
	for (const name of await readdir(directory)) {
		const path = join(directory, name);
		(await stat(path)).isDirectory() ? output.push(...await walk(path)) : output.push(path);
	}
	return output;
}

const files = await walk(clientRoot);
const pages = files.filter((path) => path.endsWith('.html'));
const filePaths = new Set(files.map((path) => `/${path.slice(clientRoot.length + 1).replaceAll('\\', '/')}`));
const pagesByRoute = new Map();

for (const page of pages) {
	const relative = `/${page.slice(clientRoot.length + 1).replaceAll('\\', '/')}`;
	const route = relative === '/index.html'
		? '/'
		: relative === '/404.html'
			? '/404.html'
			: relative.replace(/index\.html$/, '');
	pagesByRoute.set(route, page);
}

const idsByPage = new Map();
async function pageIds(page) {
	if (!idsByPage.has(page)) {
		const html = await readFile(page, 'utf8');
		idsByPage.set(page, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1])));
	}
	return idsByPage.get(page);
}

const broken = [];
for (const [route, page] of pagesByRoute) {
	const html = await readFile(page, 'utf8');
	for (const match of html.matchAll(/href="([^"]+)"/g)) {
		const href = match[1];
		if (href.startsWith('#')) {
			if (href.length > 1 && !(await pageIds(page)).has(decodeURIComponent(href.slice(1)))) {
				broken.push(`${route} -> ${href}`);
			}
			continue;
		}
		if (href.startsWith('//') || /^[a-z][a-z0-9+.-]*:/i.test(href)) continue;
		const resolved = new URL(href, `https://loopspec.invalid${route}`);
		const targetPath = resolved.pathname;
		const targetHash = resolved.hash.slice(1);
		if (targetPath.includes('.')) {
			if (!filePaths.has(targetPath)) broken.push(`${route} -> ${href}`);
			continue;
		}
		const normalized = targetPath.endsWith('/') ? targetPath : `${targetPath}/`;
		const targetPage = pagesByRoute.get(normalized);
		if (!targetPage) {
			broken.push(`${route} -> ${href}`);
			continue;
		}
		if (targetHash && !(await pageIds(targetPage)).has(decodeURIComponent(targetHash))) {
			broken.push(`${route} -> ${href}`);
		}
	}
}

if (broken.length) {
	throw new Error(`Broken internal documentation links:\n${[...new Set(broken)].join('\n')}`);
}

await access(serverEntry);
await access(resolve(clientRoot, 'og.png'));
await access(resolve(clientRoot, 'favicon.png'));

const builtText = (await Promise.all(pages.map((page) => readFile(page, 'utf8')))).join('\n');
for (const starterText of ['Welcome to Starlight', 'Example Guide', 'My Docs']) {
	if (builtText.includes(starterText)) throw new Error(`Starter content remains: ${starterText}`);
}

console.log(`${pages.length} HTML pages; routes, anchors, assets, worker, and starter cleanup are valid.`);
