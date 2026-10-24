---
name: picture
description: Answer with a drawn metaphor that carries its numbers, then text under it. Use without being asked when the user asks how much, after tax, budget, how many, how exactly, what's happening, explain again, in simple terms, compare, vs, better than, where are we, what's left, what's next, status, or in Russian объясни, сколько, сравни, где мы, что осталось, ничего не понял. Also the `keep` sub-command that copies the last picture into the gallery repo.
---

# Picture

Two piles instead of two bars. A clinic with two lit rooms instead of a router diagram. A trail with tents behind you instead of a checklist. The picture carries the meaning in its shape, the numbers and words sit on it, and the text comes after.

## The one rule

Lead with the picture. The shape must be true to the numbers; the labels make it exact. If the numbers cannot be drawn to scale in the metaphor, fall back to a plain box diagram, never to a decorative scene.

## Four shapes, four metaphor families

| Question shape | Typical words | Metaphor family | Honesty test |
|---|---|---|---|
| Quantity, split, money | how much, after tax, budget, how many, сколько | piles, jars filling, slices of one loaf | one unit per coin or slice; say the unit under the picture |
| Mechanism, how it works | how exactly, what's happening, explain again, in simple terms, объясни | rooms and doors, a clinic, a kitchen, a post office | every moving part in the metaphor maps to one real part; nothing decorative |
| Comparison, which is better | compare, vs, better than, ours vs theirs, сравни | a scale, two shelves, two piles side by side | the verdict is visible in the shape before any label is read |
| Position, where are we | where are we, what's left, what's next, status, где мы | a trail with camps, a climb, a race track | done, in progress and open are three different marks; the pin is the present |

Choose the metaphor from the physics of the question, never from its noun. A cloud for "the cloud" teaches nothing.

## Drawing contract

- Inline SVG through `show_widget`, `viewBox="0 0 680 H"`, after `read_me` with the `diagram` module once per session. The same SVG is what gets captured, so it must stand on its own outside the chat: a first `<rect>` as a light paper background (`#FFFFFF`, rx 8), literal hex colours only, a `<style>` block for fonts. No widget theme variables (`var(--...)`) and no `c-*` classes: the gallery has neither and would paint them black, and `capture.py` rejects them. The widget guide allows hardcoded colours for scenes, which is what a picture-mode drawing is.
- Static markup only. `capture.py` rejects scripts, `on...=` handlers, `foreignObject`, iframes and external or `javascript:` links in the SVG and in plate labels.
- Labels in the language of the question. A Russian question gets Russian labels.
- One line directly under the picture names the unit or the mapping ("one coin = $5K", "lit room = active expert").
- Text follows: two to four short sentences, then the exact numbers as a line or a small table. Not a paragraph.
- If `show_widget` is not available in the session, publish the same SVG inside a small HTML artifact.
- Examples to copy the register from: `examples/jars.svg` (quantity), `examples/clinic.svg` (mechanism), `examples/trail.svg` (status). `examples/README.md` says what each answered.

## Capture before showing, every time

Write the question and the SVG to temp files in the session scratchpad, then run:

```bash
python3 <this skill's folder>/scripts/capture.py \
  --question-file /path/q.txt --svg-file /path/a.svg \
  --shape quantity --metaphor "piles of coins" --why "one coin = \$5K" --lang en
```

`--shape` is one of `quantity`, `mechanism`, `comparison`, `status`. The script writes `~/.claude/picture-mode/last/<stamp>/` and prints the folder. Remember that printed path for this session: other sessions capture into the same place, so `keep` must be given this exact folder. The capture is what `keep` copies later, so it must be the picture the user sees. Set `PICTURE_MODE_HOME` only in tests.

## Cost ladder

1. Drawn metaphor with numbers (default). Seconds, nothing extra spent.
2. Annotated plate. Only when the user says "poster", "plate", "make it rich", or keeps with that intent. Generate the scene with whatever image model the setup has (slower and more expensive than a drawing), never with text painted in; lay the numbers and labels over it as an HTML layer (absolutely positioned tags over the image, as in the spike). Capture with `--plate plate.png --labels labels.html`.

## Repeat-ask escalation

On "again", "simpler", "in simple terms", "I'm lost", "ничего не понял" about an understand-type question, the next answer is a picture even if the first was text. The second answer is never more prose. Copy work (outreach, CV, contract clauses), bug fixes and personal conversation are excluded: there, "again" means shorter and plainer text.

## `keep [N] [--scaled]`

1. Ask one question: keep the numbers as they are, or scaled to illustrative values. Default: as they are, while the gallery repo is private.
2. If scaled: redraw from the same template with the new numbers, show it, capture it again, then keep that one.
3. Run `python3 <this skill's folder>/scripts/keep.py --folder <path capture.py printed> [--scaled]`. Use the bare `keep.py [N]` form (Nth-newest across all sessions) only when this session captured nothing; it prints the question it took, so check that it is the right one. The script works in a temporary git worktree branched from `main`: it adds `entries/<date>-<slug>/` with `kept` and `scaled` stamped into `meta.json`, commits it on its own `keep/<slug>` branch, and leaves the gallery checkout, index and current branch untouched. The gallery path comes from `~/.claude/picture-mode/config.json`.
4. Offer to push the branch and open a PR against `main`.

## Done check

- [ ] The shape is true to the numbers; the unit line sits under the picture
- [ ] Labels follow the question's language
- [ ] Captured before showing (a new folder under `~/.claude/picture-mode/last/`), its path remembered for `keep --folder`
- [ ] Literal colours on a paper rect, no `var(--...)`, no `c-*` classes
- [ ] Text after the picture, short, with the exact numbers
- [ ] No image generation unless the user asked for a plate
