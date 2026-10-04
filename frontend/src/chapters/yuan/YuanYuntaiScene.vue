<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import SceneViewer from '@/components/scene/SceneViewer.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import type { Chapter, Hotspot, Scene } from '@/types'

/**
 * 元代 Y02 云台主场景 + Y03 六体文字透镜（规格 §8 / §9）
 *
 * 内容红线相关的设计决策（对应 §2.2 / §2.3 / §32 与 extra.content_red_lines）：
 *
 * 1. 界面统一表述为「六种书写系统的题刻」，绝不写成「六个民族的六种语言」。
 *    Script（书写系统）/ Language（语言）/ Text（文本）/ Inscription（题刻）
 *    在数据与文案里始终分开，不做一一对应。
 * 2. 六处文字区域全部来自 `scene.hotspots` 的预先标注多边形，
 *    不做摄像头识别、不做 OCR、不做拍照识古文字、不做实时翻译。
 * 3. 「为什么是六体？」为固定知识卡，只陈述可确认事实与「不做什么」，
 *    不给任何一处题刻绑定单一民族标签，也不输出任何碑文释读。
 * 4. 券顶 / 石雕是场景构造热点，与「六体文字」分开统计，避免把六处题刻
 *    说成「这个空间里只有六样东西」。
 * 5. 佛教造像只说明「存在有公开资料支持的石雕」，不给定名、不编造寓意。
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
   画布坐标：SceneViewer 固定 16 / 9，这里用 1600 × 900 的 viewBox，
   preserveAspectRatio="none" 让 0–1 归一化热点坐标可以直接换算，
   SVG 矢量场景与热点层永远对齐（替换真实影像时也不需要改坐标）。
   ------------------------------------------------------------------ */
const VB_W = 1600
const VB_H = 900

const hotspots = computed<Hotspot[]>(() => {
  const base: Hotspot[] = props.scene?.hotspots ?? []
  try {
    const raw = localStorage.getItem('tongxin.yuan.hotspots.debug.v1')
    if (!raw) return base
    const over = JSON.parse(raw) as Record<string, number[][]>
    return base.map((h) => (over[h.id] ? { ...h, normalized_points: over[h.id] } : h))
  } catch { return base }
})
const hasHotspots = computed(() => hotspots.value.length > 0)

/** 券顶与石雕属于空间构造热点，不计入「六体文字」的进度与透镜区域 */
const NON_SCRIPT_LABELS = ['券顶', '石雕']

const scriptHotspots = computed<Hotspot[]>(() => {
  const list = hotspots.value
  const byPrefix = list.filter((h) => h.entity_id.startsWith('script_'))
  if (byPrefix.length) return byPrefix
  // 兜底：内容侧若调整 entity_id 命名，用标签排除「券顶 / 石雕」仍然可用
  return list.filter((h) => !NON_SCRIPT_LABELS.includes(h.label ?? ''))
})

const scriptTotal = computed(() => scriptHotspots.value.length)

function statusOf(h: Hotspot): 'UNSEEN' | 'SEEN' | 'SELECTED' {
  if (props.selectedEntityId && props.selectedEntityId === h.entity_id) return 'SELECTED'
  return props.hotspotStatus[h.id] ?? 'UNSEEN'
}

function isSeen(h: Hotspot): boolean {
  const s = statusOf(h)
  return s === 'SEEN' || s === 'SELECTED'
}

const seenScriptCount = computed(() => scriptHotspots.value.filter(isSeen).length)

/* ---------------- 几何换算 ---------------- */

function polyPath(pts: number[][]): string {
  return (
    pts
      .map((p, i) => `${i === 0 ? 'M' : 'L'}${(p[0] * VB_W).toFixed(1)} ${(p[1] * VB_H).toFixed(1)}`)
      .join(' ') + ' Z'
  )
}

/** point 形态热点没有多边形，按固定视觉尺寸补一个方框，保证透镜里也能框选 */
function pathOf(h: Hotspot): string {
  const pts = h.normalized_points
  if (!Array.isArray(pts) || pts.length === 0) return ''
  if (typeof pts[0] === 'number') {
    const [x, y] = pts as unknown as number[]
    const dx = 0.045
    const dy = 0.075
    return polyPath([
      [Math.max(0, x - dx), Math.max(0, y - dy)],
      [Math.min(1, x + dx), Math.max(0, y - dy)],
      [Math.min(1, x + dx), Math.min(1, y + dy)],
      [Math.max(0, x - dx), Math.min(1, y + dy)],
    ])
  }
  return polyPath(pts as number[][])
}

function centroidOf(h: Hotspot): { x: number; y: number } {
  const pts = h.normalized_points
  if (!Array.isArray(pts) || pts.length === 0) return { x: 0.5, y: 0.5 }
  if (typeof pts[0] === 'number') {
    const [x, y] = pts as unknown as number[]
    return { x, y }
  }
  const arr = pts as number[][]
  const sx = arr.reduce((s, p) => s + p[0], 0) / arr.length
  const sy = arr.reduce((s, p) => s + p[1], 0) / arr.length
  return { x: sx, y: sy }
}

/** 券洞石壁上预先标注的题刻 / 造像区域（内容未就绪时用示意位置） */
const FALLBACK_PANELS: number[][][] = [
  [[0.3, 0.06], [0.7, 0.06], [0.7, 0.17], [0.3, 0.17]],
  [[0.17, 0.26], [0.28, 0.24], [0.29, 0.37], [0.18, 0.39]],
  [[0.31, 0.27], [0.41, 0.25], [0.42, 0.39], [0.3, 0.4]],
  [[0.5, 0.25], [0.6, 0.23], [0.61, 0.36], [0.51, 0.38]],
  [[0.22, 0.44], [0.33, 0.42], [0.34, 0.55], [0.23, 0.57]],
  [[0.72, 0.28], [0.83, 0.26], [0.84, 0.39], [0.73, 0.41]],
  [[0.55, 0.44], [0.66, 0.42], [0.67, 0.56], [0.56, 0.58]],
  [[0.06, 0.44], [0.17, 0.42], [0.18, 0.56], [0.07, 0.58]],
]

const panelPaths = computed<string[]>(() => {
  if (hasHotspots.value) {
    return hotspots.value.map(pathOf).filter((d) => d.length > 0)
  }
  return FALLBACK_PANELS.map(polyPath)
})

/* ---------------- 石壁砌缝（透视网格） ---------------- */

const wallJoints = computed(() => {
  const lines: { x1: number; y1: number; x2: number; y2: number }[] = []
  for (const t of [0.25, 0.5, 0.75]) {
    lines.push({ x1: 120, y1: 420 + 480 * t, x2: 680, y2: 470 + 170 * t })
    lines.push({ x1: 1480, y1: 420 + 480 * t, x2: 920, y2: 470 + 170 * t })
  }
  for (const s of [0.25, 0.5, 0.75]) {
    lines.push({ x1: 120 + 560 * s, y1: 420 + 50 * s, x2: 120 + 560 * s, y2: 900 - 260 * s })
    lines.push({ x1: 1480 - 560 * s, y1: 420 + 50 * s, x2: 1480 - 560 * s, y2: 900 - 260 * s })
  }
  return lines
})

/** 券洞内石雕（佛教造像）示意：只表现「这里有造像」，不做任何尊像定名 */
const niches = [
  { cx: 250, cy: 720 },
  { cx: 390, cy: 680 },
  { cx: 500, cy: 640 },
  { cx: 1350, cy: 720 },
  { cx: 1210, cy: 680 },
  { cx: 1100, cy: 640 },
]

function nichePath(cx: number, cy: number): string {
  return `M${cx - 38} ${cy + 55} L${cx - 38} ${cy - 10} A38 38 0 0 1 ${cx + 38} ${cy - 10} L${cx + 38} ${cy + 55} Z`
}

/* ---------------- 透镜状态 ---------------- */

const lensMode = ref<'ALL' | 'UNSEEN'>('ALL')
const whyOpen = ref(false)
const debugOpen = ref(false)
const mouseXY = ref({ x: 0, y: 0 })
const debugHotspotId = ref('')
const debugPointsText = ref('')
const debugMsg = ref('')
function debugExport(): string {
  try {
    return localStorage.getItem('tongxin.yuan.hotspots.debug.v1') ?? '{}'
  } catch { return '{}' }
}
function debugLoadSelected() {
  const h = hotspots.value.find((x) => x.id === debugHotspotId.value) ?? hotspots.value[0]
  if (!h) return
  debugHotspotId.value = h.id
  debugPointsText.value = JSON.stringify(h.normalized_points)
}
function debugApply() {
  try {
    const pts = JSON.parse(debugPointsText.value)
    const raw = localStorage.getItem('tongxin.yuan.hotspots.debug.v1')
    const over = raw ? JSON.parse(raw) : {}
    over[debugHotspotId.value] = pts
    localStorage.setItem('tongxin.yuan.hotspots.debug.v1', JSON.stringify(over))
    debugMsg.value = `已暂存 ${debugHotspotId.value} 本地覆盖，导出后请回填 scene.json（标签由内容组确认）`
  } catch { debugMsg.value = '坐标不是合法 JSON（形如 [[0.31,0.27],[0.41,0.25],[0.42,0.39],[0.30,0.40]]）' }
}
function debugReset() {
  try { localStorage.removeItem('tongxin.yuan.hotspots.debug.v1') } catch { /* ignore */ }
  debugMsg.value = '已清除本地覆盖，恢复 scene.json 原坐标'
}
const SCRIPT_ORDER = ['script_sanskrit_lantsa','script_tibetan','script_phagspa','script_old_uyghur','script_chinese','script_tangut']
const lensIndex = ref(0)
const orderedRegions = computed(() => {
  const map = new Map(regions.value.map((r) => [r.h.entity_id, r]))
  return SCRIPT_ORDER.map((id) => map.get(id)).filter(Boolean) as Region[]
})
function prevScript() {
  if (!orderedRegions.value.length) return
  lensIndex.value = (lensIndex.value - 1 + orderedRegions.value.length) % orderedRegions.value.length
  emit('select-hotspot', orderedRegions.value[lensIndex.value].h)
}
function nextScript() {
  if (!orderedRegions.value.length) return
  lensIndex.value = (lensIndex.value + 1) % orderedRegions.value.length
  emit('select-hotspot', orderedRegions.value[lensIndex.value].h)
}
function onSvgMouse(e: MouseEvent) {
  const el = e.currentTarget as SVGElement
  const rect = el.getBoundingClientRect()
  mouseXY.value = { x: Number(((e.clientX - rect.left) / rect.width).toFixed(3)), y: Number(((e.clientY - rect.top) / rect.height).toFixed(3)) }
}

/** 透镜开启时，已探索的文字区域在场景热点层弱化（§9.3 BTN-Y03-03） */
const lensFilter = computed(() => {
  return (h: Hotspot) => {
    if (lensMode.value === 'ALL') return true
    // 券顶 / 石雕不属于六体文字，不受「仅看未探索」影响
    if (!scriptHotspots.value.some((s) => s.id === h.id)) return true
    return statusOf(h) === 'UNSEEN'
  }
})

interface Region {
  h: Hotspot
  d: string
  cx: number
  cy: number
  seen: boolean
  selected: boolean
}

const regions = computed<Region[]>(() =>
  scriptHotspots.value.map((h) => {
    const c = centroidOf(h)
    return {
      h,
      d: pathOf(h),
      cx: c.x * 100,
      cy: c.y * 100,
      seen: isSeen(h),
      selected: statusOf(h) === 'SELECTED',
    }
  }),
)

const visibleRegions = computed<Region[]>(() =>
  regions.value.filter((r) => lensMode.value === 'ALL' || !r.seen),
)

/** 透镜关闭时收起知识卡，避免遗留浮层 */
watch(
  () => props.lensOpen,
  (open) => {
    if (!open) whyOpen.value = false
  },
)

const svgLabel = computed(
  () =>
    `${props.scene?.name || '居庸关云台券洞'}矢量示意：拱形券洞、券顶、两侧石壁题刻区、尽端门洞透光。可点击区域均为预先标注，不依赖任何识别算法。`,
)
</script>

<template>
  <div class="ys">
    <SceneViewer
      :scene="scene"
      :hotspot-status="hotspotStatus"
      :lens-open="lensOpen"
      :lens-filter="lensFilter"
      :chapter-slug="chapter.slug"
      aspect="16 / 9"
      source-label="历史遗址实拍 · 居庸关云台东壁"
      source-url="https://commons.wikimedia.org/wiki/File:Yuntai_east_wall.jpg"
      @select="emit('select-hotspot', $event)"
    >
      <!-- ============ 券洞 SVG 矢量场景 ============ -->
      <template #background>
        <svg
          class="ys__svg"
          viewBox="0 0 1600 900"
          preserveAspectRatio="none"
          role="img"
          :aria-label="svgLabel"
        >
          <defs>
            <linearGradient id="ytVault" x1="0" y1="0" x2="0" y2="1">
              <stop class="ytVaultA" offset="0%" />
              <stop class="ytVaultB" offset="100%" />
            </linearGradient>
            <radialGradient id="ytDoorGlow" cx="50%" cy="50%" r="50%">
              <stop class="ytGlowA" offset="0%" />
              <stop class="ytGlowB" offset="55%" />
              <stop class="ytGlowC" offset="100%" />
            </radialGradient>
            <linearGradient id="ytSpillGrad" x1="0" y1="0" x2="0" y2="1">
              <stop class="ytSpillA" offset="0%" />
              <stop class="ytSpillB" offset="100%" />
            </linearGradient>
            <radialGradient id="ytVignette" cx="50%" cy="48%" r="76%">
              <stop class="ytVigA" offset="62%" />
              <stop class="ytVigB" offset="100%" />
            </radialGradient>
            <!-- 券洞内轮廓：所有石刻与造像都被裁剪在这一轮廓内，不会飘到券洞之外 -->
            <clipPath id="ytInnerClip">
              <path d="M120 900 L120 420 A680 340 0 0 1 1480 420 L1480 900 Z" />
            </clipPath>
          </defs>

          <!-- 券洞外的石体 -->
          <rect class="ytMass" x="0" y="0" width="1600" height="900" />

          <!-- 券洞内壁（透过拱门看到的整块内部空间） -->
          <path class="ytInner" d="M120 900 L120 420 A680 340 0 0 1 1480 420 L1480 900 Z" />

          <!-- 券顶（拱腹） -->
          <path
            class="ytVault"
            d="M120 420 A680 340 0 0 1 1480 420 L920 470 A120 120 0 0 0 680 470 Z"
          />

          <!-- 左右石壁 -->
          <path class="ytWall" d="M120 420 L680 470 L680 640 L120 900 Z" />
          <path class="ytWall" d="M1480 420 L920 470 L920 640 L1480 900 Z" />

          <!-- 尽端石壁 -->
          <path class="ytFarWall" d="M680 470 A120 120 0 0 1 920 470 L920 640 L680 640 Z" />

          <!-- 门洞透光 -->
          <ellipse class="ytGlow" cx="800" cy="580" rx="230" ry="165" />
          <path class="ytDoor" d="M730 640 L730 560 A70 70 0 0 1 870 560 L870 640 Z" />

          <!-- 地面与门洞在地面上的光带 -->
          <path class="ytFloor" d="M120 900 L680 640 L920 640 L1480 900 Z" />
          <path class="ytSpill" d="M730 640 L870 640 L1010 900 L590 900 Z" />

          <!-- 石壁砌缝 -->
          <g clip-path="url(#ytInnerClip)">
            <line
              v-for="(l, i) in wallJoints"
              :key="`j${i}`"
              class="ytJoint"
              :x1="l.x1"
              :y1="l.y1"
              :x2="l.x2"
              :y2="l.y2"
            />
          </g>

          <!-- 券洞内石雕示意（佛教造像，不给定名） -->
          <g class="ytNicheGroup" clip-path="url(#ytInnerClip)">
            <template v-for="(n, i) in niches" :key="`n${i}`">
              <path class="ytNiche" :d="nichePath(n.cx, n.cy)" />
              <circle class="ytFigure" :cx="n.cx" :cy="n.cy - 16" r="12" />
              <path
                class="ytFigure"
                :d="`M${n.cx - 24} ${n.cy + 42} C${n.cx - 24} ${n.cy + 2} ${n.cx + 24} ${n.cy + 2} ${n.cx + 24} ${n.cy + 42} Z`"
              />
            </template>
          </g>

          <!-- 题刻区域石块示意：与 scene.hotspots 完全同坐标，保证与透镜框选一致 -->
          <g clip-path="url(#ytInnerClip)">
            <path v-for="(d, i) in panelPaths" :key="`p${i}`" class="ytPanel" :d="d" />
          </g>

          <!-- 暗角 -->
          <rect class="ytVignette" x="0" y="0" width="1600" height="900" />
        </svg>
      </template>

      <!-- ============ 覆盖层：空态 / 六体文字透镜 ============ -->
      <template #overlay>
        <!-- 内容未就绪：仍然给出券洞空间，但不假装有标注 -->
        <div v-if="!hasHotspots" class="ys__empty">
          <DsIcon name="info" :size="15" />
          <span>题刻标注正在整理中</span>
        </div>

        <div v-else-if="lensOpen" class="ys__lens" @mousemove="onSvgMouse">
          <!-- 区域边界：坐标与热点层共用同一套 0–1 归一化数据 -->
          <svg class="ys__regions" viewBox="0 0 1600 900" preserveAspectRatio="none">
            <path
              v-for="r in visibleRegions"
              :key="r.h.id"
              class="ys__region"
              :class="{ 'is-seen': r.seen, 'is-selected': r.selected }"
              :d="r.d"
              @click="emit('select-hotspot', r.h)"
            />
          </svg>

          <!-- 区域名称标签：已探索实心 / 未探索空心（§9.1） -->
          <button
            v-for="r in visibleRegions"
            :key="`t${r.h.id}`"
            class="ys__tag"
            :class="{ 'is-seen': r.seen, 'is-selected': r.selected }"
            :style="{ left: `${r.cx}%`, top: `${r.cy}%` }"
            type="button"
            @click="emit('select-hotspot', r.h)"
          >
            <span class="ys__tag-dot" aria-hidden="true" />
            <span class="ys__tag-name">{{ r.h.label || '未命名书写系统' }}</span>
          </button>

          <!-- 透镜控件 -->
          <div class="ys__bar">
            <span class="ys__bar-title">
              <DsIcon name="layers" :size="14" />
              六体文字透镜
            </span>
            <button
              class="ys__chip"
              :class="{ 'is-on': lensMode === 'ALL' }"
              type="button"
              @click="lensMode = 'ALL'"
            >
              全部文字
            </button>
            <button
              class="ys__chip"
              :class="{ 'is-on': lensMode === 'UNSEEN' }"
              type="button"
              @click="lensMode = 'UNSEEN'"
            >
              仅看未探索
            </button>
            <button
              class="ys__chip ys__chip--why"
              :class="{ 'is-on': whyOpen }"
              type="button"
              @click="whyOpen = !whyOpen"
            >
              <DsIcon name="info" :size="13" />
              为什么是六体？
            </button>
            <button class="ys__chip" type="button" @click="prevScript()">上一个</button>
            <button class="ys__chip" type="button" @click="nextScript()">下一个</button>
            <button class="ys__chip ys__chip--why" type="button" @click="debugOpen = !debugOpen">坐标调试</button>
            <span class="ys__bar-count">已探索 {{ seenScriptCount }}/{{ scriptTotal }} 种书写系统</span>
          </div>
          <div v-if="debugOpen" class="ys__debug">
            <span>归一化坐标 x={{ mouseXY.x }} y={{ mouseXY.y }}（3072×2304，缩放自适应）</span>
            <span class="ys__debug-row">
              <select v-model="debugHotspotId" @focus="debugHotspotId || debugLoadSelected()">
                <option value="" disabled>选择热点</option>
                <option v-for="h in hotspots" :key="h.id" :value="h.id">{{ h.label || h.id }}</option>
              </select>
              <button class="ys__chip" type="button" @click="debugLoadSelected()">载入坐标</button>
            </span>
            <input v-model="debugPointsText" class="ys__debug-input" placeholder="[[x,y],…] 归一化多边形" aria-label="热点归一化坐标" />
            <span class="ys__debug-row">
              <button class="ys__chip" type="button" @click="debugApply()">本地暂存</button>
              <button class="ys__chip" type="button" @click="debugReset()">恢复原图</button>
            </span>
            <span v-if="debugMsg" class="ys__debug-msg">{{ debugMsg }}</span>
            <span class="ys__debug-hint">本地覆盖仅存浏览器；正式坐标必须回填 scene.json 并经内容组确认标签含义</span>
          </div>

          <!-- 固定知识卡：只讲概念区分与「不做什么」，不给释读、不绑定族群 -->
          <div v-if="whyOpen" class="ys__card" role="dialog" aria-label="为什么是六体？">
            <header class="ys__card-head">
              <h3 class="ys__card-title">为什么是六体？</h3>
              <button class="ys__card-close" type="button" aria-label="关闭" @click="whyOpen = false">
                <DsIcon name="close" :size="15" />
              </button>
            </header>

            <p class="ys__card-lead">
              云台券洞内保存有<strong>六种书写系统</strong>的题刻：梵文书写系统、藏文、八思巴文、
              回鹘文、汉文、西夏文。
            </p>

            <ul class="ys__card-list">
              <li>
                <strong>书写系统（Script）</strong>、<strong>语言（Language）</strong>、
                <strong>文本（Text）</strong>与<strong>某一处具体题刻（Inscription）</strong>
                是四件不同的事，本平台在数据与表述上始终分开。
              </li>
              <li>
                文字、语言与历史群体之间<strong>不是一一对应关系</strong>：同一套文字可以被用来书写
                不同语言，同一种语言也可以用不同文字书写。
              </li>
              <li>
                因此，本平台不会把「六体文字」说成「六个民族的六种语言」，也不由某一处题刻
                直接推断书写者或使用者的族群身份。
              </li>
              <li>
                券洞内同时存在佛教石雕与这些文字题刻。造像的存在有公开资料支持，但具体题材的
                定名属于专业研究范围，本平台不给出未经核验的定名或图像寓意。
              </li>
            </ul>

            <footer class="ys__card-foot">
              <button class="ys__card-link" type="button" @click="emit('open-chat', 'artifact_yuntai')">
                <DsIcon name="sparkle" :size="14" />
                向云台提问
              </button>
              <button
                class="ys__card-link"
                type="button"
                @click="emit('select-entity', 'concept_multiscript_inscription')"
              >
                <DsIcon name="document" :size="14" />
                查看「多文字题刻」
              </button>
            </footer>
          </div>
        </div>
      </template>
    </SceneViewer>
  </div>
</template>

<style scoped>
.ys {
  flex: 1;
  min-height: 0;
  display: flex;
}

/* ================= 券洞矢量场景 ================= */
.ytMass {
  fill: color-mix(in srgb, var(--color-blue-800) 66%, var(--color-ink-900));
}
.ytInner {
  fill: color-mix(in srgb, var(--color-blue-800) 46%, var(--color-blue-600));
}
.ytVault {
  fill: url(#ytVault);
}
.ytVaultA {
  stop-color: var(--color-blue-600);
  stop-opacity: 0.5;
}
.ytVaultB {
  stop-color: var(--color-blue-800);
  stop-opacity: 0.6;
}
.ytWall {
  fill: color-mix(in srgb, var(--color-blue-800) 72%, var(--color-blue-600));
}
.ytFarWall {
  fill: color-mix(in srgb, var(--color-blue-800) 44%, var(--color-blue-600));
}
.ytFloor {
  fill: color-mix(in srgb, var(--color-ink-900) 68%, var(--color-blue-800));
}
.ytDoor {
  fill: color-mix(in srgb, var(--color-paper-50) 88%, var(--color-gold-300));
}
.ytGlow {
  fill: url(#ytDoorGlow);
}
.ytGlowA {
  stop-color: var(--color-paper-50);
  stop-opacity: 0.5;
}
.ytGlowB {
  stop-color: var(--color-blue-400);
  stop-opacity: 0.24;
}
.ytGlowC {
  stop-color: var(--color-blue-400);
  stop-opacity: 0;
}
/* 门洞光线在地面上的衰减，避免看起来像一条灰色的路 */
.ytSpill {
  fill: url(#ytSpillGrad);
}
.ytSpillA {
  stop-color: var(--color-paper-50);
  stop-opacity: 0.42;
}
.ytSpillB {
  stop-color: var(--color-paper-50);
  stop-opacity: 0;
}
.ytJoint {
  stroke: color-mix(in srgb, var(--color-blue-400) 30%, transparent);
  stroke-width: 1;
  fill: none;
}
.ytNiche {
  fill: color-mix(in srgb, var(--color-ink-900) 62%, var(--color-blue-800));
  stroke: color-mix(in srgb, var(--color-gold-300) 48%, transparent);
  stroke-width: 1.2;
}
.ytFigure {
  fill: color-mix(in srgb, var(--color-gold-300) 46%, transparent);
}
.ytPanel {
  fill: color-mix(in srgb, var(--chapter-accent) 22%, transparent);
  stroke: color-mix(in srgb, var(--color-gold-300) 42%, transparent);
  stroke-width: 1.2;
  stroke-dasharray: 6 5;
}
.ytVignette {
  fill: url(#ytVignette);
}
.ytVigA {
  stop-color: var(--color-ink-900);
  stop-opacity: 0;
}
.ytVigB {
  stop-color: var(--color-ink-900);
  stop-opacity: 0.3;
}

/* ================= 空态 ================= */
.ys__empty {
  position: absolute;
  left: 50%;
  bottom: var(--sp-6);
  transform: translateX(-50%);
  z-index: var(--z-hud);
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  color: var(--color-ink-700);
  font-size: var(--fs-body-s);
  backdrop-filter: blur(6px);
}

/* ================= 透镜 ================= */
.ys__lens {
  position: absolute;
  inset: 0;
  z-index: var(--z-hud);
  pointer-events: none;
}

.ys__regions {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.ys__region {
  fill: color-mix(in srgb, var(--chapter-accent) 12%, transparent);
  stroke: color-mix(in srgb, var(--chapter-accent) 70%, transparent);
  stroke-width: 1.6;
  stroke-dasharray: 7 5;
  vector-effect: non-scaling-stroke;
  cursor: pointer;
  pointer-events: visiblePainted;
  transition:
    fill var(--dur-normal) var(--ease-standard),
    stroke var(--dur-normal) var(--ease-standard);
}
.ys__region:hover {
  fill: color-mix(in srgb, var(--chapter-accent) 26%, transparent);
}
/* 已探索：实心 */
.ys__region.is-seen {
  fill: color-mix(in srgb, var(--chapter-accent) 40%, transparent);
  stroke: var(--chapter-accent);
  stroke-dasharray: none;
  stroke-width: 2;
}
.ys__region.is-selected {
  stroke-width: 3;
}

.ys__tag {
  position: absolute;
  transform: translate(-50%, -50%);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-panel);
  border: 1px solid color-mix(in srgb, var(--chapter-accent) 60%, transparent);
  color: var(--color-ink-900);
  font-size: var(--fs-caption);
  line-height: 1.6;
  white-space: nowrap;
  pointer-events: auto;
  cursor: pointer;
  box-shadow: var(--shadow-card);
  transition:
    background-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.ys__tag:hover {
  background: var(--color-paper-50);
  border-color: var(--chapter-accent);
}
/* 未探索：空心 */
.ys__tag-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 1.5px solid var(--chapter-accent);
  background: transparent;
  flex: none;
}
/* 已探索：实心 */
.ys__tag.is-seen .ys__tag-dot {
  background: var(--chapter-accent);
}
.ys__tag.is-selected {
  background: var(--chapter-accent);
  color: #fff;
  border-color: var(--chapter-accent);
}
.ys__tag.is-selected .ys__tag-dot {
  border-color: #fff;
  background: var(--color-paper-50);
}

.ys__bar {
  position: absolute;
  top: var(--sp-3);
  left: 50%;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 6px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(8px);
  pointer-events: auto;
}
.ys__bar-title {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--fs-caption);
  font-weight: 600;
  color: var(--chapter-accent);
  padding-right: var(--sp-2);
  border-right: 1px solid var(--color-border);
}
.ys__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 11px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-ink-700);
  font-size: var(--fs-caption);
  transition:
    background-color var(--dur-fast) var(--ease-standard),
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.ys__chip:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.ys__chip.is-on {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
  color: #fff;
}
.ys__chip--why {
  border-style: dashed;
}
.ys__bar-count {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  padding-left: var(--sp-2);
  border-left: 1px solid var(--color-border);
}

/* 坐标调试条 + 低分辨率降级 */
.ys__debug {
  position: absolute;
  top: 52px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: min(560px, calc(100% - 16px));
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(12, 20, 19, 0.86);
  color: #f0e7d5;
  font-size: var(--fs-caption);
  font-variant-numeric: tabular-nums;
  pointer-events: auto;
}
.ys__debug-row { display: flex; gap: 6px; align-items: center; }
.ys__debug-input {
  width: 100%;
  font-size: var(--fs-caption);
  font-family: ui-monospace, monospace;
}
.ys__debug-msg { color: #f3d382; }
.ys__debug-hint { opacity: 0.72; }
@media (max-width: 760px) {
  .ys__bar { flex-wrap: wrap; max-width: calc(100% - 16px); border-radius: 14px; }
  .ys__bar-count { display: none; }
  .ys__card { width: calc(100% - 16px); right: 8px; top: 108px; }
  .ys__tag-name { max-width: 22vw; overflow: hidden; text-overflow: ellipsis; }
}

/* ================= 固定知识卡 ================= */
.ys__card {
  position: absolute;
  top: 62px;
  right: var(--sp-4);
  width: min(430px, 46%);
  max-height: calc(100% - 86px);
  overflow: auto;
  padding: var(--sp-4);
  border-radius: var(--radius-drawer);
  background: var(--color-paper-50);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-floating);
  pointer-events: auto;
}
.ys__card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}
.ys__card-title {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  color: var(--color-ink-900);
  margin: 0;
}
.ys__card-close {
  border: 0;
  background: transparent;
  color: var(--color-ink-500);
  padding: 2px;
  border-radius: var(--radius-btn);
  line-height: 1;
}
.ys__card-close:hover {
  background: rgba(65, 55, 42, 0.07);
  color: var(--color-ink-900);
}
.ys__card-lead {
  margin: 0 0 var(--sp-3);
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}
.ys__card-lead strong {
  color: var(--chapter-accent);
}
.ys__card-list {
  margin: 0;
  padding-left: 1.1em;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}
.ys__card-list strong {
  color: var(--color-ink-900);
}
.ys__card-foot {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  margin-top: var(--sp-4);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--color-border);
}
.ys__card-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: var(--color-paper-50);
  color: var(--color-ink-700);
  font-size: var(--fs-caption);
}
.ys__card-link:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
</style>
