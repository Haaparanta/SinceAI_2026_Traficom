# Girlypop theme v2 (design/)

Design system for the Filing Radar interface: a usage guide, colour and layout tokens for shadcn/ui and Tailwind CSS v4, and hand-drawn cybersigilism background tiles.

> [!NOTE]
> Written on 6 November 2026 from the files in this repository: `design/girlypop-theme.md`, `design/girlypop.css`, `design/sigils/` and the design-system paragraph of `pm_pack/06_AGENTS_Master_Context.md`. It summarises rather than replaces them; if this page and the files differ, the files are authoritative.

## What it is

Girlypop theme v2 is the visual and editorial rulebook for Filing Radar, the name the guide and the PM pack use for the tool that Traficom (Finland's Transport and Communications Agency) experts would use for regulatory decisions. The guide describes it as "Professional first, fun second": the feel of Apple's Human Interface Guidelines (HIG), the component structure of shadcn/ui, Tailwind CSS (Cascading Style Sheets) v4 utilities, and a soft pink personality kept out of the way of the data.

It has three parts, all under [`design/`](../../design/):

| File | Size | Purpose |
|---|---|---|
| [`design/girlypop-theme.md`](../../design/girlypop-theme.md) | 14 095 bytes (13.8 KiB), 225 lines | The guide: v2 change list, principles, colour, typography, layout, background, components, documents, voice, checklist |
| [`design/girlypop.css`](../../design/girlypop.css) | 10 767 bytes (10.5 KiB), 238 lines | The tokens: `:root` light values, `.dark` overrides, Tailwind `@theme inline` mapping, `.bg-sigil` classes, accessibility fallbacks |
| [`design/sigils/generate.py`](../../design/sigils/generate.py) | 38 497 bytes (37.6 KiB), 832 lines | Python script that draws the five SVG (Scalable Vector Graphics) tiles and `preview.html` |
| [`design/sigils/mosaic.svg`](../../design/sigils/mosaic.svg) | 208 334 bytes (203.5 KiB) | Default background tile, 960 x 960, all motifs mixed |
| [`design/sigils/thorn.svg`](../../design/sigils/thorn.svg) | 32 427 bytes (31.7 KiB) | Single-motif tile, 360 x 360, winged thorn sigil |
| [`design/sigils/needle.svg`](../../design/sigils/needle.svg) | 29 518 bytes (28.8 KiB) | Single-motif tile, 360 x 360, needles and bead swags |
| [`design/sigils/cathedral.svg`](../../design/sigils/cathedral.svg) | 30 595 bytes (29.9 KiB) | Single-motif tile, 360 x 360, gothic arch with jellyfish |
| [`design/sigils/filigree.svg`](../../design/sigils/filigree.svg) | 29 139 bytes (28.5 KiB) | Single-motif tile, 360 x 360, four-way scroll rosette |
| [`design/sigils/preview.html`](../../design/sigils/preview.html) | 335 123 bytes (327.3 KiB) | HTML (Hypertext Markup Language) page titled "Sigil Backgrounds": every tile in light and dark plus the mosaic behind a card |

The CSS contains no hex colours (checked with grep on 6 November 2026); every value is `oklch(...)`, a gradient, a shadow or a font stack. OKLCH is the Oklab perceptual colour space written as lightness, chroma and hue angle (background, not from the files).

## Why it matters for this challenge

The challenge asks for an auditable workflow whose findings an expert can review and whose draft correspondence an expert can check before anything is sent; see [the challenge brief](../challenge-brief/README.md). Two of the five evaluation criteria concern how results are presented: C, workflow usefulness, innovation and output quality (20 %), and E, auditability and evidence quality (15 %). The theme's rules for those surfaces are strict: risk is never shown by colour alone, frequencies and scores use monospaced tabular numbers, and findings, decisions, the audit log and exports use plain language with no jokes and no emoji.

The [PM pack](../pm-pack/README.md) (the planning documents in `pm_pack/`) lists the theme as the design system of the provisional stack (React, Vite, TypeScript, shadcn/ui, Tailwind CSS v4, MapLibre GL for the map and Recharts for the frequency chart). The theme's map tokens were added in v2 because the map is the central view, and its chart tokens serve the frequency chart.

## What changed in v2

The guide's change list, condensed. Contrast ratios refer to WCAG AA, level AA of the Web Content Accessibility Guidelines, which the guide applies as at least 4.5:1 for text and 3:1 for UI (user interface) shapes; see [Understanding contrast (minimum)](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html).

| # | Change | Reason given in the guide |
|---|---|---|
| 1 | `--primary` darkened from lightness 0.66 to 0.57; the bright pink kept as `--primary-soft` for decoration only | White text on v1 pink was 3.4:1 and failed WCAG AA; now 4.8:1 |
| 2 | `--destructive` moved from hue 20 to 27 and darkened | v1 was 4.4:1 and looked like primary pink; now 5.4:1 |
| 3 | Risk scale tokens `--risk-low`, `--risk-medium`, `--risk-high` with foregrounds | The main output is a risk score; all pairs pass AA at 6.4 to 9.6:1 in light and dark |
| 4 | Map tokens (land, Finland outline, footprint fill and stroke) | The central view is a map; v1 had none |
| 5 | Dark-mode charts, sidebar, gloss and shadow | Missing in v1, so dark mode fell back to light values |
| 6 | `--success` and `--destructive-foreground` | Needed by shadcn `Sonner`, `Badge` and `Alert` |
| 7 | Tailwind v4 `@theme inline` block | Turns tokens into utilities such as `bg-risk-high` and `font-display` |
| 8 | `ui-rounded` first in the display font stack | The only way to reach SF Rounded on the web on Apple devices |
| 9 | Fallbacks for reduced motion, reduced transparency, missing `backdrop-filter` and high contrast | Glass and springy motion must degrade gracefully |
| 10 | Serious-context voice rule (guide section 8) | Playful microcopy on regulatory findings would undermine trust with the partner |
| 11 | GitHub-compatible document callouts (guide section 7) | v1 callouts used background colours that GitHub Markdown cannot render |
| 12 | Chart lilac and mint darkened | Easier to tell apart from pink and readable as thin lines on white |
| 13 | No emoji anywhere | Personality comes from colour, shape and the background instead |
| 14 | Cybersigilism background with a mosaic tile that mixes all motifs | A visual signature without adding noise to content |

The guide states that all contrast figures were calculated from the OKLCH values (OKLCH to sRGB to WCAG relative luminance), and the CSS header says every text and background pair was checked to pass WCAG AA (at least 4.5:1). On 6 November 2026 the figures were recomputed for this page with the standard OKLab-to-sRGB conversion: 4.8:1, 5.4:1, 15.9:1, 5.3:1, 17.0:1, 7.1:1 and 7.9:1 all reproduced, as did the v1 figure of 3.4:1; the risk pairs came out at 6.4 to 8.2:1 in light mode and 8.3 to 9.6:1 in dark mode.

## Role, goal and principles

The guide's role instruction is a senior product designer following Apple's HIG and building with shadcn/ui and Tailwind CSS v4. The product should feel like a pastel iPhone wallpaper, a lip-gloss tube and a well-organised planner, but read like a confident, competent product.

Sparkle budget: 80 % clean Apple neutrality and 20 % sparkle in general; on screens showing findings, risk or decisions, 95 / 5.

| Principle | Meaning in this theme |
|---|---|
| Clarity | Text always legible; pink is an accent, never body text on saturated pink; text contrast at least 4.5:1, UI shapes at least 3:1 |
| Deference | Content leads; chrome is soft, translucent and quiet; decoration never competes with data |
| Depth | Frosted glass, soft pink-tinted shadows, gentle motion |
| Consistency | Every value comes from a token; no one-off hex codes |
| Delight | Micro-moments only: a sparkle on success, a springy toggle, a heart-shaped empty state |
| Trust (new in v2) | Scores, evidence, decisions and exports are plain, precise and sparkle-free |

## Colour

Usage ratio from the guide: neutrals about 70 %, lavender and peach about 20 %, pink about 10 % (calls to action, active states, focus rings, key numbers).

| Token | Use for | Never use for |
|---|---|---|
| `primary` | The one main button per screen, active tab, focus ring | Large backgrounds, body text |
| `primary-soft` | Decorative strokes, chart highlights, sparkles | Anything with text on top |
| `secondary` | Secondary buttons, selected rows, tags | Errors |
| `accent` | Notes, onboarding hints | Status |
| `destructive` | Delete, irreversible actions, errors | High-risk scores (use `risk-high`) |
| `risk-*` | Risk badges, score pills, map markers | Buttons |

Colour is never the only signal: a risk badge always carries a label such as "High · 82", and map markers also differ in shape or size.

### Token inventory in girlypop.css

Light values are set on `:root`; the `.dark` class overrides the groups marked below. Names are quoted exactly from the file.

| Group | Tokens | Overridden in `.dark` |
|---|---|---|
| Radius | `--radius` (0.875rem, 14 px) | No |
| Base and surfaces | `--background`, `--foreground`, `--card`, `--card-foreground`, `--popover`, `--popover-foreground`, `--muted`, `--muted-foreground` | Yes |
| Brand | `--primary`, `--primary-foreground`, `--primary-soft`, `--secondary`, `--secondary-foreground`, `--accent`, `--accent-foreground` | Yes |
| Status | `--destructive`, `--destructive-foreground`, `--success` | Yes |
| Risk | `--risk-low`, `--risk-low-foreground`, `--risk-medium`, `--risk-medium-foreground`, `--risk-high`, `--risk-high-foreground` | Yes |
| Lines and focus | `--border`, `--input`, `--ring` | Yes |
| Chart | `--chart-1` pink, `--chart-2` lilac, `--chart-3` peach, `--chart-4` mint, `--chart-5` butter | Yes |
| Map | `--map-land`, `--map-focus-outline`, `--map-footprint`, `--map-footprint-stroke` | Yes |
| Sidebar | `--sidebar`, `--sidebar-foreground`, `--sidebar-primary`, `--sidebar-primary-foreground`, `--sidebar-accent`, `--sidebar-accent-foreground`, `--sidebar-border`, `--sidebar-ring` | Yes |
| Effects | `--gloss` (135 degree gradient), `--shadow-soft` (two pink-tinted shadows in light, black in dark) | Yes |
| Sigil | `--sigil-fill`, `--sigil-opacity`, `--sigil-size`, `--sigil-size-single` | `--sigil-fill` and `--sigil-opacity` only |
| Motion | `--ease-spring` `cubic-bezier(0.34, 1.56, 0.64, 1)`, `--ease-out` `cubic-bezier(0.22, 1, 0.36, 1)` | No |
| Fonts | `--font-sans`, `--font-display`, `--font-mono` | No |

Values that carry a contrast note in the CSS, plus the risk and sigil tokens:

| Token | Light | Dark | Note in the CSS |
|---|---|---|---|
| `--background` | `oklch(0.985 0.008 350)` blush white | `oklch(0.17 0.03 330)` midnight plum | - |
| `--foreground` | `oklch(0.24 0.04 340)` berry ink | `oklch(0.96 0.015 350)` | 15.9:1 light, 17.0:1 dark |
| `--muted-foreground` | `oklch(0.52 0.03 340)` | `oklch(0.72 0.03 340)` | 5.3:1 on background (light), 7.1:1 on card (dark) |
| `--primary` | `oklch(0.57 0.2 352)` | `oklch(0.75 0.17 352)` | 4.8:1 under white text (light); dark `--primary-foreground` 7.9:1 |
| `--primary-soft` | `oklch(0.72 0.17 352)` | `oklch(0.75 0.17 352)` | Decoration only, never under text |
| `--destructive` | `oklch(0.55 0.21 27)` | `oklch(0.68 0.2 20)` | 5.4:1 with white (light) |
| `--success` | `oklch(0.45 0.11 160)` | `oklch(0.78 0.12 160)` | - |
| `--risk-low` / `--risk-low-foreground` | `oklch(0.94 0.05 165)` / `oklch(0.38 0.08 165)` | `oklch(0.3 0.05 165)` / `oklch(0.88 0.08 165)` | Always shown with a text label |
| `--risk-medium` / `--risk-medium-foreground` | `oklch(0.95 0.07 90)` / `oklch(0.42 0.09 65)` | `oklch(0.32 0.05 75)` / `oklch(0.9 0.09 90)` | Same |
| `--risk-high` / `--risk-high-foreground` | `oklch(0.94 0.04 20)` / `oklch(0.46 0.17 25)` | `oklch(0.32 0.08 22)` / `oklch(0.86 0.08 20)` | Same |
| `--sigil-fill` | gradient `oklch(0.57 0.2 352)` to `oklch(0.45 0.12 300)` | gradient `oklch(0.8 0.15 352)` to `oklch(0.78 0.1 300)` | Pink to lilac |
| `--sigil-opacity` | 0.16 | 0.2 | See strength limits below |

Font stacks: `--font-sans` is `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", system-ui, sans-serif`; `--font-display` is `ui-rounded, "SF Pro Rounded", "Nunito"` falling back to `--font-sans`; `--font-mono` is `ui-monospace, "SF Mono", "JetBrains Mono", monospace`.

### Tailwind mapping and what it leaves out

The `@theme inline` block ([Tailwind theme variables](https://tailwindcss.com/docs/theme)) re-exports tokens under the names Tailwind v4 turns into utilities: `--color-*` for the base, brand, status, risk, line, chart and sidebar colours (`bg-primary`, `text-risk-high-foreground`, `bg-risk-high`), `--font-sans`, `--font-display` and `--font-mono` (`font-display`), `--radius-sm` (radius minus 4 px), `--radius-md` (minus 2 px), `--radius-lg` (the radius) and `--radius-xl` (plus 4 px), and `--shadow-soft` (`shadow-soft`).

Where the CSS and the guide differ: the guide says the block makes "every token" a utility, but the block does not map `--map-land`, `--map-focus-outline`, `--map-footprint`, `--map-footprint-stroke`, `--gloss`, `--ease-spring`, `--ease-out` or any `--sigil-*` token. Use those as `var(--map-land)` and so on (for MapLibre styles the value is passed directly anyway), or add them to the block. The guide's `rounded-2xl` and `rounded-3xl` classes are not derived from `--radius` either, so they keep Tailwind's own sizes (background, not from the files).

### Accessibility fallbacks

| Condition | Effect in the CSS |
|---|---|
| `prefers-reduced-motion: reduce` | `animation-duration` and `transition-duration` forced to 0.01 ms on every element and pseudo-element |
| `prefers-reduced-transparency: reduce` | `--popover` and `--sidebar` become opaque in both modes; the sigil background is hidden |
| `@supports not (backdrop-filter: blur(1px))` | `--popover` becomes opaque in both modes |
| `prefers-contrast: more` | Stronger `--border` and `--muted-foreground` in both modes; the sigil background is hidden |
| `print` | The sigil background is hidden |

## Typography

| Role | Size / line height (px) | Weight | Font |
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

Titles use `tracking-tight`; body text has normal tracking. Sentence case everywhere, with all caps only for tiny eyebrow labels. Frequencies, coordinates and scores use the mono data style so columns line up (the guide's example is 10 700-12 750 MHz).

## Layout, spacing, shape and motion

| Rule | Value |
|---|---|
| Grid | 8 pt, with 4 pt for fine adjustments; generous whitespace |
| Max width | 720 px for documents, 1200 px for apps |
| Mobile | 16 px side gutter, no horizontal scroll |
| Radius | Cards `rounded-2xl`, buttons and badges `rounded-full`, inputs `rounded-xl`, dialogs `rounded-3xl` |
| Depth | `shadow-soft` on cards; glass panels use `bg-popover backdrop-blur-xl border border-white/40` (dark: `border-white/10`) |
| Motion | `--ease-spring` for toggles and small pops at 200 to 300 ms; `--ease-out` for panels and data appearing, with no overshoot on data; respect `prefers-reduced-motion` |
| Touch targets | At least 44 x 44 px |

## Cybersigilism background

An infinitely repeating background of ornamental linework inspired by cybersigilism tattoo art, drawn by `generate.py` to look like ink on paper rather than clean vector icons. By default one page shows many motifs at once: the mosaic tile mixes every motif at different sizes, angles and mirrorings, with small glyphs and sparkles in the gaps.

### Drawing style

| Technique | What the script does |
|---|---|
| Pen pressure | Main strokes are filled outlines that swell in the middle and taper to points |
| Hand wobble | Every stroke is bent by smooth, low-frequency noise, so nothing is perfectly straight or round |
| Overdraw | Major strokes get a second, thinner pass slightly beside the first |
| Pencil construction lines | Faint guide circles and centre lines stay under the ink at 35 % strength |
| Ornament | Ball-ended scrolls, fans of three curls, thorn vines along strokes, four-point sparkles, bead chains, pendants and stipple |
| No two alike | Every motif instance is drawn separately from a seeded random generator, so repeats differ slightly |

### Tiles

| Tile | Class | Content | Artwork / display size | Generator seed, fillers |
|---|---|---|---|---|
| Mosaic (default) | `bg-sigil` | Winged thorn sigil (large and small), needle cluster, cathedral arch with jellyfish, filigree rosette (large and small), barbed arc with bead swags and pendants, ten small glyph sigils and about forty sparkles, curl fans and bead drops in the gaps | 960 px / 720 px | 11, 40 fillers, 10 glyphs |
| Thorn | `bg-sigil bg-sigil--thorn` | Spine, three tiers of sweeping spikes with thorn vines, outer barbed arcs, curl fans | 360 px / 300 px | 21, 6 fillers |
| Needle | `bg-sigil bg-sigil--needle` | Needles with sparkles, curl fans and thorn vines; barbed arc; bead swags and pendants | 360 px / 300 px | 31, 6 fillers |
| Cathedral | `bg-sigil bg-sigil--cathedral` | Pointed gothic arch with crockets, rose window and tracery framing a jellyfish | 360 px / 300 px | 41, 6 fillers |
| Filigree | `bg-sigil bg-sigil--filigree` | Four-way rosette of ball-ended scrolls, blades with vines, curl fans, whiskers and dot rings | 360 px / 300 px | 51, 6 fillers |

The mosaic layout is the `MOSAIC_LAYOUT` list in `generate.py` (motif, x, y, scale, rotation in degrees, mirror flag):

| Motif | x, y | Scale | Rotation | Mirrored |
|---|---|---|---|---|
| thorn | 150, 240 | 1.0 | -4 | No |
| cathedral | 480, 250 | 1.0 | 0 | No |
| needle | 800, 225 | 1.0 | 5 | No |
| filigree | 290, 705 | 1.0 | 8 | No |
| arc | 640, 650 | 0.95 | -5 | No |
| thorn | 925, 725 | 0.62 | 9 | Yes |
| filigree | 610, 915 | 0.45 | 0 | No |

### How the tiles are built

- Seamless tiling: each tile's content is drawn nine times, shifted by one tile in every direction, so anything crossing an edge continues on the opposite edge. In the SVG this is a `<g id="m">` definition followed by nine `<use>` copies.
- Layout check: `build()` measures distances toroidally (across tile edges), prints a warning when two motif footprints overlap, then scatters the small glyph sigils into the larger gaps and the fillers into whatever is left.
- Colour: the SVG files are black on transparent and are used as CSS masks, so colour comes from `--sigil-fill` and follows light and dark mode.
- Script structure: path and geometry helpers, a `Pen` class (seeded random, wobble, ink, pencil, overdraw, SVG output), ornament helpers, one `draw_*` function per motif plus `draw_arc`, `draw_glyph` and `draw_filler`, a `MOTIFS` table with footprint circles for layout, `build()`, `data_uri()`, `preview()` and the `__main__` block. Standard library only (`math`, `random`, `re`, `urllib.parse`, `pathlib`, `typing`).

### Regenerating the tiles

Edit `generate.py`, not the SVG files (each SVG carries the comment "Generated by generate.py; edit that, not this file"). From the repository root:

```bash
python3 design/sigils/generate.py
```

The script writes next to itself. Output on 6 November 2026 (Python 3.15.2, 0.2 s; run on a copy of the script in a scratch folder, and the six files were byte-identical to the committed ones, so regeneration is deterministic):

```text
wrote mosaic.svg  203 KB  (10 glyphs, 40 fillers)
wrote thorn.svg  32 KB  (0 glyphs, 6 fillers)
wrote needle.svg  29 KB  (0 glyphs, 6 fillers)
wrote cathedral.svg  30 KB  (0 glyphs, 6 fillers)
wrote filigree.svg  28 KB  (0 glyphs, 6 fillers)
wrote preview.html  327 KB
```

`preview.html` is rebuilt at the same time. It inlines every tile as a data URI because browsers block CSS masks loaded from `file://` URLs, so it opens straight from disk; that is why it is 335 123 bytes. It shows the mosaic at 60 % strength (640 px tile), the mosaic "in use" at product strength (720 px tile, 16 % light and 20 % dark) behind a sample card reading "Filing ABC-SAT-2" with a "High · 82" badge, and each single motif in light and dark at 60 % strength on a 240 px tile.

### How it repeats and how to use it

The `.bg-sigil` rules live in `@layer base` of `girlypop.css`:

- `.bg-sigil` is `position: relative; isolation: isolate; min-height: 100vh`.
- `.bg-sigil::before` is `position: fixed; inset: 0; z-index: -1; pointer-events: none`, painted with `background: var(--sigil-fill)` at `opacity: var(--sigil-opacity)`, and masked with `url("./sigils/mosaic.svg") 0 0 / var(--sigil-size) var(--sigil-size) repeat` (both `mask` and `-webkit-mask`; see [CSS mask](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/mask)).
- `.bg-sigil--thorn`, `.bg-sigil--needle`, `.bg-sigil--cathedral` and `.bg-sigil--filigree` swap the mask image and set `--sigil-size` to `--sigil-size-single`.

Use: add `class="bg-sigil"` to `<body>` or a full-page wrapper, one background class per page; the mosaic is how motifs are mixed. The mask URLs are relative to the CSS file, and the CSS comment says to adjust them if the file moves.

### Strength, size and text on the pattern

| Setting | Value |
|---|---|
| `--sigil-opacity` | 0.16 light, 0.20 dark; never above 0.20 light or 0.24 dark |
| `--sigil-size` | 720 px for the mosaic; 560 px on phones for more motifs per screen; up to 900 px on large dashboards |
| `--sigil-size-single` | 300 px for single-motif tiles |
| Text directly on the pattern | Page titles, eyebrow labels and subtitles in `foreground` or `secondary-foreground`: at least 9.7:1 over the pattern |
| Tokens that fail on the pattern (light) | `muted-foreground` drops to 4.2:1 and `primary` text to 3.7:1 where they cross a line, so they go only on cards |
| Dark mode | All text tokens stay above 4.5:1 |
| Long text and data | Always on cards |

Where not to use it: inside cards, tables, maps, charts, dialogs, exported memos or printouts. It is a page background only, hidden automatically for `prefers-reduced-transparency`, `prefers-contrast: more` and print, and it is static; never animate it.

## shadcn/ui component treatments

Components are [shadcn/ui](https://ui.shadcn.com/) primitives with theme classes, not custom one-offs.

| Component | Treatment |
|---|---|
| `Button` default | Pill, `bg-primary text-primary-foreground`, `--gloss` overlay on hover, `active:scale-[0.97]` |
| `Button` secondary | Lavender fill, berry text |
| `Button` ghost | `text-primary`, hover `bg-primary/10` |
| `Button` destructive (v2) | `bg-destructive text-destructive-foreground`, always with a confirm dialog |
| `Card` | `bg-card rounded-2xl shadow-soft p-6` |
| `Badge` | Pill, pastel fills with dark text; risk badges `bg-risk-* text-risk-*-foreground` |
| `Input`, `Textarea` | `rounded-xl`, 2 px `ring` focus with 2 px offset |
| `Switch` | Pink when on, springy thumb |
| `Tabs` | iOS segmented control: muted track, white sliding pill |
| `Dialog`, `Sheet` | Frosted glass, `rounded-3xl`, bottom sheet on mobile |
| `Sonner` | Glass pill; success uses a `success` check icon, errors a `destructive` alert icon ([lucide](https://lucide.dev/) icons, not emoji) |
| `Sidebar` | Translucent blush; active item is a pink pill with white text |
| `Chart` | `--chart-1` to `--chart-5`, rounded bar tops, minimal gridlines, direct labels instead of legends |
| `Table` (v2) | Zebra rows in `muted`, sticky header, mono numbers right-aligned |
| Map (v2) | `map-land` fill, Finland outlined in `map-focus-outline`, footprints in `map-footprint` with `map-footprint-stroke` |

## Document rules

Section 7 of the guide covers READMEs, reports and docs. The pages in this `docs/` folder follow it.

| Element | Rule |
|---|---|
| Title block | Plain H1 plus one muted subtitle line |
| Callouts | GitHub alerts (`> [!TIP]`, `> [!NOTE]`, `> [!WARNING]`) so they render on GitHub; in HTML, Tip uses `secondary`, Note `accent`, Warning `risk-high` with a `destructive` left border |
| Tables | Zebra rows in `muted`, rounded corners, bold header |
| Code blocks | `muted` background, `rounded-xl`, mono font |
| Dividers | Thin `border` line (`---` in Markdown) |
| Links | `primary`; underlined on hover, and always underlined inside body paragraphs (v2) |
| Images | `rounded-2xl` plus `shadow-soft` |

The alert syntax is documented in [GitHub's basic writing and formatting syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).

## Voice and microcopy

Ordinary interface copy is warm, encouraging and competent. The guide's examples: "Done! Looking good." instead of "Operation successful"; "Nothing here yet. Add your first one to get started." instead of "No items found"; "Hmm, that email doesn't look quite right." instead of "Error: invalid input"; "Save changes" instead of "Submit".

> [!IMPORTANT]
> Serious-context rule (v2). Use plain, precise language with no jokes for risk scores, findings, evidence and explanations; approve, dismiss and investigate decisions and the audit log; exported memos and anything that may leave the team; and errors, legal, security and data-protection text.

| Context | Example from the guide |
|---|---|
| Finding | "Downlink 10.7–11.7 GHz overlaps 2 protected assets in southern Finland." |
| Decision saved | "Decision saved: Investigate. Logged at 14:32." |
| Empty queue (light tone allowed) | "All filings reviewed. Nothing waiting." |

## Do and don't

Do: keep backgrounds near-white and let pink be precious; use glass and soft shadows for depth; one primary action per screen; pair every colour signal with text or shape.

Don't: put body text on saturated pink or any text on `primary-soft`; use glitter textures, Comic Sans or more than three pastel hues per view; use `destructive` red for risk or pink for errors; trade accessibility for cuteness.

## Shipping checklist

- [ ] All colours come from `girlypop.css` tokens, light and dark.
- [ ] Text contrast at least 4.5:1, UI shapes at least 3:1.
- [ ] Spacing on the 8 pt grid; touch targets at least 44 px.
- [ ] shadcn/ui primitives with theme classes, not custom one-offs.
- [ ] Fun elements at most 20 % of visual weight (5 % on decision screens).
- [ ] No emoji anywhere; no playful copy on findings, decisions or exports.
- [ ] Sigil background on the page root only (one class per page), behind content, hidden for reduced transparency, high contrast and print.
- [ ] Works with reduced motion, reduced transparency and high contrast.

## Adopting the theme in the app

The design-system paragraph of [`pm_pack/06_AGENTS_Master_Context.md`](../../pm_pack/06_AGENTS_Master_Context.md) (summarised in [the PM pack page](../pm-pack/README.md)) gives these steps; the `frontend/` folder it refers to does not exist in the repository yet.

1. Import `design/girlypop.css` into `frontend/src/globals.css`. The CSS header says it belongs after `@import "tailwindcss";`.
2. Follow `design/girlypop-theme.md`; use only theme tokens, no hex codes.
3. Risk badges use the `risk-*` tokens with a text label.
4. Put `bg-sigil` on the app's `<body>` for the mosaic background; `design/sigils/preview.html` shows the result.
5. Keep text that sits directly on the pattern in `foreground` or `secondary-foreground`.
6. No emoji anywhere in the UI or docs; no playful copy on findings, decisions or exports.

## Caveats

- Contrast figures are calculated from token values, not measured in a browser, and the text-on-pattern figures (9.7:1, 4.2:1, 3.7:1) come from the guide only.
- `ui-rounded` reaches SF Rounded only on Apple devices; other platforms fall through to Nunito or the sans stack, so the display face differs by platform.
- Glass surfaces need `backdrop-filter`; without it, and under reduced transparency, popovers become opaque by the fallbacks above.
- The `.bg-sigil` masks are loaded from relative `./sigils/*.svg` URLs and browsers block CSS masks from `file://` pages, so test the background through a dev server, not by opening an HTML file from disk; `preview.html` works from disk only because it inlines the tiles.
- Map, gloss, easing and sigil tokens are plain CSS variables, not Tailwind utilities.
- The mosaic is 208 334 bytes and `preview.html` 335 123 bytes; commit regenerated files only when the drawing changed.
- `generate.py` uses `tuple[float, float]` aliases at module level, so it needs Python 3.9 or newer (background, not from the files); it was run with Python 3.15.2.

## Related pages

- [Documentation index](../README.md)
- [Challenge brief](../challenge-brief/README.md): evaluation criteria and submission items the interface must serve
- [PM pack](../pm-pack/README.md): the provisional stack, the folder tree and the agent rules that cite this theme
- [Repository README](../../README.md)
