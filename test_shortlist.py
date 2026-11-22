import json
from pathlib import Path
import tempfile
import unittest
import shortlist


class ShortlistTests(unittest.TestCase):
    def sample(self, title="Puzzle <one>"):
        return {"version": 1, "bookmarks": [{"url": "https://EXAMPLE.com:443/play?mode=rare#daily", "title": title, "tags": ["daily", "trivia"]}]}

    def test_normalization_preserves_game_mode_and_fragment(self):
        self.assertEqual(shortlist.validate(self.sample())["bookmarks"][0]["url"], "https://example.com/play?mode=rare#daily")

    def test_unsafe_schemes_credentials_and_whitespace_are_rejected(self):
        for url in ["javascript:alert(1)", "data:text/html,test", "http://example.com", "https://user:secret@example.com", "https://example.com/\nplay", "https://example.com/\u007fplay", "https://example.com/\u00a0play", "https://example.com:bad/"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                shortlist.normalize_url(url)

    def test_export_escapes_titles_and_attribute_injection(self):
        data = self.sample('<script>alert("x")</script>')
        data["bookmarks"][0]["url"] = 'https://example.com/?q="onclick="x&mode=rare'
        output = shortlist.export_html(data)
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertIn("&quot;onclick=&quot;", output)
        self.assertNotIn('href="https://example.com/?q="', output)

    def test_duplicate_canonical_url_is_rejected(self):
        data = self.sample()
        data["bookmarks"].append({"url": "https://example.com/play?mode=rare#daily", "title": "Duplicate"})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            shortlist.validate(data)

    def test_invalid_save_preserves_existing_bytes_and_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shortlist.json"
            shortlist.save(path, self.sample())
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                shortlist.save(path, {"version": 1, "bookmarks": [{"url": "javascript:x", "title": "Bad"}]})
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual([p.name for p in path.parent.iterdir()], ["shortlist.json"])

    def test_unicode_roundtrip_and_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shortlist.json"
            shortlist.save(path, self.sample("毎日のパズル"))
            data = shortlist.load(path)
            self.assertIn("毎日のパズル", shortlist.export_html(data, "daily"))
            self.assertNotIn("毎日のパズル", shortlist.export_html(data, "geography"))

    def test_malformed_saved_json_fails_instead_of_resetting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shortlist.json"
            path.write_text('{"version":1,"bookmarks":', encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaises(json.JSONDecodeError):
                shortlist.load(path)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
