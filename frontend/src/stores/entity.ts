import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getEntity, getEntitySources } from '@/api/endpoints'
import { postExplorationEvent } from '@/api/endpoints'
import type { Entity, Source } from '@/types'

const FALLBACK_ENTITY_NAMES: Record<string, { name: string; type: Entity['entity_type']; summary: string }> = {
  artifact_yuntai: { name: '居庸关云台', type: 'HeritageStructure', summary: '券洞内保存有多种书写系统题刻，是理解元代宗教、文字与人群往来的重要遗存。' },
  script_sanskrit_lantsa: { name: '梵文书写系统', type: 'Script', summary: '云台题刻所见书写系统之一。界面只呈现已审核的名称、位置与相关背景。' },
  script_tibetan: { name: '藏文', type: 'Script', summary: '云台题刻所见书写系统之一。文字、语言与人群不能在界面中简单一一对应。' },
  script_phagspa: { name: '八思巴文', type: 'Script', summary: '云台题刻所见书写系统之一，需结合具体文本、位置与历史材料理解。' },
  script_old_uyghur: { name: '回鹘文', type: 'Script', summary: '云台题刻所见书写系统之一，本演示不进行未经审核的自动释读。' },
  script_chinese: { name: '汉文', type: 'Script', summary: '云台题刻所见书写系统之一，与其他题刻共同处于同一建筑空间。' },
  script_tangut: { name: '西夏文', type: 'Script', summary: '云台题刻所见书写系统之一，其出现不等于对具体人群身份作简单判断。' },
  concept_buddhist_stone_carving: { name: '券洞石雕', type: 'Concept', summary: '券洞空间中的石雕内容，与文字题刻共同构成建筑遗存。' },
}

function fallbackEntity(id: string): Entity {
  const fallback = FALLBACK_ENTITY_NAMES[id]
  return {
    id,
    entity_type: fallback?.type ?? 'Concept',
    name: fallback?.name ?? id.replaceAll('_', ' '),
    display_name: fallback?.name ?? id.replaceAll('_', ' '),
    short_summary: fallback?.summary ?? '该条目的完整资料需要连接内容服务后查看。',
    verification_label: id.startsWith('script_') ? 'historical_fact' : 'curatorial',
    review_status: 'review',
    extra: { offline_fallback: true },
  }
}

/**
 * 实体详情抽屉 + 史料来源抽屉（设计系统 §27 / §35 / §54 双 Drawer）
 *
 * 关闭来源后回到实体，是产品要求的行为（§85 返回逻辑）。
 */
export const useEntityStore = defineStore('entity', () => {
  const cache = ref<Record<string, Entity>>({})

  const current = ref<Entity | null>(null)
  const drawerOpen = ref(false)
  const loading = ref(false)

  const sources = ref<Source[]>([])
  const sourcesLoading = ref(false)
  const sourceDrawerOpen = ref(false)

  async function load(id: string, chapterId?: string, context?: Record<string, any>) {
    loading.value = true
    drawerOpen.value = true
    try {
      let entity = cache.value[id]
      if (!entity) {
        if (FALLBACK_ENTITY_NAMES[id]) {
          // 比赛现场与纯前端预览必须即时响应：先展示审核过的内置摘要，
          // 再在后台尝试用内容服务的完整数据替换，不等待 30 秒网络超时。
          entity = fallbackEntity(id)
          void getEntity(id)
            .then((remote) => {
              cache.value[id] = remote
              if (current.value?.id === id) current.value = remote
            })
            .catch(() => undefined)
        } else {
          try {
            entity = await getEntity(id)
          } catch {
            entity = fallbackEntity(id)
          }
        }
        cache.value[id] = entity
      }
      current.value = entity
      // 进度上报失败不能阻断内容浏览
      if (chapterId) {
        void postExplorationEvent({
          chapter_id: chapterId,
          event_type: 'ENTITY_VIEW',
          entity_id: id,
          metadata: context,
        })
      }
      return entity
    } finally {
      loading.value = false
    }
  }

  /** §10.3 BTN-Y04-05「下一个文字 →」按预设顺序切换 */
  async function loadByEntity(entity: Entity) {
    current.value = entity
    cache.value[entity.id] = entity
  }

  async function openSources(id: string, chapterId?: string) {
    sourceDrawerOpen.value = true
    sourcesLoading.value = true
    try {
      const res = await getEntitySources(id)
      sources.value = res.sources
      if (chapterId) {
        void postExplorationEvent({
          chapter_id: chapterId,
          event_type: 'SOURCE_VIEW',
          entity_id: id,
        })
      }
      return res.sources
    } catch {
      sources.value = []
      return []
    } finally {
      sourcesLoading.value = false
    }
  }

  function closeSources() {
    sourceDrawerOpen.value = false
    sources.value = []
  }

  function close() {
    drawerOpen.value = false
    current.value = null
    closeSources()
  }

  return {
    cache,
    current,
    drawerOpen,
    loading,
    sources,
    sourcesLoading,
    sourceDrawerOpen,
    load,
    loadByEntity,
    openSources,
    closeSources,
    close,
  }
})
