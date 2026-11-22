"""Portable, local-only HTTPS bookmarks. Python 3.10+, standard library only."""
import argparse
import html
import json
import os
import sys
from pathlib import Path
import tempfile
from urllib.parse import urlsplit, urlunsplit


def normalize_url(value):
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
        raise ValueError("URL must be a nonempty HTTPS address without whitespace")
    parts = urlsplit(value)
    if parts.scheme.lower() != "https" or not parts.hostname:
        raise ValueError("Only HTTPS bookmarks are supported")
    if parts.username is not None or parts.password is not None:
        raise ValueError("Do not store credentials in bookmark URLs")
    host = parts.hostname.encode("idna").decode("ascii").lower()
    if ":" in host:
        host = "[" + host + "]"
    port = parts.port
    authority = host + (":" + str(port) if port and port != 443 else "")
    return urlunsplit(("https", authority, parts.path or "/", parts.query, parts.fragment))


def validate(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Expected an object with version: 1")
    if not isinstance(data.get("bookmarks"), list):
        raise ValueError("bookmarks must be an array")
    result, seen = [], set()
    for row in data["bookmarks"]:
        if not isinstance(row, dict):
            raise ValueError("Every bookmark must be an object")
        url = normalize_url(row.get("url"))
        title, tags = row.get("title"), row.get("tags", [])
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Every bookmark needs a nonempty title")
        if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
            raise ValueError("tags must be an array of nonempty strings")
        if url in seen:
            raise ValueError("Duplicate normalized URL: " + url)
        seen.add(url)
        result.append({"url": url, "title": title.strip(), "tags": sorted(set(t.strip() for t in tags))})
    return {"version": 1, "bookmarks": result}


def load(path):
    path = Path(path)
    if not path.exists():
        return {"version": 1, "bookmarks": []}
    return validate(json.loads(path.read_text(encoding="utf-8")))


def save(path, data):
    # Validate before opening a temporary file. Malformed input never replaces the original.
    payload = json.dumps(validate(data), ensure_ascii=False, indent=2) + "\n"
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def export_html(data, tag=None):
    rows = validate(data)["bookmarks"]
    if tag:
        rows = [r for r in rows if tag in r["tags"]]
    items = "\n".join('<li><a rel="noopener noreferrer" href="' + html.escape(r["url"], quote=True) + '">' + html.escape(r["title"]) + '</a> <small>' + html.escape(", ".join(r["tags"])) + '</small></li>' for r in rows)
    return '<!doctype html>\n<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Puzzle shortlist</title><body><h1>Puzzle shortlist</h1><p>A local bookmark export. No remote scripts or analytics.</p><ul>\n' + items + '\n</ul></body></html>\n'


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default="shortlist.json", help="local JSON file; parent directory must exist")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="add one bookmark; duplicate URLs are rejected")
    add.add_argument("url")
    add.add_argument("--title", required=True)
    add.add_argument("--tag", action="append", default=[])
    listing = commands.add_parser("list", help="print JSON to stdout")
    listing.add_argument("--tag")
    export = commands.add_parser("html", help="print an HTML document to stdout")
    export.add_argument("--tag")
    commands.add_parser("check", help="validate an existing file")
    args = parser.parse_args(argv)
    try:
        data = load(args.file)
        if args.command == "add":
            data["bookmarks"].append({"url": args.url, "title": args.title, "tags": args.tag})
            save(args.file, data)
            print("Saved bookmark")
        elif args.command == "html":
            print(export_html(data, args.tag), end="")
        elif args.command == "list":
            selected = [r for r in data["bookmarks"] if not args.tag or args.tag in r["tags"]]
            print(json.dumps(selected, ensure_ascii=False, indent=2))
        else:
            if not Path(args.file).exists():
                raise ValueError("No shortlist file exists yet")
            print("Valid shortlist: " + str(len(data["bookmarks"])) + " bookmarks")
    except (ValueError, TypeError, UnicodeError, OSError) as error:
        parser.exit(2, "Error: " + str(error) + "\n")


if __name__ == "__main__":
    main()

