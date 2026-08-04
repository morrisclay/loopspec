// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
	outDir: './dist/client',
	integrations: [
		starlight({
			title: 'LoopSpec',
			description: 'Specify, inspect, and argue about cybernetic agent loops.',
			favicon: '/favicon.png',
			customCss: [
				'@fontsource-variable/geist',
				'@fontsource-variable/jetbrains-mono',
				'./src/styles/custom.css',
			],
			components: { Head: './src/components/Head.astro' },
			social: [
				{ icon: 'github', label: 'Source on GitHub', href: 'https://github.com/morrisclay/loopspec' },
			],
			lastUpdated: true,
			head: [{ tag: 'meta', attrs: { name: 'theme-color', content: '#151a16' } }],
			sidebar: [
				{
					label: 'Start',
					items: [
						{ label: 'What LoopSpec is', slug: 'start/overview' },
						{ label: 'Your first loop', slug: 'start/first-loop' },
						{ label: 'Install and run', slug: 'start/install' },
					],
				},
				{
					label: 'Work with loops',
					items: [
						{ label: 'Lint an existing loop', slug: 'guides/linting-existing' },
						{ label: 'Read and resolve findings', slug: 'guides/findings' },
						{ label: 'Draw diagrams', slug: 'guides/diagrams' },
						{ label: 'Review semantic changes', slug: 'guides/semantic-diff' },
						{ label: 'Compose multiple loops', slug: 'guides/multi-loop-systems' },
					],
				},
				{
					label: 'Cybernetic design',
					items: [
						{ label: 'The control-loop kernel', slug: 'concepts/control-loop-kernel' },
						{ label: 'Cybernetic contract', slug: 'concepts/cybernetic-contract' },
						{ label: 'Attention', slug: 'concepts/attention' },
						{ label: 'Calibration', slug: 'concepts/calibration' },
						{ label: 'Governance and viability', slug: 'concepts/governance-viability' },
					],
				},
				{
					label: 'Patterns',
					items: [{ label: 'Loop pattern cookbook', slug: 'patterns' }],
				},
				{
					label: 'Reference',
					items: [
						{ label: 'Command line', slug: 'reference/cli' },
						{ label: 'Language keys', slug: 'reference/language' },
						{ label: 'Check catalog', slug: 'reference/checks' },
						{ label: 'Diagram notation', slug: 'reference/diagram-notation' },
						{ label: 'Assurance and rules', slug: 'reference/assurance-and-rules' },
						{ label: 'Versions and compatibility', slug: 'reference/compatibility' },
					],
				},
				{
					label: 'Evidence',
					items: [
						{ label: 'What is established', slug: 'evidence/status' },
						{ label: 'Real-loop study', slug: 'evidence/real-loops' },
						{ label: 'Validation protocol', slug: 'evidence/validation' },
					],
				},
			],
		}),
	],
});
