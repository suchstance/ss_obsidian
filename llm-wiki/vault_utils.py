"""Shared helpers for reading Obsidian note frontmatter and tags."""

import datetime

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
    return f"#{tag}" in body


def note_has_tag(text, tag):
    """True if a note's raw text carries `tag` in frontmatter tags or as an inline #tag."""
    fm, body = split_frontmatter(text)
    fm = fm or {}
    if "__parse_error__" in fm:
        return False, fm["__parse_error__"]
    tags = normalize_tags(fm.get("tags"))
    return (tag in tags or has_inline_tag(body, tag)), None
