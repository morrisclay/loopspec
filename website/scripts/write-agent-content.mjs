import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { basename, dirname, extname, join, relative, resolve, sep } from 'node:path';

const sourceRoot = resolve('src/content/docs');
const outputRoot = resolve('dist/client');
const site = 'https://loopspec.cyborg.build';

async function walk(directory) {
	const output = [];
	for (const name of await readdir(directory, { withFileTypes: true })) {
		const path = join(directory, name.name);
		if (name.isDirectory()) output.push(...await walk(path));
		else if (['.md', '.mdx'].includes(extname(name.name))) output.push(path);
	}
	return output;
}

function parseSource(source) {
	const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
	const frontmatter = match?.[1] ?? '';
	let body = match ? source.slice(match[0].length) : source;
	const title = frontmatter.match(/^title:\s*(.+)$/m)?.[1]?.replace(/^['"]|['"]$/g, '') ?? 'Untitled';
	const description = frontmatter.match(/^description:\s*(.+)$/m)?.[1]?.replace(/^['"]|['"]$/g, '') ?? '';

	const lines = body.split(/\r?\n/);
	const withoutImports = [];
	let inImport = false;
	for (const line of lines) {
		if (!inImport && /^import\s/.test(line)) inImport = true;
		if (inImport) {
			if (/;\s*$/.test(line)) inImport = false;
			continue;
		}
		withoutImports.push(line);
	}
	body = withoutImports.join('\n').trim();

	return { title, description, body };
}

function routeFor(path) {
	const id = relative(sourceRoot, path).split(sep).join('/').replace(/\.(?:md|mdx)$/, '');
	if (id === 'index') return '/';
	if (basename(id) === 'index') return `/${dirname(id).split(sep).join('/')}/`;
	return `/${id}/`;
}

function markdownPathFor(route) {
	return route === '/' ? '/index.md' : `${route}index.md`;
}

const entries = [];
for (const path of await walk(sourceRoot)) {
	const route = routeFor(path);
	if (route === '/404/') continue;
	const parsed = parseSource(await readFile(path, 'utf8'));
	const markdownPath = markdownPathFor(route);
	const destination = resolve(outputRoot, `.${markdownPath}`);
	await mkdir(dirname(destination), { recursive: true });
	const summary = parsed.description ? `\n> ${parsed.description}\n` : '';
	await writeFile(destination, `# ${parsed.title}\n${summary}\n${parsed.body}\n`);
	entries.push({ route, markdownPath, ...parsed });
}

const sections = new Map();
for (const entry of entries.sort((a, b) => a.route.localeCompare(b.route))) {
	const section = entry.route === '/' ? 'Overview' : entry.route.split('/').filter(Boolean)[0];
	const label = section.charAt(0).toUpperCase() + section.slice(1).replaceAll('-', ' ');
	if (!sections.has(label)) sections.set(label, []);
	sections.get(label).push(entry);
}

const llms = [
	'# LoopSpec',
	'',
	'> A specification language and structural design toolkit for agentic feedback loops.',
	'',
	'LoopSpec documents what a loop observes, decides, changes, learns, and must preserve. The documentation distinguishes structural assurance from runtime or dynamical claims.',
];
for (const [section, sectionEntries] of sections) {
	llms.push('', `## ${section}`, '');
	for (const entry of sectionEntries) {
		const note = entry.description ? `: ${entry.description}` : '';
		llms.push(`- [${entry.title}](${site}${entry.markdownPath})${note}`);
	}
}
llms.push(
	'',
	'## Optional',
	'',
	'- [Source repository](https://github.com/morrisclay/loopspec): Source code, schemas, examples, and canonical documents.',
	'- [cyborg.build](https://cyborg.build/): Parent research programme.',
	'',
);
await writeFile(resolve(outputRoot, 'llms.txt'), llms.join('\n'));

console.log(`Prepared ${entries.length} Markdown page alternates and llms.txt.`);
