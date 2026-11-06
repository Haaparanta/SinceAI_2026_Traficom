# Girlypop theme v2

Professional first, fun second: Apple-level polish, shadcn/ui structure, soft pink personality. Tuned for **Filing Radar**, a tool that Traficom experts use for regulatory decisions.

Tokens live in [`girlypop.css`](girlypop.css) and the background tiles in [`sigils/`](sigils/). This file explains how to use them.

---

## What changed in v2

| # | Upgrade | Why |
|---|---|---|
| 1 | `--primary` darkened from L 0.66 to **0.57** | White text on v1 pink was **3.4:1** and failed WCAG AA. Now 4.8:1. The bright pink is kept as `--primary-soft` for decoration only. |
| 2 | `--destructive` moved from hue 20 to **27** and darkened | v1 destructive was 4.4:1 (fail) and looked almost like primary pink. "Delete" and "Save" must never look alike. Now 5.4:1. |
| 3 | **Risk scale** tokens (`--risk-low/medium/high` + foregrounds) | Filing Radar's main output is a risk score. All pairs pass AA (6.4–9.6:1) in light and dark. |
| 4 | **Map** tokens (land, Finland outline, footprint fill/stroke) | The central view is a map; v1 had no tokens for it. |
| 5 | Dark-mode **charts, sidebar, gloss, shadow** | Missing from v1, so dark mode fell back to light values. |
| 6 | `--success`, `--destructive-foreground` | Needed by shadcn `Sonner`, `Badge` and `Alert`. |
| 7 | Tailwind v4 `@theme inline` block | Makes every token a utility (`bg-risk-high`, `font-display`). v1 had no mapping. |
| 8 | `ui-rounded` first in the display font stack | The only way to get SF Rounded on the web on Apple devices. |
| 9 | Fallbacks for reduced motion, reduced transparency, no `backdrop-filter`, high contrast | Glass and springy motion must degrade gracefully. |
| 10 | **Serious-context rule** for voice (section 8) | Playful microcopy on regulatory findings would undermine trust with the partner. |
| 11 | GitHub-compatible document callouts (section 7) | v1 callouts used background colours, which GitHub Markdown can't render. |
| 12 | Chart lilac and mint darkened | Easier to tell apart from pink and readable as thin lines on white. |
| 13 | **No emoji** anywhere: headings, body text, callouts, toasts or microcopy | Keeps the product professional; personality comes from colour, shape and the background instead. |
| 14 | **Cybersigilism background**: hand-drawn, infinitely repeating sigil tiles; the default mosaic mixes all motifs on one page (section 5a) | Gives the theme its own visual signature without adding noise to content. |

All contrast figures were calculated from the OKLCH values (OKLCH → sRGB → WCAG relative luminance).

---

## 1. Role & goal

Act as a senior product designer following Apple's Human Interface Guidelines, building with **shadcn/ui + Tailwind CSS v4**.

- **Feels like:** a pastel iPhone wallpaper, a glossy lip-gloss tube, a well-organised planner.
- **Reads like:** a confident, competent product. Fun lives in the details, never in the way.
- **Rule of thumb:** 80 % clean Apple neutrality, 20 % sparkle. **On screens showing findings, risk or decisions: 95 / 5.**

## 2. Design principles

| Principle | Meaning here |
|---|---|
| **Clarity** | Text always legible. Pink is an accent; never body text on saturated pink. Text contrast ≥ 4.5:1, UI shapes ≥ 3:1. |
| **Deference** | Content leads. Chrome is soft, translucent, quiet. Decoration never competes with data. |
| **Depth** | Frosted glass, soft pink-tinted shadows, gentle motion. |
| **Consistency** | Every value comes from a token. No one-off hex codes. |
| **Delight** | Micro-moments only: a sparkle on success, a springy toggle, a heart-shaped empty state. |
| **Trust** (v2) | Anything consequential (scores, evidence, decisions, exports) is plain, precise and sparkle-free. |

## 3. Colour

See `girlypop.css` for values. Usage ratio: neutrals ~70 % · lavender/peach ~20 % · pink ~10 % (CTAs, active states, focus rings, key numbers).

| Token | Use for | Never use for |
|---|---|---|
| `primary` | The one main button per screen, active tab, focus ring | Large backgrounds, body text |
| `primary-soft` | Decorative strokes, chart highlights, sparkles | Anything with text on top |
| `secondary` | Secondary buttons, selected rows, tags | Errors |
| `accent` | Notes, onboarding hints | Status |
| `destructive` | Delete, irreversible actions, errors | High-risk scores (use `risk-high`) |
| `risk-*` | Risk badges, score pills, map markers | Buttons |

**Colour is never the only signal.** Risk badges always show a label ("High · 82"), and map markers also differ in shape or size.

## 4. Typography

| Role | Size / line height | Weight | Font |
|---|---|---|---|
| Large title | 34 / 41 | 700 | Display |
| Title 1 | 28 / 34 | 700 | Display |
| Title 2 | 22 / 28 | 600 | Display |
| Headline | 17 / 22 | 600 | Sans |
| Body | 17 / 24 | 400 | Sans |
| Callout | 16 / 21 | 400 | Sans |
| Footnote | 13 / 18 | 400 | Sans, muted |
| Caption | 12 / 16 | 500 | Sans, muted |
| Data (v2) | 15 / 20 | 500 | Mono, `tabular-nums` |

- `tracking-tight` on titles; normal on body.
- Sentence case everywhere. ALL CAPS only for tiny eyebrow labels.
- **No emoji** in headings, body text, labels, callouts or microcopy.
- v2: frequencies, coordinates and scores use the mono data style with tabular numbers so columns line up (e.g. `10 700–12 750 MHz`).

## 5. Layout, spacing & shape

- 8 pt grid (4 pt for fine adjustments). Generous whitespace.
- Max width: 720 px for documents, 1200 px for apps. Mobile: 16 px side gutter, no horizontal scroll.
- Radius: cards `rounded-2xl`, buttons `rounded-full`, inputs `rounded-xl`, badges `rounded-full`, dialogs `rounded-3xl`.
- Depth: `shadow-soft` on cards; glass panels use `bg-popover backdrop-blur-xl border border-white/40` (dark: `border-white/10`).
- Motion: `--ease-spring` for toggles and small pops (200–300 ms); `--ease-out` for panels and data appearing (v2: no overshoot on data). Respect `prefers-reduced-motion`.
- Touch targets ≥ 44 × 44 px.

## 5a. Cybersigilism background

A hand-drawn, infinitely repeating background of ornamental linework inspired by cybersigilism tattoo art. By default one page shows **many different motifs at once**: the mosaic tile mixes every motif at different sizes, angles and mirrorings, with small glyphs and sparkles filling the gaps.

### Drawing style

The tiles are drawn like ink on paper, not as clean vector icons:

- **Pen pressure:** main strokes swell in the middle and taper to sharp points, like a fine-liner.
- **Hand wobble:** every line bends slightly with smooth noise, so nothing is perfectly straight or round.
- **Overdraw:** major strokes have a second, thinner pass slightly beside the first, as when an artist goes over a line.
- **Pencil construction lines:** faint guide circles and centre lines are left under the ink at 35 % strength.
- **Ornament:** ball-ended scrolls, fans of three curls, thorn vines along strokes (alternating thorns and curls), four-point sparkles, bead chains, pendants and stipple.
- **No two alike:** every motif instance is drawn separately, so repeated motifs differ slightly.

### Tiles

| Tile | Class | Content | Artwork / display size |
|---|---|---|---|
| **Mosaic** (default) | `bg-sigil` | Winged thorn sigil (large and small), needle cluster, cathedral arch with jellyfish, filigree rosette (large and small), barbed arc with bead swags and pendants, ten small glyph sigils and about forty sparkles, curl fans and bead drops in the gaps | 960 / 720 px |
| Thorn | `bg-sigil bg-sigil--thorn` | Winged sigil: spine, three tiers of sweeping spikes with thorn vines, outer barbed arcs, curl fans | 360 / 300 px |
| Needle | `bg-sigil bg-sigil--needle` | Needles with sparkles, curl fans and thorn vines; barbed arc; bead swags and pendants | 360 / 300 px |
| Cathedral | `bg-sigil bg-sigil--cathedral` | Pointed gothic arch with crockets, rose window and tracery framing a jellyfish | 360 / 300 px |
| Filigree | `bg-sigil bg-sigil--filigree` | Four-way rosette of ball-ended scrolls, blades with vines, curl fans, whiskers and dot rings | 360 / 300 px |

- **Files:** [`sigils/`](sigils/). All tiles are generated by [`sigils/generate.py`](sigils/generate.py). Edit the script and run `python3 design/sigils/generate.py`; it also rebuilds [`sigils/preview.html`](sigils/preview.html), which shows every tile in light and dark plus an example of the mosaic behind a card.
- **Seamless tiling:** each tile is drawn nine times, shifted by one tile in every direction, so anything crossing an edge continues on the opposite edge. The mosaic layout is checked for overlaps across edges, and the small glyphs and fillers are scattered only into free space.
- **How it repeats:** the tile is a CSS `mask` with `repeat`, painted with `--sigil-fill` (a pink-to-lilac gradient). Colour comes from tokens and switches with dark mode; the SVG files are black on transparent.
- **Use:** add `class="bg-sigil"` to `<body>` or a full-page wrapper. The pattern is `position: fixed`, behind everything (`z-index: -1`), and ignores pointer events. Use one background class per page; the mosaic is how you mix motifs.

### Strength and size

- `--sigil-opacity`: 0.16 light, 0.20 dark. Never above 0.20 light or 0.24 dark.
- **Text directly on the pattern** (page titles, eyebrow labels, subtitles) uses `foreground` or `secondary-foreground`: at least 9.7:1 over the pattern. In light mode, `muted-foreground` drops to 4.2:1 and `primary` text to 3.7:1 where they cross a line, so those only go on cards. In dark mode all text tokens stay above 4.5:1. Long text and data always sit on cards.
- `--sigil-size`: 720 px for the mosaic. Use 560 px on phones for more motifs per screen, up to 900 px on large dashboards.
- `--sigil-size-single`: 300 px for single-motif tiles.

### Where not to use it

Inside cards, tables, maps, charts, dialogs, exported memos or printouts. It is a page background only. It is hidden automatically for `prefers-reduced-transparency`, `prefers-contrast: more` and print. It is static; never animate it.

## 6. shadcn/ui components

| Component | Treatment |
|---|---|
| `Button` default | Pill, `bg-primary text-primary-foreground`, `--gloss` overlay on hover, `active:scale-[0.97]` |
| `Button` secondary | Lavender fill, berry text |
| `Button` ghost | `text-primary`, hover `bg-primary/10` |
| `Button` destructive (v2) | `bg-destructive text-destructive-foreground`, always with a confirm dialog |
| `Card` | `bg-card rounded-2xl shadow-soft p-6` |
| `Badge` | Pill, pastel fills with dark text; risk badges use `bg-risk-* text-risk-*-foreground` |
| `Input` / `Textarea` | `rounded-xl`, 2 px `ring` focus with 2 px offset |
| `Switch` | Pink when on, springy thumb |
| `Tabs` | iOS segmented control: muted track, white sliding pill |
| `Dialog` / `Sheet` | Frosted glass, `rounded-3xl`, bottom sheet on mobile |
| `Sonner` | Glass pill; success uses a `success` check icon, errors a `destructive` alert icon (lucide icons, not emoji) |
| `Sidebar` | Translucent blush; active item = pink pill with white text |
| `Chart` | `--chart-1…5`, rounded bar tops, minimal gridlines, direct labels over legends |
| `Table` (v2) | Zebra rows in `muted`, sticky header, mono numbers right-aligned |
| Map (v2) | `map-land` fill, Finland outlined in `map-focus-outline`, footprints in `map-footprint` with `map-footprint-stroke` |

## 7. Documents (README, reports, docs)

- **Title block:** plain H1 + one muted subtitle line.
- **Callouts** use GitHub alerts so they render on GitHub:

  ```md
  > [!TIP]
  > Tip text

  > [!NOTE]
  > Note text

  > [!WARNING]
  > Warning text
  ```

  In HTML, the same callouts use: Tip = `secondary`, Note = `accent`, Warning = `risk-high` with a `destructive` left border.
- **Tables:** zebra rows in `muted`, rounded corners, bold header.
- **Code blocks:** `muted` background, `rounded-xl`, mono font.
- **Dividers:** thin `border` line (`---` in Markdown).
- **Links:** `primary`, underline on hover (v2: always underlined inside body paragraphs, for accessibility).
- **Images:** `rounded-2xl` + `shadow-soft`.

## 8. Voice & microcopy

Warm, encouraging, competent — like a friend who is very good at their job.

| Instead of | Say |
|---|---|
| "Operation successful" | "Done! Looking good." |
| "No items found" | "Nothing here yet. Add your first one to get started." |
| "Error: invalid input" | "Hmm, that email doesn't look quite right." |
| "Submit" | "Save changes" |

**Serious-context rule (v2).** In these places use plain, precise language with no jokes:

- Risk scores, findings, evidence and explanations
- Approve / dismiss / investigate decisions and the audit log
- Exported memos and anything that may be sent outside the team
- Errors, legal, security and data-protection text

| Context | Example |
|---|---|
| Finding | "Downlink 10.7–11.7 GHz overlaps 2 protected assets in southern Finland." |
| Decision saved | "Decision saved: Investigate. Logged at 14:32." |
| Empty queue (light tone OK) | "All filings reviewed. Nothing waiting." |

## 9. Do & don't

**Do**
- Keep backgrounds near-white; let pink be precious.
- Use glass and soft shadows for depth.
- One primary action per screen.
- Pair every colour signal with text or shape.

**Don't**
- Put body text on saturated pink, or text on `primary-soft`.
- Use glitter textures, Comic Sans, or more than three pastel hues per view.
- Use `destructive` red for risk, or pink for errors.
- Trade accessibility for cuteness.

## 10. Shipping checklist

- [ ] All colours come from `girlypop.css` tokens (light + dark).
- [ ] Text contrast ≥ 4.5:1, UI shapes ≥ 3:1.
- [ ] Spacing on the 8 pt grid; touch targets ≥ 44 px.
- [ ] shadcn/ui primitives with theme classes, not custom one-offs.
- [ ] Fun elements ≤ 20 % of visual weight (≤ 5 % on decision screens).
- [ ] No emoji anywhere; no playful copy on findings, decisions or exports.
- [ ] Sigil background is on the page root only (one class per page), sits behind content, and is hidden for reduced transparency, high contrast and print.
- [ ] Works with reduced motion, reduced transparency and high contrast.
