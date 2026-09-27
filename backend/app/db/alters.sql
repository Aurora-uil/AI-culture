-- 《同心千年》补充字段 / 表
--
-- schema.sql 是已建表的权威定义，不直接修改。内容层在实现过程中需要的
-- 少量补充统一放在这里，全部使用 IF NOT EXISTS，可重复执行。
-- seed_postgres.py 与应用启动时都会调用。

-- 章节 slug：前端路由使用 han / northern-wei / tang / yuan / qing / contemporary
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS slug text;

-- 跨章共用实体（如「长安」同属汉代与唐代）的完整归属。
-- chapter_id 保留为「主归属章节」，chapter_ids 记录它被哪些章引用。
-- 同一个历史对象本就跨越多个时代，共用节点才能让总图谱真正连起来。
ALTER TABLE entities ADD COLUMN IF NOT EXISTS chapter_ids jsonb DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_entities_chapter_ids ON entities USING gin(chapter_ids);

-- AI 角色头像（前端 Character.image_url）
ALTER TABLE characters ADD COLUMN IF NOT EXISTS image_url text;

-- 回答关联实体（regenerate 时需要回放，避免只存引用不存实体）
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS related_entity_ids jsonb DEFAULT '[]'::jsonb;

-- 回答反馈（点赞 / 点踩 / 报告问题）
CREATE TABLE IF NOT EXISTS chat_message_feedback (
    id         text PRIMARY KEY,
    message_id text NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    kind       text NOT NULL,              -- helpful | not_helpful | inaccurate | other
    note       text,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_message ON chat_message_feedback(message_id);

-- 章节额外数据（progress_weights 等），内容目录缺失时的兜底来源
CREATE TABLE IF NOT EXISTS chapter_extras (
    chapter_id text PRIMARY KEY REFERENCES chapters(id) ON DELETE CASCADE,
    data       jsonb DEFAULT '{}'::jsonb,
    updated_at timestamptz DEFAULT now()
);
