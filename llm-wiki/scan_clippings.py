#!/usr/bin/env python3
"""
Phase 1 of the LLM wiki pipeline: scan an Obsidian vault, find every note
tagged 'clippings', and write a flat JSON index describing them.

Usage:
    python3 scan_clippings.py --vault /path/to/your/vault
    python3 scan_clippings.py --vault /path/to/your/vault --tag clippings --output index.json

The index is the input for later phases (connection-finding, write-back).
It is safe to re-run any time; it never modifies your vault.
"""

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

import yaml


def json_default(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return str(obj)


def split_frontmatter(text):
    """Return (frontmatter_dict, body) for a note's raw text, or (None, text)."""
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_text = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            try:
                fm = yaml.safe_load(fm_text)
            except yaml.YAMLError as e:
                return {"__parse_error__": str(e)}, body
            return (fm or {}), body
    return None, text


def normalize_tags(fm_tags):
    """Frontmatter 'tags' can be a YAML list or a comma-separated string. Return a clean list."""
    if fm_tags is None:
        return []
    if isinstance(fm_tags, str):
        return [t.strip().lstrip("#") for t in fm_tags.split(",") if t.strip()]
    if isinstance(fm_tags, list):
        out = []
        for t in fm_tags:
            if t is None:
                continue
            out.append(str(t).strip().lstrip("#"))
        return out
    return [str(fm_tags).strip().lstrip("#")]


def has_inline_tag(body, tag):
    needle = f"#{tag}"
    return needle in body


def scan_vault(vault_path, tag):
    vault_path = Path(vault_path)
    entries = []
    errors = []
    skipped_non_matching = 0

    for md_path in sorted(vault_path.rglob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            errors.append({"path": str(md_path), "error": str(e)})
            continue

        fm, body = split_frontmatter(text)
        fm = fm or {}

        if "__parse_error__" in fm:
            errors.append({"path": str(md_path), "error": f"frontmatter YAML error: {fm['__parse_error__']}"})
            continue

        tags = normalize_tags(fm.get("tags"))
        matched = tag in tags or has_inline_tag(body, tag)

        if not matched:
            skipped_non_matching += 1
            continue

        rel_path = str(md_path.relative_to(vault_path))
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        entries.append(
            {
                "path": rel_path,
                "title": fm.get("title") or md_path.stem,
                "tags": tags,
                "moc": fm.get("MoC") or fm.get("moc"),
                "source": fm.get("source") or fm.get("url"),
                "description": fm.get("description"),
                "created": fm.get("created") or fm.get("date"),
                "frontmatter": fm,
                "body": body.strip(),
                "content_hash": content_hash,
            }
        )

    return entries, errors, skipped_non_matching


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault", required=True, help="Path to your Obsidian vault (or a folder within it)")
    parser.add_argument("--tag", default="clippings", help="Tag to filter on (default: clippings)")
    parser.add_argument("--output", default="index.json", help="Where to write the JSON index (default: index.json)")
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser()
    if not vault_path.is_dir():
        print(f"Error: {vault_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    entries, errors, skipped = scan_vault(vault_path, args.tag)

    output_path = Path(args.output)
    output_path.write_text(
        json.dumps({"vault": str(vault_path), "tag": args.tag, "notes": entries}, indent=2, default=json_default),
        encoding="utf-8",
    )

    tag_counts = {}
    for e in entries:
        for t in e["tags"]:
            if t != args.tag:
                tag_counts[t] = tag_counts.get(t, 0) + 1

    print(f"Scanned vault: {vault_path}")
    print(f"Matched notes (tag '{args.tag}'): {len(entries)}")
    print(f"Skipped (no match): {skipped}")
    if tag_counts:
        print("Co-occurring tags:")
        for t, c in sorted(tag_counts.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
    if errors:
        print(f"Errors ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print(f"  {e['path']}: {e['error']}", file=sys.stderr)
    print(f"Index written to: {output_path}")


if __name__ == "__main__":
    main()
