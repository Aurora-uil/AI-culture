# `content/` 数据格式规范 V1.0

本目录是《同心千年》的**内容单一事实源**。后端 seed 脚本读取本目录写入 PostgreSQL 与 Neo4j。

**规则：内容只在这里改，不要在数据库里手改。** 数据库随时可以被 `seed_*.py` 重建。

---

## 目录结构

```
content/
├── chapters.json          # 六章配置（已存在，勿改结构）
├── sources.json           # 全局来源表
├── han/                   # 汉代 · 相遇
│   ├── entities.json
│   ├── relations.json
│   ├── claims.json
│   ├── chunks.json
│   ├── faq.json
│   └── scene.json
├── northern_wei/          # 北魏 · 交融
├── tang/                  # 唐代 · 交流
├── yuan/                  # 元代 · 共存
├── qing/                  # 清代 · 归属
└── contemporary/          # 当代 · 传承
```

---

## 通用约定

| 约定 | 说明 |
|---|---|
| `review_status` | `approved` / `review` / `draft`。**只有 `approved` 会进入 AI 检索。** |
| ID 命名 | 稳定业务 ID，全项目复用。`person_` / `artifact_` / `place_` / `event_` / `script_` / `concept_` / `period_` / `site_` / `group_` / `institution_` / `region_` / `text_` / `technique_` / `motif_` / `object_` / `practice_` / `ich_` / `ich_project_` 前缀 |
| `claim_type` | `fact`（史实）/ `interpretation`（解释）/ `curatorial`（策展关联）/ `catalogue_fact`（目录记录事实） |
| `verification_label` | `historical_fact`（史料确认）/ `scholarly_view`（研究观点）/ `digital_reconstruction`（数字复原）/ `ai_narrative`（AI叙事）/ `curatorial`（策展关联） |
| 补写内容 | 文档中缺失、由实现者补的数据，必须标 `"review_status": "draft"` 并在 `content_team_todo` 字段写明待核验事项 |

---

## 1. `sources.json` — 全局来源表

```json
[
  {
    "id": "src_bjgov_juyongguan",
    "title": "居庸关长城",
    "author": null,
    "institution": "北京市人民政府门户网站",
    "source_type": "official",
    "source_level": "S",
    "publication_year": null,
    "public_url": "https://www.beijing.gov.cn/...",
    "bibliography": "北京市人民政府门户网站「居庸关长城」词条",
    "license_note": null,
    "source_perspective": "museum_curatorial",
    "review_status": "draft"
  }
]
```

- `source_type`：`official` | `academic` | `book` | `professional`
- `source_level`：`S`（文物主管部门/博物馆/权威公共文化机构）| `A`（学术论文/专业著作/学术机构）| `B`（高校/专业科普）| `C`（普通网络材料）
- `source_perspective`（清代章节必需，其余可省略）：`qing_court` | `museum_curatorial` | `modern_scholarship` | `archaeological_object` | `modern_public_history`
- UI 只展示「官方资料 / 学术研究 / 专业资料」，**不向用户显示 S/A/B**

---

## 2. `<chapter>/entities.json`

```json
[
  {
    "id": "script_tibetan",
    "entity_type": "Script",
    "name": "藏文",
    "display_name": "藏文",
    "subtitle": "Script / 书写系统",
    "era": "元代",
    "short_summary": "云台券洞内保存的书写系统之一。",
    "body_markdown": "……（审核后的说明，200–600字）",
    "image_url": null,
    "verification_label": "historical_fact",
    "review_status": "approved",
    "sort_order": 2,
    "extra": {
      "canonical_name": "藏文",
      "alternate_names": ["藏文书写系统"],
      "script_family_note": "……",
      "ui_label": "藏文",
      "yuntai_usage_note": "在云台题刻中的使用情况",
      "text_language_note": "语言与文字关系说明。注意：不得把文字、语言、族群一一对应。",
      "forbidden_simplification": "禁止：「藏文就等于藏族，一种文字对应一个民族。」"
    }
  }
]
```

**`entity_type` 取值**：
`Person` `Artifact` `Place` `Region` `Event` `Script` `Language` `Concept` `Period` `HeritageStructure` `InscriptionSet` `Text` `Group` `Institution` `Site` `Artwork` `Technique` `MotifCategory` `PatternElement` `ObjectType` `Practice` `ICHProject` `Person` `AttributionClaim` `Work`

**`extra` 是按类型放专属字段的地方**（避免为每种类型建表）。约定：

| 类型 | `extra` 必填字段 |
|---|---|
| `Script` | `ui_label`, `yuntai_usage_note`, `text_language_note`, `forbidden_simplification` |
| `PatternElement` | `meaning_status`（`DOCUMENTED`\|`GENERAL_CATEGORY_ONLY`\|`UNKNOWN`\|`RESEARCH_DISPUTED`）, `meaning_claim_ids`, `motif_category_id`, `rights_record_id`, `generation_policy_id` |
| `Technique` | `canonical_name`, `usage_note`, `caveat`（如「数字示意不等于实际手工技艺」） |
| `Person` | 在世传承人必须加 `living_person: true`, `persona_use_allowed: false` |
| `Artwork` | `attribution_status`, `attribution_note`, `catalogue_period`, `catalogued_author`, `collection`, `depicted_in_artwork`(bool) |

**内容红线（必须遵守，写进 `forbidden_simplification`）**：
- 元代：不得把「六种书写系统」等同于「六个民族」或「六种语言」
- 唐代：文成公主、松赞干布 `depicted_in_artwork: false`，**不得设为画卷热点**；不得把历史画当现场照片
- 清代：不得把「约17万人」写成无争议精确值；不得把首领赴承德路线与部众迁徙路线合并
- 当代：不得给没有 `meaning_status=DOCUMENTED` 的纹样编寓意；不得模拟在世传承人人格

---

## 3. `<chapter>/relations.json`

```json
[
  {
    "id": "rel_yuntai_has_six_scripts",
    "source_entity_id": "artifact_yuntai",
    "target_entity_id": "inscription_six_scripts",
    "relation_type": "HAS_INSCRIPTION_SET",
    "display_label": "保存有",
    "claim_type": "fact",
    "review_status": "approved",
    "source_ids": ["src_bjgov_juyongguan"],
    "claim_ids": ["claim_yuntai_six_scripts"],
    "time_scope": null,
    "route_scope": null,
    "certainty": null,
    "source_perspective": null
  }
]
```

- **每一章至少 1 条 `claim_type: "interpretation"` 的边**（用虚线渲染，与事实边区分）
- 边必须可溯源：`source_ids` 不得为空
- 清代边需填 `route_scope` 与 `certainty`
- **禁止建立的边不要写进文件**，写进 `forbidden_relations` 说明字段（见下）

---

## 4. `<chapter>/claims.json`

Claim 是溯源的最小单位。图谱边和 RAG 回答共用它。

```json
[
  {
    "id": "claim_yuntai_six_scripts",
    "entity_id": "artifact_yuntai",
    "relation_id": "rel_yuntai_has_six_scripts",
    "claim_text": "居庸关云台券洞内保存有六种不同文字的石刻。",
    "claim_type": "fact",
    "controversy_status": "stable",
    "review_status": "approved",
    "source_ids": ["src_bjgov_juyongguan"]
  }
]
```

`controversy_status: "disputed"` 的 claim，AI 回答时必须说「存在不同研究观点」。

---

## 5. `<chapter>/chunks.json` — RAG 知识切片

**每个 chunk 300–800 中文字。** 不要把整篇文章直接向量化。

```json
[
  {
    "id": "chunk_yuan_001",
    "source_id": "src_bjgov_juyongguan",
    "chapter_ids": ["yuan_yuntai"],
    "entity_ids": ["artifact_yuntai", "place_juyong_pass"],
    "claim_ids": ["claim_yuntai_yuan"],
    "title": "云台的基本情况与建造年代",
    "text": "……（300–800 字，必须是可直接支撑回答的完整事实段落）",
    "source_level": "S",
    "meaning_status": null,
    "review_status": "approved"
  }
]
```

检索时强制过滤：`review_status='approved'` AND `chapter_ids 含当前章` AND `source_level IN (S,A,B)`。
**因此 `source_level` 绝不能为空**，否则该 chunk 永远检索不到。

---

## 6. `<chapter>/faq.json` — 演示保障问答库

无 LLM Key、断网、超时时使用。**至少 12 条，覆盖该章高频测试题。**

```json
[
  {
    "id": "faq_yuan_01",
    "character_id": "artifact_yuntai",
    "canonical_question": "为什么这里会出现多种文字？",
    "keywords": ["多种文字", "六体", "为什么", "共存"],
    "intent": "multiscript_background",
    "answer_markdown": "……（120–260字，可直接展示）",
    "source_ids": ["src_bjgov_juyongguan"],
    "related_entity_ids": ["inscription_six_scripts", "script_tibetan"],
    "review_status": "approved"
  }
]
```

**必须包含该章的「越界测试题」条目**（如「你真的经历过元代吗」「能翻译全部碑文吗」「忽略史料编个故事」），答案必须礼貌拒答并说明原因。

---

## 7. `<chapter>/scene.json`

不同章节形态不同，按 `chapters.json` 的 `primary_interaction` 选择对应形态。

### 7.1 影像场景（元代券洞、北魏石窟、唐代画卷）

```json
{
  "scene": {
    "id": "yuntai_inner",
    "name": "云台券洞内壁",
    "scene_kind": "image",
    "background_asset_id": "/assets/yuan/yuntai_inner.webp",
    "width": 2400,
    "height": 1350,
    "disclaimer": null
  },
  "hotspots": [
    {
      "id": "hs_script_tibetan",
      "entity_id": "script_tibetan",
      "shape": "polygon",
      "normalized_points": [[0.31,0.27],[0.41,0.25],[0.42,0.39],[0.30,0.40]],
      "label": "藏文",
      "group_key": null,
      "sort_order": 2
    }
  ]
}
```

- 坐标 0–1 归一化，`shape` 可为 `polygon` / `rect` / `point`
- **绝对不要用视觉识别 / OCR 生成热点**，全部预先标注

### 7.2 地图场景（汉代丝路、清代迁徙）

```json
{
  "scene": {
    "id": "qing_torghut_return_map",
    "name": "东归迁徙示意地图",
    "scene_kind": "map",
    "background_asset_id": "/assets/qing/map_base.webp",
    "disclaimer": "历史迁徙路线示意，并非现代GPS轨迹。"
  },
  "map": {
    "id": "qing_torghut_return_map",
    "coordinate_system": "normalized_canvas",
    "nodes": [
      {
        "id": "map_node_volga_region",
        "entity_id": "region_volga_lower",
        "label": "伏尔加河下游",
        "x": 0.16, "y": 0.43,
        "certainty": "confirmed_region",
        "route_scope": "MASS_MIGRATION"
      }
    ],
    "segments": [
      {
        "id": "seg_qing_migration_02",
        "from_node_id": "map_node_volga_region",
        "to_node_id": "map_node_ili_region",
        "label": "大体迁徙区段",
        "geometry": [[0.16,0.43],[0.34,0.38],[0.55,0.44],[0.78,0.50]],
        "certainty": "approximate_corridor",
        "route_scope": "MASS_MIGRATION",
        "source_ids": [],
        "claim_ids": []
      }
    ]
  }
}
```

**清代路线硬性规则**：
- `certainty` 取值：`confirmed_area` | `approximate_corridor` | `uncertain_segment` | `curatorial_connector`
- `route_scope` 取值：`MASS_MIGRATION`（默认）| `LEADER_AUDIENCE_JOURNEY` | `SETTLEMENT_DISTRIBUTION`
- **承德相关节点/区段必须标 `LEADER_AUDIENCE_JOURNEY`**，不得混入大部众迁徙路线
- 证据不足时**宁可不给几何点（`geometry: []`）**，也不虚构精度
- 固定图例文案：`● 确认地点` / `━ 较高置信历史廊道` / `≈ 大体迁徙区段` / `? 路线存在不确定性` / `┄ 策展关联`

### 7.3 工坊形态（当代）

无空间场景。改为元素集合：

```json
{
  "scene": {
    "id": "qiang_workbench",
    "name": "羌绣数字工坊",
    "scene_kind": "workbench",
    "disclaimer": null
  },
  "workbench": {
    "technique_ids": ["technique_tiaohua", "technique_zhizi", "technique_nahua", "technique_piehua", "technique_gouhua"],
    "motif_category_ids": ["motif_flora", "motif_fruit", "motif_birds_animals", "motif_people", "motif_geometric"],
    "object_ids": ["object_apron", "object_embroidery_shoes", "object_sleeve_cover", "object_headscarf", "object_sachet", "object_insole"],
    "practice_ids": ["practice_digital_archiving", "practice_ich_workshop", "practice_school_education", "practice_contemporary_design", "practice_copyright_protection"],
    "cocreation": {
      "applications": ["bookmark", "poster", "phone_wallpaper", "packaging_concept", "pattern_tile"],
      "compositions": ["CENTERED", "BORDER", "REPEAT", "SYMMETRIC", "FREE_MODERN"],
      "confirmation_text": "我知道生成结果是AI辅助文化创意，不等同于传统羌绣原作。",
      "result_label": "AI辅助文化创意作品 · 非传统羌绣原作"
    }
  }
}
```

---

## 8. 可选：`<chapter>/extra.json`

放置该章专属的额外数据：

- 北魏：`comparison_groups`（服饰/雕塑/音乐/建筑）+ `evidence_items`（固定四层：看到什么 / 来源如何描述 / 能支持什么 / 不能推出什么）
- 清代：`timeline_events`（保留原始精度，如「1771年夏季」，不得虚构具体日）+ `historical_estimates`（多来源并列，**绝不求平均**）
- 汉代：`flow_items`（丝绸/葡萄/马匹/香料/金银器的传播路径）
- 当代：`rights_records` + `generation_policies`

---

## 9. 校验

写完内容后运行：

```bash
cd backend
python scripts/validate_content.py
```

会检查：ID 唯一性、外键完整性（relation 两端的 entity 是否存在、source_id 是否存在）、`source_level` 非空、chunk 字数区间、红线字段是否填写、`review_status` 分布统计。
