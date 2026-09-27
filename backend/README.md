# 《同心千年》后端

FastAPI + PostgreSQL + Neo4j。内容层支持 Claim 级溯源，AI 层采用 5 段 Prompt 链
并强制「无证据不回答」。

---

## 一、启动步骤（三步）

```bash
# 1. 启动数据库容器（PostgreSQL 5433 / Neo4j 7687）
cd C:\Users\HUO\Desktop\同心千年
docker compose up -d

# 2. 把 content/ 写入数据库（两个脚本都幂等，可反复执行）
cd backend
.venv/Scripts/python.exe scripts/seed_postgres.py
.venv/Scripts/python.exe scripts/seed_neo4j.py

# 3. 启动服务
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000 --reload
```

或者用封装好的启动脚本（会先做一次环境自检）：

```bash
cd backend
.venv/Scripts/python.exe run.py            # 自检 + 启动（含热重载）
.venv/Scripts/python.exe run.py --check    # 只自检，不启动
```

启动后：

| 地址 | 说明 |
|---|---|
| `http://127.0.0.1:8000/api/v1/health` | 健康检查（含 LLM 是否为演示保障模式） |
| `http://127.0.0.1:8000/docs` | 交互式接口文档 |

前端在 `frontend/`，`npm run dev` 后访问 `http://localhost:5173`，
Vite 已把 `/api` 代理到 `127.0.0.1:8000`。

### 首次配置

```bash
cd backend
cp .env.example .env
```

**`.env` 里 `LLM_API_KEY` 留空即可直接跑** —— 系统会自动进入「演示保障模式」，
由已审核的预设问答库作答，界面会明确标注，不会伪装成实时 AI。
填入 Key 后自动切换为实时 RAG。

---

## 二、脚本一览

| 脚本 | 作用 | 是否需要 Key |
|---|---|---|
| `scripts/validate_content.py` | 校验 `content/`：ID 唯一性、外键完整性、`source_level` 非空、chunk 字数 300–800、红线字段、review_status 分布 | 否 |
| `scripts/seed_postgres.py` | 把 `content/` 写入 PostgreSQL（`ON CONFLICT DO UPDATE`，幂等） | 否 |
| `scripts/seed_neo4j.py` | 把实体与关系写入 Neo4j（`MERGE`，幂等） | 否 |
| `scripts/build_vectors.py` | 计算 chunk 向量。**无 `EMBEDDING_API_KEY` 时跳过并提示** | 是 |
| `scripts/eval_ai.py` | 跑各章高频测试题，输出四项指标 | 否 |

内容改了以后重新跑一次 `seed_postgres.py` + `seed_neo4j.py` 即可，
不要手改数据库 —— 数据库随时可以从 `content/` 重建。

验收前建议按顺序跑一遍：

```bash
.venv/Scripts/python.exe scripts/validate_content.py
.venv/Scripts/python.exe scripts/seed_postgres.py
.venv/Scripts/python.exe scripts/seed_neo4j.py
.venv/Scripts/python.exe scripts/eval_ai.py
```

---

## 三、目录结构

```
backend/
├── app/
│   ├── config.py            配置（pydantic-settings 读 .env）
│   ├── main.py              FastAPI 入口、CORS、全局中文异常处理
│   ├── db/
│   │   ├── schema.sql       表结构（已建表，权威定义，不修改）
│   │   ├── alters.sql       补充字段 / 表（IF NOT EXISTS，可重复执行）
│   │   ├── postgres.py      engine / SessionLocal / get_db
│   │   └── neo4j.py         driver 单例 / get_graph_db
│   ├── models/              SQLAlchemy ORM（与 schema.sql 一一对应）
│   ├── schemas/             Pydantic 出参（字段名对齐前端 types/index.ts）
│   ├── services/            内容 / 图谱 / 探索 / 共创 业务逻辑
│   ├── ai/
│   │   ├── prompts/         六章 Prompt A + 通用 B/C/D/E
│   │   ├── llm/             Provider：openai_compat / anthropic / mock
│   │   ├── retriever.py     检索（强制 metadata filter）
│   │   ├── reranker.py      重排（Prompt C）
│   │   ├── guards.py        确定性规则护栏
│   │   ├── validator.py     核验（Prompt D + 引用真实性）
│   │   └── service.py       编排
│   └── api/v1/              health / chapters / entities / scenes / graph
│                            / chat / exploration / cocreation
└── scripts/                 见上表
```

---

## 四、AI 层的几条硬性约定

1. **No Context No Answer**：检索不到证据时返回 `NO_EVIDENCE`、`answer` 为空，
   绝不让模型凭常识补全。
2. **强制检索过滤**：`review_status='approved'` AND `chapter_ids` 含当前章
   AND `source_level IN (S,A,B)`。C 级来源永不进入回答。
3. **护栏是确定性的**：`ai/guards.py` 用正则/关键词表拦截越界表述，
   不依赖模型，任何回答（含兜底库回答）都要过。命中即带违规原因重写一次，
   仍违规则降级为兜底回答并标 `VALIDATION_FAILED`。
4. **`response_tier` 如实标注**，界面据此渲染，绝不把兜底伪装成实时 AI：

   | tier | 含义 |
   |---|---|
   | `live_rag` | 真实模型 + 真实检索证据 |
   | `local_retrieval` | 无模型，仅基于本地检索 |
   | `faq_fallback` | 来自已审核的预设问答库（演示保障模式） |

5. **先校验后流式**：`POST /chat/messages` 先在服务端跑完
   检索 → 改写 → 生成 → 护栏 → 核验，通过之后才用 SSE 分块吐字。
6. **进度上报永不阻断浏览**：`POST /exploration/events` 对重复上报、
   未知 `event_type`、无效会话一律返回 200。
7. **权利校验 fail-closed**：共创接口在权利查询异常时默认不生成；
   没有配置图像生成 Key 时返回预置演示样例，`is_fallback_sample: true`，
   标签固定为「AI辅助文化创意作品 · 非传统羌绣原作」。

---

## 五、常见问题

**Q：数据库为空时接口会报错吗？**
不会。所有列表接口返回空数组，详情接口返回中文 404，`/health` 返回
`status: degraded`。内容还没生成完也能正常启动。

**Q：Neo4j 挂了怎么办？**
图谱接口会自动回退到 PostgreSQL 的 `relations` 表（schema.sql 里写明
PostgreSQL 保存一份边数据用于兜底查询）；两者都为空时返回空子图。

**Q：没有 Embedding Key 会影响检索吗？**
不会。检索自动切换到纯 Python 中文检索（字符 bigram + 关键词加权），
不依赖任何外部服务。

**Q：端口被占用？**
PostgreSQL 用 5433（5432 已被本机另一个项目占用），Neo4j 用 7687，
后端默认 8000。可用 `run.py --port 8001` 换端口。

**Q：Windows 控制台中文日志乱码？**
后端已强制 UTF-8 输出；若仍乱码，执行 `chcp 65001` 切换代码页。
