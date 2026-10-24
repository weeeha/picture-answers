import { styles } from './styles.mjs';

export function escapeHtml(s) {
  return String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

const SHAPE_LABEL = { quantity: 'How much', mechanism: 'How it works', comparison: 'Which is better', status: 'Where we are' };

function page({ title, lang = 'en', body }) {
  return `<!doctype html>
<html lang="${escapeHtml(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>${escapeHtml(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono&display=swap">
<style>${styles}</style>
</head>
<body>
${body}
</body>
</html>
`;
}

function picture(entry) {
  if (entry.kind === 'plate') {
    return `<div class="plate">
<img src="./${escapeHtml(entry.plate)}" alt="${escapeHtml(entry.meta.metaphor)}">
${entry.labels}
</div>`;
  }
  return `<div class="drawing"><img src="./answer.svg" alt="${escapeHtml(entry.meta.metaphor)}"></div>`;
}

function facts(meta) {
  const rows = [
    ['Shape', SHAPE_LABEL[meta.shape] ?? meta.shape],
    ['Metaphor', meta.metaphor],
    ['Asked', meta.date],
  ];
  if (meta.lang && meta.lang !== 'en') rows.push(['Language', meta.lang]);
  const dl = rows.map(([k, v]) => `<div><dt>${escapeHtml(k)}</dt><dd>${escapeHtml(v)}</dd></div>`).join('');
  const scaled = meta.scaled ? '<p class="note">Illustrative, numbers scaled from the original answer.</p>' : '';
  return `<dl class="facts">${dl}</dl>${scaled}`;
}

export function renderEntry(entry) {
  const { meta } = entry;
  const body = `<main class="entry">
<nav><a href="../">Back to all answers</a></nav>
<p class="shape">${escapeHtml(SHAPE_LABEL[meta.shape] ?? meta.shape)}</p>
<h1 class="question">${escapeHtml(entry.question)}</h1>
<figure>
${picture(entry)}
<figcaption>${escapeHtml(meta.why)}</figcaption>
</figure>
${facts(meta)}
</main>`;
  return page({ title: entry.question, lang: meta.lang, body });
}

export function renderIndex(entries) {
  const items = entries
    .map((e) => {
      const file = e.kind === 'plate' ? e.plate : 'answer.svg';
      const thumb = `<img src="./${escapeHtml(e.slug)}/${escapeHtml(file)}" alt="">`;
      return `<li>
<a href="./${escapeHtml(e.slug)}/">
<span class="thumb" aria-hidden="true">${thumb}</span>
<span class="shape">${escapeHtml(SHAPE_LABEL[e.meta.shape] ?? e.meta.shape)}</span>
<span class="question" lang="${escapeHtml(e.meta.lang ?? 'en')}">${escapeHtml(e.question)}</span>
<span class="metaphor">${escapeHtml(e.meta.metaphor)}</span>
</a>
</li>`;
    })
    .join('\n');
  const body = `<main class="index">
<header>
<h1>Picture mode</h1>
<p>Questions I actually asked, answered with a drawing that carries the numbers. The shape says it first, the labels make it exact.</p>
<p class="count">${entries.length} ${entries.length === 1 ? 'answer' : 'answers'} kept</p>
</header>
${entries.length ? `<ol class="answers">\n${items}\n</ol>` : '<p class="empty">No answers kept yet. After a picture answer, run <code>keep</code> from the picture skill to add it here.</p>'}
</main>`;
  return page({ title: 'Picture mode', body });
}
