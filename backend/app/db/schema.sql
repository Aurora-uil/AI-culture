-- 《同心千年》PostgreSQL Schema
--
-- 设计原则（来自各章实施规格）：
--   1. 主键一律使用稳定业务 ID（如 artifact_yuntai），前后端与图谱共用同一套 ID。
--   2. Claim 级溯源：不是「实体挂来源」，而是「具体事实主张挂来源」（claim / claim_sources）。
--   3. 审核门禁：review_status != 'approved' 的内容绝不进入 AI 检索。
--   4. 文字 / 语言 / 群体必须分开建模，不得一一对应。
--   5. 权利状态与知识展示权限分离（rights_records 独立于 sources）。
--
-- 本文件由 docker-entrypoint-initdb.d 在首次初始化时执行，也可由
-- scripts/seed_postgres.py 以幂等方式重复执行。

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 一、内容层
-- ============================================================

CREATE TABLE IF NOT EXISTS chapters (
    id                text PRIMARY KEY,
    era               text NOT NULL,
    theme             text NOT NULL,              -- 关键词：相遇/交融/交流/共存/归属/传承
    title             text NOT NULL,
    date_label        text,
    guiding_question  text NOT NULL,              -- §24.1 契约字段
    display_question  text,                       -- 页面内文案（与 guiding_question 并存）
    hero_asset        text,
    accent            text,
    primary_interaction text,                     -- route_flow / script_lens / ...
    ai_character_id   text,
    core_entity_ids   jsonb DEFAULT '[]'::jsonb,
    narration         text,                       -- C01「听它讲述」固定文本，不走 LLM
    sort_order        int  DEFAULT 0,
    status            text DEFAULT 'approved',
    created_at        timestamptz DEFAULT now(),
    updated_at        timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sources (
    id               text PRIMARY KEY,
    title            text NOT NULL,
    author           text,
    institution      text NOT NULL,
    source_type      text NOT NULL,               -- official|academic|book|professional
    source_level     text NOT NULL,               -- S|A|B|C
    publication_year int,
    public_url       text,
    bibliography     text,
    license_note     text,
    -- 来源视角（清代章节要求）：qing_court / museum_curatorial /
    -- modern_scholarship / archaeological_object / modern_public_history
    source_perspective text,
    review_status    text NOT NULL DEFAULT 'approved',
    CONSTRAINT sources_level_chk CHECK (source_level IN ('S','A','B','C')),
    CONSTRAINT sources_status_chk CHECK (review_status IN ('draft','review','approved'))
);

CREATE TABLE IF NOT EXISTS entities (
    id                 text PRIMARY KEY,
    entity_type        text NOT NULL,             -- Person/Artifact/Place/Event/Script/Concept/...
    name               text NOT NULL,
    display_name       text,
    subtitle           text,
    era                text,
    chapter_id         text REFERENCES chapters(id) ON DELETE CASCADE,
    short_summary      text,                      -- 一句话说明（≤120字）
    body_markdown      text,                      -- 审核后的长介绍
    image_url          text,
    -- historical_fact | scholarly_view | digital_reconstruction | ai_narrative | curatorial
    verification_label text NOT NULL DEFAULT 'historical_fact',
    review_status      text NOT NULL DEFAULT 'approved',
    sort_order         int DEFAULT 0,
    -- 类型专属字段（如 Script 的 ui_label / text_language_note；
    -- 纹样的 meaning_status；建筑的建立年代等）。避免为每种类型建表。
    extra              jsonb DEFAULT '{}'::jsonb,
    created_at         timestamptz DEFAULT now(),
    updated_at         timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_entities_chapter ON entities(chapter_id);
CREATE INDEX IF NOT EXISTS idx_entities_type    ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_status  ON entities(review_status);

-- Claim：把「具体事实主张」单独记录，这是溯源的最小单位。
CREATE TABLE IF NOT EXISTS claims (
    id                 text PRIMARY KEY,
    entity_id          text REFERENCES entities(id) ON DELETE CASCADE,
    relation_id        text,                      -- 图谱边也可挂 claim
    claim_text         text NOT NULL,
    claim_type         text NOT NULL DEFAULT 'fact',
    controversy_status text NOT NULL DEFAULT 'stable',   -- stable|disputed
    review_status      text NOT NULL DEFAULT 'approved',
    CONSTRAINT claims_type_chk CHECK (claim_type IN ('fact','interpretation','curatorial','catalogue_fact')),
    CONSTRAINT claims_controversy_chk CHECK (controversy_status IN ('stable','disputed'))
);

CREATE INDEX IF NOT EXISTS idx_claims_entity ON claims(entity_id);

CREATE TABLE IF NOT EXISTS claim_sources (
    claim_id     text NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_id    text NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    locator      text,                            -- 页码 / 段落 / 章节
    support_type text DEFAULT 'direct',           -- direct|indirect
    note         text,
    PRIMARY KEY (claim_id, source_id)
);

-- 图谱边。同时写入 Neo4j；PostgreSQL 保存一份用于内容管理与兜底查询。
CREATE TABLE IF NOT EXISTS relations (
    id                text PRIMARY KEY,
    source_entity_id  text NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id  text NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type     text NOT NULL,              -- LOCATED_IN / USES_SCRIPT / ...
    display_label     text NOT NULL,              -- 中文显示词：位于 / 使用 / 保存有
    claim_type        text NOT NULL DEFAULT 'fact',
    review_status     text NOT NULL DEFAULT 'approved',
    source_ids        jsonb DEFAULT '[]'::jsonb,
    claim_ids         jsonb DEFAULT '[]'::jsonb,
    time_scope        text,
    route_scope       text,                       -- 清代：MASS_MIGRATION 等
    certainty         text,                       -- confirmed / approximate / uncertain
    source_perspective text,
    chapter_id        text REFERENCES chapters(id) ON DELETE CASCADE,
    CONSTRAINT relations_claim_type_chk CHECK (claim_type IN ('fact','interpretation','curatorial','catalogue_fact'))
);

CREATE INDEX IF NOT EXISTS idx_rel_source ON relations(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relations(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_rel_chapter ON relations(chapter_id);

-- RAG 切片。metadata filter 为强制：review_status=approved
-- AND chapter_ids @> [chapter] AND source_level IN (S,A,B)
--
-- 向量以 double precision[] 存储而非 pgvector 固定维度列：
-- 不同 embedding 供应商维度不同（1024 / 1536 / 768），固定维度会导致
-- 换供应商即全表报错。语料规模仅数百条，numpy 暴力余弦耗时在微秒级。
-- 若日后需要 pgvector 索引，可加一列 vector(N) 由 build_vectors.py 同步写入。
CREATE TABLE IF NOT EXISTS rag_chunks (
    id            text PRIMARY KEY,
    source_id     text REFERENCES sources(id) ON DELETE CASCADE,
    chapter_ids   jsonb DEFAULT '[]'::jsonb,
    entity_ids    jsonb DEFAULT '[]'::jsonb,
    claim_ids     jsonb DEFAULT '[]'::jsonb,
    title         text,
    text          text NOT NULL,
    token_count   int,
    source_level  text,
    meaning_status text,                          -- 当代：DOCUMENTED / UNKNOWN / ...
    review_status text NOT NULL DEFAULT 'approved',
    embedding     double precision[],
    embedding_dim int
);

CREATE INDEX IF NOT EXISTS idx_chunks_review  ON rag_chunks(review_status);
CREATE INDEX IF NOT EXISTS idx_chunks_chapter ON rag_chunks USING gin(chapter_ids);

-- AI 角色配置
CREATE TABLE IF NOT EXISTS characters (
    id                    text PRIMARY KEY,
    name                  text NOT NULL,
    character_type        text NOT NULL,          -- person|artifact|narrator
    base_entity_id        text REFERENCES entities(id) ON DELETE SET NULL,
    chapter_id            text REFERENCES chapters(id) ON DELETE CASCADE,
    subtitle              text,
    disclaimer            text NOT NULL,          -- 必须在界面固定显示的 AI 身份说明
    system_prompt_version text DEFAULT 'v1',
    enabled               boolean DEFAULT true
);

-- 演示保障：预审核问答库（断网 / 无 Key / 超时 时使用）
CREATE TABLE IF NOT EXISTS fallback_faq (
    id                 text PRIMARY KEY,
    chapter_id         text REFERENCES chapters(id) ON DELETE CASCADE,
    character_id       text,
    canonical_question text NOT NULL,
    keywords           jsonb DEFAULT '[]'::jsonb,
    intent             text,
    answer_markdown    text NOT NULL,
    source_ids         jsonb DEFAULT '[]'::jsonb,
    related_entity_ids jsonb DEFAULT '[]'::jsonb,
    review_status      text NOT NULL DEFAULT 'approved'
);

CREATE INDEX IF NOT EXISTS idx_faq_chapter ON fallback_faq(chapter_id);

-- ============================================================
-- 二、章节专属内容
-- ============================================================

-- 场景（元代券洞、北魏双石窟、唐代画卷、汉代地图、清代地图）
CREATE TABLE IF NOT EXISTS scenes (
    id                  text PRIMARY KEY,
    chapter_id          text REFERENCES chapters(id) ON DELETE CASCADE,
    name                text NOT NULL,
    scene_kind          text DEFAULT 'image',     -- image | map | artwork | workbench
    background_asset_id text,
    width               int,
    height              int,
    -- 场景性质说明，例如「历史迁徙路线示意，并非现代GPS轨迹」
    disclaimer          text,
    version             int DEFAULT 1,
    status              text DEFAULT 'approved'
);

-- 预标注热点。坐标 0–1 归一化，不依赖任何视觉识别算法。
CREATE TABLE IF NOT EXISTS scene_hotspots (
    id               text PRIMARY KEY,
    scene_id         text NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    entity_id        text REFERENCES entities(id) ON DELETE CASCADE,
    shape            text DEFAULT 'polygon',      -- point|rect|polygon|geo
    normalized_points jsonb NOT NULL,
    label            text,
    -- 清代：确定地点 / 较高置信廊道 / 大体区段 / 不确定 / 策展关联
    certainty        text,
    route_scope      text,
    group_key        text,                        -- 北魏对照：同一对照组的 key
    sort_order       int DEFAULT 0,
    enabled          boolean DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_hotspot_scene ON scene_hotspots(scene_id);

-- 历史地图节点与区段（汉代丝路、清代迁徙）
CREATE TABLE IF NOT EXISTS historical_maps (
    id                text PRIMARY KEY,
    chapter_id        text REFERENCES chapters(id) ON DELETE CASCADE,
    name              text NOT NULL,
    background_asset_id text,
    coordinate_system text DEFAULT 'normalized_canvas',
    disclaimer        text
);

CREATE TABLE IF NOT EXISTS map_nodes (
    id          text PRIMARY KEY,
    map_id      text NOT NULL REFERENCES historical_maps(id) ON DELETE CASCADE,
    entity_id   text REFERENCES entities(id) ON DELETE SET NULL,
    label       text NOT NULL,
    x           double precision NOT NULL,
    y           double precision NOT NULL,
    certainty   text DEFAULT 'confirmed_region',
    route_scope text,
    sort_order  int DEFAULT 0
);

CREATE TABLE IF NOT EXISTS map_segments (
    id           text PRIMARY KEY,
    map_id       text NOT NULL REFERENCES historical_maps(id) ON DELETE CASCADE,
    from_node_id text NOT NULL,
    to_node_id   text NOT NULL,
    label        text,
    geometry     jsonb DEFAULT '[]'::jsonb,       -- 归一化折线点集；宁可留空也不虚构精度
    certainty    text DEFAULT 'approximate',      -- confirmed_area|approximate_corridor|uncertain_segment|curatorial_connector
    route_scope  text DEFAULT 'MASS_MIGRATION',
    source_ids   jsonb DEFAULT '[]'::jsonb,
    claim_ids    jsonb DEFAULT '[]'::jsonb,
    review_status text DEFAULT 'approved'
);

CREATE INDEX IF NOT EXISTS idx_seg_map ON map_segments(map_id);

-- 证据时间轴（清代）
CREATE TABLE IF NOT EXISTS timeline_events (
    id             text PRIMARY KEY,
    chapter_id     text REFERENCES chapters(id) ON DELETE CASCADE,
    entity_id      text REFERENCES entities(id) ON DELETE SET NULL,
    display_date   text NOT NULL,                 -- 1771年夏季 —— 保留原始精度
    date_precision text,                          -- day|month_or_period|season|year|decade|period
    sort_value     numeric,                       -- 仅用于排序，不用于展示
    title          text NOT NULL,
    summary        text,
    entity_ids     jsonb DEFAULT '[]'::jsonb,
    claim_ids      jsonb DEFAULT '[]'::jsonb,
    source_ids     jsonb DEFAULT '[]'::jsonb,
    sort_order     int DEFAULT 0
);

-- 历史数字的多来源并列。绝不求平均、绝不输出唯一「精确值」。
CREATE TABLE IF NOT EXISTS historical_estimates (
    id            text PRIMARY KEY,
    chapter_id    text REFERENCES chapters(id) ON DELETE CASCADE,
    entity_id     text REFERENCES entities(id) ON DELETE SET NULL,
    metric        text NOT NULL,                  -- departure_population
    display_name  text NOT NULL,                  -- 东归出发人数
    value_text    text NOT NULL,                  -- 「约17万人」—— 原样保留，不格式化
    numeric_value double precision,
    numeric_min   double precision,
    numeric_max   double precision,
    unit          text,
    source_id     text REFERENCES sources(id) ON DELETE SET NULL,
    claim_id      text REFERENCES claims(id) ON DELETE SET NULL,
    scope_note    text,                           -- 统计口径说明
    estimate_type text DEFAULT 'source_reported',
    display_policy text DEFAULT 'show_all_approved',
    review_status text DEFAULT 'approved'
);

CREATE INDEX IF NOT EXISTS idx_est_metric ON historical_estimates(chapter_id, metric);

-- 北魏证据对照
CREATE TABLE IF NOT EXISTS comparison_groups (
    id          text PRIMARY KEY,
    chapter_id  text REFERENCES chapters(id) ON DELETE CASCADE,
    name        text NOT NULL,                    -- 服饰 / 雕塑 / 音乐 / 建筑
    description text,
    sort_order  int DEFAULT 0
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id            text PRIMARY KEY,
    chapter_id    text REFERENCES chapters(id) ON DELETE CASCADE,
    entity_id     text REFERENCES entities(id) ON DELETE SET NULL,
    group_key     text REFERENCES comparison_groups(id) ON DELETE SET NULL,
    site_key      text,                           -- yungang | longmen
    title         text NOT NULL,
    -- 固定四层：看到什么 / 来源如何描述 / 能支持什么 / 不能推出什么
    observed      text,
    described_by_source text,
    supports      text,
    does_not_support text,
    caveat        text,                           -- 固定提示（如「数字示意不等于实际手工技艺」）
    image_url     text,
    claim_ids     jsonb DEFAULT '[]'::jsonb,
    source_ids    jsonb DEFAULT '[]'::jsonb,
    review_status text DEFAULT 'approved'
);

CREATE INDEX IF NOT EXISTS idx_evidence_chapter ON evidence_items(chapter_id, group_key);

-- ============================================================
-- 三、权利与 AIGC（当代章节）
-- ============================================================

-- 每一个视觉资产都必须能回答：谁提供、能否展示、能否裁切、
-- 能否作为生成输入、能否用于训练、能否商用、是否需署名。
CREATE TABLE IF NOT EXISTS rights_records (
    id                     text PRIMARY KEY,
    asset_id               text NOT NULL,
    entity_id              text REFERENCES entities(id) ON DELETE SET NULL,
    rights_holder          text,
    rights_basis           text,
    license_document_ref   text,
    can_display            boolean DEFAULT false,
    can_crop               boolean DEFAULT false,
    can_transform          boolean DEFAULT false,
    can_use_for_generation boolean DEFAULT false,
    can_use_for_training   boolean DEFAULT false,
    can_download_original  boolean DEFAULT false,
    commercial_use         boolean DEFAULT false,
    attribution_required   boolean DEFAULT false,
    attribution_text       text,
    valid_from             date,
    valid_until            date,
    territory              text,
    notes                  text,
    review_status          text DEFAULT 'approved'
);

-- 元素是否允许进入 AI 共创，由后台配置，不由 LLM 实时判断。
CREATE TABLE IF NOT EXISTS generation_policies (
    id                 text PRIMARY KEY,
    entity_id          text REFERENCES entities(id) ON DELETE CASCADE,
    policy_type        text NOT NULL,             -- ALLOW_COMBINATION | ALLOW_COLOR_VARIATION | ALLOW_SCALE_ONLY | DISPLAY_ONLY | REVIEW_REQUIRED | BLOCKED
    allowed_operations jsonb DEFAULT '[]'::jsonb,
    blocked_operations jsonb DEFAULT '[]'::jsonb,
    review_note        text,
    approved_by        text,
    review_status      text DEFAULT 'approved'
);

CREATE TABLE IF NOT EXISTS creation_baskets (
    id                   text PRIMARY KEY,
    exploration_session_id text,
    status               text DEFAULT 'open',
    created_at           timestamptz DEFAULT now(),
    updated_at           timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS creation_basket_items (
    basket_id          text NOT NULL REFERENCES creation_baskets(id) ON DELETE CASCADE,
    entity_id          text NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    item_type          text,                      -- pattern | technique | motif_category | object
    rights_validated   boolean DEFAULT false,
    generation_policy_id text REFERENCES generation_policies(id) ON DELETE SET NULL,
    added_at           timestamptz DEFAULT now(),
    PRIMARY KEY (basket_id, entity_id)
);

CREATE TABLE IF NOT EXISTS generation_jobs (
    id                    text PRIMARY KEY,
    exploration_session_id text,
    basket_id             text REFERENCES creation_baskets(id) ON DELETE SET NULL,
    status                text NOT NULL DEFAULT 'PENDING',
    application_type      text,                   -- bookmark|poster|phone_wallpaper|packaging_concept|pattern_tile
    composition_option    text,                   -- CENTERED|BORDER|REPEAT|SYMMETRIC|FREE_MODERN
    color_option          text,
    user_text             text,
    compiled_prompt_ref   text,
    model_provider        text,
    model_name            text,
    model_version         text,
    error_code            text,
    created_at            timestamptz DEFAULT now(),
    completed_at          timestamptz
);

CREATE TABLE IF NOT EXISTS generated_assets (
    id                text PRIMARY KEY,
    generation_job_id text REFERENCES generation_jobs(id) ON DELETE CASCADE,
    asset_path        text,
    thumbnail_path    text,
    -- 固定标签，不可省略：AI辅助文化创意作品 · 非传统羌绣原作
    label             text NOT NULL DEFAULT 'AI辅助文化创意作品 · 非传统羌绣原作',
    is_fallback_sample boolean DEFAULT false,     -- 是否为「演示保障样例」
    validation_status text DEFAULT 'PASSED',
    created_at        timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS generation_provenance (
    id                     text PRIMARY KEY,
    generated_asset_id     text REFERENCES generated_assets(id) ON DELETE CASCADE,
    element_ids            jsonb DEFAULT '[]'::jsonb,
    technique_reference_ids jsonb DEFAULT '[]'::jsonb,
    source_ids             jsonb DEFAULT '[]'::jsonb,
    rights_record_ids      jsonb DEFAULT '[]'::jsonb,
    prompt_template_version text,
    compiler_output_hash   text,
    model_name             text,
    model_version          text,
    ai_added_note          text,                  -- 「AI新增：构图排列 / 数字背景 / 色彩组合」
    generated_at           timestamptz DEFAULT now()
);

-- ============================================================
-- 四、会话与探索
-- ============================================================

-- 匿名用户，不采集身份证 / 手机号 / 敏感个人信息
CREATE TABLE IF NOT EXISTS exploration_sessions (
    id                  text PRIMARY KEY,
    anonymous_user_id   text,
    chapter_id          text REFERENCES chapters(id) ON DELETE CASCADE,
    started_at          timestamptz DEFAULT now(),
    last_active_at      timestamptz DEFAULT now(),
    completed_at        timestamptz,
    progress            numeric DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exploration_events (
    id         bigserial PRIMARY KEY,
    session_id text REFERENCES exploration_sessions(id) ON DELETE CASCADE,
    event_type text NOT NULL,                     -- CHAPTER_ENTER / ENTITY_VIEW / CHAT_ASK / ...
    entity_id  text,
    relation_id text,
    source_id  text,
    metadata   jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_exp_events_session ON exploration_events(session_id);

CREATE TABLE IF NOT EXISTS exploration_node_state (
    session_id    text NOT NULL REFERENCES exploration_sessions(id) ON DELETE CASCADE,
    entity_id     text NOT NULL,
    first_seen_at timestamptz DEFAULT now(),
    last_seen_at  timestamptz DEFAULT now(),
    view_count    int DEFAULT 1,
    PRIMARY KEY (session_id, entity_id)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id                     text PRIMARY KEY,
    exploration_session_id text,
    chapter_id             text REFERENCES chapters(id) ON DELETE CASCADE,
    character_id           text REFERENCES characters(id) ON DELETE SET NULL,
    created_at             timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id             text PRIMARY KEY,
    session_id     text NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role           text NOT NULL,                 -- user|assistant
    content        text NOT NULL,
    answer_mode    text DEFAULT 'narrative',      -- narrative|factual
    -- DONE | NO_EVIDENCE | MODEL_TIMEOUT | VALIDATION_FAILED | FALLBACK_DEMO
    status         text DEFAULT 'DONE',
    uncertainty    text,
    response_tier  text,                          -- live_rag | local_retrieval | faq_fallback
    model_name     text,
    prompt_version text,
    created_at     timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_msg_session ON chat_messages(session_id, created_at);

CREATE TABLE IF NOT EXISTS chat_message_citations (
    message_id text NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    source_id  text REFERENCES sources(id) ON DELETE SET NULL,
    chunk_id   text,
    claim_id   text,
    sort_order int DEFAULT 0,
    PRIMARY KEY (message_id, source_id, chunk_id)
);

-- ============================================================
-- 五、初始数据由 seed 脚本写入（scripts/seed_postgres.py）
-- ============================================================
