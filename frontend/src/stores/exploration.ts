import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  createExplorationSession,
  generateSummary,
  getProgress,
  postExplorationEvent,
} from '@/api/endpoints'
import { useSessionStore } from './session'
import type { ExplorationEventType, ExplorationProgress, ExplorationSummary } from '@/types'

/**
 * 探索进度与文化足迹。
 *
 * 原则（各章规格一致）：
 *  - 本地先乐观更新，后台异步持久化；
 *  - 进度上报失败绝不阻断内容浏览；
 *  - 不做游戏经验值、不做积分（设计系统 §15）。
 */
export const useExplorationStore = defineStore('exploration', () => {
  const session = useSessionStore()

  const currentChapterId = ref<string | null>(null)
  const progress = ref<ExplorationProgress | null>(null)
  const summary = ref<ExplorationSummary | null>(null)
  const summaryLoading = ref(false)

  /** 本地乐观记录，避免每次都等网络 */
  const localVisited = ref<Set<string>>(new Set())
  const localAnswered = ref(0)
  const localGraphOpened = ref(false)
  const localRelationExpanded = ref(false)
  const localRelationEvidenceViewed = ref(false)

  const visitedCount = computed(() => localVisited.value.size)

  async function ensureSession(chapterId: string) {
    currentChapterId.value = chapterId
    if (session.sessionId) {
      try {
        progress.value = await getProgress(chapterId)
      } catch {
        /* 后端不可用时静默降级为本地进度 */
      }
      return session.sessionId
    }
    try {
      const res = await createExplorationSession(chapterId, session.anonymousUserId ?? undefined)
      session.setSession(res.session_id)
      return res.session_id
    } catch {
      return null
    }
  }

  /** 上报事件。失败静默 —— 绝不阻断浏览。 */
  function track(
    eventType: ExplorationEventType,
    payload: {
      entity_id?: string
      relation_id?: string
      source_id?: string
      metadata?: Record<string, any>
    } = {},
    chapterId?: string,
  ) {
    const cid = chapterId ?? currentChapterId.value
    if (!cid) return
    if (payload.entity_id) localVisited.value.add(payload.entity_id)
    if (eventType === 'CHAT_ASK') localAnswered.value += 1
    if (eventType === 'GRAPH_OPEN') localGraphOpened.value = true
    if (eventType === 'GRAPH_NODE_EXPAND') localRelationExpanded.value = true
    if (eventType === 'RELATION_EVIDENCE_VIEW') localRelationEvidenceViewed.value = true

    void postExplorationEvent(
      { chapter_id: cid, event_type: eventType, ...payload },
      session.sessionId ?? undefined,
    )
  }

  async function refresh(chapterId?: string) {
    const cid = chapterId ?? currentChapterId.value
    if (!cid) return
    try {
      progress.value = await getProgress(cid)
    } catch {
      /* ignore */
    }
  }

  async function buildSummary(chapterId: string) {
    if (summary.value) return summary.value
    summaryLoading.value = true
    try {
      summary.value = await generateSummary(chapterId, session.sessionId ?? undefined)
      return summary.value
    } catch {
      summary.value = {
        summary:
          '你本次主要浏览了本章的核心节点，并查看了与之相关的史料来源。可以换一个时代，继续看看这些内容之间还存在哪些联系。',
        next_entity_ids: [],
      }
      return summary.value
    } finally {
      summaryLoading.value = false
    }
  }

  function reset() {
    localVisited.value = new Set()
    localAnswered.value = 0
    localGraphOpened.value = false
    localRelationExpanded.value = false
    localRelationEvidenceViewed.value = false
    summary.value = null
  }

  return {
    currentChapterId,
    progress,
    summary,
    summaryLoading,
    localVisited,
    localAnswered,
    localGraphOpened,
    localRelationExpanded,
    localRelationEvidenceViewed,
    visitedCount,
    ensureSession,
    track,
    refresh,
    buildSummary,
    reset,
  }
})
