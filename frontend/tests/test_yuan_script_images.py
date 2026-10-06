import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENTITIES_PATH = ROOT / "content" / "yuan" / "entities.json"
PUBLIC_DIR = ROOT / "frontend" / "public"
ENTITY_DRAWER_PATH = ROOT / "frontend" / "src" / "components" / "entity" / "EntityDrawer.vue"

EXPECTED_IMAGES = {
    "script_sanskrit_lantsa": "/assets/yuan/scripts/sanskrit-lantsa-east-wall.jpg",
    "script_tibetan": "/assets/yuan/scripts/tibetan-east-wall.jpg",
    "script_phagspa": "/assets/yuan/scripts/phagspa-east-wall.jpg",
    "script_old_uyghur": "/assets/yuan/scripts/old-uyghur-east-wall.jpg",
    "script_tangut": "/assets/yuan/scripts/tangut-east-wall.jpg",
    "script_chinese": "/assets/yuan/scripts/chinese-east-wall.jpg",
}


class YuanScriptImagesTest(unittest.TestCase):
    def test_each_script_uses_its_own_local_historical_detail(self) -> None:
        entities = json.loads(ENTITIES_PATH.read_text(encoding="utf-8"))
        by_id = {entity["id"]: entity for entity in entities}

        actual = {entity_id: by_id[entity_id]["image_url"] for entity_id in EXPECTED_IMAGES}
        self.assertEqual(EXPECTED_IMAGES, actual)
        self.assertEqual(6, len(set(actual.values())))

        for entity_id, image_url in actual.items():
            image_path = PUBLIC_DIR / image_url.removeprefix("/")
            self.assertTrue(image_path.is_file(), f"{entity_id} 缺少局部图：{image_path}")
            self.assertGreater(image_path.stat().st_size, 10_000)
            extra = by_id[entity_id]["extra"]
            self.assertEqual("BabelStone / Wikimedia Commons", extra["image_credit"])
            self.assertEqual("CC BY-SA 3.0", extra["image_license"])

    def test_entity_drawer_identifies_historical_detail_and_credit(self) -> None:
        component = ENTITY_DRAWER_PATH.read_text(encoding="utf-8")
        self.assertIn("entity.extra?.image_caption", component)
        self.assertIn("entity.extra?.image_credit", component)
        self.assertIn("entity.extra?.image_license", component)


if __name__ == "__main__":
    unittest.main()
