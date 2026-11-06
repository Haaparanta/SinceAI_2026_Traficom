# 🎀 Girlypop theme v2

Professional first, fun second: Apple-level polish, shadcn/ui structure, soft pink personality. Tuned for **Filing Radar**, a tool that Traficom experts use for regulatory decisions.

Tokens live in [`girlypop.css`](girlypop.css). This file explains how to use them.

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
- One emoji max per heading, H1/H2 only (🎀 ✨ 💖 🌸 🫧). **None in data tables, findings or exports.**
- v2: frequencies, coordinates and scores use the mono data style with tabular numbers so columns line up (e.g. `10 700–12 750 MHz`).

## 5. Layout, spacing & shape

- 8 pt grid (4 pt for fine adjustments). Generous whitespace.
- Max width: 720 px for documents, 1200 px for apps. Mobile: 16 px side gutter, no horizontal scroll.
- Radius: cards `rounded-2xl`, buttons `rounded-full`, inputs `rounded-xl`, badges `rounded-full`, dialogs `rounded-3xl`.
- Depth: `shadow-soft` on cards; glass panels use `bg-popover backdrop-blur-xl border border-white/40` (dark: `border-white/10`).
- Motion: `--ease-spring` for toggles and small pops (200–300 ms); `--ease-out` for panels and data appearing (v2: no overshoot on data). Respect `prefers-reduced-motion`.
- Touch targets ≥ 44 × 44 px.

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
| `Sonner` | Glass pill; ✨ on success, 🍒 on error |
| `Sidebar` | Translucent blush; active item = pink pill with white text |
| `Chart` | `--chart-1…5`, rounded bar tops, minimal gridlines, direct labels over legends |
| `Table` (v2) | Zebra rows in `muted`, sticky header, mono numbers right-aligned |
| Map (v2) | `map-land` fill, Finland outlined in `map-focus-outline`, footprints in `map-footprint` with `map-footprint-stroke` |

## 7. Documents (README, reports, docs)

- **Title block:** H1 with one emoji + one muted subtitle line.
- **Callouts** — v2 uses GitHub alerts so they render on GitHub, with the theme emoji as the first word:

  ```md
  > [!TIP]
  > 💡 Tip text

  > [!NOTE]
  > 🌸 Note text

  > [!WARNING]
  > 🍒 Warning text
  ```

  In HTML, the same callouts use: Tip = `secondary`, Note = `accent`, Warning = `risk-high` with a `destructive` left border.
- **Tables:** zebra rows in `muted`, rounded corners, bold header.
- **Code blocks:** `muted` background, `rounded-xl`, mono font.
- **Dividers:** thin `border` line, or a centred `✦` for section breaks.
- **Links:** `primary`, underline on hover (v2: always underlined inside body paragraphs, for accessibility).
- **Images:** `rounded-2xl` + `shadow-soft`.

## 8. Voice & microcopy

Warm, encouraging, competent — like a friend who is very good at their job.

| Instead of | Say |
|---|---|
| "Operation successful" | "Done! Looking cute ✨" |
| "No items found" | "Nothing here yet — let's add your first one 💖" |
| "Error: invalid input" | "Hmm, that email doesn't look quite right." |
| "Submit" | "Save changes" |

**Serious-context rule (v2).** In these places use plain, precise language with no emoji or jokes:

- Risk scores, findings, evidence and explanations
- Approve / dismiss / investigate decisions and the audit log
- Exported memos and anything that may be sent outside the team
- Errors, legal, security and data-protection text

| Context | Example |
|---|---|
| Finding | "Downlink 10.7–11.7 GHz overlaps 2 protected assets in southern Finland." |
| Decision saved | "Decision saved: Investigate. Logged at 14:32." |
| Empty queue (playful OK) | "All filings reviewed — nothing waiting 🌸" |

## 9. Do & don't

✅ **Do**
- Keep backgrounds near-white; let pink be precious.
- Use glass and soft shadows for depth.
- One primary action per screen.
- Pair every colour signal with text or shape.

❌ **Don't**
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
- [ ] No emoji or playful copy on findings, decisions or exports.
- [ ] Works with reduced motion, reduced transparency and high contrast.
