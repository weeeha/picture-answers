import { readdir, readFile, stat } from 'node:fs/promises';
import { join } from 'node:path';

// Same rule capture.py applies: labels are inlined into the page, so nothing in them may run code.
const UNSAFE = /<\s*(script|foreignobject|iframe|object|embed)\b|\son[a-z]+\s*=|javascript:/i;

async function exists(path) {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

async function loadOne(dir, slug) {
  const root = join(dir, slug);
  const question = (await readFile(join(root, 'question.txt'), 'utf8')).trim();
  const meta = JSON.parse(await readFile(join(root, 'meta.json'), 'utf8'));
  if (await exists(join(root, 'answer.svg'))) {
    return { slug, question, meta, kind: 'svg', svg: (await readFile(join(root, 'answer.svg'), 'utf8')).trim() };
  }
  if (await exists(join(root, 'plate.png'))) {
    const labelsPath = join(root, 'labels.html');
    const labels = (await exists(labelsPath)) ? await readFile(labelsPath, 'utf8') : '';
    if (UNSAFE.test(labels)) throw new Error(`entry ${slug}: labels.html has unsafe markup`);
    return { slug, question, meta, kind: 'plate', plate: 'plate.png', labels };
  }
  throw new Error(`entry ${slug}: no answer.svg and no plate.png`);
}

const sortKey = (e) => `${e.meta.kept ?? e.meta.date ?? ''}|${e.meta.date ?? ''}|${e.meta.stamp ?? e.slug}`;

/** Every kept answer under dir, newest first by meta.kept, then meta.date. */
export async function loadEntries(dir) {
  const names = [];
  for (const d of await readdir(dir, { withFileTypes: true })) if (d.isDirectory()) names.push(d.name);
  const entries = await Promise.all(names.map((n) => loadOne(dir, n)));
  return entries.sort((a, b) => sortKey(b).localeCompare(sortKey(a)));
}
