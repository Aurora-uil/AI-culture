<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import SceneViewer from '@/components/scene/SceneViewer.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import { getMap } from '@/api/endpoints'
import type { Chapter, HistoricalMap, Hotspot, MapNode, MapSegment, RouteCertainty, RouteScope, Scene } from '@/types'

/**
 * 清代 Q02 东归迁徙主地图 + Q03 路线透镜（规格 §8 / §9，设计系统 §57）
 *
 * 本组件是「红线最多」的一屏，以下为内容红线对应的设计决策：
 *
 * 1. 路线精度绝不能高于证据精度（§2.3）。certainty 直接决定渲染方式，
 *    任何情况下都不会把 uncertain_segment 画成一条细实线。
 * 2. geometry 为空的区段（如 seg_qing_migration_01）不编造中途点，
 *    只用「虚线 + ?」表达两个已知区域之间的不确定性。
 * 3. 大部众迁徙（MASS_MIGRATION）与首领赴承德（LEADER_AUDIENCE_JOURNEY）
 *    始终分开渲染、分开成图；切换到首领行程时，大部众迁徙只作为灰色位置
 *    参照，并在界面上固定说明「不是同一条路线」。
 * 4. 不使用现代导航语言（最优路径 / 导航 / 里程规划），不做日历式逐日行程。
 * 5. 底图不以现代政治边界为主视觉；淡化显示的地理参照固定标注「现代位置参照」。
 * 6. 固定图例与固定免责声明常驻，不随缩放 / 切换隐藏。
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

/* ------------------------------------------------------------------
   Scene 类型未声明 map 字段（后端 SceneOut 也没有该字段），
   这里用局部扩展类型读取 content/<chapter>/scene.json 的地图结构，
   并在 scene 内没有 map 时自行走 GET /map/{map_id} 补取，
   避免修改共享类型文件与 chapter store。
   ------------------------------------------------------------------ */
interface QingSegment extends MapSegment {
  evidence_note?: string
  render_type?: string
}

interface SceneWithMap extends Scene {
  map?: HistoricalMap | null
}

interface QingMap extends Omit<HistoricalMap, 'segments'> {
  segments: QingSegment[]
  default_route_scope?: RouteScope
}

/**
 * 后端 `GET /chapters/{id}/scene` 不返回 map 字段（SceneOut 无此字段），
 * 地图数据在 `GET /map/{map_id}`，且 map_id 与 scene_id 同名。
 * 因此 scene 内没有 map 时，组件自行补取一次；失败不阻断页面，
 * 只是落到「迁徙路线数据正在整理中」的空态。
 */
const remoteMap = ref<QingMap | null>(null)

const mapData = computed<QingMap | null>(() => {
  const raw = (props.scene as SceneWithMap | null)?.map
  if (raw) return raw as QingMap
  return remoteMap.value
})

async function loadRemoteMap() {
  if ((props.scene as SceneWithMap | null)?.map) return
  const sceneId = props.scene?.id
  if (!sceneId) {
    remoteMap.value = null
    return
  }
  try {
    remoteMap.value = (await getMap(sceneId)) as unknown as QingMap
  } catch {
    remoteMap.value = null
  }
}

onMounted(loadRemoteMap)
watch(() => props.scene?.id, loadRemoteMap)

const allNodes = computed<MapNode[]>(() => mapData.value?.nodes ?? [])
const allSegments = computed<QingSegment[]>(() => mapData.value?.segments ?? [])
const hasMap = computed(() => allNodes.value.length > 0 || allSegments.value.length > 0)

/* ---------------- route_scope 切换（§8.7 BTN-Q02-06 / 07 / 08） ---------------- */

const SCOPE_META: { key: RouteScope; label: string }[] = [
  { key: 'MASS_MIGRATION', label: '大部众迁徙' },
  { key: 'LEADER_AUDIENCE_JOURNEY', label: '首领赴承德' },
  { key: 'SETTLEMENT_DISTRIBUTION', label: '安置分布' },
]

/** 默认 MASS_MIGRATION；首领相关节点 / 区段只有用户主动切换后才出现 */
const activeScope = ref<RouteScope>((mapData.value?.default_route_scope as RouteScope) ?? 'MASS_MIGRATION')
/** 用户是否已经手动切换过图层（手动切换后不再被内容默认值覆盖） */
const scopeTouched = ref(false)

watch(mapData, (m) => {
  if (!m || scopeTouched.value) return
  if (m.default_route_scope) activeScope.value = m.default_route_scope
})

function chooseScope(s: RouteScope) {
  scopeTouched.value = true
  activeScope.value = s
  // 切换图层时清空选中，避免右侧证据卡停留在另一个 scope 的区段上
  selectedSegmentId.value = null
  selectedNodeId.value = null
}

const isLeaderScope = computed(() => activeScope.value === 'LEADER_AUDIENCE_JOURNEY')
const isContextScope = computed(() => activeScope.value !== 'MASS_MIGRATION')

const visibleNodes = computed(() => allNodes.value.filter((n) => n.route_scope === activeScope.value))
const visibleSegments = computed(() =>
  allSegments.value.filter((s) => s.route_scope === activeScope.value),
)

/** 非当前 scope 的大部众迁徙：仅作灰色位置参照，绝不与首领行程合并成一条线 */
const contextNodes = computed(() =>
  isContextScope.value ? allNodes.value.filter((n) => n.route_scope === 'MASS_MIGRATION') : [],
)
const contextSegments = computed(() =>
  isContextScope.value ? allSegments.value.filter((s) => s.route_scope === 'MASS_MIGRATION') : [],
)

/* ---------------- 可信度分级渲染（§2.3 + 设计系统 §57） ---------------- */

const CERTAINTY_META: Record<RouteCertainty, { zh: string; symbol: string; canConfirm: string }> = {
  confirmed_area: {
    zh: '确认地点 / 确认区域',
    symbol: '●',
    canConfirm: '公开资料一致支持的抵达区域或方向。',
  },
  approximate_corridor: {
    zh: '较高置信历史廊道',
    symbol: '━',
    canConfirm: '大体方向与廊道范围；具体行进线不可确认。',
  },
  uncertain_segment: {
    zh: '路线存在不确定性',
    symbol: '?',
    canConfirm: '两个已知区域之间的移动发生过；中途路径无法复原。',
  },
  curatorial_connector: {
    zh: '策展关联',
    symbol: '┄',
    canConfirm: '为帮助理解先后关系而建立的关联，不是一条行进路线。',
  },
}

/** 后端出参里 certainty 是普通字符串，遇到未知取值时回退为「不声称」，而不是猜一个等级 */
const FALLBACK_CERTAINTY = {
  zh: '未标注可信度',
  symbol: '·',
  canConfirm: '本区段没有标注可信度等级，请以史料来源页为准。',
}
type CertaintyMeta = (typeof CERTAINTY_META)[RouteCertainty]

function metaOf(c: string): CertaintyMeta {
  return CERTAINTY_META[c as RouteCertainty] ?? FALLBACK_CERTAINTY
}

/** 固定图例文案，不得改写（SCHEMA §7.2） */
const LEGEND = [
  { symbol: '●', label: '确认地点', tone: 'confirmed' },
  { symbol: '━', label: '较高置信历史廊道', tone: 'corridor' },
  { symbol: '≈', label: '大体迁徙区段', tone: 'approx' },
  { symbol: '?', label: '路线存在不确定性', tone: 'uncertain' },
  { symbol: '┄', label: '策展关联', tone: 'curatorial' },
]

/** 固定免责声明，必须常驻显示 */
const FIXED_DISCLAIMER = '历史迁徙路线示意，并非现代GPS轨迹。'

/** 本平台明确不声称的内容（§8.8「不能推出什么」固定文案） */
const NOT_CLAIMED = '每一天的精确位置；每一个中途点；一条唯一固定路径。'

/* ---------------- 几何 ---------------- */

const VB_W = 1600
const VB_H = 900

function nodeById(id: string): MapNode | undefined {
  return allNodes.value.find((n) => n.id === id)
}

/** 区段折线：geometry 为空时不编造中途点，退化为两端已知区域的连线 */
function segmentPoints(s: QingSegment): number[][] {
  if (Array.isArray(s.geometry) && s.geometry.length >= 2) return s.geometry as number[][]
  const from = nodeById(s.from_node_id)
  const to = nodeById(s.to_node_id)
  if (!from || !to) return []
  return [
    [from.x, from.y],
    [to.x, to.y],
  ]
}

function toPath(pts: number[][]): string {
  if (!pts.length) return ''
  return pts
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${(p[0] * VB_W).toFixed(1)} ${(p[1] * VB_H).toFixed(1)}`)
    .join(' ')
}

function pathOf(s: QingSegment): string {
  return toPath(segmentPoints(s))
}

function midpointOf(s: QingSegment): { x: number; y: number } | null {
  const pts = segmentPoints(s)
  if (pts.length < 2) return null
  const i = Math.floor((pts.length - 1) / 2)
  const a = pts[i]
  const b = pts[i + 1]
  return { x: ((a[0] + b[0]) / 2) * 100, y: ((a[1] + b[1]) / 2) * 100 }
}

/** 不确定区段的 ? 标识位置（先算好，避免在模板里做类型断言） */
const uncertainMarks = computed<{ id: string; x: number; y: number }[]>(() =>
  visibleSegments.value
    .filter((s) => s.certainty === 'uncertain_segment')
    .map((s) => {
      const m = midpointOf(s)
      return m ? { id: s.id, x: m.x, y: m.y } : null
    })
    .filter((m): m is { id: string; x: number; y: number } => m !== null),
)

/** MapNode 的 certainty 允许 confirmed_region，映射到路线可信度枚举后再取图例 */
function certaintyOf(n: MapNode): RouteCertainty {
  return n.certainty === 'confirmed_region' ? 'confirmed_area' : n.certainty
}

/** 确定性区段的实心圆点（confirmed_area） */
function dotsOf(s: QingSegment): number[][] {
  const pts = segmentPoints(s)
  return pts.length >= 2 ? pts : []
}

/* ---------------- 交互：区段证据卡 / 节点 ---------------- */

const selectedSegmentId = ref<string | null>(null)
const selectedNodeId = ref<string | null>(null)

const selectedSegment = computed<QingSegment | null>(
  () => allSegments.value.find((s) => s.id === selectedSegmentId.value) ?? null,
)

const selectedNode = computed<MapNode | null>(
  () => allNodes.value.find((n) => n.id === selectedNodeId.value) ?? null,
)

function onSegmentClick(s: QingSegment) {
  selectedSegmentId.value = selectedSegmentId.value === s.id ? null : s.id
  selectedNodeId.value = null
}

function onNodeClick(n: MapNode) {
  selectedNodeId.value = selectedNodeId.value === n.id ? null : n.id
  selectedSegmentId.value = null

  // 复用统一热点通道：优先使用 scene.hotspots 里已登记的实体热点，
  // 场景未提供热点时（清代 scene.json 不含 hotspots）合成一个点热点，
  // 保证上层 C02Scene 的 onHotspot 逻辑与其它章节完全一致。
  const entityId = n.entity_id ?? n.id
  const existing = props.scene?.hotspots?.find((h) => h.entity_id === entityId)
  if (existing) {
    emit('select-hotspot', existing)
    return
  }
  emit('select-hotspot', {
    id: `hs_${n.id}`,
    entity_id: entityId,
    shape: 'point',
    normalized_points: [n.x, n.y],
    label: n.label,
    certainty: n.certainty === 'confirmed_region' ? 'confirmed_area' : n.certainty,
    route_scope: n.route_scope,
    sort_order: n.sort_order ?? 0,
  })
}

/** §8.7 BTN-Q02-10「为什么不是GPS？」方法卡 */
const methodOpen = ref(false)

const scopeNote = computed(() => {
  if (isLeaderScope.value) {
    return '首领赴承德与大部众迁徙不是同一条路线。灰色底纹为大部众迁徙示意，仅作位置参照，两者未被合并渲染。'
  }
  if (activeScope.value === 'SETTLEMENT_DISTRIBUTION') {
    return '安置以聚合区域表示，表达的是安置方向，不是一次行进路线。第一版不展示到具体游牧地界。'
  }
  return '本图层只表达「自伏尔加河流域向东、最终抵达伊犁河流域」的大体方向与廊道，不代表逐日行程，也不代表唯一固定路径。'
})
</script>

<template>
  <div class="qm">
    <!-- ============ 地图主区 ============ -->
    <div class="qm__stage">
      <SceneViewer
        :scene="scene"
        :hotspot-status="hotspotStatus"
        :lens-open="lensOpen"
        :chapter-slug="chapter.slug"
        aspect="16 / 9"
      >
        <!-- 抽象欧亚大陆底图：不以现代政治边界为主视觉 -->
        <template #background>
          <svg
            class="qm__svg"
            viewBox="0 0 1600 900"
            preserveAspectRatio="none"
            role="img"
            aria-label="东归迁徙示意地图底图：抽象欧亚大陆轮廓，西侧伏尔加河下游，东侧伊犁河流域。淡化的现代地理参照，不作为主视觉。"
          >
            <defs>
              <linearGradient id="qmLand" x1="0" y1="0" x2="0" y2="1">
                <stop class="qmLanda" offset="0%" />
                <stop class="qmLanda2" offset="100%" />
              </linearGradient>
            </defs>

            <rect class="qmBase" x="0" y="0" width="1600" height="900" />

            <!-- 大陆轮廓（抽象） -->
            <path
              class="qmLand"
              d="M40 330 C150 214 330 176 520 196 C716 216 900 148 1128 150
                 C1330 152 1508 196 1568 258 L1568 566 C1452 606 1300 646 1148 626
                 C978 604 820 646 640 656 C458 666 254 636 116 604 Z"
            />

            <!-- 草原廊道带 -->
            <path
              class="qmSteppe"
              d="M70 448 C400 404 900 414 1530 452 L1530 548 C900 516 400 506 70 540 Z"
            />

            <!-- 河流：西侧伏尔加河下游、东侧伊犁河 -->
            <path class="qmRiver" d="M330 176 C300 250 258 306 208 366 C182 398 166 452 152 522" />
            <path class="qmRiver" d="M1246 236 C1272 312 1292 396 1272 470" />

            <!-- 山地示意 -->
            <g class="qmMountain">
              <path d="M1010 336 L1052 268 L1094 336 Z" />
              <path d="M1068 344 L1112 274 L1156 344 Z" />
              <path d="M940 346 L976 296 L1012 346 Z" />
              <path d="M858 352 L888 312 L918 352 Z" />
            </g>

            <!-- 内陆水体示意 -->
            <ellipse class="qmLake" cx="152" cy="576" rx="54" ry="82" />

            <!-- 经纬网 -->
            <g class="qmGrid">
              <line x1="0" y1="300" x2="1600" y2="300" />
              <line x1="0" y1="600" x2="1600" y2="600" />
              <line x1="400" y1="0" x2="400" y2="900" />
              <line x1="800" y1="0" x2="800" y2="900" />
              <line x1="1200" y1="0" x2="1200" y2="900" />
            </g>

            <!-- 现代地理参照标注（淡化显示时必须固定标注） -->
            <g class="qmRefGroup">
              <line class="qmRefLine" x1="1180" y1="742" x2="1288" y2="640" />
              <circle class="qmRefDot" cx="1288" cy="640" r="4" />
            </g>
          </svg>
        </template>

        <template #overlay>
          <div class="qm__overlay">
            <!-- 路线层 -->
            <svg class="qm__routes" viewBox="0 0 1600 900" preserveAspectRatio="none">
              <!-- 灰色位置参照：非当前 scope 的大部众迁徙 -->
              <g class="qm__context">
                <path
                  v-for="s in contextSegments"
                  :key="`ctx-${s.id}`"
                  class="qmRoute qmRoute--context"
                  :d="pathOf(s)"
                />
              </g>

              <!-- 当前 scope 的区段：certainty 决定渲染方式 -->
              <g class="qm__primary">
                <template v-for="s in visibleSegments" :key="s.id">
                  <!-- approximate_corridor：实线宽带，不是细线 -->
                  <template v-if="s.certainty === 'approximate_corridor'">
                    <path class="qmRoute qmRoute--band" :d="pathOf(s)" />
                    <path class="qmRoute qmRoute--bandCore" :d="pathOf(s)" />
                  </template>

                  <!-- confirmed_area：实心线 + 实心圆点 -->
                  <template v-else-if="s.certainty === 'confirmed_area'">
                    <path class="qmRoute qmRoute--solid" :d="pathOf(s)" />
                    <circle
                      v-for="(p, i) in dotsOf(s)"
                      :key="`d${i}`"
                      class="qmDot"
                      :cx="p[0] * 1600"
                      :cy="p[1] * 900"
                      r="6"
                    />
                  </template>

                  <!-- uncertain_segment：虚线 + ? 标识 -->
                  <path
                    v-else-if="s.certainty === 'uncertain_segment'"
                    class="qmRoute qmRoute--dashed"
                    :d="pathOf(s)"
                  />

                  <!-- curatorial_connector：点划线 -->
                  <path v-else class="qmRoute qmRoute--dotdash" :d="pathOf(s)" />

                  <!-- 宽命中区，便于点击区段 -->
                  <path
                    class="qmRoute qmRoute--hit"
                    :class="{ 'is-active': selectedSegmentId === s.id }"
                    :d="pathOf(s)"
                    @click="onSegmentClick(s)"
                  />
                </template>
              </g>
            </svg>

            <!-- ? 标识：不确定区段 -->
            <span
              v-for="m in uncertainMarks"
              :key="`q-${m.id}`"
              class="qm__qmark"
              :style="{ left: `${m.x}%`, top: `${m.y}%` }"
              title="路线存在不确定性"
              >?</span
            >

            <!-- 节点 -->
            <button
              v-for="n in visibleNodes"
              :key="n.id"
              class="qm__node"
              :class="[
                n.certainty === 'confirmed_region' ? 'is-confirmed' : 'is-approx',
                { 'is-active': selectedNodeId === n.id, 'is-right': n.x > 0.85 },
              ]"
              :style="{ left: `${n.x * 100}%`, top: `${n.y * 100}%` }"
              type="button"
              :aria-label="`${n.label}，${metaOf(certaintyOf(n)).zh}`"
              @click="onNodeClick(n)"
            >
              <span class="qm__node-dot" aria-hidden="true" />
              <span class="qm__node-label">{{ n.label }}</span>
            </button>

            <!-- 灰色参照节点（非当前 scope） -->
            <span
              v-for="n in contextNodes"
              :key="`ctx-${n.id}`"
              class="qm__ctxnode"
              :style="{ left: `${n.x * 100}%`, top: `${n.y * 100}%` }"
              aria-hidden="true"
              >{{ n.label }}</span
            >

            <!-- 固定免责声明常驻 -->
            <p class="qm__disclaimer">{{ FIXED_DISCLAIMER }}</p>

            <!-- 现代位置参照标注 -->
            <p class="qm__modernref">现代位置参照（淡化）</p>

            <!-- 首领行程提示：与大部众迁徙不是同一条路线 -->
            <p v-if="isLeaderScope" class="qm__separate">
              <DsIcon name="alert" :size="14" />
              首领赴承德与大部众迁徙<strong>不是同一条路线</strong>，本图层不将两者合并为一条连续路线。
            </p>

            <!-- 无地图数据 -->
            <div v-if="!hasMap" class="qm__empty">
              <DsIcon name="info" :size="15" />
              <span>迁徙路线数据正在整理中</span>
            </div>
          </div>
        </template>
      </SceneViewer>
    </div>

    <!-- ============ 侧栏：范围切换 / 图例 / 证据卡 ============ -->
    <aside class="qm__side">
      <!-- route_scope -->
      <section class="qm__block">
        <h3 class="qm__block-title">图层范围</h3>
        <div class="qm__scopes">
          <button
            v-for="s in SCOPE_META"
            :key="s.key"
            class="qm__scope"
            :class="{ 'is-on': activeScope === s.key }"
            type="button"
            @click="chooseScope(s.key)"
          >
            {{ s.label }}
          </button>
        </div>
        <p class="qm__scope-note">{{ scopeNote }}</p>
      </section>

      <!-- 固定图例 -->
      <section class="qm__block">
        <h3 class="qm__block-title">图例 · 路线可信度</h3>
        <ul class="qm__legend">
          <li v-for="l in LEGEND" :key="l.label" class="qm__legend-item">
            <span class="qm__legend-symbol" :class="`is-${l.tone}`">{{ l.symbol }}</span>
            <span class="qm__legend-label">{{ l.label }}</span>
          </li>
        </ul>
        <button class="qm__method" type="button" @click="methodOpen = !methodOpen">
          <DsIcon name="info" :size="14" />
          为什么不是 GPS？
        </button>
        <p v-if="methodOpen" class="qm__method-text">
          本图使用「归一化示意画布」坐标，不是历史 GPS 坐标，也不做里程与时间推算。
          区段的可信度直接决定绘制方式：证据不足时用虚线或廊道带表示，
          宁可只画宽带区域，也不画一条看起来精确的细线。史料之间不一致时，界面如实
          标注存在不同研究观点。
        </p>
      </section>

      <!-- 固定免责声明 -->
      <p class="qm__side-disclaimer">{{ FIXED_DISCLAIMER }}</p>

      <!-- 区段证据卡 -->
      <section v-if="selectedSegment" class="qm__card">
        <header class="qm__card-head">
          <h3 class="qm__card-title">{{ selectedSegment.label || '未命名区段' }}</h3>
          <button class="qm__card-close" type="button" aria-label="关闭" @click="selectedSegmentId = null">
            <DsIcon name="close" :size="15" />
          </button>
        </header>

        <p class="qm__card-kicker">这段路线属于：</p>
        <p class="qm__card-certainty" :class="`is-${selectedSegment.certainty}`">
          <span class="qm__legend-symbol" :class="`is-${selectedSegment.certainty}`">
            {{ metaOf(selectedSegment.certainty).symbol }}
          </span>
          {{ selectedSegment.certainty }}
          <span class="qm__card-certainty-zh">
            （{{ metaOf(selectedSegment.certainty).zh }}）
          </span>
        </p>

        <p class="qm__card-kicker">我们可以确认：</p>
        <p class="qm__card-body">
          {{ selectedSegment.evidence_note || metaOf(selectedSegment.certainty).canConfirm }}
        </p>

        <p class="qm__card-kicker">目前不在本平台声称：</p>
        <p class="qm__card-body qm__card-body--warn">{{ NOT_CLAIMED }}</p>

        <p v-if="!selectedSegment.geometry?.length" class="qm__card-body qm__card-body--muted">
          本区段在数据中没有提供几何折线。证据不足时平台宁可不给几何点，也不虚构精度。
        </p>

        <footer class="qm__card-foot">
          <button
            v-if="selectedSegment.from_node_id"
            class="qm__card-link"
            type="button"
            @click="selectedNodeId = selectedSegment.from_node_id"
          >
            查看起点节点
          </button>
          <span class="qm__card-scope">route_scope：{{ selectedSegment.route_scope }}</span>
        </footer>
      </section>

      <!-- 节点信息卡 -->
      <section v-else-if="selectedNode" class="qm__card">
        <header class="qm__card-head">
          <h3 class="qm__card-title">{{ selectedNode.label }}</h3>
          <button class="qm__card-close" type="button" aria-label="关闭" @click="selectedNodeId = null">
            <DsIcon name="close" :size="15" />
          </button>
        </header>
        <p class="qm__card-kicker">节点性质：</p>
        <p class="qm__card-body">{{ metaOf(certaintyOf(selectedNode)).zh }}</p>
        <p class="qm__card-kicker">所属图层：</p>
        <p class="qm__card-body">{{ selectedNode.route_scope }}</p>
        <p v-if="selectedNode.route_scope === 'LEADER_AUDIENCE_JOURNEY'" class="qm__card-body qm__card-body--warn">
          本节点不属于大部众迁徙终点，也不与大部众迁徙路线合并为一条连续路线。
        </p>
        <footer class="qm__card-foot">
          <button class="qm__card-link" type="button" @click="onNodeClick(selectedNode)">
            <DsIcon name="document" :size="14" />
            打开节点详情
          </button>
        </footer>
      </section>

      <!-- 默认说明 -->
      <section v-else class="qm__hint">
        <p>点击地图上的节点或路线区段，查看这一段路线可以确认到什么程度。</p>
      </section>
    </aside>
  </div>
</template>

<style scoped>
.qm {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: var(--gap-module);
  align-items: start;
}

.qm__stage {
  min-width: 0;
  display: flex;
}

/* ================= 底图 ================= */
.qmBase {
  fill: var(--color-paper-100);
}
.qmLand {
  fill: url(#qmLand);
  stroke: color-mix(in srgb, var(--chapter-accent) 34%, transparent);
  stroke-width: 1.4;
}
.qmLanda {
  stop-color: var(--color-paper-200);
  stop-opacity: 0.9;
}
.qmLanda2 {
  stop-color: var(--color-paper-100);
  stop-opacity: 0.7;
}
.qmSteppe {
  fill: color-mix(in srgb, var(--color-gold-300) 24%, transparent);
}
.qmRiver {
  fill: none;
  stroke: color-mix(in srgb, var(--color-blue-400) 60%, transparent);
  stroke-width: 2.4;
  stroke-linecap: round;
}
.qmMountain {
  fill: color-mix(in srgb, var(--chapter-accent) 26%, transparent);
}
.qmLake {
  fill: color-mix(in srgb, var(--color-blue-400) 30%, transparent);
}
.qmGrid {
  stroke: color-mix(in srgb, var(--chapter-accent) 10%, transparent);
  stroke-width: 1;
}
.qmRefLine {
  stroke: color-mix(in srgb, var(--color-ink-500) 40%, transparent);
  stroke-width: 1;
  stroke-dasharray: 4 4;
}
.qmRefDot {
  fill: color-mix(in srgb, var(--color-ink-500) 50%, transparent);
}

/* ================= 覆盖层 ================= */
.qm__overlay {
  position: absolute;
  inset: 0;
  z-index: var(--z-hud);
  pointer-events: none;
}

.qm__routes {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.qmRoute {
  fill: none;
  vector-effect: non-scaling-stroke;
  pointer-events: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}
/* 大体迁徙区段：实线宽带，不是细线 */
.qmRoute--band {
  stroke: color-mix(in srgb, var(--chapter-accent) 26%, transparent);
  stroke-width: 24;
}
.qmRoute--bandCore {
  stroke: color-mix(in srgb, var(--chapter-accent) 62%, transparent);
  stroke-width: 2.5;
}
/* 确认区域：实线 + 实心圆点 */
.qmRoute--solid {
  stroke: color-mix(in srgb, var(--chapter-accent) 55%, transparent);
  stroke-width: 9;
}
.qmDot {
  fill: var(--chapter-accent);
  pointer-events: none;
}
/* 存在不确定性：虚线 */
.qmRoute--dashed {
  stroke: var(--evidence-disputed);
  stroke-width: 3;
  stroke-dasharray: 14 10;
}
/* 策展关联：点划线 */
.qmRoute--dotdash {
  stroke: var(--evidence-curatorial);
  stroke-width: 3;
  stroke-dasharray: 14 7 3 7;
}
/* 灰色位置参照 */
.qmRoute--context {
  stroke: color-mix(in srgb, var(--color-ink-500) 34%, transparent);
  stroke-width: 6;
  stroke-dasharray: 10 8;
}
/* 命中区 */
.qmRoute--hit {
  stroke: transparent;
  stroke-width: 30;
  pointer-events: stroke;
  cursor: pointer;
}
.qmRoute--hit.is-active {
  stroke: color-mix(in srgb, var(--chapter-accent) 22%, transparent);
}

/* ---------- ? 标识 ---------- */
.qm__qmark {
  position: absolute;
  transform: translate(-50%, -140%);
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-paper-50);
  border: 1.5px solid var(--evidence-disputed);
  color: var(--evidence-disputed);
  font-size: var(--fs-caption);
  font-weight: 700;
  line-height: 1;
}

/* ---------- 节点 ---------- */
.qm__node {
  position: absolute;
  /* 圆点中心对准归一化坐标，标签向一侧延伸，避免节点位置被整体偏移 */
  transform: translate(-7px, -50%);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  pointer-events: auto;
  cursor: pointer;
  white-space: nowrap;
}
.qm__node-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex: none;
  transition:
    width var(--dur-fast) var(--ease-standard),
    height var(--dur-fast) var(--ease-standard);
}
/* confirmed_area → 实心圆点 */
.qm__node.is-confirmed .qm__node-dot {
  background: var(--chapter-accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--chapter-accent) 22%, transparent);
}
/* approximate_corridor → 空心虚线圆 */
.qm__node.is-approx .qm__node-dot {
  background: var(--color-paper-50);
  border: 2px dashed color-mix(in srgb, var(--chapter-accent) 70%, transparent);
}
.qm__node:hover .qm__node-dot,
.qm__node.is-active .qm__node-dot {
  width: 18px;
  height: 18px;
}
.qm__node-label {
  font-size: var(--fs-caption);
  color: var(--color-ink-900);
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  padding: 2px 8px;
  backdrop-filter: blur(4px);
}
/* 靠近右边缘的节点：标签翻到左侧，否则会被场景 overflow 裁掉 */
.qm__node.is-right {
  flex-direction: row-reverse;
  transform: translate(calc(-100% + 7px), -50%);
}
.qm__node.is-active .qm__node-label {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}

.qm__ctxnode {
  position: absolute;
  transform: translate(-50%, -50%);
  font-size: var(--fs-caption);
  color: color-mix(in srgb, var(--color-ink-500) 78%, transparent);
  white-space: nowrap;
}

/* ---------- 固定提示 ---------- */
.qm__disclaimer {
  position: absolute;
  left: 50%;
  top: var(--sp-3);
  transform: translateX(-50%);
  margin: 0;
  padding: 5px 14px;
  border-radius: var(--radius-pill);
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  color: var(--color-ink-700);
  font-size: var(--fs-caption);
  white-space: nowrap;
}
.qm__modernref {
  position: absolute;
  right: 136px;
  top: 76%;
  margin: 0;
  font-size: var(--fs-caption);
  color: color-mix(in srgb, var(--color-ink-500) 80%, transparent);
}
.qm__separate {
  /* 放在固定免责声明正下方居中，避开 SceneViewer 自身的左下角说明与右下角 AI 标识 */
  position: absolute;
  left: 50%;
  top: calc(var(--sp-3) + 36px);
  transform: translateX(-50%);
  max-width: 78%;
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--evidence-disputed) 16%, var(--color-paper-50));
  border: 1px solid color-mix(in srgb, var(--evidence-disputed) 45%, transparent);
  color: var(--color-ink-900);
  font-size: var(--fs-caption);
}
.qm__separate strong {
  color: var(--evidence-disputed);
}
.qm__empty {
  position: absolute;
  left: 50%;
  bottom: var(--sp-6);
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  color: var(--color-ink-700);
  font-size: var(--fs-body-s);
}

/* ================= 侧栏 ================= */
.qm__side {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  max-height: 100%;
  overflow: auto;
  padding-right: 2px;
}
.qm__block {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--sp-4);
}
.qm__block-title {
  margin: 0 0 var(--sp-3);
  font-family: var(--font-display);
  font-size: var(--fs-body);
  color: var(--color-ink-900);
}
.qm__scopes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}
.qm__scope {
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: var(--color-paper-50);
  color: var(--color-ink-700);
  font-size: var(--fs-caption);
  transition:
    background-color var(--dur-fast) var(--ease-standard),
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.qm__scope:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.qm__scope.is-on {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
  color: #fff;
}
.qm__scope-note {
  margin: var(--sp-3) 0 0;
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
}

.qm__legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.qm__legend-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
}
.qm__legend-symbol {
  flex: none;
  width: 22px;
  text-align: center;
  font-size: var(--fs-body);
  line-height: 1;
}
.qm__legend-symbol.is-confirmed,
.qm__legend-symbol.is-corridor,
.qm__legend-symbol.confirmed_area {
  color: var(--chapter-accent);
}
.qm__legend-symbol.is-approx,
.qm__legend-symbol.approximate_corridor {
  color: color-mix(in srgb, var(--chapter-accent) 60%, transparent);
}
.qm__legend-symbol.is-uncertain,
.qm__legend-symbol.uncertain_segment {
  color: var(--evidence-disputed);
}
.qm__legend-symbol.is-curatorial,
.qm__legend-symbol.curatorial_connector {
  color: var(--evidence-curatorial);
}

.qm__method {
  margin-top: var(--sp-3);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: var(--radius-btn);
  border: 1px dashed var(--color-border);
  background: transparent;
  color: var(--color-ink-500);
  font-size: var(--fs-caption);
}
.qm__method:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.qm__method-text {
  margin: var(--sp-3) 0 0;
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
}

.qm__side-disclaimer {
  margin: 0;
  padding: 7px var(--sp-3);
  border-radius: var(--radius-btn);
  background: color-mix(in srgb, var(--chapter-accent) 10%, var(--color-paper-50));
  border: 1px solid color-mix(in srgb, var(--chapter-accent) 28%, transparent);
  color: var(--color-ink-900);
  font-size: var(--fs-caption);
  text-align: center;
}

/* ---------- 证据卡 ---------- */
.qm__card {
  background: var(--color-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--sp-4);
  box-shadow: var(--shadow-card);
}
.qm__card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}
.qm__card-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--fs-body);
  line-height: var(--lh-h3);
  color: var(--color-ink-900);
}
.qm__card-close {
  border: 0;
  background: transparent;
  color: var(--color-ink-500);
  padding: 2px;
  border-radius: var(--radius-btn);
  line-height: 1;
  flex: none;
}
.qm__card-close:hover {
  background: rgba(65, 55, 42, 0.07);
  color: var(--color-ink-900);
}
.qm__card-kicker {
  margin: var(--sp-3) 0 var(--sp-1);
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.qm__card-certainty {
  margin: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--sp-2);
  font-family: var(--font-ui);
  font-size: var(--fs-body-s);
  font-weight: 600;
  color: var(--color-ink-900);
  /* 枚举值整词换行，不在词中间断开 */
  overflow-wrap: anywhere;
}
.qm__card-certainty-zh {
  flex-basis: 100%;
  font-weight: 400;
  color: var(--color-ink-500);
}
.qm__card-body {
  margin: 0;
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}
.qm__card-body--warn {
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-btn);
  background: color-mix(in srgb, var(--evidence-disputed) 12%, transparent);
  border-left: 3px solid var(--evidence-disputed);
  color: var(--color-ink-900);
}
.qm__card-body--muted {
  margin-top: var(--sp-2);
  color: var(--color-ink-500);
}
.qm__card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-top: var(--sp-4);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--color-border);
}
.qm__card-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: var(--color-paper-50);
  color: var(--color-ink-700);
  font-size: var(--fs-caption);
}
.qm__card-link:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.qm__card-scope {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  word-break: break-all;
  text-align: right;
}
.qm__hint {
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  border: 1px dashed var(--color-border);
  color: var(--color-ink-500);
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-s);
}
.qm__hint p {
  margin: 0;
}

@media (max-width: 1366px) {
  .qm {
    grid-template-columns: minmax(0, 1fr) 288px;
    gap: var(--sp-6);
  }
}
</style>
