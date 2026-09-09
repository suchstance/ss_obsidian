# LLM Wiki over Clippings
#### Co-created with Claude Code

Both scripts share the same tag-matching logic (`vault_utils.py`): a note
matches `clippings` if that tag is in frontmatter `tags` (list or comma
string) or appears inline as `#clippings` in the body.

## `scan_clippings.py` — Phase 1: Ingestion

Walks an Obsidian vault, finds every note tagged `clippings`, and writes a
flat JSON index describing them. Read-only — never modifies your vault.

```bash
python3 scan_clippings.py --vault /path/to/your/vault
```

Options:
- `--vault` (required) — path to your vault, or any folder within it
- `--tag` — tag to filter on (default: `clippings`)
- `--output` — where to write the index (default: `index.json`)

## `move_clippings.py` — collect clippings into one folder

Moves every note tagged `clippings` into a single folder (default:
`<vault>/clippings`). Safe to re-run — notes already there are skipped, and
a name collision gets a `(2)`, `(3)`, ... suffix instead of overwriting.

```bash
# On Windows cmd/PowerShell (use `python` instead of `python3` if that's what you have):
python move_clippings.py --vault "C:\path\to\your\vault" --dry-run
python move_clippings.py --vault "C:\path\to\your\vault"
```

Options:
- `--vault` (required)
- `--dest` — destination folder (default: `<vault>/clippings`)
- `--tag` — tag to filter on (default: `clippings`)
- `--dry-run` — list what would move without touching any files (recommended first run)

Each entry in the index includes: `path`, `title`, `tags`, `moc`, `source`,
`description`, `created`, the full parsed `frontmatter`, the note `body`,
and a `content_hash` (sha256 of the raw file) — the hash lets later phases
skip notes that haven't changed since the last run.

## Known gap in current templates

`clipper_templates/goodreads.json` tags book notes with genre tags
(`genres/scifi`, etc.) but not the bare `clippings` tag, so book notes are
currently invisible to this scan. Only default clippings are available for the wiki creation

## Next phases

1. **Ingestion** (this script) — done.
2. **Connection-finding** — feed the index to Claude to propose related
   notes/topics across categories.
3. **Write-back** — insert a clearly-marked, idempotent `## Related` section
   into each note (frontmatter or body), never touching your own writing.
