import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { loadEntries } from '../lib/entries.mjs';
import { build } from '../lib/build.mjs';
import { readFile, readdir } from 'node:fs/promises';

async function entry(root, slug, files) {
  const dir = join(root, slug);
  await mkdir(dir, { recursive: true });
  for (const [name, body] of Object.entries(files)) await writeFile(join(dir, name), body);
}

const meta = (extra = {}) => JSON.stringify({ date: '2026-10-24', shape: 'quantity', metaphor: 'piles', why: 'one coin = $5K', lang: 'en', ...extra });

test('loadEntries reads the three seeds, and keeps working as entries are kept', async () => {
  const e = await loadEntries('entries');
  const slugs = e.map((x) => x.slug);
  for (const seed of ['2026-10-24-mixture-of-experts', '2026-10-24-so-how-many-hours-is-3', '2026-10-24-where-are-we']) assert.ok(slugs.includes(seed), seed);
  assert.ok(e.every((x) => (x.kind === 'svg' && x.svg.startsWith('<svg')) || x.kind === 'plate'));
});

test('loadEntries sorts newest kept first, then by date', async () => {
  const root = await mkdtemp(join(tmpdir(), 'pm-'));
  await entry(root, 'old', { 'question.txt': 'old', 'meta.json': meta({ kept: '2026-10-01' }), 'answer.svg': '<svg></svg>' });
  await entry(root, 'new', { 'question.txt': 'new', 'meta.json': meta({ kept: '2026-10-20' }), 'answer.svg': '<svg></svg>' });
  await entry(root, 'mid', { 'question.txt': 'mid', 'meta.json': meta({ date: '2026-10-10' }), 'answer.svg': '<svg></svg>' });
  const e = await loadEntries(root);
  assert.deepEqual(e.map((x) => x.slug), ['new', 'mid', 'old']);
});

test('loadEntries throws naming an entry with no picture', async () => {
  const root = await mkdtemp(join(tmpdir(), 'pm-'));
  await entry(root, 'empty-one', { 'question.txt': 'q', 'meta.json': meta() });
  await assert.rejects(loadEntries(root), /entry empty-one: no answer\.svg and no plate\.png/);
});

test('plate entry loads labels and plate path', async () => {
  const root = await mkdtemp(join(tmpdir(), 'pm-'));
  await entry(root, 'plate-one', { 'question.txt': 'q', 'meta.json': meta({ kind: 'plate' }), 'plate.png': 'png', 'labels.html': '<div class="tag">$97K</div>' });
  const [e] = await loadEntries(root);
  assert.equal(e.kind, 'plate');
  assert.equal(e.plate, 'plate.png');
  assert.match(e.labels, /<div/);
});

test('loadEntries skips files that are not folders', async () => {
  const root = await mkdtemp(join(tmpdir(), 'pm-'));
  await writeFile(join(root, '.DS_Store'), 'x');
  await entry(root, 'one', { 'question.txt': 'q', 'meta.json': meta(), 'answer.svg': '<svg></svg>' });
  assert.equal((await loadEntries(root)).length, 1);
});

test('plate labels with script-capable markup fail the build', async () => {
  const root = await mkdtemp(join(tmpdir(), 'pm-'));
  await entry(root, 'bad-plate', { 'question.txt': 'q', 'meta.json': meta({ kind: 'plate' }), 'plate.png': 'png', 'labels.html': '<img src=x onerror="alert(1)">' });
  await assert.rejects(loadEntries(root), /entry bad-plate: labels\.html has unsafe markup/);
});

test('build writes each page and copies its picture next to it', async () => {
  const src = await mkdtemp(join(tmpdir(), 'pm-src-'));
  const out = await mkdtemp(join(tmpdir(), 'pm-out-'));
  await entry(src, 'one', { 'question.txt': 'q', 'meta.json': meta({ kept: '2026-10-24' }), 'answer.svg': '<svg xmlns="http://www.w3.org/2000/svg"></svg>' });
  const n = await build(src, out);
  assert.equal(n, 1);
  assert.ok((await readFile(join(out, 'index.html'), 'utf8')).includes('./one/answer.svg'));
  assert.deepEqual((await readdir(join(out, 'one'))).sort(), ['answer.svg', 'index.html']);
});
