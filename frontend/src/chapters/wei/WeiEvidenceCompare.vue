<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import SceneViewer from '@/components/scene/SceneViewer.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import { getComparison } from '@/api/endpoints'
import type { Chapter, ComparisonGroup, EvidenceItem, Hotspot, Scene } from '@/types'

/**
 * C02 北魏变体 · N02 云冈—龙门双场景 + N03 文化证据对照透镜
 * （规格 §8 / §9，设计系统 §23.2 / §59）
 *
 * 内容红线（决定了本组件的两个关键设计）：
 *  1. **不能把云冈与龙门做成简单的「前后对比」（规格 §2.4）。**
 *     两处遗存的年代与背景并不相同，这里是「同类文化要素的并存与变化」，
 *     不是「前者变成后者」的替代关系。因此界面上固定显示这句说明，
 *     并且证据卡的第 ④ 层永远回答「不能直接推出什么」。
 *  2. 每条证据必须完整显示固定四层：
 *     看到什么 / 来源如何描述 / 能支持什么 / 不能直接推出什么（规格 §9.3）。
 *     **不允许 LLM 自由生成对照结论**（规格 §9.4），所以本组件不做任何自动归纳。
 *
 * 数据来源：`GET /chapters/{id}/comparison`；接口不可用时退回内置演示数据
 * （四层文案全部取自 content/northern_wei/claims.json 中已存在的 claim，不新编内容）。
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

/* ---------------------------------------------------------------- 尺寸自适应 */

/**
 * 用 ResizeObserver 把 SVG 的 viewBox 设成元素的真实像素尺寸。
 * 这样归一化坐标 (0–1) 与 SVG 用户坐标严格线性对应：
 * 石窟轮廓与热点不会错位，图形也不会被拉伸变形。
 */
const boxEl = ref<HTMLElement | null>(null)
const boxW = ref(600)
const boxH = ref(700)
let ro: ResizeObserver | null = null

function observeBox(el: HTMLElement | null) {
  ro?.disconnect()
  if (!el) return
  ro = new ResizeObserver((entries) => {
    const r = entries[0]?.contentRect
    if (!r || r.width < 10 || r.height < 10) return
    boxW.value = Math.round(r.width)
    boxH.value = Math.round(r.height)
  })
  ro.observe(el)
}

onBeforeUnmount(() => ro?.disconnect())

/** 归一化 → 当前像素坐标 */
function px(nx: number): number {
  return nx * boxW.value
}
function py(ny: number): number {
  return ny * boxH.value
}
/** 统一缩放系数：以元素高度为基准，保证人物比例不随宽高比变形 */
function sc(rel: number): number {
  return (rel * boxH.value) / 200
}

/* ---------------------------------------------------------------- 类别定义 */

interface CategoryVM {
  key: string
  name: string
}

/**
 * 内置对照类别（设计系统 §23.2 顶部工具条）。
 * 类别键与后端 `group_key` 对齐；`inscription` / `institution` 归入「社会生活 / 建筑」，
 * 因为这两种证据在四层写法上与这两类同构。
 */
const BUILTIN_CATEGORIES: CategoryVM[] = [
  { key: 'art', name: '艺术证据' },
  { key: 'life', name: '社会生活' },
  { key: 'costume', name: '服饰' },
  { key: 'sculpture', name: '雕塑' },
  { key: 'music', name: '音乐' },
  { key: 'architecture', name: '建筑' },
]

const CATEGORY_NAME: Record<string, string> = {
  art: '艺术证据',
  life: '社会生活',
  costume: '服饰',
  sculpture: '雕塑',
  music: '音乐',
  architecture: '建筑',
}

/** 把后端可能出现的各种 group_key / 中文名归一化成类别键 */
const GROUP_ALIAS: Record<string, string> = {
  art: 'art',
  artistic: 'art',
  art_exchange: 'art',
  艺术: 'art',
  艺术证据: 'art',
  造像: 'sculpture',
  造像艺术: 'sculpture',
  life: 'life',
  society: 'life',
  social: 'life',
  social_life: 'life',
  inscription: 'life',
  institution: 'life',
  社会生活: 'life',
  文字: 'life',
  文字墓志: 'life',
  墓志: 'life',
  costume: 'costume',
  clothing: 'costume',
  服饰: 'costume',
  服饰生活: 'costume',
  sculpture: 'sculpture',
  statue: 'sculpture',
  style: 'sculpture',
  雕塑: 'sculpture',
  music: 'music',
  音乐: 'music',
  architecture: 'architecture',
  building: 'architecture',
  建筑: 'architecture',
  都城制度: 'architecture',
}

function normGroup(raw: string | null | undefined): string | null {
  if (!raw) return null
  const k = String(raw).trim().toLowerCase()
  return GROUP_ALIAS[k] ?? GROUP_ALIAS[String(raw).trim()] ?? null
}

/* ---------------------------------------------------------------- 证据数据 */

interface EvidenceVM {
  id: string
  entityId: string
  siteKey: 'yungang' | 'longmen'
  groupKeys: string[]
  title: string
  observed: string
  describedBySource: string
  supports: string
  doesNotSupport: string
  caveat?: string
  /** 博物馆藏辅助材料 / 年代超出北魏的比较材料，必须单独标注（规格 §8.3） */
  auxiliary?: boolean
}

/**
 * 内置演示证据。四层文案直接来自 content/northern_wei/claims.json 中已存在的 claim，
 * 不新增任何历史判断；正式内容接入后（extra.json + /comparison 接口）会被替换。
 */
const FALLBACK_EVIDENCE: EvidenceVM[] = [
  {
    id: 'fb_yungang_tanyao',
    entityId: 'evidence_yungang_tanyao',
    siteKey: 'yungang',
    groupKeys: ['art', 'sculpture'],
    title: '云冈早期大型洞窟与造像',
    observed: '云冈早期大型洞窟与造像，构成观察北魏时期佛教石窟艺术传播与本土表达的具体材料。',
    describedBySource: '来源把它描述为「观察北魏时期佛教石窟艺术传播与本土表达的具体材料」。',
    supports: '可用于观察北魏时期佛教石窟艺术在云冈的呈现方式。',
    doesNotSupport: '不能据此判断某位皇帝的个人审美，也不能把某一窟的开凿年代精确到具体年份。',
  },
  {
    id: 'fb_yungang_art_exchange',
    entityId: 'evidence_yungang_art_exchange',
    siteKey: 'yungang',
    groupKeys: ['art'],
    title: '云冈石窟中的多种艺术因素',
    observed: '云冈石窟中可见多种艺术因素的组合，既包含外来影响，也包含与中国文化传统相结合的表达。',
    describedBySource: '来源将其描述为外来影响与中国文化传统结合并存的表达。',
    supports: '可观察不同艺术来源在同一石窟空间中的并存与混合。',
    doesNotSupport: '不能把风格变化简单归因于某一次政治决定或某一群工匠。',
  },
  {
    id: 'fb_yungang_architecture',
    entityId: 'evidence_yungang_architecture',
    siteKey: 'yungang',
    groupKeys: ['architecture'],
    title: '云冈的窟形与建筑形象',
    observed: '云冈石窟的窟形与雕刻中包含摹拟木构建筑与毡帐形式的形象。',
    describedBySource: '来源称其为「观察北魏建筑与外来因素结合的实物材料」。',
    supports: '可观察北魏建筑形象中木构传统与毡帐等外来因素在同一空间中的并存。',
    doesNotSupport: '不能据此复原任何一座已消失的木构建筑的具体形制或尺寸。',
  },
  {
    id: 'fb_yungang_music',
    entityId: 'evidence_yungang_music',
    siteKey: 'yungang',
    groupKeys: ['music'],
    title: '云冈第 12 窟「音乐窟」',
    observed: '云冈第 12 窟因集中雕刻大量伎乐天与乐器形象，被称为「音乐窟」。',
    describedBySource: '来源认为其中乐器包含中原传统乐器与经丝路传入的乐器，是多种音乐因素在同一空间中的并存。',
    supports: '可观察多种音乐因素在同一空间中的并存关系。',
    doesNotSupport: '不能据此推定当时实际演奏的曲目、乐队编制或音响效果。',
  },
  {
    id: 'fb_longmen_guyang',
    entityId: 'evidence_longmen_guyang',
    siteKey: 'longmen',
    groupKeys: ['art', 'sculpture', 'architecture'],
    title: '龙门古阳洞北魏阶段窟龛',
    observed: '古阳洞保存北魏时期的造像、龛饰与题记；窟龛中出现仿木构的屋形龛与柱、斗栱等建筑形象。',
    describedBySource: '来源称其可用于观察龙门北魏阶段的艺术特征，以及北朝木构建筑形象的演变。',
    supports: '可观察北魏阶段龙门窟龛的艺术特征与仿木构建筑形象。',
    doesNotSupport: '不能把云冈与龙门理解为「前者变成后者」的替代关系，两处年代与背景并不相同。',
  },
  {
    id: 'fb_longmen_inscriptions',
    entityId: 'evidence_longmen_inscriptions',
    siteKey: 'longmen',
    groupKeys: ['life'],
    title: '龙门造像题记与「龙门二十品」',
    observed: '龙门石窟北魏阶段保存大量造像题记，其中「龙门二十品」多数出自古阳洞。',
    describedBySource: '来源称其为「研究北朝书法与造像背景的重要材料」。',
    supports: '可通过题记观察造像者身份、发愿内容与书法面貌。',
    doesNotSupport: '题记只覆盖有能力刻记的人群，不能代表当时全体社会成员，也不能当作完整统计。',
  },
  {
    id: 'fb_longmen_costume',
    entityId: 'evidence_longmen_costume',
    siteKey: 'longmen',
    groupKeys: ['costume'],
    title: '龙门供养人形象与造像衣饰',
    observed: '龙门北魏阶段窟龛中的供养人形象与造像衣饰。',
    describedBySource: '来源称其为「可供观察当时服饰形制的图像证据」。',
    supports: '可观察北魏阶段服饰形制在图像中的表现。',
    doesNotSupport: '造像衣饰受仪轨与图像传统影响，不能直接等同于日常实际穿着。',
  },
  {
    id: 'fb_longmen_music',
    entityId: 'evidence_longmen_music',
    siteKey: 'longmen',
    groupKeys: ['music'],
    title: '龙门北魏阶段伎乐雕刻',
    observed: '龙门北魏阶段洞窟中保存伎乐天与乐器雕刻，古阳洞是其中较有代表性的一处。',
    describedBySource: '来源称其乐器组合「可与云冈材料进行比较研究」。',
    supports: '可与云冈的乐器材料并置观察，看同类图像在两处遗产中的呈现。',
    doesNotSupport: '两处年代与背景并不相同，不能据此得出单一的音乐演变序列。',
  },
  {
    id: 'fb_yuanyu_epitaph',
    entityId: 'evidence_yuanyu_epitaph',
    siteKey: 'longmen',
    groupKeys: ['life'],
    title: '元羽墓志（博物馆藏）',
    observed: '中国国家博物馆藏元羽墓志，内容涉及迁都洛阳（493 年）与 496 年改姓。',
    describedBySource: '来源指出其涉及籍贯书写的变化，可与迁都后的制度调整对照观察。',
    supports: '可与迁都、姓氏变化等资料对照，观察北魏后期身份与制度的变化。',
    doesNotSupport: '一方墓志可以反映墓主个人的身份与制度背景，但不能代表当时所有社会群体发生了同步、一致的变化。',
    caveat: '博物馆藏材料，不是石窟现场证据。',
    auxiliary: true,
  },
  {
    id: 'fb_attendant_costume',
    entityId: 'evidence_attendant_costume',
    siteKey: 'longmen',
    groupKeys: ['costume'],
    title: '侍从陶俑服饰（博物馆藏）',
    observed: '侍从陶俑的服饰形象，如小冠、上衣下裤等着装组合。',
    describedBySource: '来源称其为「观察北魏后期服饰形制提供了实物材料」。',
    supports: '可观察北魏后期服饰形制的实物材料。',
    doesNotSupport: '陶俑属随葬明器，其服饰表现未必完全对应生前的实际穿着。',
    caveat: '博物馆藏材料，作为「北朝比较材料」并置，年代未必与石窟证据完全重合。',
    auxiliary: true,
  },
]

/* ---------------------------------------------------------------- 数据接入 */

const apiItems = ref<EvidenceItem[] | null>(null)
const apiGroups = ref<ComparisonGroup[]>([])

async function loadComparison() {
  const id = props.chapter?.id
  if (!id) return
  try {
    const res = await getComparison(id)
    if (res && Array.isArray(res.items) && res.items.length) {
      apiItems.value = res.items
      apiGroups.value = Array.isArray(res.groups) ? res.groups : []
    }
  } catch {
    // 接口不可用时不阻断浏览：退回内置演示证据，并在界面上如实标注
  }
}

onMounted(async () => {
  observeBox(boxEl.value)
  await loadComparison()
})
watch(
  () => props.chapter?.id,
  () => {
    apiItems.value = null
    void loadComparison()
  },
)

const usingFallback = computed(() => !apiItems.value)

const evidence = computed<EvidenceVM[]>(() => {
  const list = apiItems.value
  if (!list) return FALLBACK_EVIDENCE
  return list.map<EvidenceVM>((it) => {
    const g = normGroup(it.group_key)
    return {
      id: it.id,
      entityId: it.entity_id || it.id,
      siteKey: it.site_key === 'yungang' ? 'yungang' : 'longmen',
      groupKeys: g ? [g] : [],
      title: it.title || it.id,
      observed: it.observed,
      describedBySource: it.described_by_source,
      supports: it.supports,
      doesNotSupport: it.does_not_support,
      caveat: it.caveat ?? undefined,
      auxiliary: it.id.startsWith('artifact_') || it.id.startsWith('evidence_artifact'),
    }
  })
})

const categories = computed<CategoryVM[]>(() => {
  if (apiGroups.value.length) {
    const out: CategoryVM[] = []
    for (const g of apiGroups.value) {
      const key = normGroup(g.id) ?? normGroup(g.name)
      if (!key) continue
      if (out.some((c) => c.key === key)) continue
      out.push({ key, name: g.name || CATEGORY_NAME[key] || g.id })
    }
    if (out.length) return out
  }
  return BUILTIN_CATEGORIES
})

/* ---------------------------------------------------------------- 对照选择 */

const activeCategory = ref<string | null>(null)

function toggleCategory(key: string) {
  activeCategory.value = activeCategory.value === key ? null : key
}

const activeName = computed(
  () => categories.value.find((c) => c.key === activeCategory.value)?.name ?? '',
)

function isMatched(e: EvidenceVM): boolean {
  if (!activeCategory.value) return true
  return e.groupKeys.includes(activeCategory.value)
}

function leftItems(): EvidenceVM[] {
  return evidence.value.filter((e) => e.siteKey === 'yungang')
}
function rightItems(): EvidenceVM[] {
  return evidence.value.filter((e) => e.siteKey === 'longmen')
}

/** 某一侧在当前类别下是否有已审核证据 —— 没有就如实说明，不隐藏 */
function sideHasMatch(site: 'yungang' | 'longmen'): boolean {
  if (!activeCategory.value) return true
  return evidence.value.some((e) => e.siteKey === site && isMatched(e))
}

/* ---------------------------------------------------------------- 热点分侧与高亮 */

/** 热点归属：优先看 group_key / id / entity_id 里的 yungang / longmen 线索 */
function sideOfHotspot(h: Hotspot): 'yungang' | 'longmen' {
  const raw = `${h.group_key ?? ''} ${h.id} ${h.entity_id ?? ''}`.toLowerCase()
  if (raw.includes('longmen') || raw.includes('long_men') || raw.includes('luoyang')) return 'longmen'
  return 'yungang'
}

/** 热点对应的类别：先按 entity_id 找证据卡，再退回 group_key */
function hotspotGroups(h: Hotspot): string[] {
  const hit = evidence.value.find((e) => e.entityId === h.entity_id)
  if (hit) return hit.groupKeys
  const g = normGroup(h.group_key)
  return g ? [g] : []
}

const sceneHotspots = computed(() => props.scene?.hotspots ?? [])
const leftHotspots = computed(() => sceneHotspots.value.filter((h) => sideOfHotspot(h) === 'yungang'))
const rightHotspots = computed(() => sceneHotspots.value.filter((h) => sideOfHotspot(h) === 'longmen'))

function sceneForSide(site: 'yungang' | 'longmen', list: Hotspot[]): Scene | null {
  const s = props.scene
  if (!s) return null
  return {
    ...s,
    // 历史遗址实拍优先；加载失败时 SceneViewer 自动回退到各自的 SVG 示意。
    background_asset_id:
      site === 'yungang'
        ? '/assets/wei/yungang-cave20-original.jpg'
        : '/assets/wei/longmen-guyang-original.jpg',
    // 两侧共用的免责声明在下方统一显示一次，避免重复两遍
    disclaimer: null,
    hotspots: list,
    id: `${s.id}__${site}`,
  }
}

/** 选中类别时，非该类热点弱化（交给 SceneViewer 的透镜滤镜） */
function lensFilterFor(site: 'yungang' | 'longmen') {
  return (h: Hotspot) => {
    if (!activeCategory.value) return true
    if (!sideHasMatch(site)) return true
    return hotspotGroups(h).includes(activeCategory.value)
  }
}

function onSelect(h: Hotspot) {
  emit('select-hotspot', h)
}

/* ---------------------------------------------------------------- 石窟示意图形 */

/** 云冈昙曜五窟：中间大佛 + 两侧胁侍，拱形大龛 */
const yungangNiches = computed(() => [
  { id: 'y-main', nx: 0.5, w: 0.34, top: 0.15, bottom: 0.92 },
  { id: 'y-left', nx: 0.16, w: 0.18, top: 0.36, bottom: 0.9 },
  { id: 'y-right', nx: 0.84, w: 0.18, top: 0.36, bottom: 0.9 },
])

/** 龙门：卢舍那大佛的矩形浅龛 + 左侧屋形龛 + 右侧题记壁面 */
const longmenNiches = computed(() => [
  { id: 'l-main', nx: 0.5, w: 0.3, top: 0.2, bottom: 0.9 },
  { id: 'l-left', nx: 0.15, w: 0.18, top: 0.42, bottom: 0.88 },
])
/** 题记壁面：占据右侧 0.72–0.95，避免与龛像重叠 */
const INSCRIPTION = { x: 0.72, y: 0.42, cols: 4, rows: 3, cw: 0.045, ch: 0.08 }

/** 屋形龛轮廓（仿木构：屋檐 + 柱 + 斗栱），用来对应「建筑」类证据 */
function roofPath(nx: number, w: number, top: number, bottom: number): string {
  const x0 = px(nx - w / 2)
  const x1 = px(nx + w / 2)
  const y0 = py(top)
  const y1 = py(bottom)
  const eave = y0 + (y1 - y0) * 0.18
  const mid = (x0 + x1) / 2
  return [
    `M${x0 - 8} ${eave}`,
    `L${mid} ${y0}`,
    `L${x1 + 8} ${eave}`,
    `L${x1} ${eave}`,
    `L${x1} ${y1}`,
    `L${x0} ${y1}`,
    `L${x0} ${eave}`,
    'Z',
  ].join(' ')
}

/** 拱形龛轮廓（云冈）：直壁 + 半圆券顶 */
function archNichePath(nx: number, w: number, top: number, bottom: number): string {
  const x0 = px(nx - w / 2)
  const x1 = px(nx + w / 2)
  const yTop = py(top)
  const yBottom = py(bottom)
  // 券顶半径同时受龛宽与龛高约束：画面很宽很扁时按宽度取半径会让拱券撑出画面
  const r = Math.min(px(w) / 2, (yBottom - yTop) / 2)
  return [
    `M${x0} ${yBottom}`,
    `L${x0} ${yTop + r}`,
    `A${r} ${r} 0 0 1 ${x1} ${yTop + r}`,
    `L${x1} ${yBottom}`,
    'Z',
  ].join(' ')
}

/** 斗栱示意：屋檐下的一组小方块（龙门左侧屋形龛） */
const ROOF = { nx: 0.15, w: 0.24, top: 0.14, bottom: 0.42 }
const longmenBrackets = computed(() => {
  const y = py(ROOF.top) + 8
  const start = px(ROOF.nx - ROOF.w / 2) + 8
  const span = px(ROOF.w) - 16
  const items: { x: number; w: number }[] = []
  const n = 3
  for (let i = 0; i < n; i++) {
    items.push({ x: start + (span / n) * i + span / (n * 2) - 4, w: 8 })
  }
  return { y, items }
})

/** 题记方格：示意「龙门二十品」所在的题记壁面 */
const inscriptionGrid = computed(() => {
  const out: { x: number; y: number; w: number; h: number }[] = []
  const cols = INSCRIPTION.cols
  const rows = INSCRIPTION.rows
  const x0 = px(INSCRIPTION.x)
  const y0 = py(INSCRIPTION.y)
  const cw = px(INSCRIPTION.cw)
  const ch = py(INSCRIPTION.ch)
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      out.push({ x: x0 + c * (cw + 5), y: y0 + r * (ch + 6), w: cw, h: ch })
    }
  }
  return out
})

const uid = Math.random().toString(36).slice(2, 9)
</script>

<template>
  <div class="wei">
    <!-- 顶部：对照类别工具条 -->
    <header class="wei__bar">
      <div class="wei__cats">
        <button
          v-for="c in categories"
          :key="c.key"
          type="button"
          class="wei__cat"
          :class="{ 'is-on': activeCategory === c.key }"
          @click="toggleCategory(c.key)"
        >
          {{ c.name }}
        </button>
        <button
          v-if="activeCategory"
          type="button"
          class="wei__cat wei__cat--clear"
          @click="activeCategory = null"
        >
          <DsIcon name="close" :size="12" />清空对照
        </button>
      </div>
      <span class="wei__count">
        {{ activeCategory ? `正在对照：${activeName}` : '选择一种证据类型，比较两个历史空间' }}
      </span>
    </header>

    <!-- 内容红线：不是前后对比（规格 §2.4） -->
    <p class="wei__redline">
      <DsIcon name="info" :size="13" />
      <span
        >两处遗存年代与背景并不相同，这里展示的是同类文化要素的并存与变化，不是简单的前后替代关系。</span
      >
    </p>

    <div class="wei__panes">
      <!-- 左：云冈 -->
      <section class="wei__pane">
        <header class="wei__pane-head">
          <span class="wei__pane-name">云冈石窟</span>
          <span class="wei__pane-era">平城时期</span>
        </header>

        <div ref="boxEl" class="wei__stage">
          <SceneViewer
            v-if="scene"
            :scene="sceneForSide('yungang', leftHotspots)"
            chapter-slug="northern-wei"
            aspect="auto"
            source-label="历史遗址实拍 · 云冈石窟第20窟"
            source-url="https://commons.wikimedia.org/wiki/File:Cave_20,_Yungang_Grottoes.jpg"
            :lens-open="lensOpen || !!activeCategory"
            :lens-filter="lensFilterFor('yungang')"
            @select="onSelect"
          >
            <template #background>
              <svg :viewBox="`0 0 ${boxW} ${boxH}`" preserveAspectRatio="none" class="wei__svg">
                <defs>
                  <linearGradient :id="`wei-cliff-${uid}`" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="var(--color-paper-200)" />
                    <stop offset="100%" stop-color="var(--color-paper-100)" />
                  </linearGradient>
                  <!-- 坐佛：局部坐标 (0,0) 为足下，向上 200 单位 -->
                  <g :id="`wei-buddha-${uid}`">
                    <circle cx="0" cy="-152" r="36" fill="none" stroke="var(--chapter-accent)" stroke-width="1.4" opacity="0.5" />
                    <circle cx="0" cy="-152" r="19" fill="var(--chapter-accent)" opacity="0.18" />
                    <circle cx="0" cy="-152" r="19" fill="none" stroke="var(--chapter-accent)" stroke-width="1.6" />
                    <circle cx="0" cy="-170" r="7" fill="var(--chapter-accent)" opacity="0.35" />
                    <path d="M-40 0 L-27 -104 Q0 -124 27 -104 L40 0 Z" fill="var(--chapter-accent)" opacity="0.16" stroke="var(--chapter-accent)" stroke-width="1.5" stroke-linejoin="round" />
                    <ellipse cx="0" cy="-8" rx="47" ry="14" fill="var(--chapter-accent)" opacity="0.12" stroke="var(--chapter-accent)" stroke-width="1.3" />
                    <path d="M-24 -78 Q0 -66 24 -78" fill="none" stroke="var(--chapter-accent)" stroke-width="1.2" opacity="0.6" />
                    <path d="M-28 -52 Q0 -40 28 -52" fill="none" stroke="var(--chapter-accent)" stroke-width="1.2" opacity="0.6" />
                    <path d="M-32 -26 Q0 -14 32 -26" fill="none" stroke="var(--chapter-accent)" stroke-width="1.2" opacity="0.6" />
                  </g>
                  <!-- 胁侍 / 菩萨：局部坐标同上 -->
                  <g :id="`wei-attendant-${uid}`">
                    <circle cx="0" cy="-176" r="23" fill="none" stroke="var(--chapter-accent)" stroke-width="1.2" opacity="0.45" />
                    <circle cx="0" cy="-176" r="13" fill="var(--chapter-accent)" opacity="0.2" stroke="var(--chapter-accent)" stroke-width="1.3" />
                    <path d="M-16 0 L-12 -150 Q0 -164 12 -150 L16 0 Z" fill="var(--chapter-accent)" opacity="0.14" stroke="var(--chapter-accent)" stroke-width="1.3" stroke-linejoin="round" />
                  </g>
                  <!-- 飞天：飘带 + 弧线，克制示意 -->
                  <g :id="`wei-flying-${uid}`">
                    <path d="M-30 6 Q-8 -14 22 -4" fill="none" stroke="var(--chapter-accent)" stroke-width="1.3" opacity="0.6" />
                    <path d="M-26 12 Q0 -2 26 8" fill="none" stroke="var(--chapter-accent)" stroke-width="1" opacity="0.4" />
                    <circle cx="20" cy="-6" r="5" fill="var(--chapter-accent)" opacity="0.3" />
                  </g>
                </defs>

                <rect :width="boxW" :height="boxH" fill="var(--color-paper-50)" />
                <!-- 崖壁底色 -->
                <rect :width="boxW" :height="boxH" :fill="`url(#wei-cliff-${uid})`" opacity="0.55" />

                <!-- 云冈：拱形大龛 -->
                <template v-for="n in yungangNiches" :key="`yn-${n.id}`">
                  <path
                    :d="archNichePath(n.nx, n.w, n.top, n.bottom)"
                    fill="var(--chapter-accent)"
                    opacity="0.07"
                    stroke="var(--chapter-accent)"
                    stroke-width="1.4"
                  />
                </template>

                <!-- 主尊大佛 + 两侧胁侍 -->
                <use
                  :href="`#wei-buddha-${uid}`"
                  :transform="`translate(${px(0.5)} ${py(0.92)}) scale(${sc(0.74)})`"
                />
                <use
                  :href="`#wei-attendant-${uid}`"
                  :transform="`translate(${px(0.16)} ${py(0.9)}) scale(${sc(0.46)})`"
                />
                <use
                  :href="`#wei-attendant-${uid}`"
                  :transform="`translate(${px(0.84)} ${py(0.9)}) scale(${sc(0.46)})`"
                />

                <!-- 飞天 -->
                <use :href="`#wei-flying-${uid}`" :transform="`translate(${px(0.33)} ${py(0.26)}) scale(${sc(0.2)})`" />
                <use :href="`#wei-flying-${uid}`" :transform="`translate(${px(0.67)} ${py(0.24)}) scale(${sc(0.2)})`" />

                <text :x="px(0.5)" :y="py(0.985)" class="wei__svg-label" text-anchor="middle">
                  昙曜五窟 · 大佛与胁侍（示意）
                </text>
              </svg>
            </template>
          </SceneViewer>
          <div v-else class="wei__stage-empty">
            <DsIcon name="grid" :size="26" />
            <span>场景数据尚未接入，以下是示意性石窟轮廓。</span>
          </div>
        </div>

        <ul class="wei__cards">
          <li v-if="!sideHasMatch('yungang')" class="wei__slot-empty">
            本侧暂无「{{ activeName }}」类别的已审核证据 —— 这正是两处遗存材料分布并不对称的真实情况。
          </li>
          <li
            v-for="e in leftItems()"
            :key="e.id"
            class="wei__card"
            :class="{ 'is-dim': !isMatched(e), 'is-hit': activeCategory && isMatched(e) }"
          >
            <header class="wei__card-head">
              <span class="wei__card-title">{{ e.title }}</span>
              <span v-if="e.auxiliary" class="wei__card-tag">北朝比较材料</span>
            </header>
            <dl class="wei__layers">
              <div class="wei__layer"><dt>① 看到什么</dt><dd>{{ e.observed }}</dd></div>
              <div class="wei__layer"><dt>② 来源如何描述</dt><dd>{{ e.describedBySource }}</dd></div>
              <div class="wei__layer"><dt>③ 能支持什么</dt><dd>{{ e.supports }}</dd></div>
              <div class="wei__layer wei__layer--no"><dt>④ 不能直接推出什么</dt><dd>{{ e.doesNotSupport }}</dd></div>
            </dl>
            <p v-if="e.caveat" class="wei__card-caveat">注意：{{ e.caveat }}</p>
            <div class="wei__card-actions">
              <button type="button" class="wei__act" @click="emit('select-entity', e.entityId)">
                <DsIcon name="document" :size="12" />看这条证据
              </button>
              <button type="button" class="wei__act" @click="emit('open-chat', e.entityId)">
                <DsIcon name="sparkle" :size="12" />向它提问
              </button>
            </div>
          </li>
        </ul>
      </section>

      <!-- 右：龙门 -->
      <section class="wei__pane">
        <header class="wei__pane-head">
          <span class="wei__pane-name">龙门石窟</span>
          <span class="wei__pane-era">洛阳时期</span>
        </header>

        <div class="wei__stage">
          <SceneViewer
            v-if="scene"
            :scene="sceneForSide('longmen', rightHotspots)"
            chapter-slug="northern-wei"
            aspect="auto"
            source-label="历史遗址实拍 · 龙门石窟古阳洞"
            source-url="https://commons.wikimedia.org/wiki/File:Ancient_Buddhist_Grottoes_at_Longmen-_Guyang_Grotto_Main_Buddha.jpg"
            :lens-open="lensOpen || !!activeCategory"
            :lens-filter="lensFilterFor('longmen')"
            @select="onSelect"
          >
            <template #background>
              <svg :viewBox="`0 0 ${boxW} ${boxH}`" preserveAspectRatio="none" class="wei__svg">
                <rect :width="boxW" :height="boxH" fill="var(--color-paper-50)" />
                <rect :width="boxW" :height="boxH" :fill="`url(#wei-cliff-${uid})`" opacity="0.45" />

                <!-- 龙门：矩形浅龛 -->
                <template v-for="n in longmenNiches" :key="`ln-${n.id}`">
                  <rect
                    :x="px(n.nx - n.w / 2)"
                    :y="py(n.top)"
                    :width="px(n.w)"
                    :height="py(n.bottom) - py(n.top)"
                    fill="var(--chapter-accent)"
                    opacity="0.07"
                    stroke="var(--chapter-accent)"
                    stroke-width="1.4"
                  />
                </template>

                <!-- 卢舍那大佛与胁侍 -->
                <use
                  :href="`#wei-buddha-${uid}`"
                  :transform="`translate(${px(0.5)} ${py(0.9)}) scale(${sc(0.68)})`"
                />
                <use
                  :href="`#wei-attendant-${uid}`"
                  :transform="`translate(${px(0.35)} ${py(0.88)}) scale(${sc(0.44)})`"
                />
                <use
                  :href="`#wei-attendant-${uid}`"
                  :transform="`translate(${px(0.65)} ${py(0.88)}) scale(${sc(0.44)})`"
                />

                <!-- 屋形龛：仿木构建筑形象（建筑类证据） -->
                <path
                  :d="roofPath(ROOF.nx, ROOF.w, ROOF.top, ROOF.bottom)"
                  fill="var(--chapter-accent)"
                  opacity="0.08"
                  stroke="var(--chapter-accent)"
                  stroke-width="1.3"
                />
                <template v-for="(b, i) in longmenBrackets.items" :key="`bk-${i}`">
                  <rect :x="b.x" :y="longmenBrackets.y" :width="b.w" height="7" fill="var(--chapter-accent)" opacity="0.25" />
                </template>

                <!-- 题记壁面（文字类证据） -->
                <rect
                  :x="px(INSCRIPTION.x) - 8"
                  :y="py(INSCRIPTION.y) - 10"
                  :width="px(INSCRIPTION.cw) * 4 + 20"
                  :height="py(INSCRIPTION.ch) * 3 + 22"
                  fill="none"
                  stroke="var(--chapter-accent)"
                  stroke-width="1"
                  stroke-dasharray="4 4"
                  opacity="0.45"
                />
                <rect
                  v-for="(g, i) in inscriptionGrid"
                  :key="`ig-${i}`"
                  :x="g.x"
                  :y="g.y"
                  :width="g.w"
                  :height="g.h"
                  fill="var(--chapter-accent)"
                  opacity="0.1"
                  stroke="var(--chapter-accent)"
                  stroke-width="0.8"
                />
                <text :x="px(0.83)" :y="py(0.4)" class="wei__svg-label" text-anchor="middle">造像题记（示意）</text>

                <text :x="px(0.5)" :y="py(0.985)" class="wei__svg-label" text-anchor="middle">
                  卢舍那大佛与胁侍 · 屋形龛（示意）
                </text>
              </svg>
            </template>
          </SceneViewer>
          <div v-else class="wei__stage-empty">
            <DsIcon name="grid" :size="26" />
            <span>场景数据尚未接入，以下是示意性石窟轮廓。</span>
          </div>
        </div>

        <ul class="wei__cards">
          <li v-if="!sideHasMatch('longmen')" class="wei__slot-empty">
            本侧暂无「{{ activeName }}」类别的已审核证据。
          </li>
          <li
            v-for="e in rightItems()"
            :key="e.id"
            class="wei__card"
            :class="{ 'is-dim': !isMatched(e), 'is-hit': activeCategory && isMatched(e) }"
          >
            <header class="wei__card-head">
              <span class="wei__card-title">{{ e.title }}</span>
              <span v-if="e.auxiliary" class="wei__card-tag">北朝比较材料</span>
            </header>
            <dl class="wei__layers">
              <div class="wei__layer"><dt>① 看到什么</dt><dd>{{ e.observed }}</dd></div>
              <div class="wei__layer"><dt>② 来源如何描述</dt><dd>{{ e.describedBySource }}</dd></div>
              <div class="wei__layer"><dt>③ 能支持什么</dt><dd>{{ e.supports }}</dd></div>
              <div class="wei__layer wei__layer--no"><dt>④ 不能直接推出什么</dt><dd>{{ e.doesNotSupport }}</dd></div>
            </dl>
            <p v-if="e.caveat" class="wei__card-caveat">注意：{{ e.caveat }}</p>
            <div class="wei__card-actions">
              <button type="button" class="wei__act" @click="emit('select-entity', e.entityId)">
                <DsIcon name="document" :size="12" />看这条证据
              </button>
              <button type="button" class="wei__act" @click="emit('open-chat', e.entityId)">
                <DsIcon name="sparkle" :size="12" />向它提问
              </button>
            </div>
          </li>
        </ul>
      </section>
    </div>

    <!-- 场景说明统一显示一次：原图与预标注热点的证据边界。 -->
    <p class="wei__foot">
      <span v-if="scene?.disclaimer">{{ scene.disclaimer }}</span>
      <span v-else>两处石窟画面为示意性轮廓，用于帮助理解空间关系，不等同于考古意义上的精确复原。</span>
      <span v-if="usingFallback" class="wei__foot-flag">证据卡当前为内置演示数据，正式内容接入后自动替换。</span>
    </p>
  </div>
</template>

<style scoped>
.wei {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  min-height: 0;
}

/* ---------- 顶部工具 ---------- */
.wei__bar {
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--sp-4);
}
.wei__cats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}
.wei__cat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 13px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard),
    background-color var(--dur-fast) var(--ease-standard);
}
.wei__cat:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.wei__cat.is-on {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
  color: #fff;
}
.wei__cat--clear {
  color: var(--color-ink-500);
}
.wei__count {
  margin-left: auto;
  flex: none;
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

/* ---------- 内容红线提示 ---------- */
.wei__redline {
  flex: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-btn);
  background: color-mix(in srgb, var(--chapter-accent) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--chapter-accent) 28%, transparent);
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}

/* ---------- 双屏（设计系统 §59：1440 下左右各 50%） ---------- */
.wei__panes {
  flex: 1;
  min-height: 0;
  /* C02 骨架的高度是内容驱动（flex: 1 的父级高度不确定），
     每侧内部又全部绝对定位、不贡献内容高度，所以这里用视口高度兜一个下限，
     保证双屏始终有可用高度，同时绝不把整页撑出视口。 */
  min-height: calc(100vh - var(--header-h) - 296px);
  display: flex;
  gap: var(--sp-6);
}
/**
 * 每侧内部一律用绝对定位：石窟画面与证据卡的**内容高度不会被计入
 * 最小内容高度**，否则一屏证据会把整页越撑越高（C02 的高度链是
 * flex: 1 + min-height: 0，内容高度仍会参与父级 intrinsic 计算）。
 */
.wei__pane {
  position: relative;
  flex: 1 1 50%;
  min-width: 0;
  min-height: 0;
}
.wei__pane-head {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 30px;
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  border-bottom: 1px solid var(--color-border);
}
.wei__pane-name {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  color: var(--chapter-accent);
}
.wei__pane-era {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

.wei__stage {
  position: absolute;
  top: 38px;
  left: 0;
  right: 0;
  height: 44%;
  min-height: 110px;
}
.wei__stage :deep(.scene) {
  height: 100%;
}
.wei__svg {
  width: 100%;
  height: 100%;
  display: block;
}
.wei__svg-label {
  font-family: var(--font-ui);
  font-size: 11px;
  fill: var(--color-ink-500);
}
.wei__stage-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

/* ---------- 证据卡 ---------- */
.wei__cards {
  position: absolute;
  top: calc(38px + 44% + var(--sp-2));
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  padding-right: 4px;
}
.wei__card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-panel);
  padding: var(--sp-3);
  transition:
    opacity var(--dur-normal) var(--ease-standard),
    border-color var(--dur-normal) var(--ease-standard),
    box-shadow var(--dur-normal) var(--ease-standard);
}
/* 弱化：仍然可读，只是不抢注意力 —— 不隐藏，避免用户以为证据不存在 */
.wei__card.is-dim {
  opacity: 0.34;
}
.wei__card.is-hit {
  border-color: var(--chapter-accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--chapter-accent) 22%, transparent);
}
.wei__card-head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}
.wei__card-title {
  font-size: var(--fs-body-s);
  font-weight: 600;
  color: var(--color-ink-900);
}
.wei__card-tag {
  flex: none;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-pill);
  color: var(--evidence-reconstruction);
  border: 1px solid color-mix(in srgb, var(--evidence-reconstruction) 45%, transparent);
}

/* 固定四层 */
.wei__layers {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.wei__layer dt {
  font-size: var(--fs-caption);
  font-weight: 600;
  color: var(--chapter-accent);
}
.wei__layer dd {
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}
.wei__layer--no dt {
  color: var(--evidence-disputed);
}
.wei__card-caveat {
  margin-top: var(--sp-2);
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--evidence-disputed);
}
.wei__card-actions {
  display: flex;
  gap: var(--sp-2);
  margin-top: var(--sp-2);
}
.wei__act {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.wei__act:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.wei__slot-empty {
  border: 1px dashed color-mix(in srgb, var(--chapter-accent) 35%, transparent);
  border-radius: var(--radius-card);
  padding: var(--sp-3);
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
  background: var(--color-paper-100);
}

/* ---------- 底部说明 ---------- */
.wei__foot {
  flex: none;
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
}
.wei__foot-flag {
  color: var(--evidence-disputed);
}
/* 队员二：390×844 适配 —— 双屏改单列，触屏点击区≥44px */
@media (max-width: 900px) {
  .wei__panes { flex-direction: column; min-height: 0; }
  .wei__pane { min-height: 420px; }
  .wei__cards { position: static; max-height: 320px; }
  .wei__stage { position: relative; top: 0; height: 260px; margin-top: 38px; }
  .wei__cat, .wei__act { min-height: 44px; }
}
</style>
