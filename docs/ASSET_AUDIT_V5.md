# 《同心千年》V5 视觉资源审计

更新日期：2026-09-24

## 1. 资源原则

1. 有可核验历史原件、遗址实拍或权威馆藏图时，优先使用历史原图。
2. 使用原图必须记录名称、来源页、作者/拍摄者与许可；“网上可见”不等于“可直接使用”。
3. 没有单一历史原图的跨时代叙事、抽象章节入口，可使用原创视觉，但必须标为“原创章节视觉”。
4. 数字复原图不得冒充文物原图或现场照片；热点必须人工复核，不使用自动识别结果直接上线。

## 2. 缺失检查结果

检查 `content/*/entities.json` 后，共发现 219 个实体中 218 个 `image_url` 为空：

| 章节 | 缺图 / 实体数 | 当前处理 |
|---|---:|---|
| 汉代 | 26 / 26 | 游戏主场景使用 AI 生成的实景化历史环境，路线、节点与证据等级仍由可校核的代码图层独立叠加；明确标注非史实照片、非精确路线复原 |
| 北魏 | 38 / 38 | 主对照场景补入云冈、龙门遗址实拍；实体图仍待逐项采集 |
| 唐代 | 27 / 28 | 主画卷补入《步辇图》历史原图；其余人物与事件图仍待逐项采集 |
| 元代 | 21 / 21 | 主场景补入居庸关云台东壁实拍；实体局部图仍待逐项采集 |
| 清代 | 41 / 41 | 迁徙路线继续使用来源可追溯的代码地图；已补 AI 写实环境图，但不是东归现场照片或精确路线，器物与画作授权仍待核验 |
| 当代 | 64 / 64 | 已补 AI 写实工坊情境与受控演示样例；正式内容仍应优先使用项目实拍与传承实践方授权图 |

实体无图时不再显示灰色空框，改为“章节史料原图 / 章节AI情境图”，并固定显示“非该实体原图”，避免误导。

## 3. 已落地历史原图

| 项目文件 | 内容 | 来源与许可 | 用途 |
|---|---|---|---|
| `frontend/public/assets/tang/bunian-original.jpg` | 《步辇图》数字图像 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Buliantu.jpg)，Public domain；故宫博物院藏品信息见[官方藏品页](https://www.dpm.org.cn/collection/paint/234620.html) | 唐代横向画卷、章节卡 |
| `frontend/public/assets/wei/yungang-cave20-original.jpg` | 云冈石窟第20窟实拍 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cave_20,_Yungang_Grottoes.jpg)，Dudva，CC0 | 北魏云冈对照、章节卡 |
| `frontend/public/assets/wei/longmen-guyang-original.jpg` | 龙门石窟古阳洞实拍 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Ancient_Buddhist_Grottoes_at_Longmen-_Guyang_Grotto_Main_Buddha.jpg)，Gary Todd，CC0 | 北魏龙门对照 |
| `frontend/public/assets/yuan/yuntai-east-wall-original.jpg` | 居庸关云台东壁实拍 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Yuntai_east_wall.jpg)，BabelStone，CC BY-SA 3.0 | 元代主场景、章节卡 |

## 4. 已落地原创视觉

| 项目文件 | 定位 | 使用边界 |
|---|---|---|
| `frontend/public/assets/global/millennia-hero-v1.png` | 首页“千年行卷”主视觉 | 原创跨时代氛围图，不对应单一史实现场 |
| `frontend/public/assets/global/chapter-atlas-v1.png` | 汉、清、当代章节入口与缺图兜底 | 只作章节视觉索引；不得作为人物、文物或遗址原图 |
| `frontend/public/assets/han/han-caravan-v1.png` | 汉代章节扉页、简报与章节卡 | 氛围性场景概念图；金线只表示叙事连接，不是张骞实际路线复原 |
| `frontend/public/assets/han/han-route-scene-v2.png` | 汉代游戏主场景实景化环境底图 | AI 生成历史环境示意；不是历史照片、具体遗址复原或张骞精确行程，路线证据由独立交互图层表达 |
| `frontend/public/assets/qing/qing-migration-v1.png` | 清代章节扉页、简报与章节卡 | 氛围性场景概念图；不得作为土尔扈特东归精确路线或现场图 |
| `frontend/public/assets/qing/qing-migration-photoreal-v2.png` | 清代章节扉页与任务简报的写实环境底图 | AI 历史环境重构；不是土尔扈特东归现场照片、精确路线或某个可识别历史人物的影像 |
| `frontend/public/assets/contemporary/qiang-workshop-v1.png` | 当代章节扉页、简报与章节卡 | 项目原创工坊视觉；不代表具体传承人或真实工作现场 |
| `frontend/public/assets/contemporary/qiang-workshop-photoreal-v2.png` | 当代章节扉页与任务简报的写实工坊底图 | AI 当代工坊情境；不是某位传承人、具体工坊或传统纹样的纪实证据 |
| `frontend/public/assets/contemporary/cocreation-sample-v1.png` | 共创服务不可用时的演示保障结果 | 必须同时标注“AI辅助文化创意作品 · 非传统羌绣原作”和“演示保障样例 · 非本次实时生成” |

原创图由 OpenAI 内置 ImageGen 生成。首页与索引提示词见 `docs/IMAGEGEN_PROMPTS_V1.md`，章节补图与共创样例提示词见 `docs/IMAGEGEN_PROMPTS_V2.md`。

## 4.1 V6 接入位置

- 六章扉页与任务简报均接入独立章节图：北魏、唐、元使用许可清晰的历史原图；汉、清、当代使用明确标注的 AI 写实情境图。
- 时间线与实体无图兜底同步改用章节独立图，不再把 3×2 合集裁切当作三章的主视觉。
- 当代离线共创只加载内容库中 `can_use_for_generation=true` 且策略为 `ALLOW_COMBINATION` 的项目自绘示意元素；其内容状态仍标记为待终审。

## 5. 仍需补齐的优先级

### P0：上线前必须处理

- 按最终图片重新标注《步辇图》人物热点、云冈/龙门对照热点、云台东壁文字热点。
- 对 CC BY-SA 3.0 的云台照片，在产品“史料与 AI”页或资源声明页持续展示作者与许可。
- 清代《万法归一图屏》、青玉册、银印等图片必须取得故宫/国博授权或找到许可清晰的开放图像后再接入。

### P1：提升内容完成度

- 汉代：五星出东方利中国锦护膊、尼雅遗址、张骞相关历史图像。
- 北魏：云冈与龙门的具体龛窟、题记、供养人服饰局部。
- 唐代：《步辇图》局部切片与藏品登记信息。
- 元代：东、西壁各书写系统的局部高清图。
- 当代：羌绣针法、纹样与传承场景的项目自摄图及授权书。

## 6. 布局策略

- 首页：左侧为标题与进入操作，右侧为“千年行卷”主视觉，金线贯穿全页。
- 章节索引：桌面端固定一屏 3×2；每张卡右侧出现章节图像，文字区保持高对比。
- 章节场景：原图优先，图上方固定来源标签；交互热点与免责声明独立叠加。
- 汉代路线场景：实景环境底图与证据路线分层呈现；底图负责沉浸感，金色路线、节点与可信度图例负责可核验叙事，任何时候不得把视觉连线解释为 GPS 精确轨迹。
- 实体抽屉：有实体原图就使用实体原图；无图仅显示章节索引，并明确“非该实体原图”。
