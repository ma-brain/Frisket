# Frisket — File format contract

Binding for every build from the moment format 1.0 is frozen (end of P1). Companion to [Specification.md](Specification.md) §7. Any change to what is written to disk follows the checklist at the end.

## 1. Promise

1. A `.frisket` file saved by any released build opens in every later build. No "pre-release" exemption after 1.0 is frozen.
2. Opening never changes the file on disk. Only an explicit save writes it, and a save that upgrades the format first keeps a backup.
3. A file from a newer build never loses data: it opens read-only when it cannot be understood fully, and unknown fields survive a save when it can.
4. No save can corrupt an existing file: writes are atomic and validated.

## 2. Container

A `.frisket` file is a ZIP archive (deflate; `mimetype` stored first, uncompressed, like ODF/EPUB so tools can sniff it).

| Path | Required | Content |
| --- | --- | --- |
| `mimetype` | yes | `application/vnd.frisket+zip` (no newline) |
| `manifest.json` | yes | Format and writer metadata (§3) |
| `document.json` | yes | The document model (Specification §7), UTF-8 JSON |
| `assets/<sha256>.<ext>` | no | Embedded assets, named by content hash |
| `assets/preview/<sha256>.png` | no | Cached preview of each linked asset (max 2048 px long edge), so a document with a missing link still renders (Working-plan T4.1) |
| `styles/<name>.csl` | no | User-added CSL citation styles used by the document (T5.6) |
| `preview.png` | no | First page, 512 px on the long edge, for Finder and the Home board |
| `extensions/<name>/…` | no | Reserved for future optional data; readers ignore unknown folders and keep them on save |

Linked assets' original bytes are not stored (only their cached preview); `document.json` records their relative path, absolute path hint and SHA-256. Snapshots, autosaves and undo history are never stored in the file (they live in the app data folder).

## 3. Manifest

```json
{
  "formatVersion": "1.0",
  "minReaderVersion": "1.0",
  "writer": { "app": "Frisket", "version": "0.1.0", "build": 214, "typst": "0.15.0" },
  "created": "2026-09-26T12:41:00Z",
  "modified": "2026-09-26T12:41:00Z",
  "documentId": "0192…",
  "kind": "poster"
}
```

- `formatVersion` is `MAJOR.MINOR` and describes `document.json` and the container.
- `minReaderVersion` is the lowest format version a reader must support to edit the file safely. It equals `formatVersion` unless a writer knows the change is ignorable by older readers.
- `writer.typst` is diagnostic only. Files never store Typst code.

## 4. Versioning rules

| Change | Bump | Example |
| --- | --- | --- |
| Add an optional field with a default, a new enum value that older readers can render as a fallback, a new optional container folder | MINOR | `block.altText`, `shape: "hexagon"` rendered as rectangle |
| Rename or remove a field, change a unit or meaning, change a required structure | MAJOR | points → mm, rich-text schema change |

- Minor bumps are additive only; `cargo xtask schema-check` enforces this by diffing the committed JSON Schema.
- Version bumps are batched per implementation phase (Working-plan §1 "Format versions after 1.0 is frozen").
- The schema for every released version is committed as `schema/frisket-X.Y.schema.json` and never edited after release.
- Enum values unknown to a reader are preserved as-is and rendered with a documented fallback (unknown block type → grey placeholder box with its rect).

## 5. Reading a file

| File version vs this build (`F` file, `A` app) | Behaviour | UI (screen 11) |
| --- | --- | --- |
| `F == A` | Open normally | — |
| `F < A` (older) | Migrate in memory; open normally; file on disk untouched. On first save, write `name.vMAJ-MIN.frisket` backup next to the original, then save in format `A` | "This poster was saved by an older Frisket" — Open / Don't upgrade (Save As copy) |
| Same major, `F.minor > A.minor`, `minReaderVersion <= A` | Open and edit; unknown fields and folders preserved on save; `formatVersion` on save stays `F` | Small banner: "Made with a newer Frisket; some features may not show" |
| `minReaderVersion > A`, or `F.major > A.major` | Open read-only: view, preflight, export PDF/PNG. Save disabled; Save As writes nothing either | "This file is from a newer Frisket" — Check for updates / Open read-only |
| Unreadable (bad ZIP, missing `document.json`, invalid JSON) | Refuse; offer the latest autosave or snapshot for that `documentId` if one exists | Error sheet with "Reveal in Finder" |

## 6. Migrations

- Implemented in `crates/frisket-format` as a chain of pure functions `migrate_X_Y_to_X_Z(serde_json::Value) -> Result<Value>`, one per released version step, applied in order before deserialising into the current model.
- Migrations operate on JSON, never on the current Rust types, so old migrations never need to change when the model does.
- Each migration has a fixture test: input from `fixtures/compat/X.Y/`, expected output snapshot (insta).
- Unknown fields: the reader deserialises into typed structs with a `#[serde(flatten)] extra: Map<String, Value>` on every object, so unknown keys are carried and written back.

## 7. Writing a file

1. Serialise `document.json` deterministically (sorted keys, fixed float formatting) so write → read → write is byte-identical.
2. Validate against the current schema.
3. Write the ZIP to a temporary file in the same folder, `fsync`, re-open and read it back (manifest + JSON parse).
4. Atomically replace the original with a rename in the same folder. Keep the original's permissions.
5. On any failure the original is untouched and the error is shown; the autosave copy is kept.

Autosave (every 30 s and on window blur) writes the same container to the app data folder keyed by `documentId`; it never touches the user's file.

## 8. Compatibility corpus

- `fixtures/compat/<version>/` holds representative files saved by each released format version: blank, poster, booklet, merge certificate, every block type, linked and embedded assets, a file with unknown fields from a "future" minor version.
- Folders are added at each format release and are never edited or deleted.
- CI (`cargo test -p frisket-format --test compat`): every fixture opens, migrates, validates, renders (render snapshot within tolerance) and round-trips.

## 9. Related files with their own versions

| File | Rule |
| --- | --- |
| Conference preflight presets (`.json`) | Own `formatVersion`, same rules |
| Brand kits (`.frisket-brand`, ZIP) | Own `formatVersion`, same rules |
| User templates | Ordinary `.frisket` files |
| Settings (app data) | Migrated silently; unknown keys kept |

## 10. Change checklist

Every pull request that changes what is written to disk:

- [ ] ADR in `docs/adr/` describing the change and why.
- [ ] Minor or major bump decided per §4; `formatVersion` constant updated.
- [ ] New `schema/frisket-X.Y.schema.json` generated; `cargo xtask schema-check` passes.
- [ ] Migration function plus fixture test (major bumps, and minor bumps that need defaults filled).
- [ ] Fallback rendering for new enum values defined and tested with an older-reader fixture.
- [ ] New fixtures added under `fixtures/compat/X.Y/` at release.
- [ ] Screen 11 wording still correct.
