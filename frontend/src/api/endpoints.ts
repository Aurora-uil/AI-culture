import { http, probeApiHealth } from './client'
import type {
  Chapter,
  Character,
  CocreationElement,
  CocreationValidation,
  ComparisonGroup,
  Entity,
  EstimateGroup,
  EvidenceItem,
  ExplorationProgress,
  ExplorationSummary,
  ExplorationEventType,
  GenerationResult,
  HealthStatus,
  HistoricalMap,
  RecommendedQuestion,
  RelationEvidence,
  Scene,
  Source,
  SubGraph,
  TimelineEvent,
} from '@/types'

/* ---------------- 系统 ---------------- */

export const getHealth = () => probeApiHealth(true) as Promise<HealthStatus>

/* ---------------- 章节与内容 ---------------- */

export const getChapters = () => http.get<Chapter[]>('/chapters').then((r) => r.data)

export const getChapter = (id: string) => http.get<Chapter>(`/chapters/${id}`).then((r) => r.data)

export const getNarration = (id: string) =>
  http.get<{ narration: string }>(`/chapters/${id}/narration`).then((r) => r.data)

export const getRecommendedQuestions = (id: string, characterId?: string) =>
  http
    .get<RecommendedQuestion[]>(`/chapters/${id}/recommended-questions`, {
      params: characterId ? { character_id: characterId } : undefined,
    })
    .then((r) => r.data)

export const getCharacters = (chapterId?: string) =>
  http
    .get<Character[]>('/characters', { params: chapterId ? { chapter_id: chapterId } : undefined })
    .then((r) => r.data)

/* ---------------- 实体 ---------------- */

export const getEntity = (id: string) => http.get<Entity>(`/entities/${id}`).then((r) => r.data)

export const getEntities = (params?: { chapter_id?: string; entity_type?: string }) =>
  http.get<Entity[]>('/entities', { params }).then((r) => r.data)

export const getEntitySources = (id: string) =>
  http.get<{ entity_id: string; sources: Source[] }>(`/entities/${id}/sources`).then((r) => r.data)

export const getEntityRelations = (id: string) =>
  http.get<SubGraph>(`/entities/${id}/relations`).then((r) => r.data)

/* ---------------- 场景 / 地图 / 时间轴 ---------------- */

export const getScene = (sceneId: string) => http.get<Scene>(`/scenes/${sceneId}`).then((r) => r.data)

export const getChapterScene = (chapterId: string) =>
  http.get<Scene>(`/chapters/${chapterId}/scene`).then((r) => r.data)

export const getMap = (mapId: string) =>
  http.get<HistoricalMap>(`/map/${mapId}`).then((r) => r.data)

export const getTimeline = (chapterId: string) =>
  http.get<TimelineEvent[]>(`/timeline/${chapterId}`).then((r) => r.data)

export const getEstimates = (chapterId: string, metric?: string) =>
  http
    .get<EstimateGroup[]>(`/chapters/${chapterId}/estimates`, {
      params: metric ? { metric } : undefined,
    })
    .then((r) => r.data)

export const getComparison = (chapterId: string) =>
  http
    .get<{ groups: ComparisonGroup[]; items: EvidenceItem[] }>(`/chapters/${chapterId}/comparison`)
    .then((r) => r.data)

export const getFlowItems = (chapterId: string) =>
  http.get<any[]>(`/chapters/${chapterId}/flow-items`).then((r) => r.data)

/* ---------------- 图谱 ---------------- */

export const getSubGraph = (params: {
  center_entity_id: string
  depth?: number
  limit?: number
  types?: string
}) => http.get<SubGraph>('/graph/subgraph', { params }).then((r) => r.data)

export const getRelationEvidence = (relationId: string) =>
  http.get<RelationEvidence>(`/graph/relations/${relationId}/evidence`).then((r) => r.data)

export const getGraphOverview = () => http.get<SubGraph>('/graph/overview').then((r) => r.data)

/* ---------------- AI 对话 ---------------- */

export const createChatSession = (chapterId: string, characterId: string) =>
  http
    .post<{ session_id: string; created_at: string }>('/chat/sessions', {
      chapter_id: chapterId,
      character_id: characterId,
    })
    .then((r) => r.data)

export interface AskPayload {
  session_id: string
  question: string
  current_entity_id?: string
}

/**
 * 提问。后端采用「先校验后流式」：先完成检索→生成→核验，
 * 通过后再以 SSE 吐字，避免说出未经验证的内容。
 */
export async function askQuestion(
  payload: AskPayload,
  handlers: {
    onStatus?: (status: string) => void
    onToken?: (text: string) => void
    onFinal?: (data: any) => void
    onError?: (err: unknown) => void
  },
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${'/api/v1'}/chat/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(payload),
    signal,
  })

  if (!res.ok || !res.body) {
    throw new Error(`chat request failed: ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  const flush = (raw: string) => {
    // SSE 帧以空行分隔
    const frames = raw.split('\n\n')
    const rest = frames.pop() ?? ''
    for (const frame of frames) {
      let event = 'message'
      let data = ''
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      if (!data) continue
      let parsed: any = data
      try {
        parsed = JSON.parse(data)
      } catch {
        /* 保留原始字符串 */
      }
      if (event === 'status') handlers.onStatus?.(parsed.status)
      else if (event === 'token') handlers.onToken?.(parsed.text ?? '')
      else if (event === 'final') handlers.onFinal?.(parsed)
      else if (event === 'error') handlers.onError?.(parsed)
    }
    return rest
  }

  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      buffer = flush(buffer)
    }
    if (buffer.trim()) flush(buffer + '\n\n')
  } catch (err) {
    if ((err as any)?.name === 'AbortError') return
    handlers.onError?.(err)
    throw err
  }
}

export const submitFeedback = (
  messageId: string,
  payload: { kind: string; note?: string },
) => http.post(`/chat/messages/${messageId}/feedback`, payload).then((r) => r.data)

/* ---------------- 探索 ---------------- */

export const createExplorationSession = (chapterId: string, anonymousUserId?: string) =>
  http
    .post<{ session_id: string; chapter_id: string }>('/exploration/sessions', {
      chapter_id: chapterId,
      anonymous_user_id: anonymousUserId,
    })
    .then((r) => r.data)

/** 进度上报失败不能阻断内容浏览 —— 调用方一律 catch 后忽略 */
export const postExplorationEvent = (
  payload: {
    chapter_id: string
    event_type: ExplorationEventType
    entity_id?: string
    relation_id?: string
    source_id?: string
    metadata?: Record<string, any>
  },
  sessionId?: string,
) =>
  http
    .post('/exploration/events', { session_id: sessionId, ...payload })
    .then((r) => r.data)
    .catch(() => null)

export const getProgress = (chapterId?: string) =>
  http
    .get<ExplorationProgress>('/exploration/progress', {
      params: chapterId ? { chapter_id: chapterId } : undefined,
    })
    .then((r) => r.data)

export const generateSummary = (chapterId: string, sessionId?: string) =>
  http
    .post<ExplorationSummary>('/exploration/summary', {
      chapter_id: chapterId,
      session_id: sessionId,
    })
    .then((r) => r.data)

/* ---------------- AI 共创（当代） ---------------- */

export const validateCocreation = (payload: {
  element_ids: string[]
  technique_reference_ids?: string[]
  application_type?: string
  composition_option?: string
}) => http.post<CocreationValidation>('/cocreation/validate', payload).then((r) => r.data)

export const createGenerationJob = (payload: {
  exploration_session_id?: string
  element_ids: string[]
  technique_reference_ids?: string[]
  application_type: string
  composition_option: string
  color_option?: string
  user_text?: string
}) => http.post<GenerationResult>('/cocreation/jobs', payload).then((r) => r.data)

export const getProvenance = (assetId: string) =>
  http.get<any>(`/cocreation/provenance/${assetId}`).then((r) => r.data)

export const getCocreationElements = (chapterId: string) =>
  http.get<CocreationElement[]>(`/chapters/${chapterId}/cocreation-elements`).then((r) => r.data)
