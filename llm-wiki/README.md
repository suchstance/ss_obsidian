# LLM Wiki over Clippings — Phase 1: Ingestion
#### Co-created with Claude Code

`scan_clippings.py` walks an Obsidian vault, finds every note tagged
`clippings` (in frontmatter `tags`, as a list or comma string, or as an
inline `#clippings` in the body), and writes a flat JSON index describing
them. It never modifies your vault — read-only.

## Usage

```bash
python3 scan_clippings.py --vault /path/to/your/vault
```

Options:
- `--vault` (required) — path to your vault, or any folder within it
- `--tag` — tag to filter on (default: `clippings`)
- `--output` — where to write the index (default: `index.json`)

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
