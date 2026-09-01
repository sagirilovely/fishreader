"""Unit tests for the Web Video Disguise & Streaming APIs."""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.config import load_config
from fishreader.web.server import WebDisguiseServer
from tests.test_web_server import call_handler


class WebVideoTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        books_dir = self.root / "books"
        books_dir.mkdir(parents=True)
        (books_dir / "sample.txt").write_text("第一章 开篇\n\n正文。\n", encoding="utf-8")

        # Create videos directory with sample video file
        videos_dir = self.root / "videos"
        videos_dir.mkdir(parents=True)
        self.sample_video = videos_dir / "clip.mp4"
        # 1024 bytes of dummy video data
        self.video_data = b"X" * 1024
        self.sample_video.write_bytes(self.video_data)

        self.config = load_config(self.root / "fish.toml", project_root=self.root)
        self.server = WebDisguiseServer(self.config, self.root, port=8892)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_video_status_config(self):
        status, _, body = call_handler(self.server, "GET", "/api/status")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertIn("video", data)
        self.assertTrue(data["video"]["enabled"])
        self.assertEqual(data["video"]["position"], "bottom_right")
        self.assertEqual(data["video"]["default_size"], "normal")
        self.assertEqual(data["video"]["ad_style"], "flashy_game")

    def test_list_videos(self):
        status, _, body = call_handler(self.server, "GET", "/api/videos")
        self.assertEqual(status, 200)
        videos = json.loads(body.decode("utf-8"))
        self.assertIsInstance(videos, list)
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["name"], "clip.mp4")
        self.assertEqual(videos[0]["fmt"], "mp4")
        self.assertEqual(videos[0]["size_bytes"], 1024)
        self.assertEqual(videos[0]["url"], "/api/videos/clip.mp4")

    def test_video_full_stream(self):
        status, headers, body = call_handler(self.server, "GET", "/api/videos/clip.mp4")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("content-type"), "video/mp4")
        self.assertEqual(headers.get("content-length"), "1024")
        self.assertEqual(headers.get("accept-ranges"), "bytes")
        self.assertEqual(body, self.video_data)

    def test_video_range_stream(self):
        # Range request: first 100 bytes (0-99)
        status, headers, body = call_handler(
            self.server, "GET", "/api/videos/clip.mp4", headers_dict={"Range": "bytes=0-99"}
        )
        self.assertEqual(status, 206)
        self.assertEqual(headers.get("content-range"), "bytes 0-99/1024")
        self.assertEqual(headers.get("content-length"), "100")
        self.assertEqual(headers.get("accept-ranges"), "bytes")
        self.assertEqual(body, self.video_data[:100])

    def test_video_not_found(self):
        status, _, _ = call_handler(self.server, "GET", "/api/videos/non_existent.mp4")
        self.assertEqual(status, 404)

    def test_video_directory_traversal_blocked(self):
        status, _, _ = call_handler(self.server, "GET", "/api/videos/../../etc/passwd")
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
