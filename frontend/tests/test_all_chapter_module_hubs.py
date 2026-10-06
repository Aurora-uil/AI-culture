"""六个章节都必须提供相互独立的三板块任务大厅。"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "frontend" / "src" / "pages" / "chapter" / "C01Guide.vue"
SCENE = ROOT / "frontend" / "src" / "pages" / "chapter" / "C02Scene.vue"
CHAT = ROOT / "frontend" / "src" / "pages" / "chapter" / "C05Chat.vue"

SLUGS = ("han", "northern-wei", "tang", "yuan", "qing", "contemporary")


class AllChapterModuleHubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.scene = SCENE.read_text(encoding="utf-8")
        cls.chat = CHAT.read_text(encoding="utf-8")

    def test_every_chapter_has_three_module_copy_entries(self) -> None:
        self.assertIn("CHAPTER_MODULE_COPY", self.guide)
        for slug in SLUGS:
            self.assertRegex(self.guide, rf"['\"]?{re.escape(slug)}['\"]?\s*:\s*\[")
        self.assertIn('v-for="module in chapterModules"', self.guide)
        self.assertNotIn('v-if="slug === \'yuan\'" class="briefing__modules"', self.guide)
        self.assertNotIn('v-if="slug !== \'yuan\'" class="briefing__actions"', self.guide)

    def test_module_paths_and_returns_are_independent(self) -> None:
        self.assertIn("{ id: 'explore'", self.guide)
        self.assertIn("{ id: 'story'", self.guide)
        self.assertIn("route.query.module === 'explore'", self.scene)
        self.assertIn("返回任务大厅", self.scene)
        self.assertIn("taskHallPath", self.chat)
        self.assertIn("任务大厅", self.chat)

    def test_exploration_does_not_start_story_progress(self) -> None:
        self.assertIn("STORY_VISIT_STORAGE_KEY", self.guide)
        self.assertIn("markStoryVisited", self.scene)
        self.assertNotIn("state.evidenceIds.length > 0 || state.actions.ENTER", self.guide)


if __name__ == "__main__":
    unittest.main()
