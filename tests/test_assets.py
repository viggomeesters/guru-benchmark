import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AssetTests(unittest.TestCase):
    def test_svg_is_self_contained_and_accessible(self):
        text = (ROOT / "assets/guru-benchmark-hero.svg").read_text(encoding="utf-8")
        self.assertIn('width="1280"', text)
        self.assertIn('height="640"', text)
        self.assertIn("<title", text)
        self.assertIn("<desc", text)
        self.assertNotRegex(text, re.compile(r"https?://(?!www\.w3\.org/2000/svg)"))
        for label in ["AK", "MP", "PS", "RH", "DHH", "SW", "MH", "SYNTHESIS"]:
            self.assertIn(f">{label}<", text)

    def test_social_preview_dimensions(self):
        data = (ROOT / "assets/social-preview.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", data[16:24])
        self.assertEqual((width, height), (1280, 640))


if __name__ == "__main__":
    unittest.main()
