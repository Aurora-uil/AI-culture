import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  askQuestion,
  createChatSession,
  getCharacters,
  getRecommendedQuestions,
  regenerateMessage,
} from '@/api/endpoints'
import { describeError } from '@/api/client'
import { useExplorationStore } from './exploration'
import type {
  AnswerMode,
  AnswerStatus,
  Character,
  ChatMessage,
  RecommendedQuestion,
  ResponseTier,
} from '@/types'

let seq = 0
const uid = (p: string) => `${p}_${Date.now().toString(36)}_${(seq++).toString(36)}`

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

  const sessionId = ref<string | null>(null)
  const character = ref<Character | null>(null)
  const chaptersCharacters = ref<Character[]>([])

  const messages = ref<ChatMessage[]>([])
  const recommended = ref<RecommendedQuestion[]>([])

  const answerMode = ref<AnswerMode>('narrative')
  const status = ref<AnswerStatus>('IDLE')
  const currentEntityId = ref<string | null>(null)
  const streaming = ref(false)

  let controller: AbortController | null = null

  const isBusy = computed(
    () => streaming.value || ['RETRIEVING', 'GENERATING', 'VALIDATING'].includes(status.value),
  )

  /** 界面状态文案（设计系统 §32）—— 不暴露内部推理 */
  const statusText = computed(() => {
    switch (status.value) {
      case 'RETRIEVING':
        return '正在查找史料……'
      case 'GENERATING':
        return '正在组织回答……'
      case 'VALIDATING':
        return '正在核验引用……'
      default:
        return ''
    }
  })

  async function init(chapterId: string, characterId: string, entityId?: string) {
    currentEntityId.value = entityId ?? null
    try {
      chaptersCharacters.value = await getCharacters(chapterId)
      character.value =
        chaptersCharacters.value.find((c) => c.id === characterId) ??
        chaptersCharacters.value[0] ??
        null
    } catch {
      character.value = null
    }

    try {
      recommended.value = await getRecommendedQuestions(chapterId, characterId)
    } catch {
      recommended.value = []
    }

    if (!sessionId.value) {
      try {
        const res = await createChatSession(chapterId, characterId)
        sessionId.value = res.session_id
      } catch {
        sessionId.value = null
      }
    }
  }

  async function ask(question: string, chapterId: string) {
    const q = question.trim()
    if (!q || isBusy.value) return

    messages.value.push({
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
      answer_mode: answerMode.value,
      status: 'RETRIEVING',
      created_at: new Date().toISOString(),
    }
    messages.value.push(assistant)

    status.value = 'RETRIEVING'
    streaming.value = true
    controller = new AbortController()

    const patch = (p: Partial<ChatMessage>) => {
      const i = messages.value.findIndex((m) => m.id === assistantId)
      if (i >= 0) messages.value[i] = { ...messages.value[i], ...p }
    }

    try {
      await askQuestion(
        {
          session_id: sessionId.value ?? 'local',
          question: q,
          answer_mode: answerMode.value,
          current_entity_id: currentEntityId.value ?? undefined,
        },
        {
          onStatus: (s) => {
            const mapped = s.toUpperCase() as AnswerStatus
            status.value = mapped
            patch({ status: mapped })
          },
          onToken: (text) => {
            const i = messages.value.findIndex((m) => m.id === assistantId)
            if (i >= 0) {
              messages.value[i].content += text
              messages.value[i].status = 'DONE'
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
              content: data.answer_markdown || messages.value.find((m) => m.id === assistantId)?.content || '',
            })
            status.value = (data.status as AnswerStatus) ?? 'DONE'
          },
          onError: () => {
            patch({
              status: 'MODEL_TIMEOUT',
              content: 'AI讲述暂时没有完成。你可以重试，或先查看相关史料。',
            })
            status.value = 'MODEL_TIMEOUT'
          },
        },
        controller.signal,
      )

      exploration.track('CHAT_ASK', { entity_id: currentEntityId.value ?? undefined }, chapterId)
    } catch (err) {
      patch({
        status: 'NETWORK_ERROR',
        content: describeError(err),
      })
      status.value = 'NETWORK_ERROR'
    } finally {
      streaming.value = false
      controller?.abort()
      controller = null
    }
  }

  function stop() {
    controller?.abort()
    controller = null
    streaming.value = false
    status.value = 'DONE'
  }

  async function regenerate(messageId: string) {
    const idx = messages.value.findIndex((m) => m.id === messageId)
    if (idx < 1) return
    const question = messages.value[idx - 1]?.content
    if (!question) return
    messages.value.splice(idx, 1)
    messages.value.splice(idx - 1, 1)
    await ask(question, exploration.currentChapterId ?? '')
  }

  function clear() {
    messages.value = []
    sessionId.value = null
    status.value = 'IDLE'
  }

  function setMode(mode: AnswerMode) {
    answerMode.value = mode
  }

  return {
    sessionId,
    character,
    chaptersCharacters,
    messages,
    recommended,
    answerMode,
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
    setMode,
  }
})
