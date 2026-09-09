#!/usr/bin/env python3
"""
Move every .md note tagged 'clippings' into a single folder.

Usage:
    python move_clippings.py --vault "C:\\path\\to\\your\\vault"
    python move_clippings.py --vault "C:\\path\\to\\your\\vault" --dry-run

By default notes are moved into a "clippings" folder created inside --vault.
Use --dest to pick a different destination. Run with --dry-run first to see
what would move without touching any files.
"""

import argparse
import sys
from pathlib import Path

from vault_utils import note_has_tag


def find_matches(vault_path, dest_path, tag):
    matches = []
    errors = []
    dest_resolved = dest_path.resolve()

    for md_path in sorted(vault_path.rglob("*.md")):
        if dest_resolved == md_path.resolve().parent:
            continue  # already in the destination folder

        try:
            text = md_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            errors.append((md_path, str(e)))
            continue

        matched, parse_error = note_has_tag(text, tag)
        if parse_error:
            errors.append((md_path, f"frontmatter YAML error: {parse_error}"))
            continue
        if matched:
            matches.append(md_path)

    return matches, errors


def unique_destination(dest_dir, filename):
    """Avoid overwriting an existing file of the same name in dest_dir."""
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    n = 2
    while True:
        candidate = dest_dir / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault", required=True, help="Path to your Obsidian vault (or a folder within it)")
    parser.add_argument("--dest", default=None, help="Destination folder (default: <vault>/clippings)")
    parser.add_argument("--tag", default="clippings", help="Tag to filter on (default: clippings)")
    parser.add_argument("--dry-run", action="store_true", help="List what would move, without moving anything")
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser()
    if not vault_path.is_dir():
        print(f"Error: {vault_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    dest_path = Path(args.dest).expanduser() if args.dest else vault_path / "clippings"

    matches, errors = find_matches(vault_path, dest_path, args.tag)

    if errors:
        print(f"Skipped {len(errors)} file(s) due to errors:", file=sys.stderr)
        for path, err in errors:
            print(f"  {path}: {err}", file=sys.stderr)

    if not matches:
        print(f"No notes tagged '{args.tag}' found under {vault_path}")
        return

    print(f"{'Would move' if args.dry_run else 'Moving'} {len(matches)} note(s) to {dest_path}:")
    for md_path in matches:
        print(f"  {md_path.relative_to(vault_path)}")

    if args.dry_run:
        print("\nDry run only, nothing was moved. Re-run without --dry-run to move these files.")
        return

    dest_path.mkdir(parents=True, exist_ok=True)
    for md_path in matches:
        target = unique_destination(dest_path, md_path.name)
        md_path.rename(target)

    print(f"\nMoved {len(matches)} note(s) into {dest_path}")


if __name__ == "__main__":
    main()
