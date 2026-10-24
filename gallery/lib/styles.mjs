/*
 * Design decisions for the picture-answers gallery (2026-10-24). These are the decisions; pages only instantiate them.
 * Families: IBM Plex Sans (prose, labels) and IBM Plex Mono (the question as typed, same family as the SVG labels). No others.
 * Type scale: 13 / 16 / 20 / 28 px. Weights 400 and 500.
 * Accent: one amber (the spike's), used for the shape label and focus ring only.
 * Surfaces: page, plus one "paper" surface that holds a drawing. Drawings carry light-theme literal colours,
 *   so paper stays light in dark mode on purpose. No cards, no shadows. Separation: spacing, then hairline.
 * Radius: 6px on paper only. Spacing steps: 4, 8, 12, 16, 24, 32, 48.
 * Motion: background-colour change on row hover, 120ms, behind prefers-reduced-motion. Nothing idles.
 * State stability: hover and focus change colour and outline only, never size or spacing.
 * 375px: index rows stack the thumbnail above the text; no horizontal scroll.
 */
export const styles = `
:root {
  --bg: #F4F5F7; --fg: #1B2430; --muted: #5B6673; --line: #D5D9DF;
  --paper: #FFFFFF; --paper-line: #D5D9DF; --hover: #EAEDF1;
  --accent: #A35F0B;
  --sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #141A21; --fg: #E6EAEE; --muted: #9AA6B2; --line: #2C3640; --paper: #F4F5F7; --paper-line: #2C3640; --hover: #1C242D; --accent: #E09A3A; color-scheme: dark; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 400 16px/1.5 var(--sans); }
main {
  max-width: 960px; margin: 0 auto; padding-block: 48px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
}
svg, img { max-width: 100%; height: auto; display: block; }
a { color: inherit; }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; border-radius: 2px; }

.shape { margin: 0; font-size: 13px; font-weight: 500; letter-spacing: 0.04em; color: var(--accent); }
.question { font-family: var(--mono); font-weight: 400; overflow-wrap: anywhere; }

/* index */
.index header { display: grid; gap: 8px; max-width: 60ch; margin-bottom: 32px; }
.index h1 { margin: 0; font-size: 28px; font-weight: 500; line-height: 1.2; }
.index header p { margin: 0; color: var(--muted); }
.index .count { font-size: 13px; }
.answers { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--line); }
.answers li { border-bottom: 1px solid var(--line); }
.answers a {
  display: grid; grid-template-columns: 220px minmax(0, 1fr); grid-template-rows: auto auto 1fr;
  column-gap: 24px; row-gap: 4px; padding: 24px 12px; text-decoration: none;
}
.answers .thumb { grid-row: 1 / 4; background: var(--paper); border: 1px solid var(--paper-line); border-radius: 6px; padding: 8px; align-self: start; }
.answers .question { font-size: 20px; line-height: 1.35; }
.answers .metaphor { font-size: 13px; color: var(--muted); }
.answers a:hover { background: var(--hover); }
@media (prefers-reduced-motion: no-preference) { .answers a { transition: background-color 120ms ease-out; } }
@media (max-width: 600px) {
  .answers a { grid-template-columns: minmax(0, 1fr); grid-template-rows: none; padding-inline: 0; }
  .answers .thumb { grid-row: auto; margin-bottom: 8px; }
}
.empty { padding: 24px 0; border-top: 1px solid var(--line); color: var(--muted); }
.empty code { font-family: var(--mono); color: var(--fg); }

/* entry */
.entry nav { margin-bottom: 32px; font-size: 13px; }
.entry nav a { color: var(--muted); text-underline-offset: 3px; }
.entry nav a:hover { color: var(--fg); }
.entry h1 { margin: 8px 0 24px; font-size: 28px; line-height: 1.3; max-width: 36ch; }
.entry figure { margin: 0 0 24px; max-width: 760px; }
.entry .drawing, .entry .plate { background: var(--paper); border: 1px solid var(--paper-line); border-radius: 6px; padding: 16px; }
.entry .drawing img, .answers .thumb img { width: 100%; }
.entry figcaption { margin-top: 12px; max-width: 62ch; }
.plate { position: relative; padding: 0; overflow: hidden; }
.plate img { width: 100%; }
.facts { display: flex; flex-wrap: wrap; gap: 12px 32px; margin: 0; padding-top: 16px; border-top: 1px solid var(--line); font-size: 13px; }
.facts div { display: grid; gap: 4px; }
.facts dt { color: var(--muted); }
.facts dd { margin: 0; }
.note { margin: 12px 0 0; font-size: 13px; color: var(--muted); }
`;
