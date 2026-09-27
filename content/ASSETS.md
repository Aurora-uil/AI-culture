# 场景与图片资源替换指南

本项目默认使用**代码生成的 SVG 矢量场景**，因此不依赖任何外部图片也能完整运行，
并且没有版权风险。

如果你后续拿到了博物馆授权图或自己生成了 AIGC 场景图，按本文档放入对应路径即可**自动替换**，
**不需要修改任何代码或坐标**。

---

## 一、替换机制

前端 `SceneViewer.vue` 的加载顺序：

```
1. 尝试加载 public/assets/<章节>/<场景文件>.webp
2. 加载失败（文件不存在）→ 自动回退到内置 SVG 矢量场景
```

也就是说：**放了图就用图，没放图就用 SVG，两种情况都不会出错。**

热点坐标是 0–1 归一化多边形，与背景图尺寸无关，所以换图后热点位置自动适配。

---

## 二、目录与命名规范

```
frontend/public/assets/
├── han/
│   └── silk_road_map.webp          汉代 · 丝路历史网络地图
├── northern-wei/
│   ├── yungang.webp                北魏 · 云冈石窟
│   └── longmen.webp                北魏 · 龙门石窟
├── tang/
│   ├── bunian.webp                 唐代 · 《步辇图》画卷
│   └── bunian_low.webp             唐代 · 低清兜底版（可选）
├── yuan/
│   ├── yuntai_inner.webp           元代 · 云台券洞内壁
│   └── hero.webp                   元代 · 章节封面
├── qing/
│   ├── map_base.webp               清代 · 东归迁徙地图底图
│   └── hero.webp                   清代 · 章节封面
├── contemporary/
│   └── hero.webp                   当代 · 羌绣章节封面
└── patterns/
    ├── pattern_qiang_001.webp      当代 · 纹样元素（须有权利记录）
    └── ...
```

**文件名必须与 `content/<章节>/scene.json` 里 `background_asset_id` 的末段一致。**
若你要用别的文件名，改 `scene.json` 里的字段即可，不必动代码。

---

## 三、尺寸建议

| 场景 | 建议尺寸 | 比例 | 说明 |
|---|---|---|---|
| 元代云台券洞 | 2400 × 1350 | 16:9 | 六处题刻需要足够分辨率，否则热点区域看不清 |
| 北魏云冈 / 龙门 | 1800 × 1350 | 4:3 | 双屏各占一半，建议竖构图留出造像全身 |
| 唐代《步辇图》 | 6000 × 1200 | 5:1 | 横长卷，需要能横向拖动的宽度 |
| 汉代丝路地图 | 2400 × 1400 | 12:7 | 东西向跨度大 |
| 清代迁徙地图 | 2400 × 1400 | 12:7 | 西起伏尔加河、东至伊犁河 |
| 章节封面 | 1200 × 900 | 4:3 | EraCard 用 |

格式优先 `.webp`（体积小），也支持 `.jpg` / `.png`。

---

## 四、替换后需要做的事

### 1. 重新标注热点坐标（**必须**）

换了背景图，原有的 0–1 归一化热点坐标就对不上了。有两种做法：

**做法 A：用标注工具**

```bash
cd backend
python scripts/annotate_hotspots.py --scene yuan/yuntai_inner
```

会启动一个本地页面，你在图上框选区域，工具直接写回 `content/yuan/scene.json`。

**做法 B：手动改 JSON**

打开 `content/yuan/scene.json`，把每个热点的 `normalized_points` 改成新图上对应位置的
0–1 归一化坐标：

```json
{
  "id": "hs_script_tibetan",
  "entity_id": "script_tibetan",
  "shape": "polygon",
  "normalized_points": [[0.31, 0.27], [0.41, 0.25], [0.42, 0.39], [0.30, 0.40]]
}
```

坐标含义：`[x, y]`，左上角为 `[0, 0]`，右下角为 `[1, 1]`。

### 2. 重新导入

```bash
cd backend
python scripts/seed_postgres.py
python scripts/seed_neo4j.py
```

### 3. 更新权利记录（**如果图片不是你自己生成的**）

任何来自第三方的图片，必须先在 `content/contemporary/extra.json` 的 `rights_records` 中
登记权利状态。**没有登记的素材默认 `can_display: false`，不会显示。**

必填项：谁提供、权利人、能否网页展示、能否裁切、能否作为生成输入、能否用于模型训练、
能否商业使用、是否需署名、授权期限。

---

## 五、AIGC 图片的额外要求

如果你用 AI 生成历史场景图，**界面上的「AI辅助历史场景示意」标识会自动显示**（`SceneViewer` 内置）。
这是硬性要求，不要移除 —— 避免观众误认为是真实历史影像或考古精确复原。

同时请在 `content/<章节>/scene.json` 的 `scene` 对象里补充：

```json
{
  "asset_source": "aigc",
  "asset_model": "使用的模型名与版本",
  "asset_prompt_ref": "提示词版本号",
  "asset_review_status": "review"
}
```

---

## 六、当前状态

| 章节 | 场景资源 | 状态 |
|---|---|---|
| 汉代 | `han/silk_road_map.webp` | 未提供 → 使用内置 SVG |
| 北魏 | `northern-wei/yungang.webp`、`longmen.webp` | 未提供 → 使用内置 SVG |
| 唐代 | `tang/bunian.webp` | 未提供 → 使用内置 SVG |
| 元代 | `yuan/yuntai_inner.webp` | 未提供 → 使用内置 SVG |
| 清代 | `qing/map_base.webp` | 未提供 → 使用内置 SVG |
| 当代 | ——（工作台布局，无背景图） | —— |

放入文件后刷新页面即生效，无需重启后端。
