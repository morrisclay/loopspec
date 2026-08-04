import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import sharp from 'sharp';

const publicDirectory = resolve('public');
await mkdir(publicDirectory, { recursive: true });

const og = `
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
      <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#344039" stroke-width="1" opacity="0.52"/>
    </pattern>
    <linearGradient id="shade" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#13201a"/>
      <stop offset="1" stop-color="#0d1511"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#shade)"/>
  <rect width="1200" height="630" fill="url(#grid)"/>

  <g transform="translate(70 70)">
    <text x="0" y="166" fill="#f2f0e8" font-family="Helvetica Neue, Arial, sans-serif"
      font-size="118" font-weight="760" letter-spacing="-5">LOOPSPEC</text>
    <line x1="0" y1="210" x2="442" y2="210" stroke="#98ad9e" stroke-width="2"/>
    <circle cx="442" cy="210" r="6" fill="#c99c4e"/>
    <text x="0" y="285" fill="#f2f0e8" font-family="Georgia, serif" font-size="48">Specify feedback</text>
    <text x="0" y="343" fill="#f2f0e8" font-family="Georgia, serif" font-size="48">before it becomes</text>
    <text x="0" y="401" fill="#f2f0e8" font-family="Georgia, serif" font-size="48">behavior.</text>
    <text x="2" y="462" fill="#98ad9e" font-family="Helvetica Neue, Arial, sans-serif"
      font-size="18" letter-spacing="3">CYBERNETIC LOOP SPECIFICATION</text>
  </g>

  <g transform="translate(625 84)" fill="none" stroke="#92aa98" stroke-width="2.5">
    <path d="M 78 202 V 76 Q 78 26 128 26 H 374 Q 424 26 424 76 V 180"/>
    <path d="M 424 245 V 390 Q 424 440 374 440 H 128 Q 78 440 78 390 V 286"/>
    <path d="M 68 84 l10 -10 l10 10 M 414 170 l10 10 l10 -10 M 88 382 l-10 10 l-10 -10"/>
    <circle cx="250" cy="26" r="18" fill="#8ea795" stroke="#dce5dc"/>
    <rect x="406" y="198" width="36" height="36" fill="#9ab09f" stroke="#e0e8e1"/>
    <path d="M 78 254 l22 38 h-44 z" fill="#e8e9df" stroke="#f4f3eb"/>
    <circle cx="228" cy="440" r="18" fill="#8ea795" stroke="#dce5dc"/>
    <path d="M 340 440 l26 -26 l26 26 l-26 26 z" fill="#c99c4e" stroke="#f4f3eb"/>
    <g fill="#9fb5a5" stroke="none" font-family="monospace" font-size="16" letter-spacing="2">
      <text x="202" y="72">REFERENCE</text>
      <text x="452" y="224">POLICY</text>
      <text x="319" y="500">ACTION</text>
      <text x="185" y="500">PROCESS</text>
      <text x="-28" y="322">OBSERVATION</text>
    </g>
  </g>
</svg>`;

const favicon = `
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="10" fill="#13201a"/>
  <path d="M17 18 V13 Q17 9 21 9 H43 Q47 9 47 13 V19 M47 26 V43 Q47 47 43 47 H21 Q17 47 17 43 V34"
    fill="none" stroke="#91aa98" stroke-width="2.5"/>
  <circle cx="32" cy="9" r="4" fill="#c99c4e"/>
  <path d="M13 32 l4 -7 l4 7 z" fill="#f2f0e8"/>
  <path d="M43 47 l4 -4 l4 4 l-4 4 z" fill="#c99c4e"/>
  <text x="32" y="31" fill="#f2f0e8" text-anchor="middle"
    font-family="Helvetica Neue, Arial, sans-serif" font-size="14" font-weight="750">LS</text>
</svg>`;

await Promise.all([
  sharp(Buffer.from(og)).png().toFile(resolve(publicDirectory, 'og.png')),
  sharp(Buffer.from(favicon)).png().toFile(resolve(publicDirectory, 'favicon.png')),
]);

console.log('Generated LoopSpec social card and favicon.');
