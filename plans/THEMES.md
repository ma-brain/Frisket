# Frisket — Themes, type scale, grids and templates

Exact design values for every task that draws document content: T3.7, T3.8, T3.6, T3.11, T3.13, T1.10, T1.12, T4.10, T4.11, T7.3, T7.5. **The implementing agent must not invent colours, fonts, sizes or margins.** If a value is missing here, stop and ask; do not guess.

Status: **final v1 defaults** unless changed by an ADR. §3 (minimum size by viewing distance) is calibrated to the approved mockup (1.5 m → 28 pt body) and is confirmed with a printed test before 1.0 (Specification §12 open question).

All resource files named here live under `resources/` at the repository root and are embedded into the binaries with `include_str!` / `include_bytes!` by the crate that owns them (named per file).

## 1. Built-in themes

Six themes, matching mockup `ui/09-theme.png`. Colour tokens are sRGB hex. Every pair in the "checked pairs" list meets WCAG 2.x AA for normal text (≥ 4.5:1); the smallest ratio per theme is shown.

| Token | Clinical navy | Forest | Plum | Graphite | Coral | Ocean |
| --- | --- | --- | --- | --- | --- | --- |
| `color.primary` | #1F3A5F | #1E4D3A | #4A2545 | #2B2D31 | #A8323F | #0B4F6C |
| `color.onPrimary` | #FFFFFF | #FFFFFF | #FFFFFF | #FFFFFF | #FFFFFF | #FFFFFF |
| `color.accent` | #AD4C0D | #8A5F00 | #1F6F78 | #0A5FC4 | #1F3A5F | #9C4A00 |
| `color.surface` (page) | #FFFFFF | #FFFFFF | #FFFFFF | #FFFFFF | #FFFFFF | #FFFFFF |
| `color.tint` (callouts, zebra) | #E8EEF6 | #E7F0EA | #F3EAF1 | #EEEFF1 | #F9EBEB | #E6F1F5 |
| `color.text` | #1D1D1F | #1C2420 | #241C23 | #1D1D1F | #2A1F20 | #15222A |
| `color.muted` (captions, affiliations) | #5E5E63 | #56605A | #5F5560 | #5A5C62 | #665557 | #51606A |
| `color.rule` (lines, table rules) | #1F3A5F | #1E4D3A | #4A2545 | #2B2D31 | #A8323F | #0B4F6C |
| Type pairing (§2) | Classic | Classic | Academic | Clear | Office | Clear |
| Figure palette (§6) | Okabe–Ito | Okabe–Ito | Okabe–Ito | Okabe–Ito | Okabe–Ito | Okabe–Ito |
| Smallest contrast ratio | 4.71 | 4.86 | 4.95 | 5.30 | 5.67 | 5.38 |
| Theme id (file name) | `clinical-navy` | `forest` | `plum` | `graphite` | `coral` | `ocean` |

Note: mockup 09 shows the Clinical navy accent as #C2560F; that value fails on `tint` (3.88:1), so the shipped value is #AD4C0D. The mockup's "Surface #e8eef6" swatch is the `tint` token.

**Checked pairs** (the T3.8 contrast test checks exactly these, for every theme): text/surface, text/tint, muted/surface, muted/tint, primary/surface, primary/tint, onPrimary/primary, accent/surface, accent/tint. Contrast = WCAG 2.x relative-luminance ratio `(L1 + 0.05) / (L2 + 0.05)` on sRGB with the 0.04045 linearisation threshold; round to 2 decimals.

**Institution (brand kit) card.** When the user has at least one brand kit (T4.10), the theme picker shows a seventh card named after the kit. Its tokens come from the kit's colours mapped onto the eight tokens above; missing tokens are taken from Clinical navy. It is not a built-in theme: failing pairs produce a preflight suggestion (T7.5), not an error.

**Usage rules** (binding for codegen, T3.5–T3.6, T5.1, T3.13):

- Header band background = `primary`, header text = `onPrimary`.
- Section headings = `primary`, with a 1.5 pt `rule` underline (poster, e-poster, handout) or no underline (flyer, booklet, certificate).
- Callout / key finding: background `tint`, heading `primary`, body `text` (details §11).
- `accent` is for highlights only: key numbers, session times, reading-order badges, arrows. Never for body text below 14 pt.
- Reading-order badges: optional 22 pt circles at the section's top-left, 1.5 pt `accent` outline, white fill, centred 14 pt `accent` numeral in the heading font, bold. Enabled badges reserve 30 pt horizontally before the section heading (circle 22 pt + 8 pt gap).
- Tables: header top rule and bottom rule = `rule` at 1 pt; header/body separator 0.5 pt; zebra rows = `tint`; no vertical rules.

## 2. Type pairings and scales

All fonts are bundled in `fonts/<Family>/` with their licence file; T0.1e copies them and lists them in `THIRD_PARTY.md`. Only the weights listed here exist; never request another weight (Typst would synthesise or fall back).

| Family | Files shipped | Licence |
| --- | --- | --- |
| Liberation Sans | Regular, Italic, Bold, Bold Italic | SIL OFL 1.1 |
| Liberation Serif | Regular, Italic, Bold, Bold Italic | SIL OFL 1.1 |
| Carlito | Regular, Italic, Bold, Bold Italic | SIL OFL 1.1 |
| Caladea | Regular, Italic, Bold, Bold Italic | Apache-2.0 |
| Lora | Regular 400, Medium 500, SemiBold 600, Bold 700, and the matching italics (static files) | SIL OFL 1.1 |
| Latin Modern Math | Regular | GUST Font License (unmodified) |

| Pairing id | Name | Headings | Body, captions, tables | Notes |
| --- | --- | --- | --- | --- |
| `classic` | Classic | Lora SemiBold (600) | Liberation Sans Regular / Bold | Default for new documents; matches mockups 02, 03, 09 and Settings › Fonts |
| `office` | Office | Carlito Bold | Carlito Regular / Bold | For content coming from Word/PowerPoint (Calibri metrics) |
| `academic` | Academic | Liberation Serif Bold | Liberation Serif Regular / Bold | Times-like, for traditional journals |
| `clear` | Clear | Liberation Sans Bold | Liberation Sans Regular / Bold | Single family, compact, high legibility |

Equations always use Latin Modern Math, sized to the surrounding text. Figures in text use lining numerals; tables enable tabular numerals (`tnum`) where the font supports it (Carlito and Caladea do; Liberation's figures are already tabular).

**Type scale.** Every size derives from `size.body` and a modular ratio `r` per document kind.

| Token | Multiplier | Used for |
| --- | --- | --- |
| `size.refs` | body × 0.60 | References, image credits (preflight: suggestion only) |
| `size.caption` | body × 0.80 | Captions, affiliations, table notes |
| `size.body` | body × 1 | Body text, table cells |
| `size.h3` | body × r | Sub-headings, table titles, callout headings |
| `size.section` | body × r² | Section headings |
| `size.h1` | body × r³ | Booklet day headings, flyer headline, callout key figure |
| `size.title` | body × r⁵ | Poster title (auto-shrinks to fit 2 lines, never below `size.h1`) |

| Document kind | `size.body` | Ratio r | Line height (× size): body / headings |
| --- | --- | --- | --- |
| Conference poster | from §3 (viewing distance) | 1.333 | 1.30 / 1.15 |
| E-poster (16:9) | 22 px at 1920 px page width, scaled linearly with width | 1.25 | 1.35 / 1.15 |
| Flyer / leaflet | 11 pt | 1.25 | 1.35 / 1.15 |
| Handout / one-pager | 10.5 pt | 1.25 | 1.35 / 1.15 |
| Programme booklet | 9.5 pt | 1.20 | 1.35 / 1.15 |
| Certificate / badge | 14 pt (badge name: 28 pt) | 1.414 | 1.25 / 1.10 |
| Blank | uses the Handout row (10.5 pt, 1.25) | 1.25 | 1.35 / 1.15 |

Rounding: **only posters round to 0.5 pt** (§3). Other kinds use exact multiples of their body size (a flyer caption is 8.8 pt). Derived sizes are computed from the unrounded body size.

## 3. Minimum body size by viewing distance (poster)

Rule: cap height ≥ viewing distance ÷ 218, with cap height ≈ 0.70 em for the bundled faces.

`size.body (pt) = distance_mm / 218 / 0.70 / 0.3528` (0.3528 = mm per pt), rounded to the nearest 0.5 pt. Derived sizes use the unrounded body, then round to 0.5 pt.

| Viewing distance | Body (min) | Caption | References | Sub-heading | Section heading | Title (before fit) |
| --- | --- | --- | --- | --- | --- | --- |
| In hand (0.5 m) | 9.5 pt | 7.5 pt | 5.5 pt | 12.5 pt | 16.5 pt | 39 pt |
| 1.0 m | 18.5 pt | 15 pt | 11 pt | 25 pt | 33 pt | 78 pt |
| 1.5 m (default) | 28 pt | 22.5 pt | 16.5 pt | 37 pt | 49.5 pt | 117.5 pt |
| 2.0 m | 37 pt | 29.5 pt | 22.5 pt | 49.5 pt | 66 pt | 156.5 pt |
| 3.0 m | 55.5 pt | 44.5 pt | 33.5 pt | 74.5 pt | 99 pt | 234.5 pt |
| Screen | E-poster row of §2 | | | | | |

- Theme inspector choices ("Sizes set for", mockup 09): In hand, 1 m, 1.5 m, 2 m, 3 m, Screen. The mockup shows four of these; the segmented control shows all six.
- Stored as JSON so it can be recalibrated without code changes: `resources/rules/min-text-size.json` = `{"capHeightDivisor": 218, "capHeightEm": 0.70, "roundTo": 0.5, "distancesMm": {"inHand": 500, "1m": 1000, "1.5m": 1500, "2m": 2000, "3m": 3000}}`. Owned by `frisket-model` (theme resolution).
- Preflight (T7.3): body text below `size.body` → issue; captions below `size.caption` → issue; references below `size.refs` → suggestion.
- Before 1.0: print an A0 test at 1.5 m and record the result in an ADR.

## 4. Grids and margins per kind

| Kind / size | Columns | Margins (outer) | Gutter | Bleed (default) |
| --- | --- | --- | --- | --- |
| Blank A4 (default document) | 1 | 15 mm | — | 0 |
| Poster A0 portrait | 3 | 40 mm | 20 mm | 0 (option 3 mm) |
| Poster A0 landscape | 4 | 40 mm | 20 mm | 0 (option 3 mm) |
| Poster A1 portrait / landscape | 3 / 4 | 28 mm | 14 mm | 0 (option 3 mm) |
| Poster 48×36 in (landscape) | 4 | 1.5 in | 0.75 in | 0 |
| E-poster 16:9 | 3 | 4% of width | 2% of width | none |
| Flyer A4 / Letter | 2 | 15 mm | 6 mm | 3 mm |
| Flyer A5 | 1 | 12 mm | — | 3 mm |
| DL tri-fold (A4 landscape) | 3 panels | 8 mm per panel | 16 mm (fold) | 3 mm |
| Handout A4 / Letter | 2 | 18 mm | 8 mm | 0 |
| Booklet A5 (facing) | 2 (mockup 12; option 1) | inside 18, outside 14, top 15, bottom 20 mm | 5 mm | 3 mm |
| Booklet A4 (facing) | 2 | inside 20, outside 16, top 18, bottom 22 mm | 6 mm | 3 mm |
| Certificate A4 landscape | 1 | 20 mm | — | 0 |
| Badge 90×55 mm | 1 | 5 mm | — | 2 mm |

Header band (posters): full width, height content-driven, padding `space.xl`; it extends to the trim edge, and into the bleed when bleed is enabled.

**Spacing scale.** Unit `u = 0.5 × size.body`.

| Token | Value | Used for |
| --- | --- | --- |
| `space.xs` | 0.5 u | Caption to figure |
| `space.s` | 1 u | Paragraph spacing, heading to body |
| `space.m` | 2 u | Between blocks inside a section |
| `space.l` | 3 u | Between sections; callout padding |
| `space.xl` | 4 u | Header band padding (poster) |

## 5. Templates

Templates are `.frisket` files in `resources/templates/<kind>/<layout>-<theme>.frisket`, generated by `cargo xtask templates` from the structure presets (T3.11) so they are never edited by hand. Poster: 3 layouts × 6 themes = 18. Other kinds: 2 layouts × 6 themes.

**Poster layouts** (A0 portrait; landscape uses the 4-column grid with the same order):

| Layout id | Name | Header | Column assignment (reading order) |
| --- | --- | --- | --- |
| `three-columns` | Three columns | Full width | Col 1: Background, Objectives, Methods · Col 2: Results (Figure 1, Table 1, text) · Col 3: Figure 2, Conclusions (callout), References, Contact & QR |
| `hero-figure` | Hero figure | Full width | Hero figure spanning all columns (≈ 30% of content height) · then Col 1: Background, Methods · Col 2: Results · Col 3: Conclusions (callout), References, Contact & QR |
| `big-finding` | Big finding | Full width | 4-column grid · Col 1: Background, Methods · Cols 2–3 (span 2): key-finding callout (`size.h1`) + key figure · Col 4: Results detail, Conclusions, References, Contact & QR |

**Other kinds**

| Kind | Layout A | Layout B |
| --- | --- | --- |
| Flyer | Headline + hero image top half; body + call to action; logo strip footer | Two columns: left image/figure, right headline, body, QR |
| Handout | Title, summary callout, key figure (full width), two-column details, contacts | Two-column brief: left summary + methods, right figure + conclusions |
| Programme booklet | Cover (primary background), day divider pages, 2-column programme with repeating session blocks (mockup 12) | Same with 1-column programme |
| Certificate | Centred: logo strip, "CERTIFICATE OF ATTENDANCE" in `accent` letter-spaced caps, `{{full_name}}` in `size.h1` heading font, event line, signatures (mockup 07) | Left-aligned with `accent` bar at the left edge |
| Badge | Name `{{full_name}}` 28 pt, affiliation `{{affiliation}}`, role colour bar (`accent`) | Name + QR `{{qr}}` right |
| E-poster | As poster `three-columns` on 16:9 | As poster `hero-figure` on 16:9 |

Placeholders use the text `[Section name — what goes here]` in `color.muted`, italic, and are flagged by the empty-placeholder preflight rule (T7.2).

## 6. Figure palettes

| Palette id | Colours (in order) | Notes |
| --- | --- | --- |
| `okabe-ito` (default) | #000000, #E69F00, #56B4E9, #009E73, #F0E442, #0072B2, #D55E00, #CC79A7 | Colour-blind safe; drop #F0E442 for lines on white |
| `viridis` (5) | #440154, #3B528B, #21918C, #5EC962, #FDE725 | Continuous / ordered |
| `cividis` (5) | #00204D, #414D6B, #7C7B78, #BCAF6F, #FFEA46 | Continuous, CVD-uniform |
| `grey` (5) | #111111, #444444, #777777, #AAAAAA, #DDDDDD | Print in black only |
| `theme` (4) | primary, accent, muted, tint mixed 40% with primary | Must pass the T7.5 distinguishability check or the UI warns |

Mockup 09 shows the palette strip twice: normal and "As seen with deuteranopia" (simulation per Specification §8, Machado et al. 2009 matrices, severity 1.0).

## 7. Export theme to R (T4.11)

Menu and button "Export theme to R…" write `frisket_theme.R` (mockup 09 caption). The file must contain, in this order:

1. A header comment: document name, theme name, generation date (ISO), and the recommended export line `ggsave("figure.pdf", width = <placed width in cm>, height = <height in cm>, units = "cm", device = cairo_pdf)`.
2. `frisket_palette_discrete <- c(...)` — the chosen figure palette, hex strings.
3. `frisket_palette_continuous <- c(low, high)` — viridis endpoints, or theme primary → tint.
4. `theme_frisket <- function(base_size = <pt>, base_family = "<body font>")` returning `ggplot2::theme_minimal(base_size, base_family) + ggplot2::theme(...)`: `base_size` = the document's `size.caption` × (placed figure width ÷ export width; 1 when unknown); text colour = `color.text`; axis and grid lines = `color.muted` at 40% alpha; plot title colour = `color.primary`.
5. `scale_colour_frisket <- function(...) ggplot2::scale_colour_manual(values = frisket_palette_discrete, ...)` and `scale_fill_frisket` likewise.

The file uses only base R and `ggplot2::` calls (no `library()` calls). It must parse with `Rscript -e 'parse("frisket_theme.R")'` (T4.11 acceptance).

## 8. Theme JSON (`resources/themes/<id>.json`, owned by `frisket-model`)

```json
{
  "id": "clinical-navy",
  "name": "Clinical navy",
  "version": 1,
  "palette": {
    "primary": "#1F3A5F", "onPrimary": "#FFFFFF", "accent": "#AD4C0D",
    "surface": "#FFFFFF", "tint": "#E8EEF6", "text": "#1D1D1F",
    "muted": "#5E5E63", "rule": "#1F3A5F"
  },
  "typePairing": "classic",
  "figurePalette": "okabe-ito",
  "defaults": { "viewingDistance": "1.5m", "showReadingOrderBadges": false }
}
```

A document stores a **copy** of its theme (Specification §7), so editing a built-in theme file later never changes existing documents.

## 9. Canvas chrome

Colours the editor draws on top of the page in the webview. Never exported or printed, never part of a theme. Defined once as CSS custom properties in `app/src/lib/styles/chrome.css`.

| Element | Light | Dark | Notes |
| --- | --- | --- | --- |
| App accent, selection outline and handles | #0A5FC4 | #4C8DFF | Handles 8 × 8 px, 1 px white border, constant screen size at any zoom |
| Smart guides while dragging (T1.9) | #FF2D55 | #FF375F | 1 px |
| Ruler guides (T1.12) | #32ADE6 | #64D2FF | 1 px, across the whole canvas |
| Overflow / warning marker | #C2410C | #FB923C | Dashed 1.5 px outline + "+" badge (mockup 03) |
| Insertion marker (Flow drop) | #0A5FC4 | #4C8DFF | 3 px bar |
| Margin and column guides | #0A5FC4 at 35% | #4C8DFF at 35% | Dashed 1 px |
| Pasteboard | #E5E5EA | #1C1C1E | Behind pages |
| Rulers | 20 px thick; background = sidebar grey; ticks and labels in secondary text colour; major ticks 60% and minor 30% of thickness; labelled ticks ≥ 50 px apart in steps of 1, 2 or 5 × 10ⁿ of the display unit | | |

## 10. Shape defaults (T1.10)

| Shape | Fill | Stroke | Stroke width |
| --- | --- | --- | --- |
| Rectangle, ellipse | `tint` | `primary` | 2 pt |
| Line | none | `rule` | 2 pt |
| Arrow | none | `accent` | 2 pt |

- Colours are stored as theme tokens, so a theme change recolours shapes; the inspector can set any token or a custom sRGB colour.
- Dash styles: solid; dashed = 3 × width on, 2 × width off; dotted = round dots 2 × width apart.
- Arrowheads: filled triangle in the stroke colour, 4 × stroke width long (at least 6 pt) and 3 × width wide, tip at the line end.
- Corner radius 0, opacity 100%.

## 11. Callout (T3.6)

| Part | Value |
| --- | --- |
| Box | `tint` fill, square corners, no border |
| Padding | `space.l` on all four sides |
| Key figure (optional) | `size.h1`, bold, `accent`, above the heading |
| Heading (optional) | `size.h3`, bold, `primary`, heading font |
| Body | `size.body`, `text`, the block's own story |
| Gaps between parts | `space.s` |

Empty key figures and headings take no space.
