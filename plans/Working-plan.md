# Frisket — Working plan

Task-level breakdown of [Specification.md](Specification.md) §10. Each phase ends in a runnable build on Gitea. P0–P3 are detailed; later phases are listed at deliverable level and get detailed when the previous phase closes. Size: S ≈ 1 unit, M ≈ 2, L ≈ 3–4.

Each task: **id · deliverable · where · acceptance**.

## P0 Foundations and spikes (M)

Exit: blank A0 page renders from Typst in a document tab; CI green on Gitea.

### Setup

| Id | Deliverable | Where | Acceptance |
| --- | --- | --- | --- |
| T0.1a | Cargo workspace with empty crates (`frisket-model`, `-format`, `-flow`, `-typeset`, `-render`, `-import`, `-features`, `-cli`), `xtask`, pinned toolchain, `#![forbid(unsafe_code)]` | `Cargo.toml`, `crates/`, `xtask/`, `rust-toolchain.toml` | `cargo test --workspace` passes |
| T0.1b | Tauri 2 + Svelte 5 + Vite + pnpm app; single window with overlay title bar and a tab strip (Home placeholder, `+`, Settings) | `app/` | `pnpm tauri dev` opens one window with working tabs |
| T0.1c | specta / tauri-specta bindings; `cargo xtask bindings --check` | `app/src/lib/bindings.ts` | Stale bindings fail CI |
| T0.1d | Gitea Actions: `core`, `ui`, `app` jobs; `cargo deny` with permissive-only allowlist; `license-checker` | `.gitea/workflows/`, `deny.toml` | All jobs green; adding a GPL crate fails CI |
| T0.1e | Bundled fonts (Liberation Sans/Serif, Carlito, Caladea, Lora, NCM Math) with licence files; `THIRD_PARTY.md` generation | `fonts/`, `xtask` | Fonts load in the Typst `World`; third-party list generated |
| T0.1f | Mirror to GitHub `ma-brain/frisket` | Gitea push mirror | Pushes to Gitea `main` appear on GitHub |

### Spikes (each ends with an ADR in `docs/adr/`)

| Id | Question | Method | Pass criterion | Fallback |
| --- | --- | --- | --- | --- |
| T0.2 | Can a custom Typst `World` compile generated markup with bundled fonts and in-memory assets, no network? | Minimal `World`, compile an A0 page with text, SVG and PDF image | Compiles offline; SVG + PNG + PDF produced | — (blocking) |
| T0.3 | Can we get a layout map (block id → rects) from Typst output? | Label each placed block, read positions from the compiled frames | Rects match placement within 0.1 pt | Wrap each block in a measured `box` and place absolutely |
| T0.4 | Measurement speed and hyphenation coverage | Measure 50 blocks at column width with caching; check hyphenation for en, de, fr, ro | Re-measure one changed block < 20 ms; list of supported languages recorded | Ragged-right, no hyphenation for unsupported languages |
| T0.5 | Is SVG per page fast enough in WKWebView for an A0 poster with 6 vector figures? | Render reference poster, pan/zoom, measure frame times | 60 fps pan/zoom via CSS transform; re-render on settle < 150 ms | PNG tiles at lower zoom thresholds |
| T0.6 | Does a ProseMirror overlay feel right over Typst-rendered text? | Overlay on one text block with theme fonts loaded as web fonts; commit re-renders | Keystroke < 16 ms; visual jump on commit judged acceptable in a hands-on test | Edit in the inspector with live canvas |
| T0.7 | Can text thread between arbitrary Free frames in Typst? | Split one story across two absolutely placed frames of different sizes | Correct break and continuation, stable across edits | "Continued" frames split at paragraph boundaries |
| T0.8 | Tab and session model | Two document tabs + Home + Settings; open the same file twice; close with unsaved changes | Second open focuses existing tab; close prompts; no leaked sessions | — |

## P1 Model, format and canvas (L)

Exit: draw, move, undo, save, reopen identical; format 1.0 frozen.

| Id | Deliverable | Where | Acceptance |
| --- | --- | --- | --- |
| T1.1 | Model types (§7 entities), typed UUID v7 ids, units, JSON Schema via schemars | `frisket-model` | Schema generated and committed as `schema/frisket-1.0.schema.json` |
| T1.2 | `Command` enum with apply + invert; undo/redo stack per session | `frisket-model`, shell | proptest: apply ∘ invert = identity |
| T1.3 | `.frisket` read/write per [File-format-contract.md](File-format-contract.md): container, manifest, deterministic JSON, atomic save, unknown-field preservation | `frisket-format` | Round-trip byte-identical; crash-during-save test leaves original intact |
| T1.4 | Version handling: older (migrate + backup), newer minor, newer major (read-only) | `frisket-format`, UI sheet | Fixtures for each case; screen 11 sheets wired |
| T1.5 | Session registry, `doc_*` commands, `doc-changed` events, `rev` handling | `app/src-tauri` | Stale renders discarded in a test |
| T1.6 | Canvas viewer: pasteboard, SVG layer, overlay layer, zoom/pan (⌘+scroll/pinch to pointer, Space+drag, ⌘0/⌘1, bottom-right control, status bar) | `app/src` | Playwright: zoom keeps the point under the pointer fixed |
| T1.7 | Free-mode frames: create, move, resize, snap, lock, z-order | model + UI | Undo restores exact geometry |
| T1.8 | Autosave (30 s, blur), crash recovery sheet (restore as tabs), snapshots (max 50) | shell, app data | Killed process recovers ≤ 30 s of work |
| T1.9 | Compat corpus `fixtures/compat/1.0/`; freeze format 1.0 | `fixtures/` | CI compat job green |

## P2 Text and styles (L)

| Id | Deliverable | Acceptance |
| --- | --- | --- |
| T2.1 | Rich-text node schema (Rust) mirrored in ProseMirror; round-trip test | Every node and mark round-trips |
| T2.2 | Typst codegen for stories; paragraph and character styles bound to theme tokens | Codegen snapshots (insta) |
| T2.3 | Overlay editor per T0.6 outcome; typing coalescing into undo | Targets: keystroke < 16 ms, re-render < 150 ms |
| T2.4 | Multi-column text within a block; overset detection and indicator | Overset flagged in outline and canvas |
| T2.5 | Font menu (built-in first, then system fonts), size, colour, align (screen 02) | Matches mockup 02 |
| T2.6 | Spell check, find and replace, special characters palette | Manual checklist |

## P3 Structure and themes (L)

| Id | Deliverable | Acceptance |
| --- | --- | --- |
| T3.1 | Flow solver: columns, spans, order, overflow, auto-arrange, balancing | Golden tests (insta JSON) |
| T3.2 | Measurement cache (content hash + width + theme hash) | Structural relayout < 100 ms on reference poster |
| T3.3 | Outline sidebar with drag reorder and status tags | Outline order = reading order |
| T3.4 | Block types: title/header, text section, callout, logo strip, shapes | Each renders from fixture |
| T3.5 | Themes (6 built-in), viewing-distance type scale, Theme view (screen 09 without brand kit) | Re-theme live on reference poster |
| T3.6 | Home board (screen 01): cards, filters, recents, search, Blank A4 default, Create/Return/double-click | Playwright flow: Home → Blank A4 → tab opens |
| T3.7 | Templates per kind (3 layouts × 6 themes); Save as template | Each template opens and renders |

## P4–P10 (deliverable level)

| Phase | Main tasks |
| --- | --- |
| P4 Figures and the R link | Image blocks (PDF/SVG vector, raster, TIFF→PNG), fit/crop, watched folders (`notify`, 300 ms debounce), Linked files view (screen 06), automatic relink by name + SHA-256, captions and numbering, icon library, brand kit, photo adjustments |
| P5 Scientific content | Tables (CSV/TSV/XLSX, paste), equations (LaTeX via MiTeX, Typst math), citations and References view (screen 08), QR codes, CONSORT/PRISMA builder, cross-references |
| P6 Export and CLI | Print PDF with bleed, crop marks, TrimBox/BleedBox; screen PDF; PNG/JPEG; A4 handout; Export sheet (screen 05); `frisket` CLI (export, relink, preflight JSON, merge, upgrade); tag 0.1 |
| P7 Preflight | Rule engine, all checks, fixes as commands, distance preview, CVD simulation, conference presets, Preflight mode (screen 04) |
| P8 Multi-page and merge | Page templates, page numbers, running headers, TOC, Document Flow across pages, booklet view (screen 12), data merge (screen 07), imposition |
| P9 Import | DOCX, MD/QMD, clipboard HTML, PPTX with "Convert to structured layout"; tag 0.5 |
| P10 Assistant, polish, release | Assistant (local endpoint), accessibility pass, performance targets, onboarding sample, updater, Settings tab complete (screen 10), licence decision applied (LICENSE, headers, notarization if commercial); tag 1.0 |
