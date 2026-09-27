<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useGraphStore } from '@/stores/graph'
import { useChapterStore, CHAPTER_ACCENT } from '@/stores/chapter'
import type { ClaimType, EntityType, GraphEdge, GraphNode } from '@/types'

echarts.use([GraphChart, TooltipComponent, LegendComponent, CanvasRenderer])

/**
 * 文化关系图谱（设计系统 §38–§41）
 *
 * 默认只显示当前实体 + 1-hop，不一次铺开整库。
 *
 * 布局采用**确定性径向布局**而非力导向：
 *   力导向每次刷新位置都不同，比赛演示时会让评委觉得画面在乱跳。
 *   这里中心固定原点，一级关系均匀分布在圆周上，完全可复现。
 */
const props = withDefaults(
  defineProps<{
    /** 是否显示图例 */
    showLegend?: boolean
  }>(),
  { showLegend: true },
)

const emit = defineEmits<{
  (e: 'select', nodeId: string): void
  (e: 'dblclick', nodeId: string): void
}>()

const store = useGraphStore()
const chapterStore = useChapterStore()

/** 中心节点用章节色（设计系统 §39）。 */
const accentColor = computed(
  () => (chapterStore.slug ? CHAPTER_ACCENT[chapterStore.slug] : '#B24A3A'),
)

const el = ref<HTMLElement | null>(null)
const chart = shallowRef<echarts.ECharts | null>(null)
const hoveredEdge = ref<GraphEdge | null>(null)

/** 节点类型 → 视觉（设计系统 §39） */
const TYPE_STYLE: Record<string, { color: string; label: string; size: number }> = {
  Person: { color: '#153D5B', label: '人物', size: 30 },
  Artifact: { color: '#B9894D', label: '文物/遗产', size: 30 },
  Artwork: { color: '#B9894D', label: '文物/遗产', size: 30 },
  HeritageStructure: { color: '#B9894D', label: '文物/遗产', size: 34 },
  InscriptionSet: { color: '#B9894D', label: '文物/遗产', size: 30 },
  Text: { color: '#B9894D', label: '文献', size: 26 },
  Place: { color: '#69737E', label: '地点', size: 26 },
  Region: { color: '#69737E', label: '地域', size: 26 },
  Site: { color: '#69737E', label: '地点', size: 26 },
  Event: { color: '#B24A3A', label: '事件', size: 30 },
  Script: { color: '#4E7A6A', label: '文字', size: 28 },
  Language: { color: '#4E7A6A', label: '语言', size: 26 },
  Technique: { color: '#4E7A6A', label: '技艺', size: 28 },
  Practice: { color: '#4E7A6A', label: '传承实践', size: 26 },
  ICHProject: { color: '#4E7A6A', label: '非遗项目', size: 34 },
  MotifCategory: { color: '#4E7A6A', label: '纹样题材', size: 26 },
  PatternElement: { color: '#4E7A6A', label: '纹样元素', size: 26 },
  ObjectType: { color: '#4E7A6A', label: '绣品', size: 26 },
  Group: { color: '#153D5B', label: '群体', size: 28 },
  Institution: { color: '#153D5B', label: '机构', size: 26 },
  Period: { color: '#69737E', label: '时期', size: 26 },
  Concept: { color: '#8A8578', label: '概念', size: 24 },
  AttributionClaim: { color: '#8A8578', label: '归属问题', size: 24 },
}

function styleOf(type: EntityType | string) {
  return TYPE_STYLE[type] ?? { color: '#8A8578', label: '概念', size: 24 }
}

/**
 * 确定性径向布局：
 *   中心节点在原点，一级节点按角度均匀分布。
 *   同一批节点每次渲染位置完全一致（设计系统 §69 要求图谱固定初始坐标）。
 */
function layout(nodes: GraphNode[], edges: GraphEdge[]) {
  const centerId = store.centerId
  const center = nodes.find((n) => n.id === centerId)

  const adjacency = new Map<string, Set<string>>()
  for (const e of edges) {
    if (!adjacency.has(e.source)) adjacency.set(e.source, new Set())
    if (!adjacency.has(e.target)) adjacency.set(e.target, new Set())
    adjacency.get(e.source)!.add(e.target)
    adjacency.get(e.target)!.add(e.source)
  }

  const ring1 = center ? [...(adjacency.get(center.id) ?? [])] : []
  const ring1Set = new Set(ring1)
  // 注意：这里要的是 **id 列表**，不是节点对象列表 —— 后面的 out.set(id, ...) 依赖它
  const rest = nodes
    .filter((n) => n.id !== centerId && !ring1Set.has(n.id))
    .map((n) => n.id)

  const out = new Map<string, { x: number; y: number }>()
  if (center) out.set(center.id, { x: 0, y: 0 })

  // 一级：半径 240，按 id 稳定排序后均匀分布
  const sorted1 = [...ring1].sort()
  sorted1.forEach((id, i) => {
    const angle = (i / Math.max(1, sorted1.length)) * Math.PI * 2 - Math.PI / 2
    out.set(id, { x: Math.cos(angle) * 240, y: Math.sin(angle) * 240 })
  })

  // 其余：半径 440，均匀分布
  const sorted2 = [...rest].sort()
  sorted2.forEach((id, i) => {
    const angle = (i / Math.max(1, sorted2.length)) * Math.PI * 2 - Math.PI / 2 + 0.22
    out.set(id, { x: Math.cos(angle) * 440, y: Math.sin(angle) * 440 })
  })

  return out
}

/** 边的线型（设计系统 §40） */
function edgeStyle(claimType: ClaimType) {
  switch (claimType) {
    case 'interpretation':
      return { type: 'dashed' as const, width: 1.5, opacity: 0.72 }
    case 'curatorial':
      return { type: [4, 3, 1, 3] as unknown as 'dashed', width: 1, opacity: 0.58 }
    case 'catalogue_fact':
      return { type: 'dotted' as const, width: 1.4, opacity: 0.7 }
    default:
      return { type: 'solid' as const, width: 1.5, opacity: 0.82 }
  }
}

function buildOption() {
  const nodes = store.visibleNodes
  const edges = store.visibleEdges
  const pos = layout(nodes, edges)
  // 注意：不能读 document.documentElement 上的 --chapter-accent ——
  // data-chapter 是挂在 .app-root 上的，:root 拿到的是默认朱砂色，
  // 会让每个章节的中心节点都变成同一种颜色。
  const accent = accentColor.value

  return {
    backgroundColor: 'transparent',
    animationDuration: 420,
    animationEasing: 'cubicOut' as const,
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(250,248,242,.97)',
      borderColor: 'rgba(65,55,42,.14)',
      borderWidth: 1,
      padding: [10, 12],
      textStyle: { color: '#1F252B', fontSize: 13, lineHeight: 20 },
      extraCssText: 'border-radius:12px;box-shadow:0 8px 28px rgba(39,34,27,.10);',
      formatter: (p: any) => {
        if (p.dataType === 'edge') {
          const e: GraphEdge = p.data.raw
          const relLabel =
            e.claim_type === 'fact'
              ? '史实'
              : e.claim_type === 'interpretation'
                ? '研究解释'
                : e.claim_type === 'curatorial'
                  ? '策展关联'
                  : '目录记录'
          const hasSource = (e.source_ids?.length ?? 0) > 0
          return `
            <div style="font-weight:600;margin-bottom:4px">${e.display_label}</div>
            <div style="color:#69737E;font-size:12px">关系类型：${relLabel}</div>
            <div style="color:${hasSource ? '#3F785A' : '#A96A28'};font-size:12px">
              ${hasSource ? '有来源支持' : '暂无来源'}
            </div>`
        }
        const d = p.data
        return `
          <div style="font-weight:600;margin-bottom:2px">${d.name}</div>
          <div style="color:#69737E;font-size:12px">${styleOf(d.nodeType).label}</div>
          ${d.summary ? `<div style="margin-top:6px;max-width:240px;font-size:12px;line-height:1.6;color:#39424C">${d.summary}</div>` : ''}
          <div style="margin-top:6px;color:${d.explored ? '#3F785A' : '#69737E'};font-size:12px">
            ${d.explored ? '已探索' : '尚未探索'}
          </div>`
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'none',
        roam: true,
        draggable: true,
        scaleLimit: { min: 0.4, max: 3 },
        // 固定坐标，不使用随机布局
        data: nodes.map((n) => {
          const st = styleOf(n.type)
          const p = pos.get(n.id) ?? { x: 0, y: 0 }
          const isCenter = n.id === store.centerId
          return {
            id: n.id,
            name: n.name,
            x: p.x,
            y: p.y,
            nodeType: n.type,
            summary: n.short_summary,
            explored: n.explored,
            symbolSize: isCenter ? st.size * 1.35 : st.size,
            itemStyle: {
              color: isCenter ? accent || st.color : st.color,
              opacity: n.explored ? 1 : 0.45,
              borderColor: n.explored ? 'rgba(255,255,255,.9)' : 'rgba(255,255,255,.5)',
              borderWidth: isCenter ? 3 : 1.5,
              shadowBlur: isCenter ? 18 : 0,
              shadowColor: isCenter ? 'rgba(39,34,27,.22)' : 'transparent',
            },
            label: {
              show: true,
              position: 'bottom',
              distance: 6,
              fontSize: isCenter ? 13 : 11.5,
              color: n.explored ? '#1F252B' : '#69737E',
              fontWeight: isCenter ? 600 : 400,
              formatter: '{b}',
            },
          }
        }),
        links: edges
          .filter((e) => pos.has(e.source) && pos.has(e.target))
          .map((e) => {
            const st = edgeStyle(e.claim_type)
            return {
              source: e.source,
              target: e.target,
              raw: e,
              lineStyle: {
                color: '#69737E',
                width: st.width,
                type: st.type,
                opacity: st.opacity,
                curveness: 0.08,
              },
            }
          }),
        emphasis: {
          focus: 'adjacency',
          scale: false,
          lineStyle: { width: 2.5, opacity: 1 },
          label: { fontSize: 13, fontWeight: 600 },
        },
        edgeSymbol: ['none', 'none'],
        edgeLabel: { show: false },
      },
    ],
  }
}

function render() {
  if (!chart.value) return
  chart.value.setOption(buildOption(), true)
}

function resize() {
  chart.value?.resize()
}

/** 容器尺寸变化时重新测量。ECharts 只在 init 时量一次容器尺寸，
 *  而图谱页的布局是异步撑开的，不主动 resize 会得到一块很小的画布。 */
let observer: ResizeObserver | null = null

onMounted(() => {
  if (!el.value) return
  chart.value = echarts.init(el.value, undefined, { renderer: 'canvas' })
  chart.value.on('click', (p: any) => {
    if (p.dataType === 'node') emit('select', p.data.id)
  })
  chart.value.on('dblclick', (p: any) => {
    if (p.dataType === 'node') emit('dblclick', p.data.id)
  })
  window.addEventListener('resize', resize)

  if (typeof ResizeObserver !== 'undefined' && el.value) {
    observer = new ResizeObserver(() => resize())
    observer.observe(el.value)
  }

  render()
  // 布局稳定后再量一次，避免首帧尺寸偏小
  requestAnimationFrame(() => resize())
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  observer?.disconnect()
  observer = null
  chart.value?.dispose()
  chart.value = null
})

watch(
  () => [store.visibleNodes, store.visibleEdges, store.centerId],
  () => render(),
  { deep: false },
)

defineExpose({ resize })
</script>

<template>
  <div class="kg">
    <div ref="el" class="kg__canvas" />

    <!-- 图例 -->
    <div v-if="showLegend" class="kg__legend">
      <div class="kg__legend-group">
        <span class="kg__legend-title">边类型</span>
        <span class="kg__legend-item"><i class="kg__line kg__line--fact" />史实</span>
        <span class="kg__legend-item"><i class="kg__line kg__line--interp" />研究解释</span>
        <span class="kg__legend-item"><i class="kg__line kg__line--curat" />策展关联</span>
      </div>
      <div class="kg__legend-group">
        <span class="kg__legend-title">状态</span>
        <span class="kg__legend-item"><i class="kg__dot kg__dot--on" />已探索</span>
        <span class="kg__legend-item"><i class="kg__dot kg__dot--off" />未探索</span>
      </div>
    </div>

    <p v-if="store.truncated || store.message" class="kg__notice">
      {{ store.message || '当前关系较多，请筛选节点类型后继续探索。' }}
    </p>
  </div>
</template>

<style scoped>
.kg {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  background:
    radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.85), transparent 62%),
    var(--color-paper-100);
  border-radius: var(--radius-card);
  overflow: hidden;
}

.kg__canvas {
  width: 100%;
  height: 100%;
}

.kg__legend {
  position: absolute;
  left: var(--sp-4);
  bottom: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-card);
  background: rgba(250, 248, 242, 0.9);
  border: 1px solid var(--color-border);
  backdrop-filter: blur(8px);
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
}
.kg__legend-group {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}
.kg__legend-title {
  color: var(--color-ink-500);
  min-width: 42px;
}
.kg__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.kg__line {
  width: 18px;
  height: 0;
  border-top-width: 1.5px;
  border-top-style: solid;
  border-color: #69737e;
}
.kg__line--interp {
  border-top-style: dashed;
}
.kg__line--curat {
  border-top-style: dotted;
}
.kg__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #153d5b;
}
.kg__dot--off {
  opacity: 0.45;
}

.kg__notice {
  position: absolute;
  right: var(--sp-4);
  top: var(--sp-4);
  max-width: 300px;
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-card);
  background: color-mix(in srgb, var(--color-warning) 12%, #fff);
  border: 1px solid color-mix(in srgb, var(--color-warning) 34%, transparent);
  color: var(--color-warning);
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
}
</style>
