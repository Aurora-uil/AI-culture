# 同心千年

**AI中华民族交往交流交融数字叙事平台**

以中华各民族在历史进程中的交往、交流、交融为主线，通过历史场景、AI 人物与文物叙事、
RAG 知识问答、关系知识图谱与个人探索路径，把分散的人物、文物、事件和文化遗产
连接成一套可以被主动探索的数字叙事系统。

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | 3.12+ | |
| Node.js | 20+ | |
| Docker Desktop | 已启动 | **必须运行**，本项目后端依赖 PostgreSQL 与 Neo4j |

> ⚠️ 本机若已有其它项目占用 5432 端口，本项目已改用 **5433**，不会冲突。

### 1. 启动数据库

```bash
docker compose up -d
docker compose ps          # 等两个容器都变成 healthy
```

启动两个容器：

| 容器 | 端口 | 用途 |
|---|---|---|
| `tongxin-postgres` | 5433 | 内容数据库（entities / sources / claims / chunks …） |
| `tongxin-neo4j` | 7474 / 7687 | 关系图谱 |

Neo4j Browser：<http://localhost:7474>（账号 `neo4j`，密码 `tongxin_dev`）

### 2. 启动后端

```bash
cd backend

# 首次：创建虚拟环境并装依赖
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS / Linux

# 配置（可选 —— 不配也能跑，见下方「演示保障模式」）
cp .env.example .env

# 导入内容数据
./.venv/Scripts/python.exe scripts/seed_postgres.py
./.venv/Scripts/python.exe scripts/seed_neo4j.py

# 启动
./.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000 --reload
```

接口文档：<http://localhost:8000/docs>
健康检查：<http://localhost:8000/api/v1/health>

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

打开 <http://localhost:5173>

> 只启动前端也可以试玩完整的元代章节。章节目录、元代场景与题刻实体带有内置演示数据；后端恢复后会自动优先使用真实接口数据。

---

## V5 五章剧情体验

汉、北魏、唐、清、当代五章现已接入统一的剧情体验引擎，共包含 50 个可交互场景。每章围绕一种不同的叙事误读展开：路线误读、尺度误读、图像误读、单因归因，以及把共同体误写成统一视觉；玩家需要检查证据、完成判断并作出会写入章节结算的最终选择。

- `frontend/src/chapters/story/fiveChapterStories.ts`：五章完整剧情、对白、证据挑战与分支结局
- `frontend/src/chapters/story/ChapterStoryExperience.vue`：通用剧情舞台、证据工作台与存档机制
- `docs/FIVE_CHAPTER_STORY_DESIGN_V1.md`：叙事设计、史学边界、45 场景拆解与验收标准
- `frontend/tests/e2e_five_story_check.py`：五章流程和移动端回归测试

体验地址统一为 `/chapter/<章节代号>/story`，其中章节代号为 `han`、`northern-wei`、`tang`、`qing` 或 `contemporary`。

---

## V7 商业化 UI 第一轮

首页、章节目录、章节开幕和五章剧情舞台已按“可游玩的数字档案馆”重新建立层级：首屏首秒可读，章节显示未启程/进行中/已封存状态，剧情顶部采用九幕档案脊线，证据挑战会从暗场切换为浅色档案工作台，并提供可持久化的大字模式。

- `docs/UI_COMMERCIALIZATION_AUDIT_V1.md`：商业文游对标、当前问题、设计方向与后续优先级
- `docs/screenshots/ui-commercial-pass/`：本轮优化前后视觉回归截图
- `frontend/tests/e2e_ui_audit.py`：首页、目录、开幕、剧情、工作台和移动端回归

第二轮进一步统一六章产品结构：五章剧情每三幕出现一次档案小结；元代章节接入十二幕脊线、全局大字模式和三次拓片式小结，同时保留深色石刻校勘台作为章节独有材质。

第三轮补齐回访与结章体验：首页可直达最近游玩章节，六章共用全局音效设置，结章页提供不剧透的三路线复盘；AI 对话、关系图谱与授权共创工作台也统一为同一套档案产品语言。对应回归脚本为 `frontend/tests/e2e_ui_round3.py`。

第四轮开始处理叙事结构本身：产品承诺改为“六个证据现场”，阶段小结同时说明边界与仍可确认的联系；五章终局选择增加“优先保护／接受代价”和二次确认，错误尝试作为修订记录进入结章。详细审视见 `docs/NARRATIVE_AUDIT_V2.md`。

---

## V3 青绿山水卷轴界面

界面已从深黑展陈风格调整为“青绿山水卷轴”：以雾青、缥瓷、矿物青、朱砂和旧金为主色，保留贯穿全站的“千年线”作为视觉线索。桌面端核心流程采用 `100dvh` 单屏舞台，不需要滚动整张网页；较长的史料与叙事只在对应内容面板内部滚动。窄屏和移动端会自动恢复纵向排布，避免为了追求一屏而牺牲可读性。

当前已按 1440 × 900 视口验证首页、章节总览、元代序章、任务简报、历史场景、章节结算和千年史册，七个核心页面的整页纵向溢出均为 0 px。

设计系统的核心实现位于：

- `frontend/src/styles/tokens.css`：青绿山水色板与全局令牌
- `frontend/src/styles/base.css`：浅色基底、字体、焦点与动效降级规则
- `frontend/src/components/global/GlobalHeader.vue`：全站浅色玻璃导航
- `frontend/tests/e2e_layout_check.py`：桌面端一屏布局与截图回归测试

### V4 锦帧叙事交互

在青绿山水视觉上继续加入“剧情游戏舞台感”：章节卡采用角色牌式聚焦与金线掠光；场景外围增加青铜画框；所有按钮、链接和历史热点共用金线涟漪与朱砂光点反馈；关键抉择完成后，以背景虚化和横向卷轴揭示“记录已写入”。这些效果只使用项目自己的历史视觉语言，不复刻参考视频的角色、商标或素材。

交互层实现位于：

- `frontend/src/components/game/GameInteractionFx.vue`：全站点击涟漪与粒子
- `frontend/src/components/game/GameQuestDock.vue`：抉择面板与卷轴式结果反馈
- `frontend/src/pages/G01Timeline.vue`：角色牌式章节选择
- `frontend/src/pages/chapter/C02Scene.vue`：沉浸式历史场景画框

系统遵循 `prefers-reduced-motion`：用户启用减少动态效果后，粒子、掠光和入场动画会被关闭或缩短。

## V2 游戏化体验

当前版本已经从“数字展陈网站”调整为“章节式历史文游”。首页的发光千年线连接六个证据现场，每个朝代都有玩家身份、具体任务、专属机制、证据探索、关键抉择与可留存的章节信物。

第一条完整可玩切片是元代《石壁上的六种声音》：玩家扮演云台营造场校勘助手，查验至少三处题刻，开启六体文字透镜，并决定怎样处理位置证据互相冲突的拓片。选择不会改写历史，只会改变玩家留下的记录和“求真 / 共情 / 联结”方法倾向。

核心实现位于：

- `frontend/src/game/catalog.ts`：六章角色、任务、机制、目标与抉择内容
- `frontend/src/stores/game.ts`：确定性的章节状态、进度与本地存档
- `frontend/src/components/game/GameQuestDock.vue`：场景内任务 HUD 与抉择界面
- `frontend/src/pages/G03Journey.vue`：跨章节“我的千年史册”，汇总身份、信物、选择与历史方法
- `frontend/tests/e2e_game_check.py`：从领取身份到章节结算的浏览器闭环测试

### 六章文物剧情锚点

六章现已统一增加“剧情锚点”：章节简报和场景任务抽屉会持续显示本章的具名文物、遗存或当代作品，以及它的审核、代表性或授权边界。汉代围绕锦护膊错误展签展开，北魏以元羽墓志为主证物，清代以《万法归一图屏》组织多来源展陈；当代章在取得具体作品授权前明确保持“授权前置”，不把通用纹样冒充传统原作。完整设计与验收规则见 [`docs/ARTIFACT_STORY_DESIGN_V1.md`](docs/ARTIFACT_STORY_DESIGN_V1.md)。

对应的浏览器回归测试为 `frontend/tests/e2e_artifact_story_check.py`，覆盖六章锚点、场景任务抽屉和移动端横向溢出。

叙事状态的设计参考了 [inkjs](https://github.com/y-lohse/inkjs) 的网页交互叙事思路和 [XState](https://github.com/statelyai/xstate) 的显式状态建模方式；当前代码保持轻量，没有直接引入额外运行时依赖。

### 离线熔断

前端会先共享一次后端健康探测。内容服务不可用时，15 秒内的后续请求会直接进入本地保障逻辑，不再由每个组件重复触发失败请求；顶部导航同时显示“本地演示”。这与“大模型未配置时的演示保障模式”是两种不同状态。

---

## 演示保障模式（重要）

**不配置大模型 API Key，整个系统依然可以完整演示。**

系统会自动进入「演示保障模式」：AI 回答改由**已审核的预设问答库**提供，
每条回答的界面都会明确标注来源层级，**不会伪装成实时生成**。

这是为比赛现场设计的：网络故障、API 超时、Key 失效都不会让演示中断。

### 接入真实大模型

编辑 `backend/.env`：

```bash
LLM_PROVIDER=openai_compatible          # 或 anthropic
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-你的key
LLM_MODEL=deepseek-chat
```

支持的供应商（填对应的 `LLM_BASE_URL` 与 `LLM_MODEL`）：

| 供应商 | LLM_BASE_URL | 示例模型 |
|---|---|---|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| 豆包 | `https://ark.cn-beijing.volces.com/api/v3` | 你的接入点 ID |
| Kimi | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| Claude | `https://api.anthropic.com`（`LLM_PROVIDER=anthropic`） | `claude-sonnet-4-6` |

改完重启后端即可，前端无需改动。顶部导航栏的「演示保障模式」标签会自动消失。

---

## 项目结构

```
同心千年/
├── content/              ★ 内容单一事实源（审核后的 JSON）
│   ├── SCHEMA.md             数据格式规范
│   ├── ASSETS.md             场景图片替换指南
│   ├── chapters.json         六章配置
│   └── <章节>/                entities / relations / claims / sources / chunks / faq / scene
│
├── backend/              FastAPI + PostgreSQL + Neo4j
│   ├── app/
│   │   ├── ai/               RAG 检索、LLM 供应商抽象、Prompt 链、内容护栏
│   │   ├── api/v1/           REST 接口
│   │   ├── models/           SQLAlchemy ORM
│   │   ├── services/         业务逻辑
│   │   └── db/               schema.sql / 连接管理
│   └── scripts/              seed 与校验脚本
│
└── frontend/             Vue 3 + TypeScript + Vite
    └── src/
        ├── components/
        │   ├── ds/               设计系统基础组件（DsButton / DsDrawer / DsIcon …）
        │   ├── global/           全局组件（GlobalHeader / EraCard / EvidenceBadge …）
        │   ├── scene/            场景与热点
        │   ├── entity/           实体详情抽屉
        │   ├── chat/             AI 对话
        │   ├── source/           史料证据
        │   ├── graph/            知识图谱（ECharts）
        │   └── exploration/      探索进度
        ├── chapters/             ★ 六章专属场景与交互
        ├── pages/                G00–G04 全局页 + C00–C09 章节页
        ├── stores/               Pinia 状态
        └── styles/               设计令牌（严格取自设计系统文档）
```

---

## 六个章节

| 章节 | 关键词 | 核心对象 | 专属交互 |
|---|---|---|---|
| 汉代 | 相遇 | 张骞 · 丝路 · 五星锦 | 路线透镜 / 物品流动 |
| 北魏 | 交融 | 孝文帝 · 云冈 · 龙门 | 证据对照透镜 |
| 唐代 | 交流 | 《步辇图》· 禄东赞 · 文成公主 | 画卷滚动 + 画内外关系 |
| 元代 | 共存 | 居庸关云台六体文字 | 六体文字透镜 |
| 清代 | 归属 | 渥巴锡 · 土尔扈特东归 | 迁徙时间轴 + 路线证据 |
| 当代 | 传承 | 羌族刺绣 | 元素知识 + AI 共创 |

六章共用同一套产品骨架（导航、进度、实体抽屉、AI 对话、史料证据、图谱、成果页），
差异只体现在主场景与核心交互上。

---

## 六条内容红线

这些不是「建议」，是写进代码与数据的硬性约束。答辩时可以重点讲。

### 1. 文字 ≠ 语言 ≠ 民族（元代）

云台券洞保存的是**六种书写系统**的题刻。数据库把
`Script`（文字）/ `Language`（语言）/ `Text`（文本）/ `Inscription`（具体题刻）
拆成不同字段，杜绝「六种文字代表六个民族」这类简化。

### 2. 历史画 ≠ 现场照片（唐代）

《步辇图》画面中的站位、神态、服饰属于艺术表现。
**文成公主与松赞干布不设为画中热点** —— 他们只能通过
「禄东赞 → 历史事件 → 文成公主」这条链条被展开，
界面上有固定说明为什么这样做。

### 3. 路线精度不得高于证据精度（清代）

迁徙路线按可信度分级渲染：`确认地点` / `较高置信历史廊道` / `大体迁徙区段` /
`路线存在不确定性` / `策展关联`，并配有固定图例与免责声明
「历史迁徙路线示意，并非现代GPS轨迹」。
首领赴承德与大部众迁徙是两条不同路线，默认只显示后者。

### 4. 历史数字不合并（清代）

当不同资料统计口径不同（如「约17万人」与「16.8万余人」），
系统**并列展示各来源的原始表述**，不计算平均值，
也不给出一个虚假的「唯一精确值」。

### 5. AI 生成 ≠ 传统原作（当代）

所有生成结果固定标注「AI辅助文化创意作品 · 非传统羌绣原作」，
并提供 Provenance 溯源抽屉说明使用了哪些元素、AI 新增了什么。
没有明确授权记录的元素不会进入生成流程。

### 6. 在世传承人不可模拟（当代）

平台使用「羌绣数字工坊讲述者」这一知识角色，
**不模拟任何在世传承人的人格、口吻或声音**。

---

## 内容可信度机制

### Claim 级溯源

不是「一个实体挂几个参考书名」，而是把**具体的事实主张（Claim）**单独建表，
再绑定支持它的来源与出处位置。RAG 问答的引用与知识图谱的每一条边**共用同一套溯源机制**。

在界面上点开图谱的任意一条边，都能看到「为什么有这条关系？」——
这条关系的类型（史实 / 研究解释 / 策展关联）、具体主张、以及支持它的来源。

### 可信度标签

界面上的每个内容都带标签，**颜色 + 图标 + 文本三重编码**（不只靠颜色区分）：

| 标签 | 含义 |
|---|---|
| ● 史料确认 | 有可靠来源直接支持 |
| ◐ 研究观点 | 属于研究解释，不是唯一结论 |
| ◇ 数字复原 | 数字化示意，不等同考古精确复原 |
| ✦ AI叙事 | AI 基于审核资料生成的第一人称叙事 |
| ┄ 策展关联 | 为帮助理解建立的主题联系，不是历史因果 |
| ! 存在争议 | 学界存在不同观点 |

### AI 护栏

回答生成前后有两层检查：

**第一层（确定性规则）** —— 正则与关键词表，命中即触发重写：

- 把六种书写系统等同六个民族 / 六种语言
- 声称目睹或亲历（「我亲眼」「我经历过」）
- 单一动因（「唯一原因就是……」）
- 替全体发言（「所有土尔扈特人」「每个人都」）
- 精确 GPS 路线（「每天走到」「精确路线」）
- 合并历史数字为唯一值
- 唐代：把文成公主说成画中人物、把历史画当照片
- 当代：把 AI 生成图称为传统羌绣、模拟在世传承人

**第二层（语义核验）** —— 用 LLM 逐项比对回答与检索到的证据，
检查年代、名称、因果是否都有依据，引用编号是否真实存在。

**无证据不回答**：检索不到可靠材料时，系统返回「资料不足」，
**不允许模型凭常识补全**。

---

## 常用命令

```bash
# 内容校验（ID 唯一性、外键完整性、红线字段、来源等级）
cd backend && ./.venv/Scripts/python.exe scripts/validate_content.py

# 跨章归一化（Claim ID 重名修复；实体跨章共用只报告不修改）
./.venv/Scripts/python.exe scripts/normalize_content.py          # 预演
./.venv/Scripts/python.exe scripts/normalize_content.py --apply  # 写入

# 重新导入内容
./.venv/Scripts/python.exe scripts/seed_postgres.py
./.venv/Scripts/python.exe scripts/seed_neo4j.py

# 重新生成待核验清单（content/REVIEW_TODO.md）
./.venv/Scripts/python.exe scripts/gen_review_todo.py

# 构建向量索引（未配置 Embedding Key 时自动跳过，检索走本地中文匹配）
./.venv/Scripts/python.exe scripts/build_vectors.py

# AI 质量评测（跑各章高频测试题，输出四项指标）
./.venv/Scripts/python.exe scripts/eval_ai.py --chapter yuan_yuntai

# 前端类型检查
cd frontend && npm run typecheck

# 前端构建
cd frontend && npm run build

# 完整游戏闭环（先在另一个终端启动前端）
python frontend/tests/e2e_game_check.py

# 1440 × 900 一屏布局回归与截图
python frontend/tests/e2e_layout_check.py
```

---

## 演示模式

通过 URL 参数切换：

| 参数 | 用途 |
|---|---|
| `?present=true` | 大屏模式：放大字号、缩短过场动画 |
| `?demo=true` | 演示保障模式：预热问题、固定图谱布局、超时自动兜底 |

例：<http://localhost:5173/timeline?present=true>

浏览器内置快捷键：顶栏「全屏」按钮可进入全屏演示。

---

## 待内容组核验清单

项目交付时，有一部分数据是**由实现方依据规格文档补写**的，
尚未经过史料核验。这些数据在数据库中标记为 `draft` 或 `review`，
**不进入 AI 检索**，并在实体上附有 `content_team_todo` 字段说明待办事项。

详见 [`content/REVIEW_TODO.md`](content/REVIEW_TODO.md)。

**最重要的三项：**

1. **元代来源链接** —— 规格文档未提供来源附录，7 条来源的书目信息与 URL 需补全
2. **元代 5 处题刻热点坐标** —— 文档只给出了「藏文」一处的坐标，其余为实现方拟定的初值
3. **当代素材授权** —— 现有纹样元素全部为「仅可展示」，共创流程靠 4 个
   **项目自绘的演示元素**（`pattern_demo_*`）支撑，正式上线前应替换为已授权素材

### 关于当代共创的演示元素

按当代章节 §2.6「没有明确授权的素材默认拒绝」，
`content/contemporary/` 里已有的 15 个纹样元素全部是 `DISPLAY_ONLY`，
没有元素能进入 AI 共创流程，比赛演示时 C08 会走不下去。

为此补充了 4 个 **由项目组自己绘制**的矢量纹样示意图 ——
权利方是本项目本身，因此可以合法地允许用于生成。这不是绕过限制，而是真实地持有了权利。

它们严格保留三条纪律：不声称是传统羌绣作品（`digital_reconstruction` + 名称带「数字示意图」）、
不编造寓意（`meaning_status = GENERAL_CATEGORY_ONLY`）、不可用于训练与商用。

生成方式见 `backend/scripts/add_demo_cocreation_elements.py`（幂等，已执行）。

---

## 已知限制

- **强依赖 Docker**：本项目按全栈方案实现，PostgreSQL 与 Neo4j 不可用时后端无法启动。
  启动脚本会给出明确的中文提示，不会抛出英文堆栈。
- **场景图为 SVG 示意**：默认使用代码生成的矢量场景，放入真实图片后自动替换，
  见 [`content/ASSETS.md`](content/ASSETS.md)。
- **不做 OCR / 古文字识别 / 人脸识别**：所有热点均为预先标注的坐标，
  这是各章规格明确的要求，也是内容准确性的保证。

---

## 技术栈

**前端** Vue 3 · TypeScript · Vite · Pinia · Vue Router · ECharts · GSAP
**后端** Python 3.12 · FastAPI · SQLAlchemy · Pydantic
**数据** PostgreSQL 16 (pgvector) · Neo4j 5
**AI** 大语言模型（可配置供应商）· RAG 检索 · 内容护栏 · 预设问答兜底
