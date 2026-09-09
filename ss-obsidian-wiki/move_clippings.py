"""
move_clippings.py

Scans a folder (and all subfolders) of Obsidian markdown notes, finds every
.md file whose frontmatter tags include "clippings" (or "#clippings"),
and MOVES those files into a "Clippings" folder inside that vault.
This assumes you do not save your web clippings into a folder, but use only tags to organize your vault.

Usage (Windows Command Prompt):
    python move_clippings.py --vault "C:\\Users\\YourName\\Documents\\ObsidianVault"

Usage (Mac/Linux Terminal):
    python3 move_clippings.py --vault /path/to/your/vault
"""

import argparse
import os
import shutil


def extract_frontmatter(text):
    """Return the text between the first two '---' lines, or None if no frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])

    return None  # no closing '---' found


def has_clippings_tag(frontmatter):
    """Check whether the frontmatter's tags include 'clippings' (with or without '#')."""
    if frontmatter is None:
        return False

    lines = frontmatter.splitlines()
    inside_tags_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith("tags:"):
            value = stripped.split(":", 1)[1].strip()
            if "clippings" in value.lower():
                return True
            inside_tags_block = True
            continue

        if inside_tags_block:
            if stripped.startswith("-"):
                if "clippings" in stripped.lower():
                    return True
                continue
            else:
                inside_tags_block = False

    return False


def find_clipping_notes(vault_path, destination_folder):
    matches = []

    for root, _dirs, files in os.walk(vault_path):
        # Don't scan inside the destination folder itself
        if os.path.abspath(root) == os.path.abspath(destination_folder):
            continue

        for filename in files:
            if not filename.lower().endswith(".md"):
                continue

            full_path = os.path.join(root, filename)

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, OSError) as e:
                print(f"  [skipped] Could not read {full_path}: {e}")
                continue

            frontmatter = extract_frontmatter(content)
            if has_clippings_tag(frontmatter):
                matches.append(full_path)

    return matches


def move_files(matches, destination_folder):
    os.makedirs(destination_folder, exist_ok=True)
    moved = []

    for path in matches:
        filename = os.path.basename(path)
        dest_path = os.path.join(destination_folder, filename)

        # avoid overwriting a file with the same name already in Clippings
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(destination_folder, f"{base} ({counter}){ext}")
                counter += 1

        shutil.move(path, dest_path)
        moved.append(dest_path)

    return moved


def main():
    parser = argparse.ArgumentParser(
        description="Scan an Obsidian vault for notes tagged 'clippings' and move them into a Clippings folder."
    )
    parser.add_argument("--vault", required=True, help="Path to your Obsidian vault folder")
    args = parser.parse_args()

    vault_path = args.vault

    if not os.path.isdir(vault_path):
        print(f"Error: '{vault_path}' is not a valid folder.")
        return

    destination_folder = os.path.join(vault_path, "Clippings")

    print(f"Scanning '{vault_path}' for notes tagged 'clippings'...\n")
    matches = find_clipping_notes(vault_path, destination_folder)

    if not matches:
        print("No notes found with a 'clippings' tag. Nothing to move.")
        return

    print(f"Found {len(matches)} note(s):")
    for path in matches:
        print(f"  {path}")

    print(f"\nMoving them into '{destination_folder}'...\n")
    moved = move_files(matches, destination_folder)

    print(f"Done. Moved {len(moved)} file(s) into:\n  {destination_folder}")


if __name__ == "__main__":
    main()
