import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getHealth } from '@/api/endpoints'
import { setExplorationSession } from '@/api/client'
import type { HealthStatus } from '@/types'

const SESSION_KEY = 'tongxin.session_id'
const ANON_KEY = 'tongxin.anon_id'

/**
 * 会话与系统状态。
 *
 * 匿名用户，不采集身份证 / 手机号 / 敏感个人信息（PRD §55）。
 * 演示模式由 URL 参数控制（设计系统 §68 / §69）：
 *   ?demo=true     演示保障模式：预热问题、固定图谱布局、AI 超时自动兜底
 *   ?present=true  大屏模式：放大字号、缩短过场、隐藏开发入口
 */
export const useSessionStore = defineStore('session', () => {
  const sessionId = ref<string | null>(null)
  const anonymousUserId = ref<string | null>(null)
  const health = ref<HealthStatus | null>(null)
  const healthChecked = ref(false)

  const isDemoMode = ref(false)
  const isPresentMode = ref(false)

  /** LLM 未配置 Key 时为 true —— 界面必须标注「演示保障模式」 */
  const demoFallback = computed(
    () => !!health.value && !health.value.llm.configured,
  )

  const backendReady = computed(() => !!health.value?.postgres && !!health.value?.neo4j)

  function bootstrap() {
    const params = new URLSearchParams(window.location.search)
    isDemoMode.value = params.get('demo') === 'true'
    isPresentMode.value = params.get('present') === 'true'

    if (isPresentMode.value) {
      document.documentElement.classList.add('present-mode')
    }

    sessionId.value = localStorage.getItem(SESSION_KEY)
    anonymousUserId.value = localStorage.getItem(ANON_KEY)
    if (!anonymousUserId.value) {
      anonymousUserId.value = `anon_${Math.random().toString(36).slice(2, 12)}`
      localStorage.setItem(ANON_KEY, anonymousUserId.value)
    }
    setExplorationSession(sessionId.value)

    void checkHealth()
  }

  function setSession(id: string) {
    sessionId.value = id
    setExplorationSession(id)
    localStorage.setItem(SESSION_KEY, id)
  }

  async function checkHealth() {
    try {
      health.value = await getHealth()
    } catch {
      health.value = null
    } finally {
      healthChecked.value = true
    }
  }

  return {
    sessionId,
    anonymousUserId,
    health,
    healthChecked,
    isDemoMode,
    isPresentMode,
    demoFallback,
    backendReady,
    bootstrap,
    setSession,
    checkHealth,
  }
})
