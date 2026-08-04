import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const siteRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repositoryRoot = resolve(siteRoot, '..');

const documents = [
	{
		source: 'docs/LINTING-EXISTING.md',
		output: 'src/content/docs/guides/linting-existing.md',
		title: 'Lint an existing loop',
		description: 'Turn code, prompts, or a runbook into a source-grounded loop specification without inventing semantics.',
	},
	{
		source: 'docs/COOKBOOK.md',
		output: 'src/content/docs/patterns/index.md',
		title: 'Loop pattern cookbook',
		description: 'Reflection, judges, tree search, verifier groups, Ralph loops, and the structural cost of each pattern.',
	},
	{
		source: 'CYBERNETICS.md',
		output: 'src/content/docs/concepts/cybernetic-contract.md',
		title: 'Cybernetic contract',
		description: 'What LoopSpec can establish structurally, where theorem claims stop, and what stronger analysis would require.',
	},
	{
		source: 'ATTENTION.md',
		output: 'src/content/docs/concepts/attention.md',
		title: 'Attention',
		description: 'How the notation directs author attention, represents signal attention, and allocates human attention.',
	},
	{
		source: 'CALIBRATION.md',
		output: 'src/content/docs/concepts/calibration.md',
		title: 'Calibration',
		description: 'How a loop joins prior beliefs to later outcomes and changes what it trusts.',
	},
	{
		source: 'REFERENCE.md',
		output: 'src/content/docs/reference/language.md',
		title: 'Language keys',
		description: 'The generated reference for every accepted authoring key in LoopSpec v1.1.',
	},
	{
		source: 'docs/CHECKS.md',
		output: 'src/content/docs/reference/checks.md',
		title: 'Check catalog',
		description: 'Every design check, what it inspects, its evidence status, assurance, and repair.',
	},
	{
		source: 'NOTATION.md',
		output: 'src/content/docs/reference/diagram-notation.md',
		title: 'Diagram notation',
		description: 'The stable visual vocabulary behind LoopSpec dependency and control-loop diagrams.',
	},
	{
		source: 'RULESET.md',
		output: 'src/content/docs/reference/assurance-and-rules.md',
		title: 'Assurance and rules',
		description: 'How checks are admitted, scoped, ranked, and kept below their evidence ceiling.',
	},
	{
		source: 'COMPATIBILITY.md',
		output: 'src/content/docs/reference/compatibility.md',
		title: 'Versions and compatibility',
		description: 'Authoring v1.1, canonical IR v2.1, migrations, and the executable conformance target.',
	},
];

const replacements = new Map([
	['../REFERENCE.md', '/reference/language/'],
	['REFERENCE.md', '/reference/language/'],
	['CHECKS.md', '/reference/checks/'],
	['COOKBOOK.md', '/patterns/'],
	['LINTING-EXISTING.md', '/guides/linting-existing/'],
	['../NOTATION.md', '/reference/diagram-notation/'],
	['../ATTENTION.md', '/concepts/attention/'],
	['../CALIBRATION.md', '/concepts/calibration/'],
	['../research/llm_as_compiler.md', '/evidence/status/'],
]);

function normalizeMarkdown(markdown, sourcePath) {
	let output = markdown.replace(/^# .+?\n+/, '');
	for (const [from, to] of replacements) output = output.replaceAll(`](${from})`, `](${to})`);
	if (sourcePath === 'docs/CHECKS.md') {
		output = output.replace(/\]\(#([a-z0-9-]+)\)/g, (_match, fragment) =>
			`](#${fragment.replaceAll('-', '_')})`,
		);
	}
	return output.trimStart();
}

for (const document of documents) {
	const source = await readFile(resolve(repositoryRoot, document.source), 'utf8');
	const destination = resolve(siteRoot, document.output);
	const frontmatter = `---\ntitle: ${JSON.stringify(document.title)}\ndescription: ${JSON.stringify(document.description)}\n---\n\n`;
	const provenance = `> This page is generated from \`${document.source}\` during every site build. Edit the canonical source, not this copy.\n\n`;
	await mkdir(dirname(destination), { recursive: true });
	await writeFile(destination, frontmatter + provenance + normalizeMarkdown(source, document.source));
}

console.log(`Synced ${documents.length} canonical LoopSpec documents.`);
