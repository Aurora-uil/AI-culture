<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import SceneViewer from '@/components/scene/SceneViewer.vue'
import SceneHotspot from '@/components/scene/SceneHotspot.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import { useChapterStore } from '@/stores/chapter'
import type { Chapter, Hotspot, Scene } from '@/types'

/**
 * C02 唐代变体 · T02《步辇图》横向画卷 + T03 画内 / 画外人物关系透镜
 * （规格 §8 / §9，设计系统 §23.3 / §58）
 *
 * 内容红线（决定了本组件的三处关键设计）：
 *  1. **文成公主与松赞干布不在画中，绝对不给热点。**
 *     规格 §2.4 与 SCHEMA.md §2 红线：二人 `depicted_in_artwork: false`。
 *     即使内容层误把这两个 entity_id 写进 `scene.hotspots`，本组件也会强制过滤
 *     （见 OUT_OF_PAINTING）—— 宁可少一个热点，也不能让用户在画中「找到」不存在的人。
 *  2. 历史画不是现场照片（规格 §2.4）。合法历史原图存在时优先显示原图；
 *     缺图才回退矢量示意，且**不使用任何图像识别 / OCR 生成热点**（规格 §8.3）。
 *  3. 画卷只提供拖动 / 滚轮 / 键盘 / MiniMap 四种浏览方式，**不自动高速卷动**（设计系统 §58）。
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

/** 透镜开关由章节 store 持有，这里只切换、不改写其它状态 */
const chapterStore = useChapterStore()
function onToggleLens() {
  chapterStore.setLens(!props.lensOpen)
}

/** SVG 内的 id 必须全局唯一 */
const uid = Math.random().toString(36).slice(2, 9)

/* ---------------------------------------------------------------- 画卷尺寸 */

const viewportEl = ref<HTMLElement | null>(null)
const vpW = ref(960)
const vpH = ref(520)

/**
 * 整幅画卷宽度 = max(视窗宽 × 1.7, 视窗高 × 原图比例)。
 * 当前公版数字图像为 3053 × 853；1.7 保证画卷始终明显宽于视窗，
 * 一定有可拖动的余量（MiniMap 才有意义），同时不把画面拉得过于稀疏。
 */
const ORIGINAL_RATIO = 3053 / 853
const trackW = computed(() => Math.round(Math.max(vpW.value * 1.7, vpH.value * ORIGINAL_RATIO)))

const hasHistoricalOriginal = computed(() => !!props.scene?.background_asset_id)

/** 人物按**高度**统一缩放 —— 无论视窗宽高比如何，人物都不会被拉扁 */
function sc(rel: number): number {
  return (rel * vpH.value) / 200
}
/** 归一化横坐标（占整幅画卷 0–1）→ 像素 */
function fx(frac: number): number {
  return frac * trackW.value
}
/** 归一化纵坐标 → 像素 */
function fy(frac: number): number {
  return frac * vpH.value
}

/* ---------------------------------------------------------------- 滚动状态 */

const scrollLeft = ref(0)
const maxScroll = ref(1)
const smooth = ref(false)

function readScroll() {
  const el = viewportEl.value
  if (!el) return
  scrollLeft.value = el.scrollLeft
  maxScroll.value = Math.max(1, el.scrollWidth - el.clientWidth)
}

let ro: ResizeObserver | null = null

function measure() {
  const el = viewportEl.value
  if (!el) return
  if (el.clientWidth > 10) vpW.value = el.clientWidth
  if (el.clientHeight > 10) vpH.value = el.clientHeight
  requestAnimationFrame(readScroll)
}

onMounted(() => {
  measure()
  ro = new ResizeObserver(measure)
  if (viewportEl.value) ro.observe(viewportEl.value)
})
onBeforeUnmount(() => ro?.disconnect())

/* ---------------------------------------------------------------- 拖动 / 滚轮 / 键盘 */

const dragging = ref(false)
let dragStartX = 0
let dragStartScroll = 0
let movedPx = 0

function onPointerDown(e: PointerEvent) {
  const el = viewportEl.value
  if (!el || e.button !== 0) return
  dragging.value = true
  movedPx = 0
  dragStartX = e.clientX
  dragStartScroll = el.scrollLeft
  el.setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  const el = viewportEl.value
  if (!el || !dragging.value) return
  const dx = e.clientX - dragStartX
  movedPx = Math.max(movedPx, Math.abs(dx))
  el.scrollLeft = dragStartScroll - dx
  readScroll()
}

function onPointerUp(e: PointerEvent) {
  const el = viewportEl.value
  dragging.value = false
  if (el && el.hasPointerCapture(e.pointerId)) el.releasePointerCapture(e.pointerId)
}

/** 滚轮 → 横向平移。纵向滚轮也翻译成横向，符合手卷的浏览直觉。 */
function onWheel(e: WheelEvent) {
  const el = viewportEl.value
  if (!el) return
  const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
  el.scrollLeft += delta
  readScroll()
}

function withSmooth(fn: () => void) {
  smooth.value = true
  fn()
  readScroll()
  window.setTimeout(() => (smooth.value = false), 320)
}

function onKeydown(e: KeyboardEvent) {
  const el = viewportEl.value
  if (!el) return
  const step = e.shiftKey ? 480 : 160
  if (e.key === 'ArrowLeft') withSmooth(() => (el.scrollLeft -= step))
  else if (e.key === 'ArrowRight') withSmooth(() => (el.scrollLeft += step))
  else if (e.key === 'Home') withSmooth(() => (el.scrollLeft = 0))
  else if (e.key === 'End') withSmooth(() => (el.scrollLeft = el.scrollWidth))
  else return
  e.preventDefault()
}

function nudge(dir: number) {
  const el = viewportEl.value
  if (!el) return
  withSmooth(() => (el.scrollLeft += dir * el.clientWidth * 0.7))
}

/** MiniMap 跳转：把点击位置居中到视窗 */
function jumpTo(frac: number) {
  const el = viewportEl.value
  if (!el) return
  withSmooth(() => (el.scrollLeft = frac * el.scrollWidth - el.clientWidth / 2))
}

const miniWin = computed(() => {
  const total = trackW.value
  const width = Math.min(1, vpW.value / total)
  const left = Math.min(1 - width, Math.max(0, scrollLeft.value / total))
  return { leftPct: left * 100, widthPct: width * 100 }
})

function onMiniClick(e: MouseEvent) {
  const r = (e.currentTarget as HTMLElement).getBoundingClientRect()
  jumpTo(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)))
}

/* ---------------------------------------------------------------- 热点 */

/**
 * 内容红线：这两个人物不在《步辇图》画面中（规格 §2.4、SCHEMA.md §2）。
 * 若内容层误将其写入 scene.json，这里强制过滤 ——
 * 宁可不显示，也不能让用户以为文成公主或松赞干布被画进了画卷。
 */
const OUT_OF_PAINTING = new Set(['person_princess_wencheng', 'person_songtsen_gampo'])

/** 整幅兜底热点（覆盖 0–1）不能进入热点层，否则会挡住拖动与所有点击 */
function isWholeCanvas(h: Hotspot): boolean {
  const pts = h.normalized_points as number[][]
  if (!Array.isArray(pts) || !pts.length || typeof pts[0] === 'number') return false
  const xs = pts.map((p) => p[0])
  const ys = pts.map((p) => p[1])
  return Math.max(...xs) - Math.min(...xs) > 0.95 && Math.max(...ys) - Math.min(...ys) > 0.95
}

const allHotspots = computed(() => props.scene?.hotspots ?? [])
const paintHotspots = computed(() =>
  allHotspots.value.filter((h) => !isWholeCanvas(h) && !OUT_OF_PAINTING.has(h.entity_id)),
)
/** 作品本体热点：点击空白画心时的兜底命中项（规格 §8.4，最低点击优先级） */
const artworkHotspot = computed(() => allHotspots.value.find((h) => isWholeCanvas(h)) ?? null)

function statusOf(h: Hotspot) {
  return props.hotspotStatus[h.id] ?? 'UNSEEN'
}

/** 透镜开启且已选中某人时，其余热点弱化（规格 §9.2） */
function isDimmed(h: Hotspot) {
  if (!props.lensOpen || !props.selectedEntityId) return false
  return h.entity_id !== props.selectedEntityId
}

/** 热点横坐标（取质心），用于 MiniMap 刻度 */
function hCenter(h: Hotspot): number {
  const pts = h.normalized_points
  if (!Array.isArray(pts) || !pts.length) return 0.5
  if (typeof pts[0] === 'number') return (pts as number[])[0] ?? 0.5
  const arr = pts as number[][]
  return arr.reduce((s, p) => s + (p[0] ?? 0), 0) / arr.length
}

/** 人物标签落在热点下沿，避免盖住人物轮廓 */
function labelStyle(h: Hotspot): Record<string, string> {
  const pts = h.normalized_points
  let x = hCenter(h)
  let yBottom = 0.5
  if (Array.isArray(pts) && pts.length && typeof pts[0] !== 'number') {
    yBottom = Math.max(...(pts as number[][]).map((p) => p[1] ?? 0))
  } else if (Array.isArray(pts) && typeof pts[0] === 'number') {
    yBottom = (pts as number[])[1] ?? 0.5
  }
  return {
    left: `${x * 100}%`,
    top: `calc(${Math.min(1, yBottom) * 100}% + 16px)`,
  }
}

function onBackdropClick() {
  // 拖拽之后不触发点击；点击空白画心落到「作品本体」，而不是无响应
  if (movedPx > 6) return
  if (artworkHotspot.value) emit('select-hotspot', artworkHotspot.value)
}

/* ---------------------------------------------------------------- 画外关系（T03） */

const relationOpen = ref(false)
const eventLineOpen = ref(false)

interface ChainNode {
  id: string
  label: string
  tag: 'IN_ARTWORK' | 'OUTSIDE_ARTWORK' | 'EVENT'
  depth: number
  via?: string
}

/**
 * 画外关系展开链（规格 §9.5 的三层结构，默认最多 3 层）。
 * 文成公主只出现在第三层，经由「禄东赞 → 使节活动 → 641 年事件」展开 ——
 * 这正是那条内容红线的产品化表达。
 */
const CHAIN: ChainNode[] = [
  { id: 'person_ludongzan', label: '禄东赞', tag: 'IN_ARTWORK', depth: 0 },
  { id: 'person_songtsen_gampo', label: '松赞干布', tag: 'OUTSIDE_ARTWORK', depth: 1, via: '奉命 / 代表' },
  { id: 'concept_diplomatic_mission', label: '唐蕃使节活动', tag: 'EVENT', depth: 1, via: '参与' },
  { id: 'event_tang_tubo_envoy_634', label: '唐蕃互遣使节（634）', tag: 'EVENT', depth: 2, via: '发生在' },
  { id: 'event_tang_tubo_marriage_641', label: '641 年唐蕃婚姻事件', tag: 'EVENT', depth: 2, via: '关联' },
  { id: 'person_princess_wencheng', label: '文成公主', tag: 'OUTSIDE_ARTWORK', depth: 3, via: '经由 641 年事件展开' },
  { id: 'place_changan', label: '长安', tag: 'OUTSIDE_ARTWORK', depth: 3, via: '事件发生地' },
]

const TAG_LABEL: Record<ChainNode['tag'], string> = {
  IN_ARTWORK: '画中可见',
  OUTSIDE_ARTWORK: '画外关联',
  EVENT: '历史事件',
}

/** 事件线：只列出内容层已建立的实体，不在前端新增年代判断 */
const EVENTS: { id: string; label: string; note: string }[] = [
  { id: 'event_tang_tubo_envoy_634', label: '唐蕃互遣使节', note: '内容层已建立的事件实体' },
  { id: 'event_taizong_receives_ludongzan', label: '唐太宗接见禄东赞', note: '即本画卷所描绘的场景' },
  { id: 'event_tang_tubo_marriage_641', label: '唐蕃婚姻事件', note: '文成公主经由该事件进入叙事' },
  { id: 'event_princess_wencheng_journey', label: '文成公主入吐蕃行程', note: '发生在画面之外' },
]

const selectedLabel = computed(() => {
  const hit = paintHotspots.value.find((h) => h.entity_id === props.selectedEntityId)
  return hit?.label ?? null
})

/* ---------------------------------------------------------------- 画卷示意图形 */

interface FigureVM {
  key: string
  kind: 'standing' | 'seated' | 'fan' | 'canopy'
  nx: number
  /** 立足基准线（占整幅高度的 0–1） */
  by: number
  hRel: number
  tone: number
}

/**
 * 人物布局。nx 与 scene.json 里人工预标注的热点横坐标大致对应：
 * 宫女 0.04–0.37 / 唐太宗 0.23–0.38 / 内官 0.48–0.58 / 禄东赞 0.60–0.71 / 引见官员 0.83–0.94。
 * 只画示意轮廓，不追求写实，也**不复制原画**。
 */
const FIGURES: FigureVM[] = [
  { key: 'pw1', kind: 'standing', nx: 0.075, by: 0.93, hRel: 0.68, tone: 0.6 },
  { key: 'pw2', kind: 'standing', nx: 0.118, by: 0.95, hRel: 0.74, tone: 0.55 },
  { key: 'pw3', kind: 'standing', nx: 0.16, by: 0.88, hRel: 0.56, tone: 0.36 },
  { key: 'fan1', kind: 'fan', nx: 0.205, by: 0.96, hRel: 0.9, tone: 0.55 },
  { key: 'canopy', kind: 'canopy', nx: 0.328, by: 0.95, hRel: 0.88, tone: 0.45 },
  { key: 'taizong', kind: 'seated', nx: 0.3, by: 0.74, hRel: 0.54, tone: 0.95 },
  { key: 'pw4', kind: 'standing', nx: 0.355, by: 0.95, hRel: 0.72, tone: 0.55 },
  { key: 'pw5', kind: 'standing', nx: 0.386, by: 0.88, hRel: 0.56, tone: 0.36 },
  { key: 'fan2', kind: 'fan', nx: 0.428, by: 0.96, hRel: 0.84, tone: 0.55 },
  { key: 'neiguan', kind: 'standing', nx: 0.53, by: 0.87, hRel: 0.62, tone: 0.85 },
  { key: 'ludongzan', kind: 'standing', nx: 0.655, by: 0.88, hRel: 0.64, tone: 1 },
  { key: 'official', kind: 'standing', nx: 0.885, by: 0.9, hRel: 0.68, tone: 0.95 },
]

/** 画心上的淡横线，避免大面积死白 */
const groundLines = computed(() => {
  const out: { y: number; o: number }[] = []
  for (let i = 0; i < 5; i++) out.push({ y: fy(0.945 + i * 0.012), o: 0.12 - i * 0.02 })
  return out
})
</script>

<template>
  <div class="tang">
    <!-- 右上角工具（设计系统 §23.3） -->
    <header class="tang__bar">
      <span class="tang__now">
        {{ selectedLabel ? `当前聚焦：${selectedLabel}` : '← 拖动画卷，找出画面里的每一个人' }}
      </span>
      <div class="tang__tools">
        <button type="button" class="tang__tool" :class="{ 'is-on': lensOpen }" @click="onToggleLens">
          <DsIcon name="person" :size="14" />人物透镜
        </button>
        <button
          type="button"
          class="tang__tool"
          :class="{ 'is-on': relationOpen }"
          @click="relationOpen = !relationOpen"
        >
          <DsIcon name="nodes" :size="14" />画外关系
        </button>
        <button
          type="button"
          class="tang__tool"
          :class="{ 'is-on': eventLineOpen }"
          @click="eventLineOpen = !eventLineOpen"
        >
          <DsIcon name="text" :size="14" />事件线
        </button>
      </div>
    </header>

    <div class="tang__body">
      <div class="tang__stage">
        <!-- 画卷视窗：拖动 / 滚轮 / 键盘三种平移方式 -->
        <div
          ref="viewportEl"
          class="tang__viewport"
          :class="{ 'is-drag': dragging, 'is-smooth': smooth }"
          tabindex="0"
          role="region"
          aria-label="《步辇图》横向画卷，可拖动、滚轮或用左右方向键平移"
          @scroll="readScroll"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointercancel="onPointerUp"
          @wheel.prevent="onWheel"
          @keydown="onKeydown"
        >
          <div class="tang__track" :style="{ width: `${trackW}px`, height: `${vpH}px` }">
            <SceneViewer
              :scene="{
                ...(scene ?? {
                  id: 'tang_scroll_fallback',
                  name: '《步辇图》横向画卷',
                  scene_kind: 'image',
                }),
                // 历史原图优先；资源缺失或加载失败时才进入 SVG 回退。
                background_asset_id: scene?.background_asset_id ?? null,
                // 免责声明在底部统一显示一次，不叠在画面上
                disclaimer: null,
                hotspots: [],
              }"
              chapter-slug="tang"
              aspect="auto"
              image-fit="contain"
              source-label="历史原图 · 《步辇图》（故宫博物院藏）"
              source-url="https://commons.wikimedia.org/wiki/File:Buliantu.jpg"
            >
              <template #background>
                <svg :viewBox="`0 0 ${trackW} ${vpH}`" preserveAspectRatio="none" class="tang__svg">
                  <defs>
                    <linearGradient :id="`tang-silk-${uid}`" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="var(--color-paper-100)" />
                      <stop offset="100%" stop-color="var(--color-paper-200)" />
                    </linearGradient>

                    <!-- 立姿人物：局部坐标 (0,0) 为足下，向上一共 200 单位。
                         这里用 g 而不是 symbol：symbol 自带 viewBox，
                         会让 use 建立一个巨大的嵌套视口，人物被缩放并挤出画外。 -->
                    <g :id="`tang-standing-${uid}`">
                      <path d="M-11 -190 h22 v-15 h-22 Z" fill="var(--chapter-accent)" opacity="0.35" />
                      <circle cx="0" cy="-176" r="14" fill="var(--chapter-accent)" opacity="0.22" stroke="var(--chapter-accent)" stroke-width="1.5" />
                      <path d="M-24 0 L-17 -118 Q0 -140 17 -118 L24 0 Z" fill="var(--chapter-accent)" opacity="0.16" stroke="var(--chapter-accent)" stroke-width="1.6" stroke-linejoin="round" />
                      <path d="M-17 -110 L-40 -56 L-30 -48 L-14 -96" fill="var(--chapter-accent)" opacity="0.12" stroke="var(--chapter-accent)" stroke-width="1.3" />
                      <path d="M17 -110 L40 -56 L30 -48 L14 -96" fill="var(--chapter-accent)" opacity="0.12" stroke="var(--chapter-accent)" stroke-width="1.3" />
                      <path d="M-18 -74 Q0 -70 18 -74" fill="none" stroke="var(--chapter-accent)" stroke-width="1.2" opacity="0.55" />
                    </g>

                    <!-- 坐姿人物（唐太宗于步辇之上） -->
                    <g :id="`tang-seated-${uid}`">
                      <path d="M-13 -146 h26 v-16 h-26 Z" fill="var(--chapter-accent)" opacity="0.4" />
                      <circle cx="0" cy="-130" r="16" fill="var(--chapter-accent)" opacity="0.24" stroke="var(--chapter-accent)" stroke-width="1.6" />
                      <path d="M-34 -58 Q-28 -108 0 -118 Q28 -108 34 -58 Z" fill="var(--chapter-accent)" opacity="0.18" stroke="var(--chapter-accent)" stroke-width="1.6" stroke-linejoin="round" />
                      <path d="M-42 -58 Q0 -44 42 -58 L36 -30 Q0 -18 -36 -30 Z" fill="var(--chapter-accent)" opacity="0.13" stroke="var(--chapter-accent)" stroke-width="1.4" stroke-linejoin="round" />
                      <path d="M-20 -84 Q0 -76 20 -84" fill="none" stroke="var(--chapter-accent)" stroke-width="1.2" opacity="0.5" />
                    </g>

                    <!-- 掌扇：长柄团扇 -->
                    <g :id="`tang-fan-${uid}`">
                      <line x1="0" y1="0" x2="0" y2="-120" stroke="var(--chapter-accent)" stroke-width="2" opacity="0.6" />
                      <ellipse cx="0" cy="-152" rx="27" ry="34" fill="var(--chapter-accent)" opacity="0.13" stroke="var(--chapter-accent)" stroke-width="1.5" />
                      <ellipse cx="0" cy="-152" rx="16" ry="21" fill="none" stroke="var(--chapter-accent)" stroke-width="0.9" opacity="0.45" />
                    </g>

                    <!-- 华盖：伞盖 + 长柄 -->
                    <g :id="`tang-canopy-${uid}`">
                      <line x1="0" y1="0" x2="0" y2="-150" stroke="var(--chapter-accent)" stroke-width="2" opacity="0.55" />
                      <path d="M-62 -150 Q0 -196 62 -150 Z" fill="var(--chapter-accent)" opacity="0.13" stroke="var(--chapter-accent)" stroke-width="1.5" stroke-linejoin="round" />
                      <path d="M-62 -150 Q-40 -140 -22 -150 Q-8 -140 8 -150 Q26 -140 44 -150" fill="none" stroke="var(--chapter-accent)" stroke-width="1.1" opacity="0.5" />
                    </g>
                  </defs>

                  <!-- 绢本底色 -->
                  <rect :width="trackW" :height="vpH" :fill="`url(#tang-silk-${uid})`" />

                  <!-- 画心淡横线 -->
                  <line
                    v-for="(g, i) in groundLines"
                    :key="`gl-${i}`"
                    x1="0"
                    :y1="g.y"
                    :x2="trackW"
                    :y2="g.y"
                    stroke="var(--chapter-accent)"
                    stroke-width="1"
                    :opacity="g.o"
                  />

                  <!-- 步辇：唐太宗所坐的抬辇平台（示意，不追求器物细部） -->
                  <g opacity="0.75">
                    <rect
                      :x="fx(0.246)"
                      :y="fy(0.745)"
                      :width="fx(0.118)"
                      :height="fy(0.042)"
                      rx="3"
                      fill="var(--chapter-accent)"
                      opacity="0.14"
                      stroke="var(--chapter-accent)"
                      stroke-width="1.4"
                    />
                    <!-- 抬辇的两根长杆 -->
                    <line :x1="fx(0.14)" :y1="fy(0.766)" :x2="fx(0.44)" :y2="fy(0.766)" stroke="var(--chapter-accent)" stroke-width="2.2" opacity="0.45" />
                    <!-- 辇座下的短足 -->
                    <line :x1="fx(0.27)" :y1="fy(0.787)" :x2="fx(0.27)" :y2="fy(0.815)" stroke="var(--chapter-accent)" stroke-width="1.6" opacity="0.4" />
                    <line :x1="fx(0.34)" :y1="fy(0.787)" :x2="fx(0.34)" :y2="fy(0.815)" stroke="var(--chapter-accent)" stroke-width="1.6" opacity="0.4" />
                  </g>

                  <!-- 人物层 -->
                  <use
                    v-for="f in FIGURES"
                    :key="f.key"
                    :href="`#tang-${f.kind}-${uid}`"
                    :opacity="f.tone"
                    :transform="`translate(${fx(f.nx)} ${fy(f.by)}) scale(${sc(f.hRel)})`"
                  />
                </svg>
              </template>

              <!-- 热点层：坐标相对**整幅画卷**的 0–1，随 track 一起平移 -->
              <template #overlay>
                <div class="tang__paint" @click="onBackdropClick">
                  <SceneHotspot
                    v-for="h in paintHotspots"
                    :key="h.id"
                    :hotspot="h"
                    :status="statusOf(h)"
                    :class="{ 'is-dimmed': isDimmed(h) }"
                    @select="emit('select-hotspot', $event)"
                  />
                  <span
                    v-for="h in paintHotspots"
                    :key="`lb-${h.id}`"
                    class="tang__lb"
                    :class="{ 'is-dim': isDimmed(h) }"
                    :style="labelStyle(h)"
                  >
                    {{ h.label || h.entity_id }}
                  </span>

                  <!-- 固定证据边界：即使使用原图，历史画也不等同于现场照片。 -->
                  <span class="tang__ai">
                    {{ hasHistoricalOriginal ? '历史画原图 · 不等同于现场照片' : 'AI辅助历史场景示意，非原画复制' }}
                  </span>
                </div>
              </template>
            </SceneViewer>
          </div>
        </div>

        <!-- 底部：MiniMap（设计系统 §58） -->
        <div class="tang__foot">
          <button type="button" class="tang__nav" aria-label="向左平移" @click="nudge(-1)">
            <DsIcon name="arrow-left" :size="14" />
          </button>
          <div
            class="tang__mini"
            role="scrollbar"
            aria-label="画卷导航缩略条"
            :aria-valuenow="Math.round((scrollLeft / maxScroll) * 100)"
            aria-valuemin="0"
            aria-valuemax="100"
            tabindex="0"
            @click="onMiniClick"
          >
            <span class="tang__mini-rail" />
            <span
              v-for="h in paintHotspots"
              :key="`mk-${h.id}`"
              class="tang__mini-tick"
              :class="{ 'is-on': h.entity_id === selectedEntityId }"
              :style="{ left: `${hCenter(h) * 100}%` }"
            />
            <span class="tang__mini-win" :style="{ left: `${miniWin.leftPct}%`, width: `${miniWin.widthPct}%` }" />
          </div>
          <button type="button" class="tang__nav" aria-label="向右平移" @click="nudge(1)">
            <DsIcon name="arrow-right" :size="14" />
          </button>
          <span class="tang__hint">拖动 / 滚轮 / ← → 键平移 · 不自动滚动</span>
        </div>

        <!-- 事件线（手动展开，不自动播放） -->
        <ol v-if="eventLineOpen" class="tang__events">
          <li v-for="(ev, i) in EVENTS" :key="ev.id" class="tang__event">
            <span class="tang__event-idx">{{ i + 1 }}</span>
            <button type="button" class="tang__event-btn" @click="emit('select-entity', ev.id)">
              {{ ev.label }}
            </button>
            <span class="tang__event-note">{{ ev.note }}</span>
          </li>
        </ol>
      </div>

      <!-- 画外关系侧栏（T03） -->
      <aside v-if="relationOpen" class="tang__rel">
        <header class="tang__rel-head">
          <span>画外关系</span>
          <button type="button" class="tang__rel-close" aria-label="关闭画外关系" @click="relationOpen = false">
            <DsIcon name="close" :size="14" />
          </button>
        </header>

        <!-- 固定知识卡（规格 §9.4，文案不得改写） -->
        <section class="tang__card">
          <h4 class="tang__card-title">为什么文成公主不在画里？</h4>
          <p class="tang__card-text">
            《步辇图》描绘的核心场景是唐太宗接见吐蕃使臣禄东赞。文成公主是与这次唐蕃婚姻事件相关的重要历史人物，但不是画面中被描绘的核心人物。因此平台通过「禄东赞 → 历史事件 → 文成公主」展开她，而不是在画中人为增加不存在的热点。
          </p>
        </section>

        <ol class="tang__chain">
          <li
            v-for="n in CHAIN"
            :key="n.id"
            class="tang__chain-item"
            :class="[`d${n.depth}`, { 'is-sel': n.id === selectedEntityId }]"
          >
            <span class="tang__chain-tag" :class="`tag-${n.tag.toLowerCase()}`">{{ TAG_LABEL[n.tag] }}</span>
            <button type="button" class="tang__chain-btn" @click="emit('select-entity', n.id)">
              {{ n.label }}
            </button>
            <span v-if="n.via" class="tang__chain-via">{{ n.via }}</span>
          </li>
        </ol>

        <div class="tang__rel-actions">
          <button type="button" class="tang__rel-act" @click="emit('open-graph', 'person_ludongzan')">
            <DsIcon name="nodes" :size="13" />看关系图谱
          </button>
          <button type="button" class="tang__rel-act" @click="emit('open-chat', 'person_ludongzan')">
            <DsIcon name="sparkle" :size="13" />向禄东赞提问
          </button>
        </div>
      </aside>
    </div>

    <!-- 场景免责声明 -->
    <p class="tang__disc">
      <span>画面为矢量示意，不是《步辇图》原作的复制，也不代表考古意义上的精确复原。</span>
      <span v-if="scene?.disclaimer">{{ scene.disclaimer }}</span>
      <span v-else class="tang__disc-flag">场景数据尚未接入，当前显示的是示意画心。</span>
    </p>
  </div>
</template>

<style scoped>
.tang {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  min-height: 0;
}

/* ---------- 工具条 ---------- */
.tang__bar {
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--sp-4);
}
.tang__now {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  min-width: 0;
}
.tang__tools {
  margin-left: auto;
  display: flex;
  gap: var(--sp-2);
  flex: none;
}
.tang__tool {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 13px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard),
    background-color var(--dur-fast) var(--ease-standard);
}
.tang__tool:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.tang__tool.is-on {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
  color: #fff;
}

/* ---------- 主体 ---------- */
.tang__body {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: var(--sp-4);
}
.tang__stage {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

/* ---------- 画卷视窗 ---------- */
.tang__viewport {
  flex: 1;
  min-height: 0;
  overflow-x: auto;
  overflow-y: hidden;
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: var(--color-paper-100);
  cursor: grab;
  user-select: none;
  outline: none;
  /* 滚动条由底部 MiniMap 取代 */
  scrollbar-width: none;
}
.tang__viewport::-webkit-scrollbar {
  display: none;
}
.tang__viewport.is-drag {
  cursor: grabbing;
}
.tang__viewport:focus-visible {
  border-color: var(--chapter-accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--chapter-accent) 25%, transparent);
}
/* 只有键盘 / MiniMap 跳转才使用平滑滚动，拖动时必须是 1:1 跟手 */
.tang__viewport.is-smooth {
  scroll-behavior: smooth;
}

.tang__track {
  position: relative;
}
.tang__track :deep(.scene) {
  height: 100%;
}
.tang__svg {
  width: 100%;
  height: 100%;
  display: block;
}

.tang__paint {
  position: absolute;
  inset: 0;
}

.tang__lb {
  position: absolute;
  transform: translateX(-50%);
  font-size: var(--fs-caption);
  color: var(--color-ink-900);
  background: rgba(250, 248, 242, 0.86);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  padding: 1px 9px;
  white-space: nowrap;
  pointer-events: none;
  transition: opacity var(--dur-normal) var(--ease-standard);
}
.tang__lb.is-dim {
  opacity: 0.25;
}

/* 画面固定标识 */
.tang__ai {
  position: absolute;
  left: var(--sp-3);
  bottom: var(--sp-3);
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
  background: rgba(250, 248, 242, 0.86);
  border: 1px solid var(--color-border);
}

/* ---------- MiniMap ---------- */
.tang__foot {
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}
.tang__nav {
  flex: none;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-ink-700);
}
.tang__nav:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.tang__mini {
  position: relative;
  flex: 1;
  min-width: 0;
  height: 20px;
  cursor: pointer;
}
.tang__mini-rail {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 2px;
  transform: translateY(-50%);
  background: var(--color-border);
  border-radius: var(--radius-pill);
}
.tang__mini-win {
  position: absolute;
  top: 3px;
  height: 14px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--chapter-accent) 22%, transparent);
  border: 1px solid var(--chapter-accent);
  transition:
    left var(--dur-fast) linear,
    width var(--dur-fast) linear;
}
.tang__mini-tick {
  position: absolute;
  top: 50%;
  width: 5px;
  height: 5px;
  margin: -2.5px 0 0 -2.5px;
  border-radius: 50%;
  background: var(--color-ink-500);
  opacity: 0.6;
}
.tang__mini-tick.is-on {
  background: var(--chapter-accent);
  opacity: 1;
}
.tang__hint {
  flex: none;
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

/* ---------- 事件线 ---------- */
.tang__events {
  flex: none;
  display: flex;
  gap: var(--sp-3);
  overflow-x: auto;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: var(--color-paper-100);
}
.tang__event {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: none;
  font-size: var(--fs-caption);
}
.tang__event-idx {
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--chapter-accent);
  color: #fff;
  font-size: 10px;
}
.tang__event-btn {
  border: 0;
  background: transparent;
  font-size: var(--fs-caption);
  font-weight: 600;
  color: var(--color-ink-900);
  padding: 0;
}
.tang__event-btn:hover {
  color: var(--chapter-accent);
}
.tang__event-note {
  color: var(--color-ink-500);
}

/* ---------- 画外关系侧栏 ---------- */
.tang__rel {
  width: 320px;
  flex: none;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  overflow-y: auto;
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: var(--color-panel);
  box-shadow: var(--shadow-card);
}
.tang__rel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--fs-h3);
  font-family: var(--font-display);
  color: var(--chapter-accent);
}
.tang__rel-close {
  border: 0;
  background: transparent;
  color: var(--color-ink-500);
  display: grid;
  place-items: center;
}
.tang__rel-close:hover {
  color: var(--color-ink-900);
}

.tang__card {
  padding: var(--sp-3);
  border-radius: var(--radius-card);
  border: 1px solid color-mix(in srgb, var(--chapter-accent) 30%, transparent);
  background: color-mix(in srgb, var(--chapter-accent) 7%, transparent);
}
.tang__card-title {
  font-size: var(--fs-body-s);
  font-weight: 600;
  color: var(--chapter-accent);
  margin-bottom: 6px;
}
.tang__card-text {
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}

.tang__chain {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tang__chain-item {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding-left: calc(var(--d, 0) * 14px);
  border-left: 1px dashed var(--color-border);
  margin-left: calc(var(--d, 0) * 6px);
  padding-top: 3px;
  padding-bottom: 3px;
}
.tang__chain-item.d0 {
  --d: 0;
}
.tang__chain-item.d1 {
  --d: 1;
}
.tang__chain-item.d2 {
  --d: 2;
}
.tang__chain-item.d3 {
  --d: 3;
  border-left-style: solid;
  border-left-color: var(--chapter-accent);
}
.tang__chain-item.is-sel .tang__chain-btn {
  color: var(--chapter-accent);
  font-weight: 600;
}
.tang__chain-tag {
  flex: none;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-pill);
  border: 1px solid currentColor;
}
.tag-in_artwork {
  color: var(--chapter-accent);
}
.tag-outside_artwork {
  color: var(--evidence-curatorial);
}
.tag-event {
  color: var(--evidence-fact);
}
.tang__chain-btn {
  border: 0;
  background: transparent;
  padding: 0;
  font-size: var(--fs-body-s);
  color: var(--color-ink-900);
}
.tang__chain-btn:hover {
  color: var(--chapter-accent);
}
.tang__chain-via {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.tang__chain-via::before {
  content: '← ';
}

.tang__rel-actions {
  display: flex;
  gap: var(--sp-2);
  margin-top: auto;
}
.tang__rel-act {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
}
.tang__rel-act:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}

/* ---------- 底部说明 ---------- */
.tang__disc {
  flex: none;
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
}
.tang__disc-flag {
  color: var(--evidence-disputed);
}

@media (max-width: 1366px) {
  .tang__rel {
    width: 272px;
  }
}
/* 队员二：390×844适配 */
@media (max-width: 900px) {
  .tang__body { flex-direction: column; }
  .tang__rel { width: 100%; max-height: 300px; }
  .tang__hint { display: none; }
  .tang__tool { min-height: 44px; }
}
</style>
