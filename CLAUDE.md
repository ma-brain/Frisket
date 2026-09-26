# Frisket — instructions for implementing agents

Frisket is a desktop publisher for scientific posters, flyers, booklets and certificates: Tauri 2 shell, Rust core crates, Svelte 5 UI, Typst as the layout and PDF engine. macOS first.

## Read before any work

1. `plans/Working-plan.md` §1 (session loop, hard rules) and §2 (conventions, definition of done). They are binding.
2. The task you were given in `plans/Working-plan.md`, its "Depends on" tasks, and every section it cites in:
   - `plans/Specification.md` — behaviour and architecture,
   - `plans/File-format-contract.md` — anything written to disk,
   - `plans/THEMES.md` — every colour, font, size and margin.
3. The mockup(s) the task names in `ui/`.

Precedence when documents disagree: Specification > File-format-contract > THEMES > Working-plan > mockups.

## Session loop (short form)

One task per session, in id order. Check dependencies are merged → restate acceptance criteria → tests first (show them failing) → smallest implementation → `make check` green with zero warnings → branch `t<ID>-<slug>` → pull request `T<ID>: <title>` with the ticked acceptance checklist and how each item was verified → stop.

## Never

- Change the file format without the File-format-contract §10 checklist.
- Add a dependency that is not listed in Specification §6 or Working-plan §2.
- Put Tauri/webview/UI code in `crates/`, or Typst code outside `frisket-typeset` / `frisket-render`.
- Mutate document data from Svelte; every edit is a `Command` via `doc_apply`.
- Hand-write TypeScript types for Rust structs; run `cargo xtask bindings`.
- Store Typst markup in the model or the file; escape every user string with `codegen::escape`.
- Invent a design value; ask if THEMES.md lacks it.
- Skip, ignore or weaken a failing test.
- Use `unsafe`, or `unwrap`/`expect` outside tests without a proof comment.

## Commands

| Command | Purpose |
| --- | --- |
| `make check` | Everything CI runs (format, clippy, tests, licences, schema, bindings, layering, UI checks) |
| `make test` | Rust and UI unit tests |
| `make e2e` | Playwright flows with mocked IPC |
| `make dev` | Run the app |
| `cargo xtask bindings` | Regenerate `app/src/lib/bindings.ts` |
| `cargo xtask schema` | Regenerate the JSON Schema of the current format version |
| `python3 plans/tasks_csv.py` | Regenerate `plans/TASKS.csv` after editing the Working plan |

## When stuck

After two failed attempts at the same error, stop and report in the pull request: what you tried, the exact error, the smallest reproduction. For Typst, read the pinned crate's source, not memory. For Tauri, use v2 docs only.
