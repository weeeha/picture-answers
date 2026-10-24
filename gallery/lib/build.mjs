import { mkdir, rm, writeFile, copyFile } from 'node:fs/promises';
import { join } from 'node:path';
import { loadEntries } from './entries.mjs';
import { renderIndex, renderEntry } from './render.mjs';

/** Render every entry under entriesDir into outDir. Pictures are copied next to their page, never inlined. */
export async function build(entriesDir, outDir) {
  const entries = await loadEntries(entriesDir);
  await rm(outDir, { recursive: true, force: true });
  await mkdir(outDir, { recursive: true });
  await writeFile(join(outDir, 'index.html'), renderIndex(entries));
  await writeFile(join(outDir, 'robots.txt'), 'User-agent: *\nDisallow: /\n');
  for (const entry of entries) {
    const dir = join(outDir, entry.slug);
    await mkdir(dir, { recursive: true });
    await writeFile(join(dir, 'index.html'), renderEntry(entry));
    const file = entry.kind === 'plate' ? entry.plate : 'answer.svg';
    await copyFile(join(entriesDir, entry.slug, file), join(dir, file));
  }
  return entries.length;
}
