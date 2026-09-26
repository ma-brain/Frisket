# Frisket — Working plan for implementation

This plan breaks [Specification.md](Specification.md) into numbered tasks that an implementing agent executes **one task per session**. Frisket starts from an empty repository; no code is carried over from the earlier Quoin (AppKit) attempt.

**Which document decides what** (binding, in this order when they disagree):

1. [Specification.md](Specification.md) — behaviour, architecture, stack, dependencies.
2. [File-format-contract.md](File-format-contract.md) — everything written to disk.
3. [THEMES.md](THEMES.md) — every colour, font, size, margin and spacing value.
4. This file — task order, scope per task, files, steps and acceptance.
5. Mockups in `../ui/` — layout and wording. If a mockup disagrees with 1–3, 1–3 win.

`TASKS.csv` lists every task (id, phase, title, depends_on, spec_refs, size) for creating Gitea issues. It is generated from this file by `python3 plans/tasks_csv.py` (which also checks that every dependency exists and comes earlier); never edit it by hand.

## 1. Instructions for the implementing agent

### Session loop

1. Read `CLAUDE.md`, then the task, its "Depends on" tasks, and every Specification / THEMES section it cites.
2. Check that every dependency is merged on `main`. If one is not, stop and say which.
3. Restate the task's acceptance criteria in your first message, before writing code.
4. Write or update tests first. They must fail before the implementation (show the failing run).
5. Implement the smallest change that makes them pass. Touch only the files listed under **Files**; if another file must change, say why in the pull request.
6. Run `make check`. Everything must pass with zero warnings.
7. Commit on a branch named `t<ID>-<slug>` (e.g. `t1.9-selection`), push to Gitea, open a pull request titled `T1.9: Hit testing and selection`.
8. In the pull request, paste the acceptance checklist with each item ticked and how it was verified (test name, command, or manual step).
9. Stop. Do not start the next task in the same session.

### Hard rules

- **Format.** Never change what is written to a `.frisket` file without following the checklist in File-format-contract §10 (version bump, schema file, migration, fixture). Before format 1.0 is frozen (T1.17), bump nothing but still update `schema/frisket-1.0.schema.json`.
- **Format versions after 1.0 is frozen.** A phase changes the format version at most once: the first task in a phase that changes the model bumps the minor version (1.1 in P2, 1.2 in P3, …) and adds the new schema file; later tasks in the same phase extend that same version and schema file. Compatibility fixtures for the version are added by the phase's last format-changing task. A major bump needs an ADR approved by the owner first.
- **Dependencies.** Never add a crate or npm package that is not in Specification §6 "Third-party dependencies" or in §2 "Toolchain" below. Ask instead. `cargo deny` and `license-checker` enforce the permissive-only rule.
- **Layering.** Never put Tauri, webview or UI code in `crates/`. Only `frisket-typeset` and `frisket-render` may depend on Typst crates. `frisket-model` depends only on `serde`, `serde_json`, `uuid`, `schemars`, `thiserror`.
- **State.** Rust owns the document. Svelte code never mutates document data; every edit is a `Command` sent through `doc_apply`. The only exception is the text inside the overlay editor while the user types (T2.4).
- **Types across the bridge.** Never hand-write a TypeScript type for a Rust struct. Regenerate `app/src/lib/bindings.ts` with `cargo xtask bindings` and commit it.
- **Safety.** Every crate has `#![forbid(unsafe_code)]`. No `unwrap()`/`expect()` outside tests and `xtask`, except on values that are provably infallible, with a comment saying why.
- **Build output location.** Never assume the Cargo target directory is `./target`; it may be on an external disk via `CARGO_TARGET_DIR` or `build.target-dir`. Scripts, `xtask` and workflows read it from `cargo metadata --format-version 1` (`target_directory`).
- **Tests.** Never delete, skip (`#[ignore]`, `.skip`) or weaken a failing test to make CI green. Report it in the pull request instead.
- **Typst.** Never store Typst markup in the document model or the file. Typst code is generated at runtime only (`frisket-typeset::codegen`). Every user string placed in generated markup goes through `codegen::escape` (T0.7).
- **Values.** Never invent a colour, size, margin or font. Take it from THEMES.md; if it is missing, ask.
- **Ambiguity.** If the task is ambiguous, write the question at the top of the pull request and implement the simplest reading that satisfies the acceptance criteria.

### When you are stuck

- After two failed attempts at the same error, stop and write a short report in the pull request: what you tried, the exact error, the smallest reproduction.
- For Typst APIs, read the source of the pinned version (`cargo doc -p typst --open` or the crate source under `~/.cargo/registry`). Do not rely on memory: the API changes between versions. Cite the item path in a code comment when behaviour is non-obvious.
- For Tauri 2, use the v2 documentation only (v1 APIs differ).

## 2. Conventions and definition of done

These apply to every task without being repeated.

### Toolchain

| Item | Value |
| --- | --- |
| Rust | Latest stable at T0.2, pinned in `rust-toolchain.toml` (channel + `rustfmt`, `clippy`) |
| Edition | 2021 for all crates |
| Node / pnpm | Node LTS pinned in `app/.nvmrc`; pnpm pinned via `packageManager` in `app/package.json` |
| Tauri | 2.x (`tauri`, `tauri-build`, `@tauri-apps/api`, `@tauri-apps/cli`), exact versions pinned at T0.3 |
| Typst | `typst`, `typst-pdf`, `typst-svg`, `typst-render` pinned with `=` at T0.7; same version for all four |
| Test-only crates allowed | `insta` (snapshots), `proptest`, `tempfile`, `assert_cmd`, `predicates`, `criterion`, `image-compare` |
| Utility crates allowed | `thiserror`, `anyhow` (binaries and xtask only), `tracing`, `tracing-subscriber`, `tokio` (app shell only), `sha2`, `hex`, `indexmap`, `once_cell`, `camino` |
| UI dev packages allowed | `vitest`, `@testing-library/svelte`, `jsdom`, `@playwright/test`, `eslint` + `eslint-plugin-svelte`, `prettier` + `prettier-plugin-svelte`, `svelte-check`, `typescript` |
| Versions | Every exact version chosen is recorded in `docs/adr/0002-toolchain-versions.md` (T0.2/T0.3/T0.7) |

### Repository layout (binding)

```text
Cargo.toml                 workspace; [workspace.dependencies] holds every version
rust-toolchain.toml  deny.toml  Makefile  CLAUDE.md  README.md  THIRD_PARTY.md
crates/
  frisket-model/           src/{lib.rs, ids.rs, geom/, units/, document/, command/, text/, theme/, blocks/, assets/, history.rs}
  frisket-format/          src/{lib.rs, container.rs, manifest.rs, read.rs, write.rs, migrate/, version.rs}
  frisket-flow/            src/{lib.rs, solver.rs, arrange.rs, balance.rs}
  frisket-typeset/         src/{lib.rs, world.rs, fonts.rs, codegen/, measure.rs, compile.rs, layout_map.rs, cache.rs}
  frisket-render/          src/{lib.rs, svg.rs, png.rs, pdf/, handout.rs, impose.rs, cvd.rs}
  frisket-import/          src/{lib.rs, tree.rs, apply.rs, docx/, markdown/, pptx/, table/, bib/, clipboard.rs}
  frisket-features/        src/{lib.rs, preflight/, merge/, watch/, assistant/, rtheme.rs, find.rs, links.rs}
  frisket-cli/             src/main.rs, src/cmd/
app/
  package.json  vite.config.ts  svelte.config.js  tsconfig.json  playwright.config.ts
  src/                     main.ts, App.svelte, lib/{bindings.ts, ipc.ts, strings.ts, stores/, styles/}, tabs/, workspace/, canvas/, editor/, sheets/, views/, settings/, home/
  src-tauri/               Cargo.toml, tauri.conf.json, capabilities/, src/{main.rs, lib.rs, session.rs, registry.rs, commands/, events.rs, menu.rs, error.rs}
resources/                 themes/, rules/, templates/, csl/, icons/, presets/, samples/
fonts/                     <Family>/ font files + licence file
schema/                    frisket-1.0.schema.json …
fixtures/                  compat/, format/, text/, layout/, figures/, tables/, citations/, preflight/, merge/, import/, reference/, snapshots/
xtask/                     src/main.rs (bindings, schema-check, deps-check, templates, tasks-csv, fixtures)
docs/                      adr/, format/, smoke.md, cli.md, user-guide/
.gitea/workflows/          ci.yml, nightly.yml, release.yml
```

### Rust conventions

- One concept per module; module file name = the main type in snake case (`page_size.rs` → `PageSize`).
- Model types derive `Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema` (and `Eq, Hash` where possible). Types crossing IPC also derive `specta::Type`; `specta` is an optional feature `ipc` of `frisket-model` so the core stays UI-free.
- Identifiers are typed newtypes over UUID v7: `pub struct BlockId(pub Uuid);` (`PageId`, `StoryId`, `AssetId`, `StyleId`, `TemplateId`, `DocId`). Generated with `Uuid::now_v7()` behind `ids::new_*()`; tests use a deterministic generator (`ids::testing::seq()`).
- Geometry: `f64` points in `frisket_model::geom::{Pt, Point, Size, Rect, Insets}`. Conversions to mm/in/px only in `frisket_model::units` and the UI.
- JSON field names are `camelCase` (`#[serde(rename_all = "camelCase")]`); enums are tagged `#[serde(tag = "type")]` with `camelCase` variants.
- Colours in the model: `ColorRef::Token(ThemeToken)` or `ColorRef::Srgb(u8, u8, u8)`; never platform colour types.
- Errors: one `thiserror` enum per crate (`ModelError`, `FormatError`, …); the shell maps them into `AppError { code, message, detail }` for IPC.
- Public items get a one-line `///` doc comment.

### Svelte / TypeScript conventions

- Svelte 5 runes only (`$state`, `$derived`, `$effect`, `$props`); no legacy `export let` or stores API except `svelte/store` in `lib/stores/` where cross-component state is needed.
- TypeScript `strict: true`, no `any` (ESLint rule `@typescript-eslint/no-explicit-any: error`).
- All IPC goes through `app/src/lib/ipc.ts` wrappers over the generated bindings; components never call `invoke` directly.
- All user-facing strings live in `app/src/lib/strings.ts` as a single exported object (English only; see Specification F14).
- Chrome colours and sizes come from CSS custom properties in `app/src/lib/styles/` (THEMES §9 for canvas chrome; Specification §5 "Visual language" for the rest).
- Every interactive element has an accessible name (`aria-label` or visible label).

### Test conventions

- Rust unit tests next to the code (`#[cfg(test)] mod tests`); integration tests in `crates/<crate>/tests/`.
- Fixtures live under `fixtures/<area>/` and are loaded through `frisket_model::testing::fixture("area/name")` (a helper that resolves from the workspace root); never absolute paths.
- Snapshots: `insta` for JSON/text (`*.snap` next to tests, reviewed in the pull request); PNG snapshots in `fixtures/snapshots/` compared with `image-compare`: pass when ≤ 0.5% of pixels differ by more than 2/255. Re-record with `RECORD=1 make test` and say so in the pull request.
- Flow and layout goldens are JSON so diffs are readable.
- UI: Vitest + testing-library for components and stores (`app/src/**/*.test.ts`); Playwright flows in `app/e2e/` run against `pnpm build && pnpm preview` with IPC mocked by `@tauri-apps/api/mocks` (`app/e2e/mocks/ipc.ts`).

### Make targets (binding names)

| Target | Runs |
| --- | --- |
| `make check` | `fmt-check lint test deny schema-check bindings-check deps-check ui-check` |
| `make test` | `cargo test --workspace` and `pnpm -C app test` |
| `make lint` | `cargo clippy --workspace --all-targets -- -D warnings`, `pnpm -C app lint` |
| `make ui-check` | `pnpm -C app check` (svelte-check) and `pnpm -C app test` |
| `make e2e` | `pnpm -C app e2e` |
| `make dev` | `pnpm -C app tauri dev` |
| `make build` | `pnpm -C app tauri build` |

### Commits and headers

- Conventional commits with the task id: `feat(flow): stack blocks in columns (T3.2)`.
- Every source file starts with `// Copyright (c) 2026 Marius A. All rights reserved.` (Rust/TS/Svelte comment syntax as appropriate). No SPDX licence identifier until the licence is decided (Specification §1).

### Definition of done

- [ ] All acceptance criteria of the task are met and listed in the pull request with how each was verified.
- [ ] New code is covered by tests at the level the task specifies.
- [ ] `make check` passes locally and in CI; zero compiler, clippy and svelte-check warnings.
- [ ] No format change without the File-format-contract §10 checklist.
- [ ] `app/src/lib/bindings.ts` regenerated if any IPC type changed.
- [ ] ADR added in `docs/adr/NNNN-<slug>.md` if the task made a decision the Specification left open.
- [ ] No new dependency outside the allowed lists.

## 3. P0 — Foundations and spikes

P0 produces a buildable repository, green CI, a single window with tabs and a blank A0 page rendered by Typst in a document tab, then answers six technical questions (spikes A–F) before features begin. Spike code lives in `spikes/<name>/` as standalone Cargo binaries excluded from the workspace default members and is never imported by the app. Each spike ends with an ADR that states the decision; later tasks follow the ADR.

### T0.1 Repository skeleton

- **Depends on:** none. **Spec:** §11.
- **Files:** `README.md`, `THIRD_PARTY.md`, `.gitignore`, `.gitattributes`, `CLAUDE.md` (already present; do not rewrite), `docs/adr/0001-record-architecture-decisions.md`, `docs/format/README.md`, empty folders with `.gitkeep`: `crates/`, `app/`, `resources/`, `fonts/`, `schema/`, `fixtures/`, `spikes/`, `xtask/`, `docs/adr/`, `.gitea/workflows/`.
- **Steps:** README states purpose, macOS 14+ Apple Silicon target, "licence not yet decided — all rights reserved", and the unnotarized first-launch note (System Settings → Privacy & Security → Open Anyway). Configure Git LFS in `.gitattributes` for `fixtures/**/*.{pdf,png,jpg,jpeg,tiff,pptx,docx,xlsx,frisket}` and `fonts/**/*.{ttf,otf}`. ADR 0001 uses the Nygard template (Context, Decision, Consequences). `.gitignore` covers `target/`, `node_modules/`, `app/dist/`, `app/src-tauri/target/`, `.DS_Store`, `*.snap.new`.
- **Acceptance:**
    - [ ] Repository pushed to `git.twin-gray.ts.net`; `git lfs ls-files` runs without error.
    - [ ] No LICENSE file exists; README states the licence status.

### T0.2 Cargo workspace and crates

- **Depends on:** T0.1. **Spec:** §6 Crates and folders.
- **Files:** `Cargo.toml`, `rust-toolchain.toml`, `crates/*/Cargo.toml`, `crates/*/src/lib.rs` (and `frisket-cli/src/main.rs`), `xtask/Cargo.toml`, `xtask/src/main.rs`, `.cargo/config.toml` (alias `xtask = "run -p xtask --"`), `docs/adr/0002-toolchain-versions.md`.
- **Steps:** create the eight crates of the repository layout (§2) with the dependency graph of Specification §6 expressed as path dependencies only: model ← format, flow, import; model + flow ← typeset; typeset ← render; model + format + render + typeset ← features; features + format + render + import ← cli. Put every external version in `[workspace.dependencies]`. Each `lib.rs` starts with `#![forbid(unsafe_code)]` and `#![warn(missing_docs)]` and contains one placeholder test. Implement `cargo xtask deps-check`: runs `cargo metadata` and fails if any crate depends on a crate not allowed by the graph above, or if a crate other than typeset/render depends on a `typst*` crate.
- **Acceptance:**
    - [ ] `cargo build --workspace` and `cargo test --workspace` succeed.
    - [ ] Adding `frisket-typeset` as a dependency of `frisket-model` makes `cargo xtask deps-check` fail (demonstrated in the pull request, then reverted).

### T0.3 Tauri app shell with one window and tabs

- **Depends on:** T0.2. **Spec:** §5 (window, tab strip), F14. **UI:** `ui/01-home.png`, `ui/10-settings.png` (tab strip only).
- **Files:** `app/package.json`, `app/.nvmrc`, `app/vite.config.ts`, `app/svelte.config.js`, `app/tsconfig.json`, `app/index.html`, `app/src/main.ts`, `app/src/App.svelte`, `app/src/tabs/{TabStrip.svelte,tabs.svelte.ts,TabRouter.svelte}`, `app/src/home/HomePlaceholder.svelte`, `app/src/settings/SettingsPlaceholder.svelte`, `app/src/lib/strings.ts`, `app/src/lib/styles/{tokens.css,chrome.css}`, `app/src-tauri/{Cargo.toml,build.rs,tauri.conf.json}`, `app/src-tauri/capabilities/default.json`, `app/src-tauri/src/{main.rs,lib.rs,menu.rs}`.
- **Steps:** Svelte 5 + Vite + TypeScript template, pnpm. One window, `titleBarStyle: "Overlay"`, `hiddenTitle: true`, min size 1100 × 700; traffic lights inset into the 44 px tab strip (`trafficLightPosition`). Tab model in `tabs.svelte.ts`: `type Tab = { id: string; kind: "home" | "document" | "settings"; title: string; docId?: string; dirty: boolean }`; one Home tab at start; `+` adds a Home tab; `⌘T` new Home tab, `⌘W` close tab, `⌃Tab`/`⌃⇧Tab` cycle, `⌘,` opens or focuses the single Settings tab. Tab shows a dot when `dirty` and `×` on hover/active (mockup). Closing the last tab opens a Home tab (the window never closes by closing tabs). Native menu (menu.rs): Frisket, File, Edit, View, Window, Help with the shortcuts above; menu items emit events the UI handles. Capabilities: only `core:default` plus the app's own commands; no `fs` plugin.
- **Acceptance:**
    - [ ] `make dev` opens one window with a Home tab; `+`, `⌘T`, `⌘W`, `⌃Tab`, `⌘,` behave as described (Vitest tests for `tabs.svelte.ts`; manual check listed).
    - [ ] Closing the last tab leaves one Home tab; a Settings tab cannot be opened twice.

### T0.4 Typed IPC bindings

- **Depends on:** T0.3. **Spec:** §6 IPC contract.
- **Files:** `app/src-tauri/src/{commands/mod.rs,commands/app.rs,error.rs}`, `app/src/lib/{bindings.ts,ipc.ts}`, `xtask/src/bindings.rs`.
- **Steps:** add `specta` + `tauri-specta`. `AppError { code: String, message: String, detail: Option<String> }` implements `serde::Serialize` + `specta::Type`. Commands `app_info() -> AppInfo { version, build, formatVersion, typstVersion }` and `ping(msg: String) -> String`. `cargo xtask bindings` writes `app/src/lib/bindings.ts`; `cargo xtask bindings --check` regenerates into a temp file and fails if it differs. `ipc.ts` re-exports typed wrappers that unwrap `Result` into thrown `AppError`.
- **Acceptance:**
    - [ ] The Home placeholder shows the version from `app_info`.
    - [ ] Changing a field of `AppInfo` without regenerating makes `cargo xtask bindings --check` fail.

### T0.5 Make targets, linting and CI

- **Depends on:** T0.4. **Spec:** §11 CI on Gitea Actions.
- **Files:** `Makefile`, `deny.toml`, `rustfmt.toml`, `clippy.toml`, `app/eslint.config.js`, `app/.prettierrc`, `.gitea/workflows/{ci.yml,nightly.yml}`, `docs/ci-runner.md`.
- **Steps:** Make targets exactly as §2. `deny.toml`: `[licenses] allow = ["MIT","Apache-2.0","Apache-2.0 WITH LLVM-exception","BSD-2-Clause","BSD-3-Clause","ISC","Zlib","CC0-1.0","Unicode-3.0","Unicode-DFS-2016","MIT-0","BSL-1.0"]`, `confidence-threshold = 0.9`, deny copyleft; `[bans] multiple-versions = "warn"`. App licences checked with `pnpm dlx license-checker --production --onlyAllow "<same list, semicolon-separated>"` in `make deny`. `ci.yml` (on pull request and push to `main`): all jobs run on the self-hosted runner label `macos-arm64` in host mode (no Docker, no GitHub Actions). Job `core` → `make fmt-check lint test deny schema-check bindings-check deps-check`; job `ui` → `pnpm install --frozen-lockfile`, `make ui-check`, `make e2e`; job `app` on runner label `macos-arm64` → `make build`, upload `.dmg`. `nightly.yml` at 02:00: benchmarks (placeholder until T10.8) and the release-configuration build. `docs/ci-runner.md` documents installing `act_runner` in host mode as a LaunchAgent on the Mac, registering it with label `macos-arm64`, and setting build environment variables in its `config.yaml` (`runner.envs`) because a LaunchAgent does not read shell profiles; an optional later Linux runner in Docker is described in one section.
- **Acceptance:**
    - [ ] A pull request shows green `core`, `ui` and `app` checks.
    - [ ] A misformatted Rust file fails `make lint`/`fmt-check`; adding a GPL-licensed crate fails `make deny` (shown, then reverted).

### T0.6 Bundled fonts and the Typst World

- **Depends on:** T0.2. **Spec:** F5 fonts, §6 Typst integration. **Design values:** THEMES §2.
- **Files:** `fonts/<Family>/*`, `THIRD_PARTY.md`, `crates/frisket-typeset/src/{world.rs,fonts.rs}`, `crates/frisket-typeset/tests/world.rs`.
- **Steps:** download the families and weights listed in THEMES §2 from their official sources (Liberation 2.x from the liberationfonts GitHub releases, Carlito and Caladea from Google Fonts/their upstream repos, Lora static files from the Cyreal/Google Fonts repo, Latin Modern Math from GUST); verify each licence file and record source URL + version + SHA-256 in `THIRD_PARTY.md`. `fonts.rs`: `BundledFonts` embeds every file with `include_bytes!` and builds a Typst `FontBook`; `SystemFonts::discover()` scans system font folders once (macOS: `/System/Library/Fonts`, `/Library/Fonts`, `~/Library/Fonts`) and is optional (Settings toggle). `world.rs`: `FrisketWorld` implements `typst::World` with: main source (generated markup), bundled fonts first then system fonts, a `HashMap<FileId, Bytes>` of in-memory files (assets, bibliographies), `today()` fixed per compile, and **no package downloads** (any `@preview` import returns an error).
- **Acceptance:**
    - [ ] Test compiles `#set text(font: "Liberation Sans"); Hello` and each other bundled family; the PDF's font list contains exactly the requested family (checked with `lopdf`).
    - [ ] A document importing `@preview/anything` fails with a clear error, and no network access is attempted.

### T0.7 Walking skeleton: a Typst page in a document tab

- **Depends on:** T0.4, T0.6. **Spec:** §5 Canvas composition, §6 Layout pipeline. **UI:** `ui/02-blank-a4.png` (canvas only).
- **Files:** `crates/frisket-typeset/src/{compile.rs,codegen/mod.rs,codegen/escape.rs}`, `crates/frisket-render/src/svg.rs`, `app/src-tauri/src/commands/render.rs`, `app/src/canvas/{Canvas.svelte,PageLayer.svelte}`, `app/src/workspace/Workspace.svelte`.
- **Steps:** `codegen::escape(&str) -> String` escapes every Typst markup special character (`\ # * _ $ @ < > [ ] { } " ' = - + / ~ ` and leading list/heading markers) — table-driven tests with 40 cases. `compile(world) -> Result<PagedDocument, Vec<Diagnostic>>`. `render::svg::page(&doc, index) -> String`. Temporary command `demo_render(size: "a0"|"a4") -> String` (removed in T1.7). A File → New Blank menu item opens a document tab showing an A0 (2383.94 × 3370.39 pt) white page centred on the grey pasteboard; the page SVG is inserted inline with `{@html svg}`; this is safe only because the SVG is produced by Rust from generated markup and never contains user-supplied SVG verbatim (user SVG figures are embedded by Typst as images, not inlined).
- **Acceptance:**
    - [ ] A document tab shows a blank A0 page rendered by Typst; `demo_render` returns in < 50 ms (test with timing, release build).
    - [ ] Escape tests pass for all 40 cases, including `#import`, `$x$`, `<label>` and `@ref` in user text rendering literally.

### T0.8 Spike A — Layout map, block measurement and hyphenation

- **Depends on:** T0.7. **Spec:** §6 Layout pipeline, §12 Risks. **Files:** `spikes/layout-map/`, `docs/adr/0003-layout-map-and-measurement.md`.
- **Steps:** (1) Measurement: compile one block alone as `#set page(width: W, height: auto, margin: 0)` and read the page height; measure 50 text blocks of 50–300 words at 3 widths; time cold and cached. (2) Layout map: generate a page with 12 blocks placed via `#place(top + left, dx: X, dy: Y, block(width: W)[…]) <b-UUID>` (or `metadata` + label) and recover each block's rectangle from the compiled document through Typst's introspection API; compare with the intended rectangles. (3) Hyphenation: compile justified paragraphs with `#set text(lang: "en"|"de"|"fr"|"ro"|"es"|"it", hyphenate: true)` and list which languages hyphenate.
- **Acceptance:**
    - [ ] ADR records: measurement median/p95 per block (target < 20 ms uncached, < 1 ms cached), the exact introspection method used for the layout map and its accuracy (target ≤ 0.1 pt), and the list of hyphenating languages.
    - [ ] If introspection is not accurate enough, ADR adopts the fallback: the solver's intended rectangles are the layout map (blocks are placed absolutely, so they cannot move).

### T0.9 Spike B — Canvas rendering performance

- **Depends on:** T0.7. **Files:** `spikes/canvas-perf/` (a copy of the app shell rendering one page), `docs/adr/0004-canvas-rendering.md`.
- **Steps:** build a synthetic A0 poster: 12 text sections, 6 vector figures (ggplot2 PDFs from `fixtures/figures/`), 2 tables. Measure in WKWebView: SVG size, time to first paint, pan/zoom frame rate with CSS `transform: translate() scale()`, and memory; then PNG tiles of 512 px from `typst-render` at 100%, 200%, 400%.
- **Acceptance:**
    - [ ] ADR states the SVG/PNG switch zoom (Specification default 200%), pan/zoom fps (target 60), re-render time after zoom settle (target < 150 ms), and chooses the tile cache size.

### T0.10 Spike C — Overlay text editor

- **Depends on:** T0.7. **Files:** `spikes/overlay-editor/`, `docs/adr/0005-overlay-editor.md`.
- **Steps:** place a ProseMirror editor exactly over one text block of the rendered page, using the bundled fonts loaded as `@font-face` from the app bundle, the same size, line height and width. Type 200 words; on each 300 ms pause, send the text to Rust, re-render, and swap the page SVG behind the editor. Measure keystroke-to-paint in the editor and edit-to-Typst-render. Compare line breaks between the overlay and Typst.
- **Acceptance:**
    - [ ] ADR records keystroke p95 (target < 16 ms), re-render p95 (target < 150 ms), how often line breaks differ, and the decision: overlay editor (default) or fallback "edit in the inspector with live canvas".

### T0.11 Spike D — Story threading across frames

- **Depends on:** T0.8. **Spec:** F4, §12 Risks. **Files:** `spikes/threading/`, `docs/adr/0006-story-threading.md`.
- **Steps:** split one 1,500-word story across three absolutely placed frames of different sizes on two pages. Try (a) Typst `columns`/page flow with frames expressed as regions, (b) measuring line by line: lay out the story at frame 1's width, find the break position that fits its height, continue the remainder in frame 2 (paragraph-level split first, then line-level via Typst's `measure` on prefixes).
- **Acceptance:**
    - [ ] ADR picks one approach with evidence (correct breaks, stability across 20 random edits, time per relayout), or adopts the fallback "continued frames split at paragraph boundaries".

### T0.12 Spike E — Figures, math and citations in Typst

- **Depends on:** T0.7. **Files:** `spikes/content/`, `docs/adr/0007-figures-math-citations.md`, `fixtures/figures/km.R`.
- **Steps:** (1) Place `fixtures/figures/km.pdf` and `km.svg` (from `km.R`, ggplot2) with `image()` and export PDF; dump operators with `lopdf` to check vector paths and whether SVG text stays text or becomes paths. (2) Convert 10 LaTeX samples (fraction, sum, integral, matrix, Greek, sub/superscripts, `\frac{a}{b}` inline, `\hat{\beta}`, `\mathbb{R}`, aligned equations) with MiTeX to Typst math and render with Latin Modern Math. (3) Load a 100-entry BibTeX file into `bibliography()` with the bundled Vancouver CSL and cite 5 items; time it.
- **Acceptance:**
    - [ ] ADR: vector yes/no for PDF and SVG with operator evidence; list of LaTeX samples that fail (target 0); bibliography of 100 entries in < 200 ms; 5 hand-checked Vancouver entries match.

### T0.13 Spike F — Flow solver prototype

- **Depends on:** T0.2. **Spec:** F2. **Files:** `spikes/flow/`, `docs/adr/0008-flow-layout.md`.
- **Steps:** pure Rust function: inputs = column count, gutter, content rect, ordered blocks `{id, span, height_at(width), column_break_before, keep_with_next}`; output = rect per block + overflow list. Algorithm: **column-by-column flow in reading order** — fill column 1 top to bottom, move to the next column when the next block does not fit or has `column_break_before`; a block spanning k columns starts at the lowest bottom among the k columns it covers and occupies all of them. The column where a block lands follows from reading order only (it is not stored).
- **Acceptance:**
    - [ ] 12 blocks in 3 columns solve in < 1 ms; 10 hand-built cases produce the expected rectangles (JSON goldens); ADR describes the algorithm exactly as later implemented in T3.2.

## 4. P1 — Model, format and canvas

P1 builds the document model, commands and undo, the `.frisket` file format 1.0, the session and IPC layer, and a Free-mode canvas where shapes can be drawn, moved, undone, saved and reopened identically. Format 1.0 is frozen at the end of P1 (T1.17).

### T1.1 Geometry and units

- **Depends on:** T0.2. **Spec:** §7 (points as `f64`).
- **Files:** `crates/frisket-model/src/geom/{mod.rs,point.rs,size.rs,rect.rs,insets.rs,transform.rs}`, `crates/frisket-model/src/units/{mod.rs,unit.rs,length.rs,parse.rs,format.rs}`.
- **Steps:** `Pt(f64)`; `Point`, `Size`, `Rect { origin, size }` with `contains`, `intersects`, `union`, `inset`, `center`; `Transform` (translate, rotate about a point, apply to point/rect bounds). `Unit` = `Mm | Cm | In | Pt | Px`; px = 1 pt for print documents and 1 CSS px for screen documents (e-poster: 1 px = 0.75 pt so that 1920 px width = 1440 pt). `Length::parse("841 mm")`, `"48 in"`, `"1920px"`, `"12,5 mm"` (decimal comma accepted) and `Length::format(unit, decimals)`.
- **Acceptance:**
    - [ ] Round-trip conversion for all units within 1e-9 (proptest, 1,000 cases).
    - [ ] Parser accepts both decimal separators and rejects `"12 furlongs"` with a typed error.

### T1.2 Command system and history

- **Depends on:** T1.1. **Spec:** §6 Key technical decisions (model and undo).
- **Files:** `crates/frisket-model/src/command/{mod.rs,command.rs,composite.rs}`, `crates/frisket-model/src/history.rs`.
- **Steps:** `pub enum Command { … }` grows task by task; this task defines the machinery with a test-only variant. `trait Apply { fn apply(self, doc: &Document) -> Result<Applied, ModelError>; }` where `Applied { doc: Document, inverse: Command, label: &'static str, dirty: DirtySet }` (`DirtySet` = pages and blocks touched, used for re-render). `Command::Composite(Vec<Command>)` applies in order and inverts in reverse. `History { undo: Vec<Entry>, redo: Vec<Entry>, limit: 500 }` with `push(entry, coalesce_key: Option<String>, now: Instant)`: an entry with the same `coalesce_key` pushed within 1 s of the previous one merges (keeps the original inverse). `undo()`/`redo()` return the command to apply and the label for menus ("Undo Move").
- **Acceptance:**
    - [ ] Property test: 1,000 random command sequences applied then inverted restore the original document exactly (`PartialEq`).
    - [ ] Coalescing test: 10 moves with the same key within 1 s → one undo step; after a 1.1 s gap → two steps.

### T1.3 Core document model

- **Depends on:** T1.2. **Spec:** §7 Entities, §3 Document kinds.
- **Files:** `crates/frisket-model/src/document/{mod.rs,document.rs,kind.rs,page.rs,page_size.rs,catalog.rs,block.rs,placement.rs,layout_mode.rs,grid.rs}`, `crates/frisket-model/src/ids.rs`, `crates/frisket-model/src/command/{page.rs,block.rs}`, `schema/frisket-1.0.schema.json`, `xtask/src/schema.rs`.
- **Steps:** implement Document, Page, Block, Placement per Specification §7 with Story, Asset, Theme, Style, PageTemplate, Bibliography as empty placeholder structs (filled later). `DocumentKind` = `Poster | EPoster | Flyer | Handout | Booklet | Certificate | Badge | Blank`. `Placement` = `Flow(FlowPlacement)` | `Free(FreePlacement { rect, rotation_deg, z })` (Flow fields added in T3.1). `PageSize { name: Option<String>, width: Pt, height: Pt }`; `catalog.rs` holds ISO A0–A6, B4–B6, US Letter/Legal/Tabloid, 48×36 in, 36×24 in, 16:9 1920×1080 px and 3840×2160 px, badge 90×55 mm, DL. Commands: `AddPage`, `RemovePage`, `AddBlock`, `RemoveBlock`, `UpdateBlock` (whole-block replace), `ReorderBlock`. `cargo xtask schema` writes `schema/frisket-1.0.schema.json` from `schemars`; `cargo xtask schema-check` fails if the committed file differs.
- **Acceptance:**
    - [ ] Every command has an apply + inverse unit test.
    - [ ] `schema-check` passes and fails after an unregenerated model change (shown, then reverted).

### T1.4 File format 1.0: read and write

- **Depends on:** T1.3. **Spec:** File-format-contract §2, §3, §7.
- **Files:** `crates/frisket-format/src/{container.rs,manifest.rs,read.rs,write.rs,json.rs}`, `crates/frisket-format/tests/roundtrip.rs`, `fixtures/format/*.frisket`, `docs/format/1.0.md`.
- **Steps:** ZIP container exactly as contract §2 (`mimetype` first and stored). `json::to_canonical_vec(&Value)`: object keys sorted, 2-space pretty print, floats written with the shortest round-trip representation (`ryu`, via `serde_json` with `float_roundtrip`), trailing newline. Unknown fields are kept: every model struct has `#[serde(flatten)] pub extra: BTreeMap<String, Value>` (add now to all existing structs, and to every struct added later). `write(path, &Document, assets)` follows contract §7 steps 1–5 (temp file in the same folder, fsync, re-open and parse, rename). `read(path) -> Result<Opened, FormatError>` returns the document plus a `VersionStatus` (filled in T1.5).
- **Acceptance:**
    - [ ] Round trip: write → read → write is byte-identical for 5 fixture documents.
    - [ ] A simulated failure between steps 3 and 4 (test hook) leaves the original file byte-identical.
    - [ ] A document with an unknown field in a block keeps it after read → write.

### T1.5 Version handling, backups and unreadable files

- **Depends on:** T1.4. **Spec:** File-format-contract §4–§6. **UI:** `ui/11-file-dialogs.png` (older / newer cards).
- **Files:** `crates/frisket-format/src/{version.rs,migrate/mod.rs}`, `crates/frisket-format/tests/versions.rs`, `fixtures/format/{older-0.9.frisket,newer-minor-1.1.frisket,newer-major-2.0.frisket,corrupt.frisket}`.
- **Steps:** `VersionStatus = Current | Older{from} | NewerMinor{found} | ReadOnly{found}` per contract §5. Migration registry `fn migrate(value, from) -> Result<Value>` keyed by version, empty until the first post-1.0 change except a test-only 0.9 → 1.0 migration that proves the chain. `backup_path(original, from)` returns `name.v1-2.frisket` style names (contract §5). Unreadable file → `FormatError::Unreadable { reason }`.
- **Acceptance:**
    - [ ] Each fixture yields the expected `VersionStatus`; the 0.9 fixture opens after migration.
    - [ ] The corrupt fixture returns `Unreadable` and is never written.

### T1.6 Sessions, registry and document commands

- **Depends on:** T1.2, T1.4, T0.4. **Spec:** §6 IPC contract, Key technical decisions (state ownership, concurrency).
- **Files:** `app/src-tauri/src/{session.rs,registry.rs,events.rs}`, `app/src-tauri/src/commands/doc.rs`, `app/src/lib/stores/documents.svelte.ts`, `app/src/lib/ipc.ts`, `app/src-tauri/tests/session.rs`.
- **Steps:** `Session { id: DocId, path: Option<PathBuf>, doc: Document, history: History, rev: u64, saved_rev: u64, read_only: bool }` behind `tokio::sync::Mutex`; `Registry` maps `DocId → Arc<Mutex<Session>>` and canonical path → `DocId`. Commands (all `async`, `Result<T, AppError>`): `doc_new(kind, size) -> DocSummary`, `doc_open(path) -> OpenResult { summary, versionStatus }` (if the path is already open, return the existing `DocId` with `alreadyOpen: true`), `doc_save(doc)`, `doc_save_as(doc, path)`, `doc_close(doc)`, `doc_apply(doc, commands, coalesceKey?) -> DocDelta { rev, dirtyPages, outline, labels }`, `doc_undo(doc)`, `doc_redo(doc)`. Every applied edit bumps `rev` and emits `doc-changed { doc, rev, dirtyPages }`. Read-only sessions reject `doc_apply` and `doc_save` with `code: "readOnly"`. Save of an `Older` document writes the backup first (contract §5). Open/Save dialogs use `tauri-plugin-dialog` from Rust (the webview never receives arbitrary file-system access).
- **Acceptance:**
    - [ ] Rust tests: open the same path twice → one session; apply/undo/redo change `rev` monotonically; read-only rejects edits.
    - [ ] Vitest: the documents store ignores a `doc-changed` event whose `rev` is older than the current one.

### T1.7 Codegen v1, page rendering and layout map

- **Depends on:** T1.3, T0.8. **Spec:** §5 Canvas composition, §6 Layout pipeline.
- **Files:** `crates/frisket-typeset/src/{codegen/page.rs,codegen/block.rs,layout_map.rs,cache.rs}`, `crates/frisket-render/src/{svg.rs,png.rs}`, `app/src-tauri/src/commands/render.rs`, `crates/frisket-typeset/tests/codegen.rs` (insta).
- **Steps:** `codegen::page(&Document, PageId) -> String` emits `#set page(width, height, margin: 0)` and one absolutely placed element per block, following ADR 0003 for labels. Unknown block types render a grey placeholder box (contract §4 fallback). `layout_map(&PagedDocument) -> LayoutMap { blocks: Vec<(BlockId, Rect)> }` per ADR 0003. Compiled pages are cached per `(DocId, PageId, rev)`. Commands: `render_page(doc, page, format: "svg"|"png", zoom, rev) -> RenderedPage { rev, svg?, width, height }` (PNG returned as raw bytes through `tauri::ipc::Response`, T0.9 tiles), `layout_map(doc, page, rev) -> LayoutMap`. Remove `demo_render` from T0.7. Compile and render run in `spawn_blocking`; a request for a `rev` older than the session's current `rev` returns `code: "stale"` without rendering.
- **Acceptance:**
    - [ ] insta snapshots of generated Typst for an empty A4 page, a page with 3 rectangles, and a page with an unknown block type.
    - [ ] Layout-map rectangles match model rectangles within 0.1 pt for 3 fixtures.

### T1.8 Document workspace: layout, canvas, zoom and status bar

- **Depends on:** T1.6, T1.7, T0.9. **Spec:** §5 Window layout, Canvas navigation. **UI:** `ui/02-blank-a4.png`, `ui/03-poster-workspace.png`.
- **Files:** `app/src/workspace/{Workspace.svelte,Toolbar.svelte,Sidebar.svelte,Inspector.svelte,StatusBar.svelte}`, `app/src/canvas/{Canvas.svelte,Pasteboard.svelte,PageLayer.svelte,Overlay.svelte,ZoomControl.svelte,viewport.svelte.ts,GestureHint.svelte}`, `app/src/canvas/viewport.test.ts`.
- **Steps:** three-pane layout with exact sizes from Specification §5 (toolbar 52 px, sidebar 260 px, inspector 300 px, status bar 28 px), sidebar and inspector collapsible (`⌥⌘S`, `⌥⌘I`). Sidebar tabs Structure / Pages / Assets and inspector tabs (context rules of §5) render empty placeholder content for now. `viewport.svelte.ts`: `{ zoom, panX, panY }`, zoom clamped 0.1–8.0, `zoomAt(factor, screenPoint)` keeps the document point under the pointer fixed. Input: `⌘`+wheel and trackpad pinch (`wheel` with `ctrlKey`) zoom toward the pointer; plain wheel pans; Space+drag pans (cursor `grab`/`grabbing`); `⌘0` fit page, `⌘1` 100%, `⌘+`/`⌘−` step through 10, 25, 50, 75, 100, 150, 200, 300, 400, 800%. Zoom and pan are one CSS transform on the pasteboard; after 150 ms without zoom change, request a new render at the settled zoom (SVG below the ADR 0004 threshold, PNG tiles at or above it). Bottom-right `ZoomControl` (−, slider, +, percentage, "Fit page", "100%") and zoom in the status bar. First-use `GestureHint` bar (dismissed state stored in `localStorage` key `frisket.hint.gestures`).
- **Acceptance:**
    - [ ] Vitest: `zoomAt` keeps the pointer's document point fixed within 0.01 pt for 20 random cases; step list and clamps correct.
    - [ ] Playwright (mocked IPC): pinch, `⌘0`, `⌘1` and the slider change the zoom shown in the status bar; layout matches the mockup regions.

### T1.9 Hit testing and selection

- **Depends on:** T1.8. **Files:** `crates/frisket-model/src/document/hit.rs` (pure hit test on the layout map), `app/src/canvas/{selection.svelte.ts,SelectionOverlay.svelte,Marquee.svelte}`, `app/src-tauri/src/commands/hit.rs`.
- **Steps:** `hit_test(&LayoutMap, &Document, Point) -> Option<BlockId>` returns the topmost block by z, respecting rotation. Click selects; Shift toggles; drag on empty pasteboard or page draws a marquee selecting intersecting blocks. Selection lives in the tab's UI state (not in the document). Overlay draws the selection outline and 8 handles in screen pixels (THEMES §9) at any zoom.
- **Acceptance:**
    - [ ] Rust tests for hit testing with rotated and overlapping blocks.
    - [ ] Manual check at 10% and 800% zoom: handles stay 8 px.

### T1.10 Move, resize, rotate, nudge

- **Depends on:** T1.9. **Files:** `app/src/canvas/tools/{select.ts,drag.svelte.ts}`, `crates/frisket-model/src/command/transform.rs`.
- **Steps:** drag moves; handles resize (Shift keeps aspect, Option resizes from centre); rotation handle 24 px above the top edge (Shift snaps to 15°). Arrow keys nudge 1 pt, Shift+arrow 10 pt. During a drag the overlay previews locally; on release one `SetFrame { block, rect, rotation }` command is sent (coalesce key `drag:<blockIds>`). Nudges coalesce with key `nudge:<blockIds>`.
- **Acceptance:**
    - [ ] Command-level tests: move, resize, rotate then undo restore exact geometry.
    - [ ] One drag = one undo step (Playwright with mocked IPC counts `doc_apply` calls = 1).

### T1.11 Rulers, guides and display unit

- **Depends on:** T1.8. **Design values:** THEMES §9. **Files:** `app/src/canvas/{Rulers.svelte,rulerTicks.ts,Guides.svelte}`, `crates/frisket-model/src/document/guide.rs`, `crates/frisket-model/src/command/{guide.rs,display_unit.rs}`.
- **Steps:** horizontal and vertical rulers (toggle `⌘R`) in the document's display unit (document field `displayUnit`). Drag from a ruler creates a guide stored on the page; drag a guide to move it; drag it back onto a ruler to delete it. Guides are snap targets (T1.12). The status bar shows page size in the display unit and a unit menu that changes it (one command).
- **Acceptance:**
    - [ ] `rulerTicks` unit tests: labelled ticks ≥ 50 px apart, steps of 1/2/5 × 10ⁿ.
    - [ ] Guides survive save/reopen; changing the unit updates rulers and status bar.

### T1.12 Snapping, smart guides, align and distribute

- **Depends on:** T1.10, T1.11. **Files:** `crates/frisket-model/src/snap.rs`, `app/src/canvas/{SmartGuides.svelte,snap.ts}`, `crates/frisket-model/src/command/align.rs`.
- **Steps:** `snap(candidate_rect, targets, threshold_pt) -> SnapResult { delta, guides }` in Rust (exposed via a synchronous-feeling command called at most once per animation frame; or ported 1:1 to TS if the round trip exceeds 8 ms — measure and record in the PR). Targets: page edges, margins, page centre, other blocks' edges and centres, ruler guides; threshold 6 screen px converted to pt at the current zoom. Holding `⌘` disables snapping. Smart guides drawn in THEMES §9 colour. Align left/centre/right/top/middle/bottom and distribute horizontally/vertically for 2+ selected blocks, each one command.
- **Acceptance:**
    - [ ] Unit tests for each target type and for `⌘` disabling snapping.
    - [ ] Align and distribute tested with inverses.

### T1.13 Shapes and basic appearance

- **Depends on:** T1.10. **Design values:** THEMES §10. **Files:** `crates/frisket-model/src/blocks/shape.rs`, `crates/frisket-typeset/src/codegen/shape.rs`, `app/src/canvas/tools/shape.ts`, `app/src/workspace/inspector/ShapeInspector.svelte`.
- **Steps:** rectangle (corner radius), ellipse, line, arrow (start/end heads). Tool buttons in the toolbar (shape tool of mockup 02). Draw by drag; Shift constrains. Defaults exactly THEMES §10. Inspector: fill, stroke colour (theme token picker + custom sRGB), stroke width, dash, opacity.
- **Acceptance:**
    - [ ] PNG snapshots for each shape with stroke and fill variants.
    - [ ] Changing the theme token of a shape's fill is one undo step.

### T1.14 Z-order, group, lock

- **Depends on:** T1.10. **Files:** `crates/frisket-model/src/command/{arrange.rs,group.rs,lock.rs}`, `crates/frisket-model/src/blocks/group.rs`.
- **Steps:** bring forward/backward/to front/to back (`⌥⌘]`, `⌥⌘[`, `⇧⌘]`, `⇧⌘[`); group/ungroup (`⌘G`, `⇧⌘G`) — a group block holds children placed in the group's coordinate space; lock (`⌘L`) prevents canvas selection (still selectable in the outline).
- **Acceptance:**
    - [ ] Commands tested with inverses; a locked block ignores canvas clicks.

### T1.15 Clipboard

- **Depends on:** T1.6, T1.10. **Files:** `app/src-tauri/src/clipboard.rs`, `app/src-tauri/src/commands/clipboard.rs`, `app/src/canvas/clipboard.ts`.
- **Steps:** copy/cut/paste/duplicate (`⌘C`, `⌘X`, `⌘V`, `⌘D`) of selected blocks. The block clipboard lives in the Rust app state (shared across all tabs of the one window) as JSON of the blocks plus the stories and embedded assets they reference; IDs are regenerated on paste. The system clipboard receives the plain text of any text in the copied blocks (via the webview Clipboard API) so pasting into other apps gives text. Paste onto the same page offsets by 10 pt (cumulative for repeated pastes); onto another page keeps coordinates.
- **Acceptance:**
    - [ ] Copy between two document tabs preserves blocks exactly (geometry, appearance, text); IDs differ.
    - [ ] Pasting into a text editor outside Frisket gives the blocks' text.

### T1.16 Autosave, crash recovery and snapshots

- **Depends on:** T1.6. **Spec:** F1, §9 (crash recovery target). **UI:** `ui/11-file-dialogs.png` ("Frisket quit unexpectedly").
- **Files:** `app/src-tauri/src/{autosave.rs,snapshots.rs}`, `app/src/sheets/{RecoverySheet.svelte,OlderFileSheet.svelte,NewerFileSheet.svelte}`, `app/src-tauri/tests/autosave.rs`.
- **Steps:** app data folder = Tauri `app_data_dir()`. Every 30 s and on window blur, each dirty session writes `autosave/<docId>.frisket` (same writer, never the user's file) plus `autosave/<docId>.json` (original path, title, time, unsaved edit count). A clean quit deletes them; at launch, leftovers trigger the recovery sheet in the Home tab: one checkbox per document, "Restore n documents" opens each as a tab marked dirty, "Discard" deletes them. Snapshots: on every explicit save, copy the saved file to `snapshots/<docId>/<timestamp>.frisket`; keep the newest 50. File menu "Revert to Saved" and "Browse Snapshots…" (list sheet; restoring opens it as the current content, one undo step). Also wire the older/newer sheets of `ui/11` to `VersionStatus` from T1.5.
- **Acceptance:**
    - [ ] Killing the process (test harness `SIGKILL`) after edits and relaunching offers recovery with ≤ 30 s of edits lost.
    - [ ] The 51st snapshot removes the oldest; opening the older and newer fixtures shows the matching sheet text of `ui/11`.

### T1.17 Compatibility corpus and format 1.0 freeze

- **Depends on:** T1.5, T1.13, T1.14, T1.11, T1.16. **Spec:** File-format-contract §8.
- **Files:** `fixtures/compat/1.0/*.frisket`, `crates/frisket-format/tests/compat.rs`, `docs/adr/0009-format-1-0-frozen.md`.
- **Steps:** create fixtures covering every entity that exists at this point (blank, shapes of each kind, groups, locked blocks, guides, rotated frames, unknown-field file). `compat.rs` opens, migrates, validates against `schema/frisket-1.0.schema.json`, renders every page (PNG snapshot) and round-trips each fixture. From this task on, every format change follows File-format-contract §10.
- **Acceptance:**
    - [ ] Compat test green in CI; ADR 0009 records the freeze and the fixture list.

## 5. P2 — Text and styles

P2 adds stories, text blocks with the overlay editor, character and paragraph formatting, styles, threading across frames, spell check, find/replace and the special-characters palette. Typst lays out all text; the overlay editor (ADR 0005) only captures input.

### T2.1 Story model and storage

- **Depends on:** T1.17. **Spec:** §7 Story and rich text schema.
- **Files:** `crates/frisket-model/src/text/{mod.rs,story.rs,node.rs,mark.rs,edit.rs}`, `crates/frisket-model/src/command/story.rs`, `app/src/editor/schema.ts`, `app/src/editor/schema.test.ts`, `fixtures/text/*.json`.
- **Steps:** `Story { id, content: Vec<BlockNode>, language: Option<String> }`. `BlockNode` = `Paragraph { style: Option<StyleId>, attrs: ParagraphAttrs, content: Vec<InlineNode> }` | `Heading { level: 1..=3, … }` | `List { ordered, start, items: Vec<ListItem> }`. `InlineNode` = `Text { text, marks: Vec<Mark> }` | `Citation { keys }` | `CrossRef { target: BlockId }` | `InlineMath { latex }` | `MergeField { name }` | `HardBreak`. `Mark` = `Bold | Italic | Superscript | Subscript | Code | Link { href } | Char { style: StyleId }`. Positions are ProseMirror-compatible integer offsets. `StoryEdit::Replace { from, to, slice }` with apply + inverse. Commands `AddStory`, `RemoveStory`, `EditStory { story, edits }`. The ProseMirror schema in `schema.ts` mirrors every node and mark one-to-one; `schema.test.ts` round-trips all fixtures JSON → ProseMirror doc → JSON. Format 1.1 (first format change of P2; see §1 hard rules).
- **Acceptance:**
    - [ ] Round-trip is lossless for 20 fixtures incl. emoji, combining accents, Romanian ș/ț, RTL Arabic, and every node/mark type (Rust and TS).
    - [ ] `EditStory` inverse property test (1,000 random edits).

### T2.2 Story codegen and style resolution

- **Depends on:** T2.1. **Spec:** §6 Typst integration. **Design values:** THEMES §2.
- **Files:** `crates/frisket-typeset/src/codegen/{story.rs,style.rs}`, `crates/frisket-typeset/tests/story_codegen.rs` (insta).
- **Steps:** convert a story into Typst markup using function calls, never markdown-like shorthand: paragraphs as `#par[...]` separated by `#parbreak()`, text via `#text(..)[escaped]`, bold `#strong[..]`/`#text(weight: "bold")`, italic `#emph[..]`, super/subscript `#super[..]`/`#sub[..]`, lists `#list(..)`/`#enum(..)`, links `#link("..")[..]`, hard break `#linebreak()`. All literal text through `escape` (T0.7). Resolved style values (font, size, colour, spacing, hyphenation, language) are emitted as `#set`/`#text` arguments; unresolved tokens are an error, never a silent default. Citations, cross-refs and math emit placeholders until P4/P5 (`[?]`).
- **Acceptance:**
    - [ ] insta snapshots for the 20 story fixtures; compiling each succeeds.
    - [ ] A story containing `#`, `$`, `@`, `<`, `*`, `_` and `]` renders those characters literally.

### T2.3 Text blocks, measurement and overset

- **Depends on:** T2.2. **Spec:** F4. **Files:** `crates/frisket-model/src/blocks/text.rs`, `crates/frisket-typeset/src/{measure.rs,codegen/text_block.rs}`, `crates/frisket-typeset/tests/measure.rs`.
- **Steps:** `TextBlock { story: StoryId, columns: 1..=4, gutter: Pt, inset: Insets, vertical_align }`. `measure::block_height(&Document, BlockId, width) -> Pt` per ADR 0003 (single-block compile at `height: auto`), cached by `(content hash, width, theme hash)` in `cache.rs`. For Free text frames with fixed height: overset = content height > frame height; report `Overset { block, hidden_lines_estimate }` in the render result, and draw the red "+" port in the overlay (THEMES §9 overflow marker). Multi-column text inside a block uses Typst `columns(n, gutter)`.
- **Acceptance:**
    - [ ] Measurement cache test: second call with same inputs hits the cache; changing one character misses it.
    - [ ] Overset detected for a fixture frame and cleared when the frame grows.

### T2.4 Overlay editor: in-place text editing

- **Depends on:** T2.3, T0.10. **Spec:** §5 Canvas composition (editor layer), Interaction model. **UI:** `ui/02-blank-a4.png` (Title block being edited).
- **Files:** `app/src/editor/{Editor.svelte,editorState.ts,toModel.ts,fromModel.ts,keymap.ts,fonts.css}`, `app/src/editor/editor.test.ts`, `crates/frisket-model/src/command/story.rs` (edit coalescing key).
- **Steps:** double-click a text block (or press Return with it selected) to open a ProseMirror view placed over the block using the layout-map rect, scaled with the canvas zoom, with the resolved theme font (bundled fonts served as `@font-face` from the app bundle), size, line height and colour. Each ProseMirror transaction maps to `StoryEdit`s sent via `doc_apply` with coalesce key `type:<storyId>` (merges per 1 s pause or word boundary, per History). Typst re-renders behind the editor; the editor background is transparent over text only while typing, and the Typst render becomes visible when editing ends (Escape, click outside) — follow ADR 0005 exactly. Tab moves to the next block in reading order. IME composition must not send partial edits.
- **Acceptance:**
    - [ ] Type, select, cut, paste, undo inside a block at 25%, 100% and 400% zoom (Playwright with mocked IPC checks sent edits; manual check in the real app listed).
    - [ ] Japanese IME and a Romanian keyboard layout input correctly (manual check listed in the PR).
    - [ ] Keystroke-to-paint p95 < 16 ms on the ADR 0005 benchmark story.

### T2.5 Character formatting and the font menu

- **Depends on:** T2.4. **Spec:** F4, F5 (font menu). **UI:** `ui/02-blank-a4.png` (inspector Text tab and font menu). **Design values:** THEMES §2.
- **Files:** `app/src/workspace/inspector/{TextInspector.svelte,FontMenu.svelte}`, `app/src/editor/marks.ts`, `crates/frisket-model/src/text/char_attrs.rs`, `app/src-tauri/src/commands/fonts.rs`.
- **Steps:** Inspector Text tab: paragraph style dropdown, font family (FontMenu), size (pt), colour (theme token or custom), align. FontMenu: header "BUILT INTO FRISKET · IDENTICAL ON EVERY MAC", the five text families with their "metrics" note exactly as in mockup 02, then "Fonts on this Mac ›" submenu from `fonts_list()` (hidden when Settings › Fonts toggle is off), then the footer note of mockup 02. Also bold/italic/underline/strikethrough/super/subscript with `⌘B`, `⌘I`, `⌘U`, `⌃⌘+`, `⌃⌘−`, tracking, OpenType toggles (ligatures, small caps, old-style/lining, tabular figures). A weight not shipped for a bundled family (THEMES §2) is not offered.
- **Acceptance:**
    - [ ] Each attribute round-trips through the file format and appears in a PNG snapshot.
    - [ ] The font menu matches mockup 02 text and order.

### T2.6 Paragraph formatting and lists

- **Depends on:** T2.5. **Files:** `app/src/workspace/inspector/ParagraphInspector.svelte`, `crates/frisket-model/src/text/{para_attrs.rs,list.rs}`, `app/src/editor/lists.ts`.
- **Steps:** alignment (left, centre, right, justify), first-line/left/right indents, space before/after, line height, hyphenation on/off, keep with next, keep lines together, widow/orphan control (mapped to Typst `par`/`block` settings as far as Typst supports them; unsupported options are not shown — list them in the PR). Bullet and numbered lists with nesting (Tab / Shift-Tab).
- **Acceptance:**
    - [ ] Golden PNG for justify + hyphenation (English); lists renumber after insert and delete.

### T2.7 Paragraph and character styles

- **Depends on:** T2.6. **Spec:** F4 styles. **UI:** `ui/12-booklet.png` (Text styles panel).
- **Files:** `crates/frisket-model/src/text/{style.rs,stylesheet.rs}`, `crates/frisket-model/src/command/style.rs`, `app/src/workspace/inspector/TextStylesPanel.svelte`.
- **Steps:** one `Style` type with `kind: Paragraph | Character`, `name`, `based_on: Option<StyleId>`, and optional attributes; values may be theme tokens (`size.section`, `color.primary`). Default stylesheet per kind: Title, Heading, Subheading, Body, Caption, References, plus booklet styles of mockup 12 (Day heading, Session title, Time & room, Talk title, Speaker). Panel lists styles used in the document with usage counts ("12×"), selected style's properties (Size, Colour, Keep with next, Space above) and "Show details" for the rest. Local overrides show a marker and "Clear overrides". Apply by click, redefine from selection, rename, delete (uses reassign to parent).
- **Acceptance:**
    - [ ] Changing a style updates all uses in one undo step; usage counts correct on a 200-paragraph fixture.

### T2.8 Threaded frames and overset

- **Depends on:** T2.3, T0.11. **Spec:** F4. **Files:** per ADR 0006: `crates/frisket-typeset/src/thread.rs`, `crates/frisket-model/src/command/thread.rs`, `app/src/canvas/ThreadPorts.svelte`.
- **Steps:** implement the approach chosen in ADR 0006. Each text frame shows in/out ports (blue arrow badges of mockup 12); clicking an out port then an empty text frame links them. Story frame order is stored in `Story.frames: Vec<BlockId>`. Overset shows the red "+" port and an "overflow" tag in the outline. The canvas shows "Text flows from page N into page M · 1 story, K frames" (mockup 12) when a threaded frame is selected.
- **Acceptance:**
    - [ ] Text flows across 3 frames on 2 pages; unlinking the middle frame reflows correctly; overset reported.

### T2.9 Spell check and find/replace

- **Depends on:** T2.4. **Files:** `crates/frisket-features/src/find.rs`, `app/src/sheets/FindBar.svelte`, `crates/frisket-model/src/command/story_language.rs`.
- **Steps:** the overlay editor sets `spellcheck="true"` and `lang` from the story language (so WKWebView uses the macOS system dictionaries); language per story, settable in the inspector. Find/replace (`⌘F`, `⌥⌘F`) across all stories with match case, whole word, regex and style filter; `FindEngine` in `frisket-features` returns match ranges; replace-all is one `Composite` command.
- **Acceptance:**
    - [ ] FindEngine unit tests (case, whole word, regex, style filter, overlapping matches); replace-all undoes in one step.
    - [ ] Misspellings are underlined in English and Romanian test stories (manual check listed).

### T2.10 Scientific characters palette

- **Depends on:** T2.4. **Spec:** F4. **Files:** `crates/frisket-model/src/text/special_chars.rs`, `app/src/editor/SpecialCharacters.svelte`.
- **Steps:** popover (`⌃⌘Space` is taken by macOS; use `⌥⌘T`) with groups: Greek upper/lower; math ± × ÷ ≤ ≥ ≈ ≠ ∞ √ ∑ ∫ ∂ ∆; units µ ° ‰ Å Ω; arrows ← → ↑ ↓ ↔ ⇒; superscript and subscript digits; dashes and spaces (en, em, thin, non-breaking). A "Recent" row keeps the last 16 (stored in app settings).
- **Acceptance:**
    - [ ] Inserting a character is one undo step; the catalogue test checks every group is non-empty and characters are unique.

## 6. P3 — Structure and themes

P3 delivers the core differentiator: Flow layout on a column grid, the outline sidebar, section, header and callout blocks, themes, templates and the Home board. Exit: a poster created from the Home board, re-themed live, with section text fitted within 90–110% while respecting the theme minimum.

### T3.1 Grid and Flow placement model

- **Depends on:** T1.17. **Spec:** F2, §7 Page. **Design values:** THEMES §4.
- **Files:** `crates/frisket-model/src/document/{grid.rs,placement.rs,layout_mode.rs,grid_defaults.rs}`, `crates/frisket-model/src/command/{grid.rs,flow.rs}`.
- **Steps:** `Grid { columns: 1..=6, gutter: Pt, margins: Insets }`; `FlowPlacement { order: u32, span: u8, column_break_before: bool, min_height: Option<Pt>, keep_with_next: bool }` (column is derived, ADR 0008). `LayoutMode = Flow | DocumentFlow | Free`. Commands `SetGrid`, `SetLayoutMode`, `SetSpan`, `MoveInFlow { block, to_index }`, `SetColumnBreak`. `grid_defaults(kind, size, orientation) -> Grid` reproduces THEMES §4 exactly (table-driven test over every row). Format minor bump (first change of P3).
- **Acceptance:**
    - [ ] Commands tested with inverses; every THEMES §4 row reproduced by `grid_defaults`.

### T3.2 Flow solver and the layout pipeline

- **Depends on:** T3.1, T2.3, T0.13. **Spec:** §6 Layout pipeline.
- **Files:** `crates/frisket-flow/src/{solver.rs,input.rs,output.rs}`, `crates/frisket-typeset/src/pipeline.rs`, `fixtures/layout/flow/*.json` (25 cases + goldens).
- **Steps:** productionise ADR 0008 in `frisket-flow` (no Typst dependency): `solve(&FlowInput) -> FlowOutput { rects: Vec<(BlockId, Rect)>, column_fill: Vec<Pt>, overflow: Vec<Overflow { block, hidden_height }> }`. Heights come from a closure `height_at(block, width)`. `pipeline::layout_page(doc, page)`: measure each Flow block at its span width (cached, T2.3) → solve → codegen places blocks absolutely at solved rects → compile → layout map. Free blocks on the page are placed as-is above flowed content (T3.10 finishes this). Deterministic: same input → same output bytes.
- **Acceptance:**
    - [ ] 25 golden cases (spans, uneven heights, overflow, keep-with-next, column break, empty columns) pass.
    - [ ] Relayout of the reference-poster stand-in fixture after a one-word edit < 100 ms (criterion benchmark).

### T3.3 Flow interaction on the canvas

- **Depends on:** T3.2, T1.9. **Spec:** §5 Interaction model. **Files:** `app/src/canvas/flow/{FlowDrag.svelte,InsertionMarker.svelte,flowDrop.ts}`, `app/src/workspace/inspector/FlowInspector.svelte`.
- **Steps:** dragging a Flow block shows the insertion marker (THEMES §9) at the target slot (between blocks or top of a column); drop sends one `MoveInFlow`. Span via the inspector segmented control "1 column / 2 columns / Full" and by dragging the block's right edge to a column boundary. "Show details" reveals min height, keep with next, column break before.
- **Acceptance:**
    - [ ] Reordering by drag produces a single `MoveInFlow` (Playwright with mocked IPC).

### T3.4 Outline sidebar

- **Depends on:** T3.1, T1.9. **Spec:** §5 Left sidebar. **UI:** `ui/03-poster-workspace.png`, `ui/02-blank-a4.png` (empty state).
- **Files:** `crates/frisket-model/src/document/outline.rs`, `app/src/workspace/sidebar/{StructureTab.svelte,OutlineRow.svelte}`.
- **Steps:** `outline(&Document, &Diagnostics) -> Vec<OutlineRow { id, depth, title, tags: Vec<Tag> }>` in Rust: blocks in reading order, figures and tables nested under their section. Tags `linked` (neutral), `low res`, `overflow` (orange text), `field` (merge field). Header row shows its summary ("title · authors · logos"). Selection syncs both ways with the canvas. Drag to reorder (= `MoveInFlow`). "+ Add section" opens a menu of section presets for the kind. Empty state and the three "Add text section / Add figure / Add table" buttons of mockup 02; the PAGE card at the bottom (size, grid, margins, "Change in the inspector →").
- **Acceptance:**
    - [ ] Selecting in the outline selects on canvas and vice versa; reorder in the outline equals reorder on canvas.

### T3.5 Section and header blocks

- **Depends on:** T3.2, T2.7. **Spec:** F3. **Design values:** THEMES §1 usage rules, §2.
- **Files:** `crates/frisket-model/src/blocks/{section.rs,header.rs,author.rs}`, `crates/frisket-typeset/src/codegen/{section.rs,header.rs}`, `crates/frisket-model/src/command/header.rs`, `app/src/workspace/inspector/HeaderInspector.svelte`.
- **Steps:** Section = heading text + role (`background | objectives | methods | results | conclusions | references | contact | custom`) + story. Header = title story, authors `{ name, affiliations: Vec<u8>, corresponding: bool }`, affiliations list, logo slots (asset refs, filled in P4). Superscripts generated from affiliation order. Header band per THEMES §1 (primary background, onPrimary text, `space.xl` padding, extends to trim/bleed).
- **Acceptance:**
    - [ ] Reordering affiliations renumbers superscripts; header PNG snapshot in two themes.

### T3.6 Callout block

- **Depends on:** T3.5. **Design values:** THEMES §11.
- **Files:** `crates/frisket-model/src/blocks/callout.rs`, `crates/frisket-typeset/src/codegen/callout.rs`, `app/src/workspace/inspector/CalloutInspector.svelte`.
- **Steps:** exactly THEMES §11: optional key figure, optional heading, body story, `tint` box, `space.l` padding.
- **Acceptance:**
    - [ ] PNG snapshots in 3 themes; empty key figure and heading take no space.

### T3.7 Theme model and token resolution

- **Depends on:** T2.7. **Spec:** F5, §7 Theme. **Design values:** THEMES §1–§3, §8.
- **Files:** `crates/frisket-model/src/theme/{theme.rs,palette.rs,pairing.rs,scale.rs,spacing.rs,distance.rs,resolve.rs}`, `resources/themes/*.json`, `resources/rules/min-text-size.json`, `crates/frisket-model/src/command/theme.rs`.
- **Steps:** styles reference tokens (`size.body`, `color.primary`, `space.l`); `resolve(&Theme, kind, page_size) -> ResolvedTokens` computes every size (THEMES §2 multipliers, §3 rule for posters, rounding rules) and colour. The document stores a copy of its theme (THEMES §8). Commands `SetTheme` (replace copy), `SetViewingDistance`, `SetPaletteColor`, `SetTypePairing`.
- **Acceptance:**
    - [ ] Resolver tests reproduce every number of the THEMES §3 table and the §2 flyer/handout/booklet examples.
    - [ ] Changing theme or distance changes every resolved size and colour in one command.

### T3.8 Built-in themes and the Theme view

- **Depends on:** T3.7. **UI:** `ui/09-theme.png`. **Design values:** THEMES §1, §6.
- **Files:** `resources/themes/{clinical-navy,forest,plum,graphite,coral,ocean}.json`, `crates/frisket-model/src/theme/contrast.rs`, `app/src/views/ThemeView.svelte`, `app/src/workspace/inspector/ThemeTab.svelte`.
- **Steps:** ship the six themes exactly as THEMES §1. Theme view (full width in the tab, "Back to page"): theme cards; PALETTE (five swatches primary/accent/surface(tint)/text/muted, editable) with "Contrast of text on surface" ratio badge; TYPE (Headings font, Body font, "Sizes set for" segmented control with the six choices of THEMES §3, "Body text at this distance"); FIGURE PALETTE with normal and deuteranopia strips (CVD from T7.11; until then show the normal strip only) and the palette picker; BRAND KIT card (filled by T4.10; shows "No brand kit yet" until then). Inspector Theme tab = compact version (picker, distance, pairing).
- **Acceptance:**
    - [ ] Automated contrast test over all nine checked pairs of every theme matches THEMES §1 ratios (±0.01).
    - [ ] Theme view matches mockup 09 regions and labels.

### T3.9 Auto-arrange and column balancing

- **Depends on:** T3.2. **Spec:** F2. **Files:** `crates/frisket-flow/src/{arrange.rs,balance.rs}`, `fixtures/layout/arrange/*.json`.
- **Steps:** auto-arrange searches span assignments and column breaks that keep reading order; objective = minimise total overflow first, then the variance of column bottoms. Bounded search (stop after 200 ms, keep best). Applied as one `Composite` command from the toolbar "Auto-arrange" button. Vertical justification (inspector option on the page) distributes spare space between blocks in each column.
- **Acceptance:**
    - [ ] On 10 overflow fixtures, auto-arrange removes overflow in ≥ 8 and never changes reading order.

### T3.10 Free frames on Flow pages

- **Depends on:** T3.3, T1.10. **Files:** `crates/frisket-typeset/src/pipeline.rs`, `crates/frisket-model/src/command/detach.rs`, `crates/frisket-model/src/document/hit.rs`.
- **Steps:** blocks with `Free` placement on a Flow page are placed above flowed content and excluded from the solver. Commands "Detach from flow" (keeps current rect) and "Return to flow" (inserts at the nearest reading-order slot). Switching a page's layout mode converts placements (Flow → Free keeps current rects; Free → Flow orders by top-left reading order).
- **Acceptance:**
    - [ ] Mode switch round trip keeps geometry; undo restores the prior mode and placements.

### T3.11 Document kinds, presets and templates

- **Depends on:** T3.5, T3.6, T3.8. **Spec:** §3 Document kinds, F1. **Design values:** THEMES §4, §5.
- **Files:** `crates/frisket-model/src/presets/{structure.rs,kinds.rs}`, `xtask/src/templates.rs`, `resources/templates/**`, `app/src-tauri/src/commands/templates.rs`.
- **Steps:** structure presets per kind (Specification §3 table). `cargo xtask templates` generates every template file of THEMES §5 (never hand-edited) and a `resources/templates/index.json` (id, kind, layout, theme, size, description text for the Home cards). "Save as Template…" writes the current document to `app_data_dir()/templates/`. Changing a document's kind later re-maps sections by role (unmatched sections are kept at the end, never deleted).
- **Acceptance:**
    - [ ] Every generated template opens with no preflight issue other than empty placeholders (checked once T7 exists; until then: opens and renders).
    - [ ] Re-running `cargo xtask templates` produces byte-identical files.

### T3.12 Home board

- **Depends on:** T3.11, T0.3. **Spec:** §3 workflow 1, F1 Home board. **UI:** `ui/01-home.png`.
- **Files:** `app/src/home/{Home.svelte,KindCard.svelte,Recents.svelte,FilterChips.svelte,StartFromFile.svelte,SelectionBar.svelte}`, `app/src-tauri/src/commands/{recents.rs,home.rs}`.
- **Steps:** exactly mockup 01: left column with "+ New blank A4", "Open…", search field, RECENT list (from `recents_list()`, stored in app data, max 20, each with thumbnail from `preview.png`, kind and relative time) and the drag-and-drop note; main area "Start something new" + subtitle, filter chips All / Posters / Print / Multi-page / From a list / My templates, eight cards (Blank A4 "Default" badge and selected at start, Conference poster, E-poster, Flyer, Handout / one-pager, Programme booklet, Certificate, Name badges), "OR START FROM A FILE" row (Abstract or manuscript, PowerPoint poster, Spreadsheet list — disabled with a tooltip "Available in a later version" until P9), and the bottom selection bar ("Blank A4 selected", Other sizes links, "Double-click a card or press Return", Create). Create/Return/double-click calls `doc_new_from_template` and replaces the Home tab with the document tab. Keyboard: arrow keys move the card selection.
- **Acceptance:**
    - [ ] Playwright: Home → Return opens a Blank A4 document tab; double-click on Conference poster opens a poster tab; filters narrow the cards.
    - [ ] Keyboard-only creation possible; every card has an accessible name.

### T3.13 Reading-order badges

- **Depends on:** T3.2, T3.5. **Design values:** THEMES §1 (badges).
- **Files:** `crates/frisket-typeset/src/codegen/badges.rs`, `crates/frisket-model/src/theme/theme.rs` (flag), `app/src/workspace/inspector/ThemeTab.svelte`.
- **Steps:** optional numbered circles at the top-left of each section in reading order, rendered into the document (they print), toggle in the Theme tab. Reserve 30 pt before the heading when on.
- **Acceptance:**
    - [ ] Badges renumber after reorder; PNG snapshot.

### T3.14 Text fitting

- **Depends on:** T3.7, T3.2. **Spec:** F4 text fitting. **Files:** `crates/frisket-typeset/src/fit.rs`, `crates/frisket-typeset/tests/fit.rs`.
- **Steps:** per section, "Fit text" scales that section's resolved sizes between 90% and 110% by binary search until its content fits its solved height, never below the THEMES §3 minimum. Stored as `fit_scale: f32` on the block.
- **Acceptance:**
    - [ ] Fits in ≤ 8 layout iterations; refuses with a message when the minimum is reached.

## 7. P4 — Figures and the R link

P4 adds assets, figure blocks for raster, PDF and SVG, watched folders that refresh figures when R re-exports them, the Linked files view, automatic relink, captions with numbering, alt text, the icon library, brand kits, theme export to R and photo adjustments. Exit: re-running an R script updates the poster within 1 s.

### T4.1 Asset model and store

- **Depends on:** T1.17. **Spec:** §7 Asset, File-format-contract §2.
- **Files:** `crates/frisket-model/src/assets/{asset.rs,kind.rs,status.rs}`, `crates/frisket-format/src/assets.rs`, `app/src-tauri/src/assets.rs`, `crates/frisket-format/tests/assets.rs`.
- **Steps:** `Asset { id, kind: Linked | Embedded, relative_path: Option<String>, absolute_path_hint: Option<String>, sha256: String, pixel_size: Option<(u32,u32)>, media_type: String, last_seen_modified: Option<i64> }`. Embedded bytes live in the container as `assets/<sha256>.<ext>` (de-duplicated). Linked assets also keep a **cached preview** inside the container at `assets/preview/<sha256>.png` (max 2048 px long edge) so a missing link still renders. Resolution order when opening: relative path from the document's folder, then absolute hint. The session keeps asset bytes in memory and feeds them to the Typst World by `FileId`. Format minor bump (first change of P4).
- **Acceptance:**
    - [ ] Moving the document and its figures folder together keeps links resolved (relative path wins); moving only the document resolves via the absolute hint.
    - [ ] A missing link renders the cached preview and reports status `missing`.

### T4.2 Figure block with raster images

- **Depends on:** T4.1, T3.2. **Spec:** F3 Figure, F6 fit modes. **UI:** `ui/03-poster-workspace.png`.
- **Files:** `crates/frisket-model/src/blocks/figure.rs`, `crates/frisket-typeset/src/codegen/figure.rs`, `crates/frisket-model/src/command/{asset.rs,figure.rs}`, `app/src/workspace/inspector/FigureInspector.svelte`, `app/src-tauri/src/commands/drop.rs`.
- **Steps:** PNG, JPEG, WebP and TIFF (TIFF converted to PNG on import with the `image` crate; the original is not stored). Fit modes fit width, fill (crop), original size; crop rect and focal point. Drag from Finder onto the canvas (Tauri `DragDropEvent`) creates a figure at the drop position (Flow slot or Free point); onto a placeholder fills it. Inspector: source row (file name + status), width segmented control (1 column / 2 columns / Full), fit segmented control, caption field. Figure badge "Figure 1 · linked" on the canvas (mockup 03).
- **Acceptance:**
    - [ ] PNG snapshots for each fit mode; PDF output embeds the image at native pixels (checked with `lopdf`: image XObject size = source size).

### T4.3 Vector PDF figures

- **Depends on:** T4.2, T0.12. **Files:** `crates/frisket-typeset/src/codegen/figure.rs`, `crates/frisket-model/src/blocks/figure.rs` (page index), `crates/frisket-render/tests/vector.rs`.
- **Steps:** place PDF figures with Typst `image(..)` per ADR 0007 (vector); multi-page PDFs get a page picker in the inspector. Canvas uses the SVG/PNG render path like everything else.
- **Acceptance:**
    - [ ] Exported PDF contains the figure's vector paths and fonts (operator check), not an image XObject.

### T4.4 SVG figures

- **Depends on:** T4.2, T0.12. **Files:** `crates/frisket-typeset/src/codegen/figure.rs`, `crates/frisket-render/tests/vector.rs`, `crates/frisket-features/src/preflight/rules/svg_text.rs` (stub registered in T7.4).
- **Steps:** place SVG with Typst `image(..)`. If ADR 0007 found that SVG text becomes paths or is lost, record the preflight suggestion "Export from R as PDF to keep text searchable" for T7.4.
- **Acceptance:**
    - [ ] `km.svg` exports as vector (operator check).

### T4.5 Watched folders and live refresh

- **Depends on:** T4.1. **Spec:** F6, §6 Linked files. **Files:** `crates/frisket-features/src/watch/{watcher.rs,debounce.rs,folder.rs}`, `app/src-tauri/src/watch.rs`, `crates/frisket-features/tests/watch.rs`.
- **Steps:** one `notify` watcher per watched folder (document setting `watchedFolders: Vec<String>`, relative paths). Debounce 300 ms per path (a generation counter discards stale timers). On change: re-hash; if SHA-256 differs, reload bytes, regenerate the cached preview, update `Asset.sha256/pixel_size/last_seen_modified` **without an undo entry** (external change, but marks the session dirty), re-render dirty pages, emit `asset-changed { doc, asset, status }`. A new file whose name matches a linked asset's name with a different extension (e.g. `forest_plot.png` → `forest_plot.pdf`) switches the link to the new file (mockup 06 hint) and emits `asset-changed`. Watchers stop when the session closes.
- **Acceptance:**
    - [ ] Integration test: overwrite a linked PDF in a temp folder → updated render available within 1 s.
    - [ ] Five writes within 200 ms produce exactly one refresh.

### T4.6 Linked files view and the Assets tab

- **Depends on:** T4.5. **Spec:** F6 link manager. **UI:** `ui/06-assets.png`, `ui/03-poster-workspace.png` (WATCHED FOLDER card).
- **Files:** `app/src/views/LinkedFilesView.svelte`, `app/src/workspace/sidebar/{AssetsTab.svelte,WatchedFolderCard.svelte}`, `crates/frisket-features/src/links.rs`, `crates/frisket-model/src/command/replace_asset.rs`, `app/src-tauri/src/commands/assets.rs`.
- **Steps:** exactly mockup 06: sidebar WATCHED FOLDERS cards (path, "n files linked · watching" or "1 change arriving…"), "+ Watch a folder…", LIBRARY (Linked files n, Icons n, Brand kit logos n) and the R hint at the bottom; main view "Linked files" with summary line, "Back to page", "Embed all", "Link a file…", filter chips (All, Needs attention · n, Figures, Tables, Logos), table columns File (name + type/size), Used in, Status (in sync / low resolution / modified / embedded / missing, coloured chips), Last change, Print quality (effective ppi at placed size), actions (Reveal, Embed, Relink…, Unlink). A low-resolution row shows the orange callout with the `ggsave(...)` line (THEMES §7 format). Relink and Embed update every reference in one `Composite` command. "Reveal" uses `tauri-plugin-opener` `reveal_item_in_dir`. The poster workspace sidebar card shows "WATCHED FOLDER / path / ✓ n figures in sync".
- **Acceptance:**
    - [ ] Relink to a renamed file restores the figure; Embed copies it into the container and removes the link; both undo in one step.
    - [ ] View matches mockup 06 columns, labels and chips.

### T4.7 Captions, numbering and cross-references

- **Depends on:** T4.2, T2.4. **Spec:** F6. **Files:** `crates/frisket-model/src/blocks/caption.rs`, `crates/frisket-typeset/src/numbering.rs`, `app/src/editor/CrossRefPicker.svelte`.
- **Steps:** figures and tables carry a caption story; labels "Figure n" / "Table n" are numbered in reading order with separate counters (computed by Frisket, not Typst's counters, so the outline can show them). `CrossRef { target }` inline nodes resolve to the current label on each layout; a missing target renders "[missing reference]" and yields a diagnostic for preflight (T7.6). `⇧⌘R` opens the picker listing figures and tables in reading order.
- **Acceptance:**
    - [ ] Reordering figures renumbers labels and cross-references in one layout pass; deleting a target shows "[missing reference]".

### T4.8 Alt text

- **Depends on:** T4.2. **Files:** `crates/frisket-model/src/document/block.rs` (`alt_text: Option<String>`), `app/src/workspace/inspector/FigureInspector.svelte`, `crates/frisket-typeset/src/codegen/figure.rs`.
- **Steps:** optional alt text on figure, icon and QR blocks; passed to Typst `image(alt: ..)` so tagged PDF carries it.
- **Acceptance:**
    - [ ] Alt text round-trips through the file and appears in the exported PDF structure (checked with `lopdf`).

### T4.9 Scientific icon library

- **Depends on:** T4.1. **Spec:** F6 icon library. **Files:** `resources/icons/{catalog.json,svg/*.svg,LICENSES/}`, `crates/frisket-model/src/blocks/{icon.rs,credits.rs}`, `crates/frisket-features/src/icons.rs`, `app/src/workspace/sidebar/IconBrowser.svelte`, `THIRD_PARTY.md`.
- **Steps:** bundle a curated subset (start with 300; mockup 06 shows the future target 1,240) from Servier Medical Art (CC BY 4.0) and Bioicons — **only icons licensed CC0 or CC BY** (Specification §12). `catalog.json` fields: id, name, tags, category, author, licence, licenceUrl, sourceUrl. Search by name/tag/category. Adding an icon embeds its SVG as an asset and snapshots its attribution. Monochrome icons tagged `tintable` take `color.primary`. An automatic "Image credits" line lists the icons in use, placed after References or in the page footer (setting).
- **Acceptance:**
    - [ ] A test enforces licence metadata on every catalog entry and rejects any licence other than CC0/CC BY.
    - [ ] The credits line updates when icons are added or removed.

### T4.10 Brand kits and logo strip

- **Depends on:** T3.8, T4.1. **Spec:** F5 brand kit, F3 logo strip. **UI:** `ui/09-theme.png` (BRAND KIT card). **Design values:** THEMES §1 (Institution card).
- **Files:** `crates/frisket-model/src/brand/kit.rs`, `crates/frisket-format/src/brand.rs` (`.frisket-brand` ZIP, own `formatVersion` per contract §9), `crates/frisket-model/src/blocks/logo_strip.rs`, `crates/frisket-typeset/src/codegen/logo_strip.rs`, `app/src/views/BrandKitEditor.svelte`.
- **Steps:** kits stored in `app_data_dir()/brand/*.frisket-brand` (logos embedded, colours, optional fonts from the bundled set). "Apply to this document" copies logos into the document as embedded assets and overrides palette tokens; the Theme view shows the Institution card. Logo strip sizes logos to equal visual weight: scale each so its bounding-box area is equal, capped by a max height, centred on a common baseline.
- **Acceptance:**
    - [ ] A document using a kit opens correctly on a machine without that kit (fixture test).

### T4.11 Export theme to R

- **Depends on:** T3.7. **Spec:** F5. **Design values:** THEMES §7. **Files:** `crates/frisket-features/src/rtheme.rs`, `resources/rtheme/frisket_theme.R.tmpl`, `crates/frisket-features/tests/rtheme.rs`.
- **Steps:** generate the file exactly as THEMES §7 from a template with named placeholders; button "Export theme to R…" in the Theme view and File menu (save dialog, default name `frisket_theme.R`).
- **Acceptance:**
    - [ ] Golden-text test; in CI, `Rscript -e 'parse("frisket_theme.R")'` runs when `Rscript` is on the runner (job skipped with a notice otherwise).

### T4.12 Basic photo adjustments

- **Depends on:** T4.2. **Spec:** F6 photo tools. **Files:** `crates/frisket-model/src/blocks/adjust.rs`, `crates/frisket-render/src/adjust.rs`, `app/src/workspace/inspector/PhotoInspector.svelte`.
- **Steps:** non-destructive quarter-turn rotation, horizontal/vertical flip, brightness, contrast, saturation on raster figures, stored as parameters. Applied with the `image` crate when feeding bytes to Typst (cached by source hash + parameters).
- **Acceptance:**
    - [ ] Adjustments round-trip and render identically on canvas and in PDF (PNG snapshot).

### T4.13 Automatic relink of moved files

- **Depends on:** T4.6. **Spec:** F6 automatic relink. **UI:** `ui/11-file-dialogs.png` ("Linked figures moved").
- **Files:** `crates/frisket-features/src/relink.rs`, `app/src/sheets/RelinkSheet.svelte`.
- **Steps:** when opening a document with missing links, search (max 2 s, max depth 4) the watched folders, the document's folder and its parent, and `~/Dropbox`, `~/Library/CloudStorage/*` for files with the same name; accept a candidate only if its SHA-256 equals the stored hash. If all missing links are found in one folder, show the sheet text of mockup 11 with "Relink manually…" and "Use the found files" (one `Composite` command).
- **Acceptance:**
    - [ ] Fixture: move three linked files into another folder → sheet proposes them; applying restores every figure; a same-name file with different content is never proposed.

## 8. P5 — Scientific content

P5 adds tables, equations, citations and the References view, QR codes, connectors and the CONSORT/PRISMA builder. Exit: the reference poster (Appendix) is fully reproducible in Frisket.

### T5.1 Table model and layout

- **Depends on:** T3.2, T2.3. **Spec:** F3 Table. **Design values:** THEMES §1 (table rules).
- **Files:** `crates/frisket-model/src/blocks/table.rs`, `crates/frisket-typeset/src/codegen/table.rs`, `fixtures/layout/tables/*.frisket`.
- **Steps:** rows × columns of cells, each cell a small story; header rows count; row and column spans; column widths `Auto | Fixed(Pt) | Fraction(f32)`; per-column alignment incl. decimal alignment (align on the decimal separator by splitting the cell text in codegen into integer and fraction parts laid out in a 2-cell sub-grid — describe the exact method in an ADR if another is chosen); zebra; default style = three-line (booktabs) per THEMES §1, using Typst `table` with `stroke` rules. Format minor bump (first change of P5).
- **Acceptance:**
    - [ ] PNG goldens for 8 table fixtures incl. spans and decimal alignment; 3 style variants.

### T5.2 Table editing

- **Depends on:** T5.1, T2.4. **Files:** `app/src/canvas/table/{TableEditor.svelte,cellSelection.ts}`, `crates/frisket-model/src/command/table.rs`.
- **Steps:** click a cell to edit (overlay editor per cell); Tab/Shift-Tab and arrows move between cells; select cell ranges; insert/delete rows and columns; merge/split; drag column borders. Each structural change is one command.
- **Acceptance:**
    - [ ] All table commands have inverse tests; keyboard-only editing of a 5×4 table is possible (Playwright).

### T5.3 Table import and paste

- **Depends on:** T5.1. **Spec:** F3, §8 Import mapping. **Files:** `crates/frisket-import/src/table/{csv.rs,xlsx.rs,paste.rs}`, `fixtures/tables/*`.
- **Steps:** CSV/TSV with delimiter detection (`,` `;` tab) and encoding detection (UTF-8 with/without BOM, Windows-1250, Windows-1252) — `calamine` for XLSX (sheet picker, used range, merged cells, numbers as displayed text). Paste from Excel/Numbers via the HTML or TSV clipboard data received from the webview `paste` event. Option to keep the table linked to its file (refresh via T4.5).
- **Acceptance:**
    - [ ] Six fixtures (comma, semicolon, UTF-8 BOM, Windows-1250, XLSX with merges, XLSX with dates) import as expected.

### T5.4 Equations

- **Depends on:** T0.12, T2.4. **Spec:** F3 Equation. **Files:** `crates/frisket-model/src/blocks/equation.rs`, `crates/frisket-typeset/src/codegen/math.rs`, `app/src/editor/EquationEditor.svelte`.
- **Steps:** display equation block and `InlineMath` node; source syntax `latex` (converted with MiTeX, per ADR 0007) or `typst`. Editor popover: source field, syntax toggle, live preview (Rust renders the equation alone to SVG), error message from the converter or compiler. Font = Latin Modern Math; size and colour follow the surrounding style.
- **Acceptance:**
    - [ ] The 10 spike samples render in blocks and inline; invalid input shows an error, never a panic.

### T5.5 Bibliography import

- **Depends on:** T1.17. **Spec:** F7. **Files:** `crates/frisket-model/src/citations/{bibliography.rs,entry.rs}`, `crates/frisket-import/src/bib/{bibtex.rs,csl_json.rs}`, `fixtures/citations/*`.
- **Steps:** store BibLaTeX source text per entry (Specification §7); parse keys, title, authors, year, journal for the UI list with the BibLaTeX parser used by hayagriva (ADR 0007; via `frisket-typeset` re-export if the parser comes from the Typst dependency tree — do not add a new crate). CSL-JSON is converted to BibLaTeX on import. A library can be linked to a Zotero Better BibTeX export file and refreshed by the watcher (T4.5).
- **Acceptance:**
    - [ ] 50-entry BibTeX fixture with accents and crossrefs lists correctly; a CSL-JSON fixture converts and cites identically.

### T5.6 Citation rendering

- **Depends on:** T5.5, T0.12. **Spec:** F7. **Files:** `crates/frisket-typeset/src/codegen/citations.rs`, `resources/csl/{vancouver,ama,apa,nature}.csl`, `resources/csl/LICENSE.txt`.
- **Steps:** citations and the bibliography are rendered by Typst (`cite`, `bibliography(style: <csl bytes>)`) inside the same compile, so numbers follow reading order. Bundled styles: Vancouver, AMA, APA 7, Nature (CC BY-SA, attributed in `THIRD_PARTY.md` and Settings › About). Users can add `.csl` files (copied into the document container as `styles/<name>.csl`, format minor bump if not already done in P5).
- **Acceptance:**
    - [ ] Hand-checked output for 5 items in each bundled style; 100 items render in < 200 ms.

### T5.7 Citing and the References view

- **Depends on:** T5.6, T2.4. **UI:** `ui/08-references.png`. **Files:** `app/src/views/ReferencesView.svelte`, `app/src/editor/CitePopup.svelte`, `crates/frisket-model/src/blocks/references.rs`.
- **Steps:** exactly mockup 08: sidebar LIBRARIES card ("escmid_refs.bib · Linked to Zotero export · 38 entries"), "+ Add .bib or CSL-JSON…", hint text; main "References" with "4 cited in this poster · 38 in the library", "Back to page", "Insert citation", search, filter chips All / Cited · n / Not cited, entry rows ([n], authors bold, title, journal · year · @key, cited/not cited chip); bottom bar showing the `@` insertion context. Right inspector: Style / Block tabs; CITATION STYLE list with a sample marker per style, "Add a .csl style…", PREVIEW of the bibliography, "Move references behind the QR code" checkbox. Typing `@` in any text opens the cite popup (search key/title/author; Return inserts; ↑↓ choose). References block regenerates on every change.
- **Acceptance:**
    - [ ] A numbered style renumbers after reordering sections; switching style updates markers and list in one command.
    - [ ] View matches mockup 08.

### T5.8 QR codes

- **Depends on:** T3.2. **Spec:** F3 QR. **Files:** `crates/frisket-model/src/blocks/qr.rs`, `crates/frisket-typeset/src/codegen/qr.rs`, `crates/frisket-render/tests/qr.rs`.
- **Steps:** content types URL, DOI (→ `https://doi.org/…`), email (`mailto:`), vCard 3.0, plain text. Generate the module matrix with the `qrcode` crate (error correction M, quiet zone 4 modules) and emit it as Typst vector rectangles (one path per row run). Optional caption text beside it (mockup 03: "[Full abstract & contact]").
- **Acceptance:**
    - [ ] Rendering the QR to PNG at 2 cm and 10 cm and sampling each module centre reproduces the `qrcode` matrix exactly (no decoder dependency); a phone scan of the exported PDF is listed as a manual check.

### T5.9 Connectors

- **Depends on:** T1.13. **Files:** `crates/frisket-model/src/blocks/connector.rs`, `crates/frisket-typeset/src/codegen/connector.rs`, `app/src/canvas/tools/connector.ts`.
- **Steps:** straight and elbow connectors attached to block anchor points (edge midpoints); they re-route when blocks move; arrowheads per end (THEMES §10).
- **Acceptance:**
    - [ ] Moving an attached block reroutes the connector; detaching keeps the last geometry.

### T5.10 CONSORT / PRISMA builder

- **Depends on:** T5.9, T3.5. **Spec:** F3 Flowchart. **Files:** `crates/frisket-features/src/flowchart/{consort.rs,prisma.rs,layout.rs}`, `app/src/sheets/FlowchartSheet.svelte`.
- **Steps:** sheet with a form of stage labels and counts (n) per arm; generates a grouped set of boxes and connectors (mockup 03 Methods column); editable afterwards; re-opening the sheet edits counts and updates the diagram. Counts may come from a linked CSV (mockup 06 `consort_counts.csv`, columns `stage,arm,n`).
- **Acceptance:**
    - [ ] CONSORT 2-arm and PRISMA 2020 generate without overlaps at widths of 1, 2 and 3 columns.

### T5.11 Reference poster reproduction

- **Depends on:** T5.1–T5.10, T4.1–T4.13. **Files:** `fixtures/reference/reference-poster.frisket`, `fixtures/reference/README.md`.
- **Steps:** build the reference poster described in the Appendix inside Frisket; commit it as the fixture for performance and snapshot tests.
- **Acceptance:**
    - [ ] Every element of the Appendix list is present; opening and exporting it is part of CI.

## 9. P6 — Export and CLI

P6 turns documents into files a print shop, a conference platform or a pipeline can use. Build 0.1 "Poster alpha" is tagged at the end of P6.

### T6.1 Export pipeline

- **Depends on:** T1.7. **Spec:** §8 Export implementation. **Files:** `crates/frisket-render/src/export/{mod.rs,job.rs,preset.rs,progress.rs}`, `app/src-tauri/src/commands/export.rs`.
- **Steps:** `ExportPreset` enum (`PrintPdf{bleed, cropMarks, slug, standard}`, `ScreenPdf{ppi}`, `Png{dpi|pixels}`, `Jpeg{dpi|pixels, quality}`, `Handout`, `Booklet`, `Merge{…}`). `export(doc snapshot, preset, dest, progress: impl Fn(Progress), cancel: CancelToken)` runs off the UI thread, reports per page, supports cancellation and writes atomically (temp file in the destination folder, then rename). Command `export(doc, preset, path)` + event `export-progress`.
- **Acceptance:**
    - [ ] Cancelling mid-export leaves no partial file; progress reaches 100% exactly once.

### T6.2 Print PDF

- **Depends on:** T6.1. **Spec:** F9, §8. **UI:** `ui/05-export.png` (Print PDF options).
- **Files:** `crates/frisket-render/src/pdf/{print.rs,marks.rs,boxes.rs,metadata.rs}`, `crates/frisket-render/tests/print_pdf.rs`.
- **Steps:** compile the page at trim + 2 × bleed (+ slug area when marks are on); background items that touch the trim edge extend into the bleed; draw crop marks (0.25 pt black, 3 mm long, offset 3 mm from trim) and optional slug line (file name, date, page) in the slug area as page content. Then `lopdf` post-processing sets `TrimBox` and `BleedBox` per page, the document title/author, and an sRGB output intent. Standards: PDF 1.7 (default), PDF/A-2b (Typst option).
- **Acceptance:**
    - [ ] PDF check test: boxes correct, all fonts embedded and subset, figures vector, page size = trim + 2 × bleed (+ slug).
    - [ ] Opens without warnings in Preview and Acrobat Reader (manual, listed in the PR).

### T6.3 Screen PDF

- **Depends on:** T6.2. **Files:** `crates/frisket-render/src/pdf/screen.rs`.
- **Steps:** no bleed or marks; raster images downsampled to 150 ppi (setting) at their placed size before compile; text links and QR blocks become link annotations (Typst `link`).
- **Acceptance:**
    - [ ] Reference poster screen PDF < 5 MB; links clickable in Preview.

### T6.4 PNG and JPEG

- **Depends on:** T6.1. **Files:** `crates/frisket-render/src/{png.rs,jpeg.rs}`.
- **Steps:** per page at a DPI (72–600) or an exact pixel size (e-poster) via `typst-render`; sRGB; JPEG quality slider. Memory guard: above 100 megapixels, render in horizontal strips and stream-encode.
- **Acceptance:**
    - [ ] A0 at 300 dpi exports with peak memory < 2 GB; e-poster 3840 × 2160 has exactly that size.

### T6.5 A4 handout

- **Depends on:** T6.2. **Spec:** F9. **Files:** `crates/frisket-render/src/handout.rs`.
- **Steps:** a wrapper Typst document places each page scaled onto A4 (orientation matching) with 10 mm margins; compute the smallest resulting body text size; if < 7 pt, return a warning shown in the Export sheet.
- **Acceptance:**
    - [ ] The reference poster handout is one A4 page; a tiny-text fixture produces the warning.

### T6.6 Export sheet

- **Depends on:** T6.2, T6.3, T6.4, T6.5. **UI:** `ui/05-export.png`. **Files:** `app/src/sheets/ExportSheet.svelte`, `app/src/sheets/export/{PresetList.svelte,PrintOptions.svelte,PreviewCard.svelte}`, `crates/frisket-render/src/export/estimate.rs`.
- **Steps:** exactly mockup 05, as a sheet inside the tab: title "Export <name>", preflight notice and "Review issues" button (wired in T7.13), preset list (Print PDF, Screen PDF, PNG image, A4 handout, Booklet print — Booklet disabled until T8.10), options panel per preset (Bleed None / 3 mm / 5 mm, Crop marks, Include slug info, Colour "sRGB · printer converts", PDF standard, Images), bleed preview with trim/bleed size, page count, **estimated size** (from asset sizes + font subsets; within ±25%), fonts embedded; "Save as" name (template `{name}_{preset}.pdf`), folder picker, "Open when done", Cancel, Export. The grey line at the bottom shows the equivalent CLI command. Settings persist per document (document field `exportSettings`).
- **Acceptance:**
    - [ ] Each preset produces its file; settings persist after save/reopen; the CLI line matches T6.9 syntax.

### T6.7 Print

- **Depends on:** T6.2. **Files:** `app/src-tauri/src/commands/print.rs`.
- **Steps:** File → Print… (`⌘P`) exports a print PDF (no bleed) to a temporary file and opens it with the system default PDF viewer (`tauri-plugin-opener`), where the user prints (tiling is done by the viewer). No native print dialog in v1.
- **Acceptance:**
    - [ ] `⌘P` opens the exported PDF in Preview (manual check listed).

### T6.8 Preview images for recents

- **Depends on:** T1.4. **Spec:** File-format-contract §2 (`preview.png`). **Files:** `crates/frisket-format/src/preview.rs`, `app/src-tauri/src/commands/recents.rs`.
- **Steps:** on every save, render page 1 at 512 px long edge and store `preview.png` in the container; the Home board's recents read it (no Finder Quick Look plugin in v1).
- **Acceptance:**
    - [ ] Recents show the first page thumbnail of saved documents.

### T6.9 Command-line tool

- **Depends on:** T6.2, T6.3, T6.4. **Spec:** F13. **Files:** `crates/frisket-cli/src/{main.rs,cmd/export.rs,cmd/info.rs,cmd/relink.rs,cmd/preflight.rs,cmd/merge.rs,cmd/upgrade.rs}`, `crates/frisket-cli/tests/cli.rs`, `docs/cli.md`, `app/src-tauri/tauri.conf.json` (`bundle.externalBin`).
- **Steps:** `clap` subcommands: `export <file> --preset print|screen|png|jpeg|handout [--out DIR] [--dpi N] [--bleed MM]`, `info <file> [--json]`, `relink <file> --folder DIR`, `preflight` and `merge` (return exit code 3 "not implemented" until T7.13 / T8.9), `upgrade <file>` (migrate to the current format, writing the backup). Exit codes: 0 ok, 1 usage, 2 file error, 3 not implemented, 4 preflight issues. The binary ships inside the app bundle as a Tauri sidecar; Settings › Command line (T10.3) installs a symlink.
- **Acceptance:**
    - [ ] `assert_cmd` tests for every subcommand and exit code; exporting the reference poster from the CLI equals the app export byte-for-byte apart from creation dates.
    - [ ] `docs/cli.md` shows calls from R (`system2("frisket", c("export", …))`), a Makefile and a Quarto post-render script.

### T6.10 Tag 0.1 "Poster alpha"

- **Depends on:** T6.1–T6.9. **Files:** `CHANGELOG.md`, `.gitea/workflows/release.yml`, `docs/smoke.md`.
- **Steps:** release workflow on tag `v*` (runner `macos-arm64`): `make build` with `bundle.macOS.signingIdentity: "-"` (ad-hoc), attach `.dmg` to a Gitea release with changelog notes. `docs/smoke.md`: the manual checklist (new document, add figure, watched-folder refresh, export print PDF, reopen).
- **Acceptance:**
    - [ ] The downloaded `.dmg` installs and runs on a second Mac after "Open Anyway"; smoke checklist passes.

## 10. P7 — Preflight

P7 builds the rule engine, all v1 checks with explanations and one-click fixes, the Preflight mode with distance and colour-vision previews, conference presets, and the CLI report.

### T7.1 Rule engine

- **Depends on:** T3.2. **Spec:** §8 Preflight engine. **Files:** `crates/frisket-features/src/preflight/{mod.rs,rule.rs,issue.rs,runner.rs,context.rs,registry.rs}`, `app/src-tauri/src/commands/preflight.rs`.
- **Steps:** `trait Rule { fn id(&self) -> &'static str; fn title(&self) -> &'static str; fn severity(&self) -> Severity; fn detect(&self, cx: &Context) -> Vec<Issue>; fn fix(&self, issue: &Issue, cx: &Context) -> Option<Command>; }` — `Severity = Issue | Suggestion`. `Issue { rule, severity, block: Option<BlockId>, page: Option<PageId>, title, explanation, path: Option<String>, fix_label: Option<String> }` (plain-language texts, as in mockup 04). `Context` = document + layout maps + resolved theme + asset statuses + export target (print/screen). Runner runs after each relayout, debounced 250 ms, and emits `preflight-updated { doc, summary: { issues, suggestions, passed } }`. Ignored issues are stored per document (`ignoredIssues: Vec<{rule, block}>`, format minor bump). Commands `preflight_run(doc)`, `preflight_ignore(doc, rule, block)`, `preflight_unignore`.
- **Acceptance:**
    - [ ] A dummy rule fires, is ignored, stays ignored after reopen, and can be un-ignored.

### T7.2 Layout rules

- **Depends on:** T7.1. **Files:** `crates/frisket-features/src/preflight/rules/{overflow.rs,overset.rs,empty_placeholder.rs,trim_safety.rs,overlap.rs}`, `fixtures/preflight/layout/*`.
- **Steps:** Flow overflow (mockup 04 wording: "<Section> doesn't fit its box · About n lines are hidden…"); overset text in threaded stories; empty placeholders (THEMES §5 placeholder text); content within 10 mm (setting) of the trim edge or extending into the bleed without being a background ("Nothing within 10 mm of the trim edge" when passed); unintended overlaps of Free frames on text.
- **Acceptance:**
    - [ ] Each rule has a positive and a negative fixture test.

### T7.3 Typography rules

- **Depends on:** T7.1, T3.7. **Design values:** THEMES §3. **Files:** `crates/frisket-features/src/preflight/rules/{min_text_size.rs,missing_font.rs,system_font.rs,long_line.rs}`.
- **Steps:** text below the minimum for kind and viewing distance (THEMES §3 severity rules; mockup 04 suggestion "reference text is small from 2 m"); fonts missing on this machine (render with the closest bundled family, issue); a document using a system font (suggestion "a colleague may not have it; switch to <closest built-in>", Specification F5); body lines longer than 90 characters (suggestion).
- **Acceptance:**
    - [ ] Fixture tests; the missing-font test uses a document referencing a non-existent family.

### T7.4 Image and link rules

- **Depends on:** T7.1, T4.5. **Files:** `crates/frisket-features/src/preflight/rules/{resolution.rs,missing_link.rs,modified_link.rs,svg_text.rs}`.
- **Steps:** effective ppi = pixels ÷ placed inches; suggestion < 150, issue < 100 (print targets only), wording of mockup 04 ("Figure 2 will print blurry · <file> is too low resolution at this size. Re-export it from R as PDF or SVG and Frisket will pick it up automatically." with the path and "Reveal in Finder"). Missing links; links modified while auto-refresh is off; SVG text lost (from T4.4, if applicable).
- **Acceptance:**
    - [ ] A fixture with a 96 ppi placement reports an issue naming the file.

### T7.5 Colour rules

- **Depends on:** T7.1. **Files:** `crates/frisket-features/src/preflight/rules/{contrast.rs,palette_cvd.rs}`, `crates/frisket-features/src/color/{wcag.rs,cvd.rs,delta_e.rs}`.
- **Steps:** WCAG 2.x contrast for text against its resolved background token (AA: 4.5:1, or 3:1 for text ≥ 18 pt or ≥ 14 pt bold), and for text placed over images by sampling the rendered PNG under the text rectangle (median luminance). Figure palette distinguishability: CIEDE2000 between every pair of palette colours under each CVD simulation ≥ 10, else suggestion. CVD = Machado et al. 2009 matrices, severity 1.0, applied in linear RGB.
- **Acceptance:**
    - [ ] Contrast maths tested against WCAG reference values; CVD matrices against published sample conversions; ΔE2000 against the Sharma et al. test data (first 10 pairs).

### T7.6 Structure rules

- **Depends on:** T7.1, T4.7, T5.7, T4.9. **Files:** `crates/frisket-features/src/preflight/rules/{numbering_order.rs,broken_crossref.rs,uncited.rs,missing_citation.rs,icon_credits.rs,alt_text.rs}`.
- **Steps:** figure/table numbers out of reading order; broken cross-references; bibliography entries not cited (suggestion); citation keys not found (issue); icon credits missing; figures without alt text (suggestion, screen targets only).
- **Acceptance:**
    - [ ] Fixture tests for each rule.

### T7.7 Fixes

- **Depends on:** T7.2, T7.3, T7.4, T7.5, T7.6, T3.9, T3.14. **Files:** `crates/frisket-features/src/preflight/fixes/*.rs`.
- **Steps:** every fix returns one `Command` (often `Composite`): "Make room" (auto-arrange scoped to the column, then fit text), "Fit text", "Set to minimum size", "Use darker text colour" (nearest theme token meeting AA), "Move behind QR", "Switch to <built-in font>", "Relink…" (opens the sheet), "Renumber". Buttons use mockup 04 labels.
- **Acceptance:**
    - [ ] After applying each fix to its fixture the rule no longer fires; undo brings the issue back.

### T7.8 Live badge

- **Depends on:** T7.1. **UI:** `ui/02-blank-a4.png`, `ui/03-poster-workspace.png` (toolbar). **Files:** `app/src/workspace/PreflightBadge.svelte`.
- **Steps:** toolbar button "Preflight · n issues" (orange, warning icon) or "Preflight · all clear" (green, check) — issues only count severity Issue; updated from `preflight-updated`. Outline tags (T3.4) come from the same results.
- **Acceptance:**
    - [ ] Badge updates within 500 ms of an edit that creates or clears an issue.

### T7.9 Preflight mode

- **Depends on:** T7.7, T7.8. **UI:** `ui/04-preflight.png`. **Files:** `app/src/views/preflight/{PreflightMode.svelte,IssueCard.svelte,PassedList.svelte}`.
- **Steps:** the Edit / Preflight switch in the toolbar changes the tab into Preflight mode: page preview left (with simulation chips and distance panel from T7.10/T7.11), right panel "Before you print" with summary sentence ("2 things need attention, 1 suggestion. Each fix is one click and can be undone."), issue cards (orange border for issues, blue title for suggestions) with explanation, path box, fix button, "Show me" (switches to Edit, selects and zooms to the block), "Ignore"/"Keep"; PASSED list with checkmarks. Status bar shows "Preflight: n issues, n suggestion, n passed".
- **Acceptance:**
    - [ ] Layout and wording match mockup 04; screen readers read the cards in order.

### T7.10 Distance preview

- **Depends on:** T7.9. **Files:** `app/src/views/preflight/DistancePreview.svelte`, `app/src/views/preflight/acuity.ts`.
- **Steps:** "Preview as seen from" slider 0.5–4 m (default = document viewing distance). The page image is scaled to the angle it subtends at that distance on the current display (assume 110 px per inch on Apple displays unless `window.devicePixelRatio` and screen size give a better estimate) and blurred with CSS `filter: blur()` matched to 1 arcminute acuity.
- **Acceptance:**
    - [ ] `acuity.ts` unit tests for scale and blur radius; preview updates within 150 ms of slider change on the reference poster.

### T7.11 Colour-vision preview

- **Depends on:** T7.9, T7.5. **Files:** `crates/frisket-render/src/cvd.rs`, `app/src-tauri/src/commands/render.rs` (`cvd` parameter).
- **Steps:** "Simulate" chips Normal vision / Protanopia / Deuteranopia / Tritanopia; Rust applies the T7.5 matrices to the page PNG. The Theme view's deuteranopia strip (T3.8) uses the same function.
- **Acceptance:**
    - [ ] PNG snapshot of a palette strip for each mode.

### T7.12 Conference presets

- **Depends on:** T7.1. **Spec:** F8. **Files:** `crates/frisket-features/src/preflight/preset.rs`, `resources/presets/*.json`, `schema/preset-1.0.schema.json`, `app/src/views/preflight/PresetPicker.svelte`.
- **Steps:** preset JSON (own `formatVersion`): name, allowed sizes and orientation, max file size, required sections (by role), required elements (logo, QR, disclosure section), minimum text size override. Import/export as files. Bundle 3 generic presets (A0 portrait, 48×36 in landscape, 16:9 e-poster).
- **Acceptance:**
    - [ ] Preset violations appear as issues; invalid preset files are rejected with clear errors.

### T7.13 CLI preflight and export gating

- **Depends on:** T7.1, T6.9, T6.6. **Files:** `crates/frisket-cli/src/cmd/preflight.rs`, `schema/preflight-report.schema.json`, `app/src/sheets/ExportSheet.svelte`.
- **Steps:** `frisket preflight <file> [--preset NAME] [--json]` prints issues; exit 4 when issues exist. The Export sheet shows "Preflight has n open issues. You can export anyway, or fix them first." and "Review issues" (switches to Preflight mode); exporting is never blocked.
- **Acceptance:**
    - [ ] JSON output validates against `schema/preflight-report.schema.json`.

## 11. P8 — Multi-page and data merge

P8 makes booklets and batch documents work: pages sidebar, spreads, page templates, fields, story flow across pages, TOC, data merge, programme sessions from CSV, merge export and booklet imposition. Exit: a 48-page booklet and 200 certificates from CSV.

### T8.1 Pages sidebar

- **Depends on:** T1.17. **Spec:** §5 Left sidebar. **UI:** `ui/12-booklet.png` (left). **Files:** `app/src/workspace/sidebar/{PagesTab.svelte,PageThumb.svelte}`, `app/src-tauri/src/commands/thumbs.rs`, `crates/frisket-model/src/command/pages.rs`.
- **Steps:** PAGE TEMPLATES cards (filled by T8.3) and PAGES thumbnails (PNG at 160 px, rendered async and cached by page rev), shown as spreads when facing pages are on, with labels ("Cover", "2", "Pages 3–4 · Day 1" — section label from T8.4); add, duplicate, delete, reorder by drag (one command).
- **Acceptance:**
    - [ ] A 64-page document scrolls at 60 fps in the sidebar; reorder is one command.

### T8.2 Facing pages and spreads on the canvas

- **Depends on:** T8.1. **Files:** `crates/frisket-model/src/document/spread.rs`, `app/src/canvas/Spreads.svelte`.
- **Steps:** document setting single pages / facing pages (first page on the right). Canvas lays out spreads side by side; inside/outside margins mirror (THEMES §4 booklet rows). Format minor bump (first change of P8).
- **Acceptance:**
    - [ ] Toggling facing pages is undoable and re-mirrors margins.

### T8.3 Page templates

- **Depends on:** T8.1, T2.8. **Spec:** F10, §7 PageTemplate. **Files:** `crates/frisket-model/src/document/page_template.rs`, `crates/frisket-typeset/src/codegen/template.rs`, `app/src/views/PageTemplateEditor.svelte`.
- **Steps:** a template holds background items, grid, header/footer stories and fields, with left/right variants for facing pages; pages reference a template; editing a template updates every page using it; an item can be overridden on one page ("Detach from template"). Template cards in the Pages tab ("Programme · 2 columns · footer", "Divider · full-bleed day").
- **Acceptance:**
    - [ ] Changing a template footer updates 48 pages in one command; overrides survive template edits.

### T8.4 Fields: page numbers and running headers

- **Depends on:** T8.3. **Files:** `crates/frisket-model/src/text/field.rs`, `crates/frisket-typeset/src/codegen/fields.rs`.
- **Steps:** inline field nodes: page number, page count, section name, document title, date. Numbering format (1, i, I, a) and start per section (sections defined on pages).
- **Acceptance:**
    - [ ] Golden test: roman numerals for the front matter, then arabic from page 5.

### T8.5 Story flow across pages (Document Flow)

- **Depends on:** T2.8, T8.3. **Spec:** §6 Layout pipeline (Document Flow). **Files:** `crates/frisket-typeset/src/document_flow.rs`, `crates/frisket-features/src/autoflow.rs`.
- **Steps:** pages in `DocumentFlow` mode let Typst paginate one story natively across consecutive pages that share a template (Specification §6). "Autoflow": when the story oversets its last page, add pages with the same template until it fits (cap 200 pages); removing text removes empty pages that autoflow created (flagged `autoflow: true`), never user-created pages. The canvas note "Text flows from page 3 into page 4 · 1 story, 2 frames" (mockup 12).
- **Acceptance:**
    - [ ] Pasting 10,000 words into the programme template produces the expected page count; deleting the text shrinks it back.

### T8.6 Table of contents

- **Depends on:** T8.4, T2.7. **Spec:** F10. **Files:** `crates/frisket-model/src/blocks/toc.rs`, `crates/frisket-typeset/src/codegen/toc.rs`.
- **Steps:** TOC block lists paragraphs with chosen styles (levels 1–3) and page numbers with dot leaders (Typst `outline` driven by Frisket-generated headings/labels); updates automatically.
- **Acceptance:**
    - [ ] TOC page numbers correct after inserting pages before the target headings.

### T8.7 Data merge

- **Depends on:** T5.3, T2.4. **Spec:** F10. **UI:** `ui/07-data-merge.png`. **Files:** `crates/frisket-features/src/merge/{source.rs,field.rs,engine.rs}`, `app/src/views/merge/{MergeInspector.svelte,RecordStepper.svelte}`.
- **Steps:** attach a CSV/XLSX as merge source (linked and watched, "Sheet "Registered" · 214 rows · linked, watching", "Change…"); insert `{{field}}` merge-field nodes in text (outline tag `field`); fields can also drive image paths and QR content. Inspector tabs Data / Fields / Output: Data = source + preview table (#, columns) with the current record highlighted; Fields = FIELD MAPPING rows `{{name}} ← column` dropdowns; Output = One PDF / One file per person, file-name pattern (`cert_{{full_name}}.pdf`), "Export n certificates". Canvas: record stepper "‹ Prev · Record 3 of 214 · Next ›" and "Show real data" checkbox. Per-record overflow warnings (e.g. names too long: they shrink to fit down to the style minimum) listed under the page with "Show records …" links.
- **Acceptance:**
    - [ ] The 200-row certificate fixture previews any record in < 100 ms; missing fields are highlighted.
    - [ ] Views match mockup 07.

### T8.8 Programme sessions from CSV

- **Depends on:** T8.7, T8.5. **UI:** `ui/12-booklet.png`. **Files:** `crates/frisket-features/src/merge/repeating.rs`.
- **Steps:** a "repeating block" (session: time, room, title, chair, talks) expands once per row, grouped by a column (e.g. day), into the Document Flow story, using the booklet styles of T2.7 (Day heading, Session title, Time & room, Talk title, Speaker).
- **Acceptance:**
    - [ ] The sessions fixture (3 days, 12 sessions, 41 talks) builds a programme with the structure of mockup 12; style usage counts equal 3/12/12/41/41.

### T8.9 Merge export

- **Depends on:** T8.7, T6.2. **Files:** `crates/frisket-render/src/export/merge.rs`, `crates/frisket-cli/src/cmd/merge.rs`.
- **Steps:** one PDF (one set of pages per record) or one file per record named from the field template (sanitise `/ : \ * ? " < > |` and control characters; de-duplicate with `-2`, `-3`). Reuse measurement caches across records. Available in the Output tab, the Export sheet and `frisket merge <file> [--out DIR] [--single]`.
- **Acceptance:**
    - [ ] 200 certificates export in < 30 s; file names are sanitised and unique.

### T8.10 Booklet imposition

- **Depends on:** T6.2, T8.2. **Spec:** F9. **Files:** `crates/frisket-render/src/impose.rs`.
- **Steps:** saddle-stitch: pad to a multiple of 4 with blank pages (warning in the sheet), pair pages (n, 1), (2, n−1), …, place two pages per sheet side on a sheet of 2 × page width (A5 pages on A4 landscape); the first sheet carries duplex short-edge instructions in the slug. Enables "Booklet print" in the Export sheet.
- **Acceptance:**
    - [ ] Pair-order unit tests for 4, 8, 16 and 52 pages; a printed 8-page test booklet folds in order (manual).

## 12. P9 — Import

P9 brings content in from Word, Markdown, Quarto, the clipboard and PowerPoint posters, mapped onto the structured model. Build 0.5 "Beta" is tagged at the end of P9.

### T9.1 Import framework

- **Depends on:** T3.5. **Spec:** §8 Import mapping. **Files:** `crates/frisket-import/src/{tree.rs,apply.rs,issue.rs}`.
- **Steps:** importers produce a `ContentTree` (sections with heading text, paragraphs as story nodes, images as bytes + name, tables, equations, lists) plus `ImportIssue`s (skipped content, with location). `apply(tree, &Document) -> Command` maps the tree into the document's structure preset: section headings matched to roles case-insensitively by a synonym table (`background|introduction → background`, `aims|objectives|purpose → objectives`, `methods|methodology|patients and methods → methods`, `results|findings → results`, `conclusion(s)|discussion → conclusions`), unmatched sections appended in order. Import is one undo step.
- **Acceptance:**
    - [ ] Applier unit tests with synthetic trees; undo removes the whole import.

### T9.2 DOCX importer

- **Depends on:** T9.1. **Files:** `crates/frisket-import/src/docx/{mod.rs,document.rs,styles.rs,numbering.rs,rels.rs}`, `fixtures/import/docx/*`.
- **Steps:** unzip with `zip`, parse `word/document.xml`, `styles.xml`, `numbering.xml`, relationships with `quick-xml`. Heading 1–2 → sections; bold/italic/super/subscript runs; lists; inline images → figures; tables → table blocks; OMML equations skipped with an issue.
- **Acceptance:**
    - [ ] Five DOCX fixtures (abstract, with table, with images, with lists, Romanian diacritics) import as specified.

### T9.3 Markdown and Quarto importer

- **Depends on:** T9.1, T5.4. **Files:** `crates/frisket-import/src/markdown/{mod.rs,qmd.rs}`, `fixtures/import/md/*`.
- **Steps:** `comrak` for CommonMark + GFM tables. QMD: parse YAML front matter (`title`, `author` → header), skip code chunks, keep chunk figure outputs only if the paths exist, `$…$`/`$$…$$` → inline/display equations (LaTeX syntax), `[@key]` → citation nodes when a bibliography is linked.
- **Acceptance:**
    - [ ] Four fixtures (plain MD, GFM tables, QMD with front matter and chunks, math) import as specified.

### T9.4 "Start from a file" on the Home board

- **Depends on:** T9.2, T9.3, T3.12. **UI:** `ui/01-home.png` (OR START FROM A FILE). **Files:** `app/src/home/StartFromFile.svelte`, `app/src/sheets/ImportPreviewSheet.svelte`.
- **Steps:** enable "Abstract or manuscript" (.docx, .md, .qmd → preview of detected sections, then choose kind: poster by default) and "Spreadsheet list" (.csv, .xlsx → certificate or badges with the merge source attached). Dropping a `.docx` on the window does the same. "PowerPoint poster" is enabled by T9.6.
- **Acceptance:**
    - [ ] Creating a poster from the DOCX abstract fixture fills Background, Methods, Results, Conclusions.

### T9.5 Rich clipboard paste

- **Depends on:** T9.1, T5.3. **Files:** `crates/frisket-import/src/clipboard.rs`, `app/src/editor/paste.ts`.
- **Steps:** in the overlay editor, pasted HTML maps headings, bold, italic, lists and links to theme styles and drops foreign fonts and colours (default "Paste and match style"; `⌥⇧⌘V` keeps character formatting). Outside text editing: images → figure; TSV or HTML table → table block.
- **Acceptance:**
    - [ ] Paste fixtures captured from Word, Pages and Safari produce clean theme-styled text.

### T9.6 PPTX poster importer

- **Depends on:** T9.1, T1.13, T5.1. **Spec:** F11. **Files:** `crates/frisket-import/src/pptx/{mod.rs,shapes.rs,text.rs,theme.rs}`, `fixtures/import/pptx/*`.
- **Steps:** each slide → a Free page of the slide size; walk the shape tree (group transforms included): text boxes → Free text frames with runs (fonts mapped to the metric-compatible bundled family: Arial/Helvetica → Liberation Sans, Times New Roman → Liberation Serif, Calibri → Carlito, Cambria → Caladea); pictures → embedded figures; rectangles/ellipses/lines → shapes; tables → table blocks; theme colours → document palette. SmartArt and charts import as their cached image when present, else an issue. Enables "PowerPoint poster" on the Home board.
- **Acceptance:**
    - [ ] Three real-world poster fixtures import with every text box and picture at the correct position (±1 pt).

### T9.7 Convert to structured layout

- **Depends on:** T9.6, T3.9. **Files:** `crates/frisket-features/src/convert.rs`, `app/src/sheets/ConvertSheet.svelte`.
- **Steps:** infer columns from frame x-positions (1-D clustering), reading order (column-major), sections (large bold text followed by body text), header (topmost wide band). The sheet shows the proposed outline and grid; the user adjusts and applies; result: a Flow page with the same content (one command).
- **Acceptance:**
    - [ ] On the three PPTX fixtures, ≥ 80% of text frames land in the correct section in the correct order (scored against hand-labelled expectations).

### T9.8 Tag 0.5 "Beta"

- **Depends on:** T9.1–T9.7, T8.1–T8.10. **Files:** `CHANGELOG.md`, `docs/beta.md`.
- **Steps:** tag, publish on Gitea, write a short beta tester guide.
- **Acceptance:**
    - [ ] Two colleagues produce a poster end to end and file feedback issues.

## 13. P10 — Assistant, polish and release

P10 adds the optional assistant, the Settings tab, accessibility, the command palette, onboarding, updates, performance work, documentation, applies the licence decision and tags 1.0.

### T10.1 Assistant endpoint and guardrails

- **Depends on:** T3.5. **Spec:** F12. **Files:** `crates/frisket-features/src/assistant/{client.rs,guard.rs,prompts.rs}`, `app/src-tauri/src/commands/assistant.rs`.
- **Steps:** OpenAI-compatible chat-completions client (`POST {endpoint}/v1/chat/completions`) using the HTTP client already in the Tauri dependency tree (no new crate; if none is available, ask). Endpoint, model name and optional API key are set in Settings › Assistant; all assistant UI is hidden when no endpoint is set. `guard::check(source, output)` extracts numbers, percentages, p-values, confidence intervals, citation nodes and cross-references from both texts; any mismatch rejects the output.
- **Acceptance:**
    - [ ] Guard tests: rejects outputs that change "HR 0.72 (95% CI 0.61–0.85)", drop a citation, or alter "p < 0.001"; UI absent with no endpoint (Vitest).

### T10.2 "Make it fit", alt-text draft, split into sections

- **Depends on:** T10.1, T7.7. **Files:** `crates/frisket-features/src/assistant/{fit.rs,alt_text.rs,split.rs}`, `app/src/sheets/SuggestionDiff.svelte`.
- **Steps:** "Make it fit" asks for up to 3 shorter versions of an overflowing section, shown as a word diff; accepting applies one command. Alt-text draft from caption, figure label and file name. Section splitter proposes IMRaD sections from pasted abstract text. Also offered as a preflight fix for overflow.
- **Acceptance:**
    - [ ] Nothing is applied without explicit acceptance; every suggestion passes the guard or is not shown (tested with a mock endpoint).

### T10.3 Settings tab

- **Depends on:** T4.10, T10.1, T6.9. **Spec:** F14 Settings. **UI:** `ui/10-settings.png`. **Files:** `app/src/settings/{Settings.svelte,General.svelte,Fonts.svelte,FiguresR.svelte,ExportDefaults.svelte,Assistant.svelte,CommandLine.svelte,Updates.svelte}`, `app/src-tauri/src/{settings.rs,commands/settings.rs}`, `app/src-tauri/src/cli_install.rs`.
- **Steps:** sections exactly as mockup 10 and Specification F14. Fonts page = mockup 10 (table of built-in families with sample "The quick brown fox · 0123456789 · α β µ ±", replaces, licence chip; toggle "Also show fonts installed on this Mac"; default body and heading font; "Equations — Latin Modern Math (built in)"; footer note). Command line: "Install command-line tool" symlinks the bundled sidecar to `/usr/local/bin/frisket` (asks for admin rights via `osascript` only if needed) or `~/.local/bin/frisket`. Settings stored in `app_data_dir()/settings.json` with unknown keys kept (contract §9). Status bar: "Frisket <version> (build n) · Format x.y · Up to date".
- **Acceptance:**
    - [ ] Every setting persists and applies without restart; Fonts page matches mockup 10.

### T10.4 Accessibility pass

- **Depends on:** T10.3, T7.9, T8.7, T9.4. **Files:** across `app/src/`, `app/src/canvas/a11y.ts`.
- **Steps:** accessible names and roles on every control; the canvas exposes blocks as an ARIA list in reading order with role and summary; full keyboard navigation (Tab through blocks, arrows nudge, `⌘K` palette); honour `prefers-reduced-motion` and `prefers-contrast`; light and dark chrome.
- **Acceptance:**
    - [ ] axe-core audit (Playwright `@axe-core/playwright`, add to allowed UI dev packages in this task) reports no serious or critical violations on Home, workspace, Preflight, Export and Settings; a poster can be edited keyboard-only.

### T10.5 Command palette and shortcuts

- **Depends on:** T3.4. **Spec:** §5 Interaction model. **Files:** `app/src/lib/actions.ts`, `app/src/sheets/CommandPalette.svelte`, `docs/shortcuts.md`.
- **Steps:** one action registry (id, title, shortcut, handler, enabled predicate) used by menus, toolbar and palette. `⌘K` opens a searchable list of every action and block insert with shortcuts shown. Help → Keyboard Shortcuts shows `docs/shortcuts.md` content.
- **Acceptance:**
    - [ ] A test compares the registry with the native menu: every menu item is in the palette.

### T10.6 Onboarding and sample documents

- **Depends on:** T9.8. **Files:** `resources/samples/{sample-poster.frisket,sample-booklet.frisket}`, `app/src/home/Onboarding.svelte`.
- **Steps:** first launch opens the Home tab with a dismissible banner "New to Frisket? Open the sample poster"; samples open read-write copies with inline tips (dismissed state stored in settings, never shown again).
- **Acceptance:**
    - [ ] First launch shows the banner; tip state persists across launches.

### T10.7 Updates

- **Depends on:** T6.10, T10.3. **Spec:** §11 Distribution without notarization. **Files:** `app/src-tauri/src/updater.rs`, `.gitea/workflows/release.yml`, `docs/releasing.md`.
- **Steps:** `tauri-plugin-updater` with a minisign key pair (private key and password in Gitea secrets `TAURI_SIGNING_PRIVATE_KEY`, `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`); the release job builds, signs, uploads `.app.tar.gz`, `.sig`, `.dmg` and `latest.json` to the Gitea release. Check daily (setting in Updates). Record in `docs/releasing.md` whether an updated ad-hoc-signed build needs Gatekeeper re-approval.
- **Acceptance:**
    - [ ] Installing 0.9.0 then publishing 0.9.1 offers and installs the update on a test Mac; the Gatekeeper finding is documented.

### T10.8 Performance pass

- **Depends on:** T8.10, T9.7. **Spec:** §9 targets. **Files:** `crates/*/benches/*.rs`, `app/e2e/perf/*.spec.ts`, `.gitea/workflows/nightly.yml`.
- **Steps:** a benchmark per Specification §9 target using the reference poster and a 48-page booklet fixture (`fixtures/reference/booklet-48.frisket`); nightly fails on > 20% regression against the stored baseline; profile and fix until all targets pass.
- **Acceptance:**
    - [ ] All §9 targets met in three consecutive nightly runs.

### T10.9 Documentation

- **Depends on:** T10.8. **Files:** `docs/user-guide/*.md`, `docs/format/*.md`, `README.md`.
- **Steps:** user guide: getting started, the R workflow (watched folders, theme export, CLI in a pipeline), preflight, export, data merge; final format documentation per format version; README install section with the Gatekeeper screenshots.
- **Acceptance:**
    - [ ] A new user follows the getting-started guide to a printed poster without other help.

### T10.10 Apply the licence decision

- **Depends on:** T10.9. **Spec:** §1 Licence, §12 Open questions. **Files:** `LICENSE` or `EULA.md`, all source headers, `README.md`, `THIRD_PARTY.md`, `.gitea/workflows/release.yml`.
- **Steps:** requires the owner's written decision (an ADR). If open source: add `LICENSE` (GPL-3.0-or-later), replace headers with SPDX lines, add `CONTRIBUTING.md` with DCO sign-off. If commercial: add the EULA, keep headers, add Developer ID signing and notarization (`APPLE_*` secrets) to the release job. In both cases regenerate `THIRD_PARTY.md` and show it in Settings › About.
- **Acceptance:**
    - [ ] ADR with the decision merged; release job builds with the chosen signing path.

### T10.11 Release 1.0

- **Depends on:** T10.1–T10.10. **Files:** `CHANGELOG.md`.
- **Steps:** freeze the format version for 1.0 (compat fixtures added), final bug bash against the Appendix fixtures, tag `v1.0.0`, publish (Gitea release; public channel per the licence ADR; GitHub mirror stays a mirror).
- **Acceptance:**
    - [ ] Zero open issues labelled `release-blocker`; the release is installable and updatable.

## 14. Appendix — reference fixtures and glossary

### Reference poster (from T5.11 onward)

A0 portrait, Clinical navy theme, `three-columns` layout, Classic pairing, viewing distance 1.5 m, containing:

- Header with a 2-line title, 6 authors, 3 affiliations, 2 logos (one SVG, one PNG).
- Sections: Background, Objectives, Methods (with a CONSORT 2-arm diagram), Results, Conclusions (callout with key figure), References (30 Vancouver entries), Contact & QR (DOI).
- 6 figures: 4 vector PDFs from R (one linked through a watched folder), 1 SVG, 1 raster PNG placed at 96 ppi (to trigger preflight).
- 2 tables: one imported from XLSX with merged header cells, one from CSV with decimal-aligned numbers.
- 2 display equations and 3 inline equations (LaTeX input).
- 3 icons from the library (credits line active).

### Fixture catalogue

| Folder | Contents | First used | Supplied by |
| --- | --- | --- | --- |
| `fixtures/format/` | older, newer-minor, newer-major, corrupt, unknown-field documents | T1.4 | Agent |
| `fixtures/compat/<version>/` | One folder per released format version (never edited or deleted) | T1.17 | Agent |
| `fixtures/text/` | Stories: Latin, Romanian diacritics, RTL, emoji, every node/mark, 5,000-word benchmark | T2.1 | Agent |
| `fixtures/layout/` | Flow cases (25), arrange cases (10), table cases (8), JSON goldens | T3.2 | Agent |
| `fixtures/figures/` | km.pdf, km.svg (generated by `km.R`), forest.png (96 ppi at 20 cm), photo.jpg, multi-page.pdf | T0.12 / T4.2 | **Human** (real ggplot2 exports) |
| `fixtures/tables/` | CSV (comma, semicolon, BOM, Windows-1250), XLSX (merges, dates) | T5.3 | Agent (XLSX: human) |
| `fixtures/citations/` | 50-entry BibTeX, 100-entry BibTeX, CSL-JSON sample, expected outputs per style | T0.12 / T5.5 | **Human** (real BibTeX) |
| `fixtures/preflight/` | One positive and one negative document per rule | T7.2 | Agent |
| `fixtures/merge/` | 200-row certificates CSV (`full_name,specialty,city,credits`), sessions CSV (3 days, 12 sessions, 41 talks) | T8.7 | Agent |
| `fixtures/import/` | DOCX (5), MD/QMD (4), paste captures, PPTX posters (3) with labelled expectations | T9.2 | **Human** (DOCX, PPTX, paste captures) |
| `fixtures/reference/` | reference-poster.frisket, booklet-48.frisket | T5.11 / T10.8 | Agent + human review |
| `fixtures/snapshots/` | Reference PNGs for snapshot tests | T1.7 | Agent (recorded) |

Real-world PPTX posters must be the owner's own or openly licensed; strip personal data before committing.

### Glossary

| Term | Meaning in Frisket |
| --- | --- |
| Block | Any placed content item: section, figure, table, equation, callout, QR, shape, icon, text frame |
| Flow page | Page whose blocks are stacked into grid columns by the Flow solver |
| Document Flow | Pages on which one story is paginated by Typst across consecutive pages (booklets) |
| Free frame | Block with absolute geometry, not managed by the Flow solver |
| Story | Rich text content that can thread through several text frames |
| Overflow | Flow content that does not fit on the page |
| Overset | Story text that does not fit in its last frame |
| Theme token | Named value (colour, size, spacing) resolved per document kind and viewing distance |
| Watched folder | Folder monitored with `notify`; changed figures refresh automatically |
| Page template | Master page: shared background, header/footer, fields |
| Preflight rule | Check producing issues, each with explanation and optional fix command |
| Command | Value describing an edit that can apply itself and produce its inverse |
| Session | The Rust-side state of one open document: model, history, rev, path |
| Tab | A UI slot in the single window: Home, a document, or Settings |
| Sheet | A dialog shown inside the current tab (Export, file version, recovery, relink) |
| Rev | Monotonic revision number of a session; render results carry it so stale ones are discarded |
| Codegen | Generation of Typst markup from the model at runtime; never stored |
| Layout map | Block id → page rectangles, returned with every render, used by overlays and hit testing |
