<script setup lang="ts">
import { computed, ref } from 'vue'
import SceneViewer from '@/components/scene/SceneViewer.vue'
import SceneHotspot from '@/components/scene/SceneHotspot.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import type { Chapter, Hotspot, RouteCertainty, Scene } from '@/types'

/**
 * C02 汉代变体 · H02 丝路历史网络主场景（规格 §8 / §9，设计系统 §23.1 / §57）
 *
 * 内容红线（决定了本组件的三处关键设计）：
 *  1. 丝路不是张骞一个人创造的固定道路（规格 §2.3）。
 *     因此路线一律以「历史交通廊道示意」呈现，并且**在路线动画之前**先显示线路性质图例：
 *     动画越顺滑，越容易让观众以为这是一条绝对精确的路线（设计系统 §57）。
 *  2. 「张骞行程相关」与「长期交通网络」必须分开（规格 §9.1），
 *     否则用户会以为所有丝路节点都由张骞本人走过。
 *  3. 证据不足时宁可不给几何点，也不虚构精度 —— 不确定段用 `?` 单独标注。
 *
 * 数据来源优先级：
 *   ① `scene.hotspots`（后端 SceneOut 的真实预标注热点）
 *   ② `scene` 上若带有 `map`（HistoricalMap 形态的透传字段）则用其 nodes / segments
 *   ③ 两者都没有时，用组件内置的**示意节点**（entity_id 全部取自 content/han/entities.json），
 *      只允许触发 `select-entity`，不伪造 `select-hotspot` 热点记录。
 */

const props = defineProps<{
  chapter: Chapter
  scene: Scene | null
  hotspotStatus: Record<string, 'UNSEEN' | 'SEEN' | 'SELECTED'>
  lensOpen: boolean
  selectedEntityId: string | null
}>()

const emit = defineEmits<{
  (e: 'select-hotspot', hotspot: Hotspot): void
  (e: 'select-entity', entityId: string): void
  (e: 'open-chat', entityId?: string): void
  (e: 'open-graph', entityId?: string): void
}>()

/* ---------------------------------------------------------------- 基础工具 */

/** 画布逻辑坐标系。元素盒子用 aspect-ratio 锁成同一比例，因此
 *  SVG 用户坐标与热点百分比坐标是严格线性对应的，不会出现错位。 */
const VB_W = 1000
const VB_H = 560

/** SVG 内的 id 必须全局唯一，避免同页多次挂载时 mask 互相覆盖 */
const uid = Math.random().toString(36).slice(2, 9)

type LegendKey = RouteCertainty | 'confirmed_region'

/** 路线 / 节点性质图例。文案取规格 §8.2 的固定说法，不得换词。 */
const CERTAINTY_META: Record<LegendKey, { glyph: string; label: string; dash: string }> = {
  confirmed_region: { glyph: '●', label: '确认地点', dash: '' },
  confirmed_area: { glyph: '●', label: '确认地点', dash: '' },
  approximate_corridor: { glyph: '≈', label: '大体走向', dash: '12 8' },
  uncertain_segment: { glyph: '?', label: '路线存在不确定性', dash: '3 9' },
  curatorial_connector: { glyph: '┄', label: '策展关联', dash: '2 7' },
}

/* ---------------------------------------------------------------- 节点数据 */

interface NodeVM {
  key: string
  /** 真实热点。为 null 表示这是内置示意节点，不能上报热点事件 */
  hotspot: Hotspot | null
  entityId: string | null
  label: string
  x: number
  y: number
  certainty: LegendKey
  /** 是否与张骞行程直接相关（规格 §9.1 必须与长期网络分开） */
  zhangqian: boolean
}

/** 热点中心：point 形态直接用坐标，polygon 形态取质心 */
function centerOf(h: Hotspot): { x: number; y: number } {
  const pts = h.normalized_points
  if (!pts || !Array.isArray(pts) || pts.length === 0) return { x: 0.5, y: 0.5 }
  if (typeof pts[0] === 'number') {
    const flat = pts as number[]
    return { x: flat[0] ?? 0.5, y: flat[1] ?? 0.5 }
  }
  const arr = pts as number[][]
  const sx = arr.reduce((s, p) => s + (p[0] ?? 0), 0) / arr.length
  const sy = arr.reduce((s, p) => s + (p[1] ?? 0), 0) / arr.length
  return { x: sx, y: sy }
}

/** 整幅兜底热点（如 0–1 全覆盖）不作为地图节点，避免遮挡全部点击 */
function isWholeCanvas(h: Hotspot): boolean {
  const pts = h.normalized_points as number[][]
  if (!Array.isArray(pts) || !pts.length || typeof pts[0] === 'number') return false
  const xs = pts.map((p) => p[0])
  const ys = pts.map((p) => p[1])
  return Math.max(...xs) - Math.min(...xs) > 0.95 && Math.max(...ys) - Math.min(...ys) > 0.95
}

/**
 * 内置示意节点。entity_id 全部来自 content/han/entities.json，
 * 只是地图内容尚未接入时的占位，**不生成假热点**。
 * 张骞行程相关：长安—河西走廊—敦煌—西域—中亚；
 * 尼雅遗址不标为张骞行程相关（它是汉晋时期的遗址，不在张骞两次出使的路线上）。
 */
const FALLBACK_NODES: NodeVM[] = [
  { key: 'fb_changan', hotspot: null, entityId: 'place_changan', label: '长安', x: 0.14, y: 0.52, certainty: 'confirmed_region', zhangqian: true },
  { key: 'fb_hexi', hotspot: null, entityId: 'region_hexi_corridor', label: '河西走廊', x: 0.3, y: 0.4, certainty: 'confirmed_region', zhangqian: true },
  { key: 'fb_dunhuang', hotspot: null, entityId: 'place_dunhuang', label: '敦煌 / 关隘区域', x: 0.46, y: 0.47, certainty: 'confirmed_region', zhangqian: true },
  { key: 'fb_xiyu', hotspot: null, entityId: 'region_western_regions', label: '西域', x: 0.61, y: 0.58, certainty: 'confirmed_region', zhangqian: true },
  { key: 'fb_niya', hotspot: null, entityId: 'site_niya', label: '尼雅遗址', x: 0.74, y: 0.78, certainty: 'uncertain_segment', zhangqian: false },
  { key: 'fb_central_asia', hotspot: null, entityId: 'region_central_asia', label: '向中亚继续展开', x: 0.87, y: 0.44, certainty: 'uncertain_segment', zhangqian: true },
]

const usingFallback = computed(() => (props.scene?.hotspots?.length ?? 0) === 0)

const nodes = computed<NodeVM[]>(() => {
  const list = props.scene?.hotspots ?? []
  if (!list.length) return FALLBACK_NODES
  return list
    .filter((h) => !isWholeCanvas(h))
    .map<NodeVM>((h) => {
      const c = centerOf(h)
      return {
        key: h.id,
        hotspot: h,
        entityId: h.entity_id ?? null,
        label: h.label || h.entity_id || '未命名节点',
        x: c.x,
        y: c.y,
        certainty: (h.certainty as LegendKey | null) ?? 'confirmed_region',
        zhangqian: h.route_scope === 'LEADER_AUDIENCE_JOURNEY',
      }
    })
    .sort((a, b) => a.x - b.x)
})

/* ---------------------------------------------------------------- 路线数据 */

interface SegmentVM {
  key: string
  d: string
  /** 折线长度（用户单位），仅用于错开动画节奏 */
  len: number
  certainty: RouteCertainty
  label: string
  zhangqian: boolean
}

/** 在两节点之间生成一条微微弯曲的弧线，避免看起来像笔直的现代道路 */
function arcPoints(a: NodeVM, b: NodeVM, bend: number): number[][] {
  const mx = (a.x + b.x) / 2
  const my = (a.y + b.y) / 2
  const dx = b.x - a.x
  const dy = b.y - a.y
  const nl = Math.hypot(-dy, dx) || 1
  const cx = mx + (-dy / nl) * bend
  const cy = my + (dx / nl) * bend
  const out: number[][] = []
  for (let i = 0; i <= 6; i++) {
    const t = i / 6
    const u = 1 - t
    out.push([u * u * a.x + 2 * u * t * cx + t * t * b.x, u * u * a.y + 2 * u * t * cy + t * t * b.y])
  }
  return out
}

/** 归一化点 → SVG path 的 d 字符串 */
function toPathD(pts: number[][]): string {
  return pts
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${(p[0] * VB_W).toFixed(1)} ${(p[1] * VB_H).toFixed(1)}`)
    .join(' ')
}

function polyLen(pts: number[][]): number {
  let len = 0
  for (let i = 1; i < pts.length; i++) {
    len += Math.hypot((pts[i][0] - pts[i - 1][0]) * VB_W, (pts[i][1] - pts[i - 1][1]) * VB_H)
  }
  return len
}

/** 内置示意路线：河西走廊—西域一线，逐段标注可信度 */
const FALLBACK_LINKS: { a: string; b: string; certainty: RouteCertainty; label: string; bend: number; zhangqian: boolean }[] = [
  { a: 'fb_changan', b: 'fb_hexi', certainty: 'approximate_corridor', label: '长安—河西走廊', bend: 0.05, zhangqian: true },
  { a: 'fb_hexi', b: 'fb_dunhuang', certainty: 'confirmed_area', label: '河西走廊—敦煌', bend: 0.035, zhangqian: true },
  { a: 'fb_dunhuang', b: 'fb_xiyu', certainty: 'approximate_corridor', label: '敦煌—西域', bend: -0.05, zhangqian: true },
  { a: 'fb_xiyu', b: 'fb_niya', certainty: 'uncertain_segment', label: '西域—尼雅（南道）', bend: 0.04, zhangqian: false },
  { a: 'fb_xiyu', b: 'fb_central_asia', certainty: 'uncertain_segment', label: '西域—中亚', bend: -0.045, zhangqian: true },
]

const segments = computed<SegmentVM[]>(() => {
  const byKey = new Map(nodes.value.map((n) => [n.key, n]))

  // ① 内容层透传的 HistoricalMap（若后端把 map 一并挂在 scene 上）
  const map = (props.scene as unknown as { map?: { segments?: unknown[] } } | null)?.map
  if (map?.segments?.length) {
    return (map.segments as Record<string, any>[]).map((s, i) => {
      const geom = (s.geometry as number[][]) ?? []
      return {
        key: String(s.id ?? `seg_${i}`),
        d: toPathD(geom),
        len: polyLen(geom),
        certainty: (s.certainty as RouteCertainty) ?? 'approximate_corridor',
        label: String(s.label ?? '历史交通廊道示意'),
        zhangqian: s.route_scope === 'LEADER_AUDIENCE_JOURNEY',
      }
    })
  }

  // ② 内置示意路线（scene.hotspots 缺失时）
  if (usingFallback.value) {
    return FALLBACK_LINKS.flatMap<SegmentVM>((l) => {
      const a = byKey.get(l.a)
      const b = byKey.get(l.b)
      if (!a || !b) return []
      const pts = arcPoints(a, b, l.bend)
      return [
        {
          key: `${l.a}__${l.b}`,
          d: toPathD(pts),
          len: polyLen(pts),
          certainty: l.certainty,
          label: l.label,
          zhangqian: l.zhangqian,
        },
      ]
    })
  }

  // ③ 有真实热点但没有路线数据：按 x 相邻顺序给出「示意连线」。
  //    连线本身一律不高于 approximate_corridor —— 不假装这是考订出来的道路；
  //    只有当两端节点中有一端本身就存疑时，才降级为 uncertain_segment。
  const list = nodes.value.filter((n) => n.hotspot)
  const out: SegmentVM[] = []
  for (let i = 1; i < list.length; i++) {
    const a = list[i - 1]
    const b = list[i]
    const pts = arcPoints(a, b, i % 2 ? 0.04 : -0.04)
    const shaky = a.certainty === 'uncertain_segment' || b.certainty === 'uncertain_segment'
    out.push({
      key: `${a.key}__${b.key}`,
      d: toPathD(pts),
      len: polyLen(pts),
      certainty: shaky ? 'uncertain_segment' : 'approximate_corridor',
      label: '历史交通廊道示意',
      zhangqian: a.zhangqian && b.zhangqian,
    })
  }
  return out
})

/* ---------------------------------------------------------------- 透镜筛选 */

type NodeFilter = 'all' | 'unseen' | 'zhangqian' | 'network'
const nodeFilter = ref<NodeFilter>('all')

function statusOf(h: Hotspot | null, key: string) {
  if (!h) return 'UNSEEN' as const
  return props.hotspotStatus[key] ?? 'UNSEEN'
}

/** 打开透镜时，节点按当前筛选弱化（不隐藏，避免用户以为内容缺失） */
function isDimmed(n: NodeVM): boolean {
  if (!props.lensOpen) return false
  if (nodeFilter.value === 'unseen') {
    return n.hotspot ? statusOf(n.hotspot, n.key) !== 'UNSEEN' : false
  }
  if (nodeFilter.value === 'zhangqian') return !n.zhangqian
  if (nodeFilter.value === 'network') return n.zhangqian
  return false
}

function isSegDimmed(s: SegmentVM): boolean {
  if (!props.lensOpen) return false
  if (nodeFilter.value === 'zhangqian') return !s.zhangqian
  if (nodeFilter.value === 'network') return s.zhangqian
  if (nodeFilter.value === 'unseen') return false
  return false
}

/** 图例只列出当前数据真正用到的性质，避免出现空图例 */
const legendItems = computed(() => {
  const keys = new Set<LegendKey>()
  for (const n of nodes.value) keys.add(n.certainty)
  for (const s of segments.value) keys.add(s.certainty)
  const order: LegendKey[] = [
    'confirmed_region',
    'confirmed_area',
    'approximate_corridor',
    'uncertain_segment',
    'curatorial_connector',
  ]
  const seen = new Set<string>()
  const out: { key: LegendKey; glyph: string; label: string; dash: string }[] = []
  for (const k of order) {
    const m = CERTAINTY_META[k]
    if (!keys.has(k) || seen.has(m.label)) continue
    seen.add(m.label)
    out.push({ key: k, glyph: m.glyph, label: m.label, dash: m.dash })
  }
  return out
})

/* ---------------------------------------------------------------- 交互 */

const hovered = ref<NodeVM | null>(null)

const selectedNode = computed<NodeVM | null>(() => {
  if (!props.selectedEntityId) return null
  return nodes.value.find((n) => n.entityId === props.selectedEntityId) ?? null
})

function onNodeClick(n: NodeVM) {
  if (n.hotspot) {
    // 有真实热点记录：走完整的热点链（选中 + 上报 + 抽屉）
    emit('select-hotspot', n.hotspot)
    return
  }
  // 内置示意节点没有热点记录，只跳到实体，不伪造热点
  if (n.entityId) emit('select-entity', n.entityId)
}

function svgPos(n: { x: number; y: number }) {
  return { cx: n.x * VB_W, cy: n.y * VB_H }
}

</script>

<template>
  <div class="han">
    <!-- 空态：场景尚未接入时给出可读说明，绝不白屏 -->
    <div v-if="!scene" class="han__empty">
      <DsIcon name="map" :size="28" />
      <p class="han__empty-title">这段内容暂时没有完成数字化整理。</p>
      <p class="han__empty-note">丝路历史网络地图准备好之后，会在这里出现。</p>
    </div>

    <template v-else>
      <div class="han__col">
        <!-- 透镜工具条（仅在路线透镜开启时出现，规格 §9.1） -->
        <div v-if="lensOpen" class="han__tools">
          <span class="han__tools-label"><DsIcon name="layers" :size="14" />路线透镜</span>
          <button
            v-for="opt in [
              { k: 'all', t: '全部节点' },
              { k: 'unseen', t: '仅未探索' },
              { k: 'zhangqian', t: '张骞行程相关' },
              { k: 'network', t: '长期交通网络' },
            ]"
            :key="opt.k"
            type="button"
            class="han__tool"
            :class="{ 'is-on': nodeFilter === opt.k }"
            @click="nodeFilter = opt.k as NodeFilter"
          >
            {{ opt.t }}
          </button>
        </div>

        <!-- 主地图：aspect-ratio 与 viewBox 一致，保证 SVG 与热点严格对齐 -->
        <div class="han__mapwrap">
          <div class="han__map">
            <SceneViewer
              :scene="{
                ...scene,
                // 写实环境只承担氛围，不作为精确历史地图；路线与节点仍由网页交互层表达。
                background_asset_id: '/assets/han/han-route-scene-v2.png',
                hotspots: [],
              }"
              chapter-slug="han"
              aspect="auto"
              :lens-open="lensOpen"
              :show-badge="false"
              source-label="AI生成历史环境示意 · 非史实照片"
            >
              <template #background>
                <div class="han__fallback-scene">
                  <span>写实历史环境图暂未加载</span>
                </div>
              </template>

              <!-- 路线与节点是独立证据层，不会烙进生成图里。 -->
              <template #overlay>
                <div class="han__atmosphere" aria-hidden="true" />
                <svg :viewBox="`0 0 ${VB_W} ${VB_H}`" preserveAspectRatio="xMidYMid meet" class="han__route-layer" aria-hidden="true">
                  <defs>
                    <!-- 路线揭示遮罩：pathLength=1 让 dashoffset 1→0 成为一次干净的「绘制」 -->
                    <mask
                      v-for="s in segments"
                      :id="`han-mask-${uid}-${s.key}`"
                      :key="`m-${s.key}`"
                      maskUnits="userSpaceOnUse"
                      x="0"
                      y="0"
                      :width="VB_W"
                      :height="VB_H"
                    >
                      <path
                        :d="s.d"
                        class="han__reveal"
                        pathLength="1"
                        fill="none"
                        stroke="#fff"
                        stroke-width="16"
                        stroke-linecap="round"
                        :style="{ animationDelay: `${200 + Math.min(s.len, 900) / 3}ms` }"
                      />
                    </mask>
                  </defs>

                  <!-- 深色衬线让金色证据线在真实地貌上保持可读。 -->
                  <g>
                    <path
                      v-for="s in segments"
                      :key="`shadow-${s.key}`"
                      :d="s.d"
                      class="han__seg-shadow"
                      :class="{ 'is-dim': isSegDimmed(s) }"
                      :mask="`url(#han-mask-${uid}-${s.key})`"
                      fill="none"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                    <path
                      v-for="s in segments"
                      :key="`line-${s.key}`"
                      :d="s.d"
                      class="han__seg"
                      :class="[`han__seg--${s.certainty}`, { 'is-dim': isSegDimmed(s) }]"
                      :mask="`url(#han-mask-${uid}-${s.key})`"
                      fill="none"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </g>

                  <!-- 节点名称仍来自内容层，而不是从生成图中识别或推断。 -->
                  <g>
                    <text
                      v-for="n in nodes"
                      :key="`t-${n.key}`"
                      :x="svgPos(n).cx"
                      :y="svgPos(n).cy + 30"
                      class="han__node-label"
                      :class="{ 'is-dim': isDimmed(n) }"
                      text-anchor="middle"
                    >
                      {{ n.label }}
                    </text>
                  </g>
                </svg>

                <div class="han__nodes">
                  <SceneHotspot
                    v-for="n in nodes.filter((x) => x.hotspot)"
                    :key="n.key"
                    :hotspot="n.hotspot!"
                    :status="props.hotspotStatus[n.key] ?? 'UNSEEN'"
                    :class="{ 'is-dimmed': isDimmed(n) }"
                    @select="onNodeClick(n)"
                  />
                  <!-- 内置示意节点没有热点记录，用中性空心点表示「待接入」 -->
                  <button
                    v-for="n in nodes.filter((x) => !x.hotspot)"
                    :key="n.key"
                    type="button"
                    class="han__ghost"
                    :class="{ 'is-dim': isDimmed(n) }"
                    :style="{ left: `${n.x * 100}%`, top: `${n.y * 100}%` }"
                    :aria-label="`${n.label}（示意节点，地图内容尚未接入）`"
                    @click="onNodeClick(n)"
                    @mouseenter="hovered = n"
                    @mouseleave="hovered = null"
                  />
                </div>
              </template>
            </SceneViewer>
          </div>
        </div>
      </div>

      <!-- 侧栏：图例 + 路线说明 + 当前节点操作 -->
      <aside class="han__side">
        <section class="han__block">
          <h3 class="han__block-title">图例</h3>
          <ul class="han__legend">
            <li v-for="l in legendItems" :key="l.key" class="han__legend-item">
              <span class="han__legend-glyph">{{ l.glyph }}</span>
              <span class="han__legend-label">{{ l.label }}</span>
            </li>
          </ul>
        </section>

        <section class="han__block">
          <h3 class="han__block-title">路线为什么不精确？</h3>
          <p class="han__note">
            本页用于帮助理解历史空间关系。古代路线会随时期、政治环境、自然条件和具体行程而变化，图中连线不等同于现代GPS导航轨迹。
          </p>
          <p v-if="usingFallback" class="han__fallback">
            地图数据尚未接入，当前显示的是示意节点；点击只会打开实体说明，不会记录热点探索。
          </p>
        </section>

        <section v-if="selectedNode" class="han__block han__block--sel">
          <h3 class="han__block-title">当前节点</h3>
          <p class="han__sel-name">{{ selectedNode.label }}</p>
          <p class="han__sel-meta">
            {{ selectedNode.zhangqian ? '与张骞行程直接相关' : '属于长期交通网络，不必然与张骞本人有关' }}
          </p>
          <div class="han__sel-actions">
            <button type="button" class="han__act" @click="emit('open-chat', selectedNode.entityId ?? undefined)">
              <DsIcon name="sparkle" :size="13" />向它提问
            </button>
            <button type="button" class="han__act" @click="emit('open-graph', selectedNode.entityId ?? undefined)">
              <DsIcon name="nodes" :size="13" />关系图谱
            </button>
          </div>
        </section>
      </aside>
    </template>
  </div>
</template>

<style scoped>
.han {
  flex: 1;
  min-width: 0;
  display: flex;
  gap: var(--sp-4);
  align-items: stretch;
}

/* ---------- 空态 ---------- */
.han__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  color: var(--color-ink-500);
}
.han__empty-title {
  font-size: var(--fs-body);
  color: var(--color-ink-700);
}
.han__empty-note {
  font-size: var(--fs-body-s);
}

/* ---------- 左列 ---------- */
.han__col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.han__tools {
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}
.han__tools-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--fs-caption);
  color: var(--chapter-accent);
  font-weight: 600;
  margin-right: var(--sp-1);
}
.han__tool {
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard),
    background-color var(--dur-fast) var(--ease-standard);
}
.han__tool:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.han__tool.is-on {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
  color: #fff;
}

.han__mapwrap {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
/* 盒子比例与 viewBox 完全一致 → SVG 用户坐标 = 元素百分比坐标 */
.han__map {
  position: relative;
  width: 100%;
  max-height: 100%;
  aspect-ratio: 1000 / 560;
}
.han__map :deep(.scene) {
  height: 100%;
  background: #3b352d;
  box-shadow: inset 0 0 0 1px rgba(245, 222, 168, 0.24), 0 18px 42px rgba(36, 58, 54, 0.18);
}
.han__map :deep(.scene__img) {
  transform: scale(1.01);
  filter: brightness(0.73) saturate(0.82) contrast(1.08);
}
.han__fallback-scene {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: rgba(246, 238, 218, 0.7);
  background: linear-gradient(145deg, #766650, #2d4543);
  font-size: var(--fs-body-s);
}
.han__atmosphere {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(16, 31, 29, 0.28), transparent 27%, transparent 78%, rgba(16, 28, 27, 0.12)),
    linear-gradient(180deg, rgba(236, 220, 183, 0.08), transparent 38%, rgba(8, 18, 18, 0.28));
}
.han__route-layer {
  position: absolute;
  inset: 0;
  z-index: 2;
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
}

/* ---------- 路线揭示动画（设计系统 §57：line draw 800–1200ms） ---------- */
.han__reveal {
  stroke-dasharray: 1;
  stroke-dashoffset: 1;
  animation: han-draw 1000ms var(--ease-standard) both;
}
@keyframes han-draw {
  from {
    stroke-dashoffset: 1;
  }
  to {
    stroke-dashoffset: 0;
  }
}

.han__seg {
  stroke: #e9ba66;
  stroke-width: 2.8;
  filter: drop-shadow(0 1px 2px rgba(24, 24, 20, 0.72));
  transition: opacity var(--dur-normal) var(--ease-standard);
}
.han__seg-shadow {
  stroke: rgba(28, 33, 28, 0.76);
  stroke-width: 7;
  opacity: 0.66;
  transition: opacity var(--dur-normal) var(--ease-standard);
}
.han__seg-shadow.is-dim { opacity: 0.08; }
.han__seg--confirmed_area {
  stroke-width: 3.2;
}
.han__seg--approximate_corridor {
  stroke-dasharray: 12 8;
  opacity: 0.85;
}
.han__seg--uncertain_segment {
  stroke-dasharray: 3 9;
  opacity: 0.7;
}
.han__seg--curatorial_connector {
  stroke-dasharray: 2 7;
  opacity: 0.6;
  stroke: #d8c0dd;
}
.han__seg.is-dim {
  opacity: 0.12;
}

.han__node-label {
  font-family: var(--font-ui);
  font-size: 13px;
  font-weight: 650;
  letter-spacing: 0.04em;
  fill: #fff8e8;
  paint-order: stroke;
  stroke: rgba(17, 31, 29, 0.92);
  stroke-width: 4.5px;
  stroke-linejoin: round;
  transition: opacity var(--dur-normal) var(--ease-standard);
}
.han__node-label.is-dim {
  opacity: 0.22;
}

.han__nodes {
  position: absolute;
  inset: 0;
  z-index: 3;
}
.han__nodes :deep(.hs__ring) {
  border-color: rgba(255, 219, 136, 0.92);
  box-shadow: 0 0 0 5px rgba(23, 36, 32, 0.26), 0 0 22px rgba(235, 179, 74, 0.36);
}
.han__nodes :deep(.hs__dot) {
  border-color: rgba(255, 242, 206, 0.92);
  background: rgba(201, 139, 47, 0.9);
}
.han__nodes :deep(.hs__tip) {
  border-color: rgba(238, 200, 119, 0.5);
  background: rgba(20, 35, 32, 0.92);
  color: #fff8e8;
}
.han__nodes :deep(.is-dimmed) {
  opacity: 0.22;
  transition: opacity var(--dur-normal) var(--ease-standard);
}

/* 内置示意节点：空心，明确区别于真实热点 */
.han__ghost {
  position: absolute;
  width: 18px;
  height: 18px;
  margin: -9px 0 0 -9px;
  border-radius: 50%;
  border: 2px solid rgba(255, 242, 206, 0.9);
  background: rgba(201, 139, 47, 0.86);
  box-shadow: 0 0 0 5px rgba(23, 36, 32, 0.24), 0 0 22px rgba(235, 179, 74, 0.34);
  transition: opacity var(--dur-normal) var(--ease-standard);
}
.han__ghost:hover {
  background: #e6b65d;
  transform: scale(1.12);
}
.han__ghost.is-dim {
  opacity: 0.2;
}

/* ---------- 侧栏 ---------- */
.han__side {
  width: 232px;
  flex: none;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  overflow-y: auto;
}
.han__block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-panel);
  padding: var(--sp-3) var(--sp-4);
}
.han__block--sel {
  border-color: color-mix(in srgb, var(--chapter-accent) 40%, transparent);
}
.han__block-title {
  font-size: var(--fs-caption);
  font-weight: 600;
  color: var(--chapter-accent);
  margin-bottom: var(--sp-2);
}
.han__legend {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.han__legend-item {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
}
.han__legend-glyph {
  flex: none;
  width: 14px;
  text-align: center;
  color: var(--chapter-accent);
  font-weight: 700;
}
.han__note {
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
}
.han__fallback {
  margin-top: var(--sp-2);
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--evidence-disputed);
}
.han__sel-name {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  color: var(--color-ink-900);
}
.han__sel-meta {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  margin-top: 2px;
}
.han__sel-actions {
  display: flex;
  gap: var(--sp-2);
  margin-top: var(--sp-3);
}
.han__act {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.han__act:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}

@media (prefers-reduced-motion: reduce) {
  .han__reveal {
    animation: none;
    stroke-dashoffset: 0;
  }
}
/* 队员二：390×844 移动端适配 —— 地图在上、说明在下，不出现横向溢出 */
@media (max-width: 900px) {
  .han { flex-direction: column; }
  .han__side { width: 100%; flex: none; }
  .han__map { aspect-ratio: 1000 / 560; }
  .han__tools { flex-wrap: wrap; }
  .han__tool { min-height: 44px; }
  .han__act { min-height: 44px; }
}
</style>
