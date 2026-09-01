"""Unit tests for the web novel-to-documentation formatter."""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.web.formatter import format_chapter_as_doc, _clean_paragraphs


class WebFormatterTest(unittest.TestCase):
    def test_clean_paragraphs(self):
        raw = "\n\n 第一段内容。 \n\n\n 第二段  有很多空格。 \n\n"
        paras = _clean_paragraphs(raw)
        self.assertEqual(len(paras), 2)
        self.assertEqual(paras[0], "第一段内容。")
        self.assertEqual(paras[1], "第二段 有很多空格。")

    def test_empty_content_fallback(self):
        doc = format_chapter_as_doc("空章节", "")
        self.assertEqual(doc.title, "空章节")
        self.assertEqual(doc.paragraph_count, 1)
        self.assertGreater(len(doc.sections), 0)

    def test_vue_theme_formatting(self):
        content = (
            "这是小说的第一段正文。\n\n"
            "主角发现了古代遗迹的秘密。\n\n"
            "周围的魔法元素开始产生剧烈波动。\n\n"
            "‘这就是传说中的力量吗？’他低声自语。\n\n"
            "法阵发出了耀眼的绿色光芒。\n\n"
            "新的冒险即将开启。\n\n"
        )
        doc = format_chapter_as_doc("第一章 初探", content, theme="vue", disguise_mode="hybrid")
        self.assertEqual(doc.theme, "vue")
        self.assertEqual(doc.title, "第一章 初探")
        self.assertGreater(len(doc.toc), 0)
        self.assertGreater(len(doc.sections), 0)

        # In hybrid mode, there should be callout and code blocks
        all_block_types = [b["type"] for s in doc.sections for b in s["blocks"]]
        self.assertIn("paragraph", all_block_types)
        self.assertIn("callout", all_block_types)
        self.assertIn("code", all_block_types)

    def test_react_theme_formatting(self):
        content = "React theme test content paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        doc = format_chapter_as_doc("Chapter 1", content, theme="react", disguise_mode="clean")
        self.assertEqual(doc.theme, "react")
        # In clean mode, no synthetic code blocks or callouts are inserted
        all_block_types = [b["type"] for s in doc.sections for b in s["blocks"]]
        self.assertIn("paragraph", all_block_types)
        self.assertNotIn("code", all_block_types)

    def test_code_dense_mode(self):
        content = "段落一\n\n段落二\n\n段落三\n\n段落四\n\n段落五"
        doc = format_chapter_as_doc("测试代码密集", content, theme="rust", disguise_mode="code_dense")
        self.assertEqual(doc.theme, "rust")
        all_block_types = [b["type"] for s in doc.sections for b in s["blocks"]]
        self.assertIn("code", all_block_types)


if __name__ == "__main__":
    unittest.main()
