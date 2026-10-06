import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_PATH = ROOT / "content" / "yuan" / "scene.json"
EXTRA_PATH = ROOT / "content" / "yuan" / "extra.json"


def bounds(points: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


class YuanHotspotLayoutTest(unittest.TestCase):
    def test_six_scripts_follow_the_east_wall_layout(self) -> None:
        scene = json.loads(SCENE_PATH.read_text(encoding="utf-8"))
        scripts = {
            hotspot["entity_id"]: hotspot
            for hotspot in scene["hotspots"]
            if hotspot["entity_id"].startswith("script_")
        }

        self.assertEqual(6, len(scripts))

        sanskrit = bounds(scripts["script_sanskrit_lantsa"]["normalized_points"])
        tibetan = bounds(scripts["script_tibetan"]["normalized_points"])

        # 东壁版式上方是梵文、藏文两条横排题刻。
        for region in (sanskrit, tibetan):
            x1, y1, x2, y2 = region
            self.assertGreater(x2 - x1, 0.8)
            self.assertLess(y2 - y1, 0.18)
        self.assertLess((sanskrit[1] + sanskrit[3]) / 2, (tibetan[1] + tibetan[3]) / 2)

        # 下方四栏从左到右依次为八思巴文、回鹘文、西夏文、汉文。
        lower_ids = [
            "script_phagspa",
            "script_old_uyghur",
            "script_tangut",
            "script_chinese",
        ]
        lower = [bounds(scripts[entity_id]["normalized_points"]) for entity_id in lower_ids]
        centers_x = [(region[0] + region[2]) / 2 for region in lower]
        self.assertEqual(centers_x, sorted(centers_x))
        for region in lower:
            x1, y1, x2, y2 = region
            self.assertLess(x2 - x1, 0.3)
            self.assertGreater(y2 - y1, 0.35)
            self.assertGreater(y1, tibetan[1])

        extra = json.loads(EXTRA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            ["script_sanskrit_lantsa", "script_tibetan", *lower_ids],
            extra["script_order"],
        )


if __name__ == "__main__":
    unittest.main()
