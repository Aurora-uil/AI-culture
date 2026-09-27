import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getRelationEvidence, getSubGraph } from '@/api/endpoints'
import { useExplorationStore } from './exploration'
import type { GraphEdge, GraphNode, RelationEvidence, SubGraph } from '@/types'

/** 图谱可视上限（设计系统 §41 / 各章 §18.5） */
export const MAX_VISIBLE_NODES = 35
export const MAX_EXPAND_PER_CLICK = 12

/**
 * 关系图谱。
 *
 * 产品目标是让用户「从一件事物继续发现联系」，不是炫图：
 *  - 默认只显示中心 + 1-hop，不一次铺开整库；
 *  - 单次展开最多新增 12 个节点；
 *  - 每一条边都可追溯来源（「为什么有这条关系？」）。
 */
export const useGraphStore = defineStore('graph', () => {
  const exploration = useExplorationStore()

  const nodes = ref<GraphNode[]>([])
  const edges = ref<GraphEdge[]>([])
  const centerId = ref<string | null>(null)
  const selectedNodeId = ref<string | null>(null)
  const loading = ref(false)
  const truncated = ref(false)
  const message = ref<string | null>(null)

  const evidence = ref<RelationEvidence | null>(null)
  const evidenceLoading = ref(false)

  const typeFilter = ref<Set<string>>(new Set())
  const onlyMine = ref(false)

  /** 演示模式下固定布局，不使用随机坐标（设计系统 §69） */
  const visibleNodes = computed(() => {
    let list = nodes.value
    if (typeFilter.value.size) {
      list = list.filter((n) => typeFilter.value.has(n.type))
    }
    if (onlyMine.value) {
      list = list.filter((n) => n.explored)
    }
    return list
  })

  const visibleNodeIds = computed(() => new Set(visibleNodes.value.map((n) => n.id)))

  const visibleEdges = computed(() =>
    edges.value.filter(
      (e) => visibleNodeIds.value.has(e.source) && visibleNodeIds.value.has(e.target),
    ),
  )

  function merge(sub: SubGraph, replace = false) {
    if (replace) {
      nodes.value = sub.nodes.map((n) => ({ ...n, is_center: n.id === sub.center_entity_id }))
      edges.value = [...sub.edges]
    } else {
      const have = new Set(nodes.value.map((n) => n.id))
      for (const n of sub.nodes) {
        if (!have.has(n.id)) nodes.value.push({ ...n, is_center: n.id === sub.center_entity_id })
      }
      const haveEdge = new Set(edges.value.map((e) => e.id))
      for (const e of sub.edges) if (!haveEdge.has(e.id)) edges.value.push(e)
    }
    truncated.value = !!sub.truncated
    message.value = sub.message ?? null
  }

  async function load(centerEntityId: string, chapterId?: string, depth = 1, replace = true) {
    loading.value = true
    centerId.value = centerEntityId
    try {
      const sub = await getSubGraph({
        center_entity_id: centerEntityId,
        depth,
        limit: MAX_VISIBLE_NODES,
      })
      merge(sub, replace)
      if (replace) selectedNodeId.value = centerEntityId
      exploration.track('GRAPH_OPEN', { entity_id: centerEntityId }, chapterId)
      return sub
    } finally {
      loading.value = false
    }
  }

  /** §18.4 BTN-Y07-06「展开一层」—— 单次最多新增 12 个节点 */
  async function expand(nodeId: string, chapterId?: string) {
    if (nodes.value.length >= MAX_VISIBLE_NODES) {
      message.value = '当前关系较多，请筛选节点类型后继续探索。'
      truncated.value = true
      return
    }
    loading.value = true
    try {
      const sub = await getSubGraph({
        center_entity_id: nodeId,
        depth: 1,
        limit: MAX_EXPAND_PER_CLICK,
      })
      merge(sub, false)
      exploration.track('GRAPH_NODE_EXPAND', { entity_id: nodeId }, chapterId)
    } finally {
      loading.value = false
    }
  }

  async function loadEvidence(relationId: string, chapterId?: string) {
    evidenceLoading.value = true
    try {
      evidence.value = await getRelationEvidence(relationId)
      exploration.track('RELATION_EVIDENCE_VIEW', { relation_id: relationId }, chapterId)
    } catch {
      evidence.value = null
    } finally {
      evidenceLoading.value = false
    }
  }

  function selectNode(id: string | null) {
    selectedNodeId.value = id
  }

  function reset(centerEntityId?: string) {
    nodes.value = []
    edges.value = []
    evidence.value = null
    selectedNodeId.value = null
    truncated.value = false
    message.value = null
    typeFilter.value = new Set()
    onlyMine.value = false
    if (centerEntityId) void load(centerEntityId, undefined, 1, true)
  }

  return {
    nodes,
    edges,
    centerId,
    selectedNodeId,
    loading,
    truncated,
    message,
    evidence,
    evidenceLoading,
    typeFilter,
    onlyMine,
    visibleNodes,
    visibleEdges,
    load,
    expand,
    loadEvidence,
    selectNode,
    reset,
  }
})
