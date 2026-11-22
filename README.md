# Portable puzzle shortlist

A small Python command-line tool for keeping your own puzzle bookmarks in a readable JSON file and exporting a local HTML page. It has no packages, login, server, remote requests, analytics, or game embeds. Python 3.10 or newer is required.

Use it when you want a file you can copy to another computer, back up, or inspect with a text editor. It stores bookmarks you supply; it does not scrape publishers or download puzzle answers.

## Quick start

Download `shortlist.py`, then run:

```sh
python shortlist.py add https://example.com/play --title "My daily puzzle" --tag daily --tag trivia
python shortlist.py list
python shortlist.py list --tag trivia
python shortlist.py check
python shortlist.py html > shortlist.html
```

Open `shortlist.html` in your browser. Only clicking a bookmark contacts its destination. To use a different file, put the global option before the command:

```sh
python shortlist.py --file weekend.json add https://example.com/quiz --title "Weekend quiz" --tag weekend
python shortlist.py --file weekend.json html --tag weekend > weekend.html
```

On Windows PowerShell, explicitly select UTF-8 when redirecting non-ASCII output:

```powershell
python shortlist.py html | Set-Content -Encoding utf8 shortlist.html
```

## The format

```json
{
  "version": 1,
  "bookmarks": [
    {
      "url": "https://example.com/play?mode=rare#daily",
      "title": "A puzzle I want to revisit",
      "tags": ["daily", "rare-answers"]
    }
  ]
}
```

The URL scheme must be HTTPS. Embedded credentials, control characters and whitespace are rejected. Hostnames are normalized, including their default port; the path, query and fragment are preserved because those can choose a game or mode. Adding a duplicate normalized URL fails instead of silently replacing your title or tags.

Titles and tags are escaped when writing HTML. Malformed JSON is an error, not a reason to silently clear the list. Saves validate first and replace the destination atomically using a temporary file in the same directory. Keep a separate backup if the contents matter to you; atomic replacement is not a backup system. The JSON schema is intentionally small and ignores unrecognized fields on the next successful save, so do not use it to round-trip unrelated application data.

## Relationship to Riddle List

This is an original companion utility published by the operator of [Riddle List](https://riddlelist.com/), a directory for comparing daily puzzles and reaching their official publishers. It uses its own file format. It does **not** export, read or migrate the live site's browser-local saved games; paste the bookmarks you want to keep yourself. Browser storage, publisher accounts, progress, streaks and subscriptions are separate.

For a practical starting point, compare the scoring styles in the [Krillion-like games collection](https://riddlelist.com/games-like/krillion/) and add the publishers you actually want to revisit. There is no bundled third-party game database and no claim that a bookmark authorizes embedding a game.

## Verification

```sh
python -m unittest -v
```

The checks cover unsafe URL schemes and credential rejection, preservation of query/fragment mode selectors, HTML escaping, duplicate normalized URLs, malformed input, unchanged existing bytes after a failed save, Unicode round trips and tag filtering. They do not establish availability or safety of a bookmarked external site.

## License and provenance

New code and documentation in this companion project are released under the MIT License. They were prepared with AI assistance and tested locally before publication. No private Riddle List application source, user data or publisher game code is included.
