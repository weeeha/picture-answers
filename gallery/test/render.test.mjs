import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadEntries } from '../lib/entries.mjs';
import { renderIndex, renderEntry, escapeHtml } from '../lib/render.mjs';

const entries = await loadEntries('entries');
const LONG_DASH = String.fromCharCode(8212);

test('renderEntry shows the drawing as an image file, with the verbatim question and the why line', () => {
  for (const entry of entries) {
    const html = renderEntry(entry);
    assert.ok(html.startsWith('<!doctype html>'));
    assert.ok(html.includes('<img src="./answer.svg"'), entry.slug);
    assert.ok(!html.includes('<svg'), 'no inline svg: styles and ids would leak, scripts would run');
    assert.ok(html.includes(escapeHtml(entry.question)));
    assert.ok(html.includes(escapeHtml(entry.meta.why)));
  }
});

test('renderEntry escapes the question so typed markup cannot inject', () => {
  const html = renderEntry({ ...entries[0], question: 'is <b>this</b> & that?' });
  assert.ok(html.includes('is &lt;b&gt;this&lt;/b&gt; &amp; that?'));
  assert.ok(!html.includes('<b>this</b>'));
});

test('renderEntry says when numbers were scaled', () => {
  assert.ok(renderEntry({ ...entries[0], meta: { ...entries[0].meta, scaled: true } }).includes('numbers scaled'));
  assert.ok(!renderEntry({ ...entries[0], meta: { ...entries[0].meta, scaled: false } }).includes('numbers scaled'));
});

test('renderEntry for a plate places the image and the label layer together', () => {
  const html = renderEntry({ slug: 'p', question: 'q', kind: 'plate', plate: 'plate.png', labels: '<div class="tag">$97K</div>', meta: { why: 'w', shape: 'quantity', metaphor: 'piles', lang: 'en', date: '2026-10-24' } });
  assert.match(html, /<div class="plate">\s*<img src="\.\/plate\.png"[^>]*>\s*<div class="tag">\$97K<\/div>/);
});

test('renderIndex lists every entry with a link to its folder', () => {
  const html = renderIndex(entries);
  for (const e of entries) assert.ok(html.includes(`href="./${e.slug}/"`), e.slug);
});

test('renderIndex shows thumbnails as image files, never inline svg', () => {
  const html = renderIndex(entries);
  for (const e of entries) assert.ok(html.includes(`<img src="./${e.slug}/answer.svg"`), e.slug);
  assert.ok(!html.includes('<svg'));
});

test('rendered html has no long dash', () => {
  assert.ok(!renderIndex(entries).includes(LONG_DASH));
  for (const e of entries) assert.ok(!renderEntry(e).includes(LONG_DASH), e.slug);
});

test('pages set lang from the entry', () => {
  assert.ok(renderEntry({ ...entries[0], meta: { ...entries[0].meta, lang: 'ru' } }).includes('<html lang="ru">'));
});

test('renderIndex with no entries says how to add the first one', () => {
  const html = renderIndex([]);
  assert.ok(html.includes('No answers kept yet'));
  assert.ok(html.includes('<code>keep</code>'));
  assert.ok(!html.includes('<ol'));
});

test('pages load only the two declared font families', () => {
  const html = renderIndex(entries);
  assert.ok(html.includes('IBM+Plex+Sans') && html.includes('IBM+Plex+Mono'));
  assert.ok(!/Instrument|Inter\b|Space\+Grotesk/.test(html));
});
