import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'
import {
  askQuestion,
  createChatSession,
  getCharacters,
  getRecommendedQuestions,
} from '@/api/endpoints'
import { describeError } from '@/api/client'
import { useExplorationStore } from './exploration'
import type {
  AnswerStatus,
  Character,
  ChatMessage,
  RecommendedQuestion,
  ResponseTier,
} from '@/types'

let seq = 0
const uid = (p: string) => `${p}_${Date.now().toString(36)}_${(seq++).toString(36)}`

interface ChapterChatState {
  sessionId: string | null
  character: Character | null
  chaptersCharacters: Character[]
  messages: ChatMessage[]
  recommended: RecommendedQuestion[]
  status: AnswerStatus
  currentEntityId: string | null
  streaming: boolean
}

function createChapterChatState(): ChapterChatState {
  return {
    sessionId: null,
    character: null,
    chaptersCharacters: [],
    messages: [],
    recommended: [],
    status: 'IDLE',
    currentEntityId: null,
    streaming: false,
  }
}

/**
 * AI 对话。
 *
 * 关键产品规则：
 *  1. 所有第一人称内容页面固定显示 AI 身份说明，不得省略。
 *  2. 回答必须标注来源层级（实时AI / 本地检索 / 演示保障），
 *     绝不把兜底回答伪装成实时 AI（各章 §13 / 设计系统 §33）。
 *  3. 无资料时明确承认资料不足，不生成虚构答案。
 */
export const useChatStore = defineStore('chat', () => {
  const exploration = useExplorationStore()

  const activeChapterId = ref<string | null>(null)
  const chapterStates = reactive<Record<string, ChapterChatState>>({})
  const idleState = reactive(createChapterChatState())
  const controllers = new Map<string, AbortController>()

  function stateFor(chapterId: string): ChapterChatState {
    if (!chapterStates[chapterId]) chapterStates[chapterId] = createChapterChatState()
    return chapterStates[chapterId]
  }

  const activeState = computed<ChapterChatState>(() => {
    const chapterId = activeChapterId.value
    return chapterId ? stateFor(chapterId) : idleState
  })

  const sessionId = computed({
    get: () => activeState.value.sessionId,
    set: (value: string | null) => { activeState.value.sessionId = value },
  })
  const character = computed({
    get: () => activeState.value.character,
    set: (value: Character | null) => { activeState.value.character = value },
  })
  const chaptersCharacters = computed({
    get: () => activeState.value.chaptersCharacters,
    set: (value: Character[]) => { activeState.value.chaptersCharacters = value },
  })
  const messages = computed({
    get: () => activeState.value.messages,
    set: (value: ChatMessage[]) => { activeState.value.messages = value },
  })
  const recommended = computed({
    get: () => activeState.value.recommended,
    set: (value: RecommendedQuestion[]) => { activeState.value.recommended = value },
  })
  const status = computed({
    get: () => activeState.value.status,
    set: (value: AnswerStatus) => { activeState.value.status = value },
  })
  const currentEntityId = computed({
    get: () => activeState.value.currentEntityId,
    set: (value: string | null) => { activeState.value.currentEntityId = value },
  })
  const streaming = computed({
    get: () => activeState.value.streaming,
    set: (value: boolean) => { activeState.value.streaming = value },
  })

  const isBusy = computed(
    () => streaming.value || ['RETRIEVING', 'GENERATING', 'VALIDATING'].includes(status.value),
  )

  /** 界面状态文案（设计系统 §32）—— 不暴露内部推理 */
  const statusText = computed(() => {
    switch (status.value) {
      case 'RETRIEVING':
        return '正在联网检索并查找史料……'
      case 'GENERATING':
        return '正在组织回答……'
      case 'VALIDATING':
        return '正在核验引用……'
      default:
        return ''
    }
  })

  async function init(chapterId: string, characterId: string, entityId?: string) {
    if (activeChapterId.value && activeChapterId.value !== chapterId) {
      stop(activeChapterId.value)
    }
    activeChapterId.value = chapterId
    const chapterState = stateFor(chapterId)
    chapterState.currentEntityId = entityId ?? null

    try {
      chapterState.chaptersCharacters = await getCharacters(chapterId)
      chapterState.character =
        chapterState.chaptersCharacters.find((c) => c.id === characterId) ??
        chapterState.chaptersCharacters[0] ??
        null
    } catch {
      chapterState.character = null
    }

    try {
      chapterState.recommended = await getRecommendedQuestions(chapterId, characterId)
    } catch {
      chapterState.recommended = []
    }

    if (!chapterState.sessionId) {
      try {
        const res = await createChatSession(chapterId, characterId)
        chapterState.sessionId = res.session_id
      } catch {
        chapterState.sessionId = null
      }
    }
  }

  async function ask(question: string, chapterId: string) {
    const q = question.trim()
    const chapterState = stateFor(chapterId)
    const chapterBusy =
      chapterState.streaming ||
      ['RETRIEVING', 'GENERATING', 'VALIDATING'].includes(chapterState.status)
    if (!q || chapterBusy) return

    chapterState.messages.push({
      id: uid('msg'),
      role: 'user',
      content: q,
      status: 'DONE',
      created_at: new Date().toISOString(),
    })

    const assistantId = uid('msg')
    const assistant: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      status: 'RETRIEVING',
      created_at: new Date().toISOString(),
    }
    chapterState.messages.push(assistant)

    chapterState.status = 'RETRIEVING'
    chapterState.streaming = true
    const controller = new AbortController()
    controllers.set(chapterId, controller)

    const patch = (p: Partial<ChatMessage>) => {
      const i = chapterState.messages.findIndex((m) => m.id === assistantId)
      if (i >= 0) chapterState.messages[i] = { ...chapterState.messages[i], ...p }
    }

    try {
      await askQuestion(
        {
          session_id: chapterState.sessionId ?? 'local',
          question: q,
          current_entity_id: chapterState.currentEntityId ?? undefined,
        },
        {
          onStatus: (s) => {
            const mapped = s.toUpperCase() as AnswerStatus
            chapterState.status = mapped
            patch({ status: mapped })
          },
          onToken: (text) => {
            const i = chapterState.messages.findIndex((m) => m.id === assistantId)
            if (i >= 0) {
              chapterState.messages[i].content += text
              chapterState.messages[i].status = 'DONE'
            }
          },
          onFinal: (data) => {
            patch({
              id: data.message_id ?? assistantId,
              citations: data.citations ?? [],
              related_entities: data.related_entities ?? [],
              uncertainty: data.uncertainty ?? 'low',
              status: (data.status as AnswerStatus) ?? 'DONE',
              response_tier: (data.response_tier as ResponseTier) ?? 'live_rag',
              content:
                data.answer_markdown ||
                chapterState.messages.find((m) => m.id === assistantId)?.content ||
                '',
            })
            chapterState.status = (data.status as AnswerStatus) ?? 'DONE'
          },
          onError: () => {
            patch({
              status: 'MODEL_TIMEOUT',
              content: 'AI讲述暂时没有完成。你可以重试，或先查看相关史料。',
            })
            chapterState.status = 'MODEL_TIMEOUT'
          },
        },
        controller.signal,
      )

      exploration.track(
        'CHAT_ASK',
        { entity_id: chapterState.currentEntityId ?? undefined },
        chapterId,
      )
    } catch (err) {
      if (controller.signal.aborted) return
      patch({
        status: 'NETWORK_ERROR',
        content: describeError(err),
      })
      chapterState.status = 'NETWORK_ERROR'
    } finally {
      chapterState.streaming = false
      if (controllers.get(chapterId) === controller) controllers.delete(chapterId)
    }
  }

  function stop(chapterId = activeChapterId.value) {
    if (!chapterId) return
    controllers.get(chapterId)?.abort()
    controllers.delete(chapterId)
    const chapterState = stateFor(chapterId)
    chapterState.streaming = false
    chapterState.status = 'DONE'
  }

  async function regenerate(messageId: string) {
    const chapterId = activeChapterId.value
    if (!chapterId) return
    const chapterState = stateFor(chapterId)
    const idx = chapterState.messages.findIndex((m) => m.id === messageId)
    if (idx < 1) return
    const question = chapterState.messages[idx - 1]?.content
    if (!question) return
    chapterState.messages.splice(idx, 1)
    chapterState.messages.splice(idx - 1, 1)
    await ask(question, chapterId)
  }

  function clear(chapterId = activeChapterId.value) {
    if (!chapterId) return
    stop(chapterId)
    chapterStates[chapterId] = createChapterChatState()
  }

  return {
    sessionId,
    activeChapterId,
    character,
    chaptersCharacters,
    messages,
    recommended,
    status,
    statusText,
    streaming,
    isBusy,
    currentEntityId,
    init,
    ask,
    stop,
    regenerate,
    clear,
  }
})
