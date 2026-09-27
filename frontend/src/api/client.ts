import axios, { type AxiosInstance } from 'axios'

/**
 * 《同心千年》API 客户端
 *
 * 约定：
 *  - 所有接口以 /api/v1 为前缀（vite 已配置代理到 127.0.0.1:8000）
 *  - 探索 / 会话 ID 由 sessionStore 维护，通过请求头传递
 *  - 进度上报失败绝不阻断内容浏览（各章规格的硬性要求）
 */

export const API_BASE = '/api/v1'

type ApiAvailability = 'unknown' | 'online' | 'offline'

let apiAvailability: ApiAvailability = 'unknown'
let offlineSince = 0
let healthProbe: Promise<any> | null = null
const OFFLINE_RETRY_MS = 15_000

export class OfflineApiError extends Error {
  code = 'TONGXIN_API_OFFLINE'

  constructor() {
    super('内容服务当前不可用，已切换到内置演示内容。')
    this.name = 'OfflineApiError'
  }
}

/**
 * 所有接口共享一次健康探测。后端离线后进入短暂熔断，避免每个组件都向
 * Vite 代理重复发送必然失败的请求；到期或用户主动刷新状态时再尝试恢复。
 */
export async function probeApiHealth(force = false) {
  if (healthProbe) return healthProbe
  if (!force && apiAvailability === 'offline' && Date.now() - offlineSince < OFFLINE_RETRY_MS) {
    throw new OfflineApiError()
  }

  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 2500)
  healthProbe = fetch(`${API_BASE}/health`, {
    headers: { Accept: 'application/json' },
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) throw new OfflineApiError()
      const data = await response.json()
      apiAvailability = 'online'
      return data
    })
    .catch((error) => {
      apiAvailability = 'offline'
      offlineSince = Date.now()
      if (error instanceof OfflineApiError) throw error
      throw new OfflineApiError()
    })
    .finally(() => {
      window.clearTimeout(timeoutId)
      healthProbe = null
    })
  return healthProbe
}

export function getApiAvailability() {
  return apiAvailability
}

export const http: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

/** 会话 ID 由 store 注入，避免各调用点重复传参 */
let explorationSessionId: string | null = null

export function setExplorationSession(id: string | null) {
  explorationSessionId = id
}

export function getExplorationSession() {
  return explorationSessionId
}

http.interceptors.request.use((config) => {
  if (explorationSessionId) {
    config.headers['X-Exploration-Session'] = explorationSessionId
  }
  return config
})

http.interceptors.request.use(async (config) => {
  await probeApiHealth()
  return config
})

/** 统一的错误信息提取 —— 界面永远不显示英文堆栈 */
export function describeError(err: unknown): string {
  if (err instanceof OfflineApiError) return err.message
  if (axios.isAxiosError(err)) {
    if (err.code === 'ECONNABORTED') return '请求超时，请稍后重试。'
    if (!err.response) return '无法连接到服务。请确认后端已启动。'
    const detail = (err.response.data as any)?.detail
    if (typeof detail === 'string') return detail
    if (err.response.status === 404) return '这段内容暂时没有完成数字化整理。'
    if (err.response.status >= 500) return '服务暂时不可用，请稍后重试。'
  }
  return '出现了一个未预期的问题，请稍后重试。'
}
