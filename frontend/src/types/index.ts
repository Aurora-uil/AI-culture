/* ============================================================
   《同心千年》前端类型定义
   与 content/SCHEMA.md 及后端 Pydantic schema 保持一致
   ============================================================ */

/** 史料可信度标签（设计系统 §81，全项目统一文案，不得换词） */
export type VerificationLabel =
  | 'historical_fact' // 史料确认   深绿 ●
  | 'scholarly_view' // 研究观点   金棕 ◐
  | 'digital_reconstruction' // 数字复原   蓝灰 ◇
  | 'ai_narrative' // AI叙事     紫灰 ✦
  | 'curatorial' // 策展关联   虚线链
  | 'disputed' // 存在争议   琥珀色 !

export type ReviewStatus = 'draft' | 'review' | 'approved'

/** 图谱边类型（设计系统 §40） */
export type ClaimType = 'fact' | 'interpretation' | 'curatorial' | 'catalogue_fact'

export type SourceType = 'official' | 'academic' | 'book' | 'professional'
export type SourceLevel = 'S' | 'A' | 'B' | 'C'
export type SourcePerspective =
  | 'qing_court'
  | 'museum_curatorial'
  | 'modern_scholarship'
  | 'archaeological_object'
  | 'modern_public_history'

export type EntityType =
  | 'Person'
  | 'Artifact'
  | 'Artwork'
  | 'Place'
  | 'Region'
  | 'Event'
  | 'Script'
  | 'Language'
  | 'Concept'
  | 'Period'
  | 'HeritageStructure'
  | 'InscriptionSet'
  | 'Text'
  | 'Group'
  | 'Institution'
  | 'Site'
  | 'Technique'
  | 'MotifCategory'
  | 'PatternElement'
  | 'ObjectType'
  | 'Practice'
  | 'ICHProject'
  | 'AttributionClaim'
  | 'Work'
  | 'Chapter'
  | 'RightsRecord'

/* ---------------- 章节 ---------------- */

export type ChapterSlug = 'han' | 'northern-wei' | 'tang' | 'yuan' | 'qing' | 'contemporary'

export type InteractionType =
  | 'route_flow'
  | 'evidence_compare'
  | 'scroll_relation'
  | 'script_lens'
  | 'migration_timeline'
  | 'knowledge_cocreation'

export interface Chapter {
  id: string
  slug: ChapterSlug
  era: string
  keyword: string
  title: string
  date_label: string
  guiding_question: string
  display_question?: string
  accent: string
  primary_interaction: InteractionType
  ai_character_id: string
  core_entity_ids: string[]
  narration?: string
  sort_order: number
  /** 该章探索进度 0–100 */
  progress?: number
}

/* ---------------- 实体 ---------------- */

export interface Entity {
  id: string
  entity_type: EntityType
  name: string
  display_name?: string
  subtitle?: string
  era?: string
  chapter_id?: string
  short_summary?: string
  body_markdown?: string
  image_url?: string | null
  verification_label: VerificationLabel
  review_status: ReviewStatus
  sort_order?: number
  extra?: Record<string, any>
  source_count?: number
  related_entity_count?: number
}

/** Script 类型实体的 extra 字段 */
export interface ScriptExtra {
  canonical_name?: string
  alternate_names?: string[]
  script_family_note?: string
  ui_label?: string
  yuntai_usage_note?: string
  text_language_note?: string
  forbidden_simplification?: string
  content_team_todo?: string
}

/** Artwork 类型实体的 extra 字段 */
export interface ArtworkExtra {
  collection?: string
  catalogue_period?: string
  catalogued_author?: string
  attribution_status?: string
  attribution_note?: string
  depicted_in_artwork?: boolean
  caveat?: string
}

/** 纹样元素实体的 extra 字段（当代章节） */
export interface PatternExtra {
  meaning_status?: MeaningStatus
  meaning_claim_ids?: string[]
  motif_category_id?: string
  rights_record_id?: string
  generation_policy_id?: string
}

/** 文化含义状态（当代章节 §2.3）：只有 DOCUMENTED 才能展示具体寓意 */
export type MeaningStatus =
  | 'DOCUMENTED'
  | 'GENERAL_CATEGORY_ONLY'
  | 'UNKNOWN'
  | 'RESEARCH_DISPUTED'

/* ---------------- 来源与 Claim ---------------- */

export interface SourceClaim {
  claim_id: string
  text: string
}

export interface Source {
  id: string
  title: string
  author?: string | null
  institution: string
  source_type: SourceType
  source_level: SourceLevel
  publication_year?: number | null
  public_url?: string | null
  bibliography?: string | null
  license_note?: string | null
  source_perspective?: SourcePerspective | null
  review_status: ReviewStatus
  /** 该来源支持了哪些具体事实（设计系统 §36 要求，不能只列参考文献名） */
  claims?: SourceClaim[]
}

export interface Claim {
  id: string
  entity_id?: string
  relation_id?: string
  claim_text: string
  claim_type: ClaimType
  controversy_status: 'stable' | 'disputed'
  review_status: ReviewStatus
  source_ids?: string[]
}

/* ---------------- 图谱 ---------------- */

export interface GraphNode {
  id: string
  type: EntityType
  name: string
  subtitle?: string
  short_summary?: string
  explored: boolean
  /** 是否中心节点（1.35× 尺寸） */
  is_center?: boolean
  /** ECharts 用的固定坐标（演示模式下固定布局，不使用随机） */
  x?: number
  y?: number
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  relation_type: string
  display_label: string
  claim_type: ClaimType
  review_status: ReviewStatus
  source_ids?: string[]
}

export interface SubGraph {
  center_entity_id: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  truncated?: boolean
  message?: string
}

export interface RelationEvidence {
  relation_id: string
  claim: string
  claim_type: ClaimType
  display_label?: string
  subject_name?: string
  object_name?: string
  sources: Pick<Source, 'id' | 'title' | 'institution' | 'source_level' | 'public_url'>[]
}

/* ---------------- 场景与热点 ---------------- */

export type HotspotStatus = 'LOCKED' | 'UNSEEN' | 'SEEN' | 'SELECTED'
export type HotspotShape = 'polygon' | 'rect' | 'point'

export interface Hotspot {
  id: string
  entity_id: string
  shape: HotspotShape
  /** 0–1 归一化坐标 */
  normalized_points: number[][] | number[]
  label?: string
  group_key?: string | null
  certainty?: RouteCertainty | null
  route_scope?: RouteScope | null
  sort_order?: number
}

export interface Scene {
  id: string
  chapter_id?: string
  name: string
  scene_kind: 'image' | 'map' | 'artwork' | 'workbench'
  background_asset_id?: string | null
  width?: number
  height?: number
  disclaimer?: string | null
  hotspots?: Hotspot[]
}

/* ---------------- 历史地图 ---------------- */

/** 路线可信度（清代 §2.3）—— 路线精度不得高于证据精度 */
export type RouteCertainty =
  | 'confirmed_area'
  | 'approximate_corridor'
  | 'uncertain_segment'
  | 'curatorial_connector'

/** 路线范围 —— 大部众迁徙与首领赴承德绝不能混为一条线 */
export type RouteScope = 'MASS_MIGRATION' | 'LEADER_AUDIENCE_JOURNEY' | 'SETTLEMENT_DISTRIBUTION'

export interface MapNode {
  id: string
  entity_id?: string | null
  label: string
  x: number
  y: number
  certainty: RouteCertainty | 'confirmed_region'
  route_scope: RouteScope
  sort_order?: number
}

export interface MapSegment {
  id: string
  from_node_id: string
  to_node_id: string
  label?: string
  geometry: number[][]
  certainty: RouteCertainty
  route_scope: RouteScope
  source_ids?: string[]
  claim_ids?: string[]
}

export interface HistoricalMap {
  id: string
  name: string
  coordinate_system: string
  disclaimer?: string | null
  nodes: MapNode[]
  segments: MapSegment[]
}

/* ---------------- 时间轴与历史数字 ---------------- */

export type DatePrecision =
  | 'day'
  | 'month_or_period'
  | 'season'
  | 'year'
  | 'decade'
  | 'period'

export interface TimelineEvent {
  id: string
  entity_id?: string | null
  display_date: string
  date_precision: DatePrecision
  title: string
  summary?: string
  entity_ids?: string[]
  source_ids?: string[]
}

/** 历史估算：必须多来源并列，绝不合并为一个「唯一精确值」 */
export interface HistoricalEstimate {
  id: string
  metric: string
  display_name: string
  value_text: string
  source_id?: string | null
  source_title?: string
  source_institution?: string
  scope_note?: string
  estimate_type?: string
}

export interface EstimateGroup {
  metric: string
  display_name: string
  estimates: HistoricalEstimate[]
  display_policy: string
}

/* ---------------- 证据对照（北魏） ---------------- */

export interface EvidenceItem {
  id: string
  entity_id?: string | null
  group_key: string
  site_key: 'yungang' | 'longmen'
  title: string
  /** 固定四层 */
  observed: string
  described_by_source: string
  supports: string
  does_not_support: string
  caveat?: string
  image_url?: string | null
  source_ids?: string[]
}

export interface ComparisonGroup {
  id: string
  name: string
  description?: string
  sort_order?: number
}

/* ---------------- AI 对话 ---------------- */

export type AnswerMode = 'narrative' | 'factual'

/** AI 回答状态机（各章 §13） */
export type AnswerStatus =
  | 'IDLE'
  | 'RETRIEVING'
  | 'GENERATING'
  | 'VALIDATING'
  | 'DONE'
  | 'NO_EVIDENCE'
  | 'MODEL_TIMEOUT'
  | 'VALIDATION_FAILED'
  | 'NETWORK_ERROR'
  | 'RATE_LIMIT'
  | 'FALLBACK_DEMO'

/** 回答来源层级 —— 界面必须如实标注，绝不把兜底伪装成实时 AI */
export type ResponseTier = 'live_rag' | 'local_retrieval' | 'faq_fallback'

export interface Citation {
  source_id: string
  title: string
  institution: string
  source_level?: SourceLevel
  public_url?: string | null
  claim_text?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  answer_mode?: AnswerMode
  status: AnswerStatus
  uncertainty?: 'low' | 'medium' | 'high'
  response_tier?: ResponseTier
  citations?: Citation[]
  related_entities?: Pick<Entity, 'id' | 'display_name' | 'name' | 'entity_type'>[]
  created_at?: string
}

export interface RecommendedQuestion {
  id: string
  text: string
  intent?: string
}

export interface Character {
  id: string
  name: string
  character_type: 'person' | 'artifact' | 'narrator'
  base_entity_id?: string | null
  subtitle?: string
  /** 必须固定显示的 AI 身份说明 */
  disclaimer: string
  image_url?: string | null
}

/* ---------------- 探索 ---------------- */

export interface ExplorationProgress {
  session_id: string
  chapter_id: string
  progress: number
  visited_entity_ids: string[]
  visited_relation_ids: string[]
  viewed_source_ids: string[]
  asked_question_count: number
  /** 六章各自的完成度 */
  chapters?: { chapter_id: string; progress: number; status: string }[]
  totals?: {
    entities: number
    artifacts: number
    places: number
    relations: number
    sources: number
  }
}

export interface ExplorationSummary {
  summary: string
  next_entity_ids: string[]
  cached?: boolean
}

export type ExplorationEventType =
  | 'CHAPTER_ENTER'
  | 'SCENE_ENTER'
  | 'ENTITY_VIEW'
  | 'LENS_OPEN'
  | 'CHAT_ASK'
  | 'CHAT_SOURCE_VIEW'
  | 'GRAPH_OPEN'
  | 'GRAPH_NODE_EXPAND'
  | 'RELATION_EVIDENCE_VIEW'
  | 'SOURCE_VIEW'
  | 'CHAPTER_COMPLETE'
  | 'COCREATION_START'
  | 'COCREATION_COMPLETE'
  | 'ARTWORK_HOTSPOT_VIEW'
  | 'OUTSIDE_RELATION_EXPAND'
  | 'MIGRATION_SEGMENT_VIEW'

/* ---------------- AI 共创（当代） ---------------- */

export type CompositionOption = 'CENTERED' | 'BORDER' | 'REPEAT' | 'SYMMETRIC' | 'FREE_MODERN'
export type ApplicationType =
  | 'bookmark'
  | 'poster'
  | 'phone_wallpaper'
  | 'packaging_concept'
  | 'pattern_tile'

export type GenerationPolicy =
  | 'ALLOW_COMBINATION'
  | 'ALLOW_COLOR_VARIATION'
  | 'ALLOW_SCALE_ONLY'
  | 'DISPLAY_ONLY'
  | 'REVIEW_REQUIRED'
  | 'BLOCKED'

export interface RightsRecord {
  id: string
  asset_id: string
  rights_holder?: string
  rights_basis?: string
  can_display: boolean
  can_crop: boolean
  can_transform: boolean
  can_use_for_generation: boolean
  can_use_for_training: boolean
  can_download_original: boolean
  commercial_use: boolean
  attribution_required: boolean
  attribution_text?: string
  review_status: ReviewStatus
}

/**
 * 可用于共创的元素。
 * 注意：`generatable` 由后端根据 generation_policy + rights_record 共同判定。
 * 「知识可展示」与「素材可用于生成」是两套权限，不能互相推导。
 */
export interface CocreationElement {
  id: string
  name: string
  entity_type: EntityType
  short_summary?: string | null
  image_url?: string | null
  meaning_status?: MeaningStatus | null
  rights_record_id?: string | null
  generation_policy_id?: string | null
  policy_type?: GenerationPolicy | null
  /** 是否允许进入 AI 生成流程 */
  generatable: boolean
}

export interface CocreationValidation {
  valid: boolean
  blocked_element_ids: string[]
  warning_codes: string[]
  required_attributions: string[]
}

export interface GenerationResult {
  asset_id: string
  generation_id: string
  image_url?: string | null
  /** 固定标签，不可省略 */
  label: string
  is_fallback_sample: boolean
  used_element_ids: string[]
  ai_added_note: string
  source_ids: string[]
  model_name?: string
  model_version?: string
  prompt_template_version?: string
  generated_at?: string
}

/* ---------------- 系统状态 ---------------- */

export interface HealthStatus {
  status: 'ok' | 'degraded'
  postgres: boolean
  neo4j: boolean
  llm: {
    configured: boolean
    provider: string
    model?: string
    /** 未配置 Key 时为 true —— 界面需显示「演示保障模式」 */
    demo_mode: boolean
  }
  embedding: { provider: string; configured: boolean }
  counts?: Record<string, number>
}
