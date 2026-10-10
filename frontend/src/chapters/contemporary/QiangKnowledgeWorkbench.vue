<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DsIcon from '@/components/ds/DsIcon.vue'
import DsButton from '@/components/ds/DsButton.vue'
import { getEntities } from '@/api/endpoints'
import { useEntityStore } from '@/stores/entity'
import type { Chapter, Entity, Hotspot, MeaningStatus, Scene } from '@/types'

/**
 * 当代 C02 羌绣知识工坊（规格 §8、§9、§19）
 *
 * 本章没有空间场景，也没有热点坐标（scene.json 明确声明）：
 * 因此本组件完全不使用视觉识别 / OCR，也不渲染任何空间背景，
 * 改为「四宫格知识工作台」——针法 / 纹样·题材 / 绣品·用途 / 传承实践。
 *
 * 内容红线对应的设计决策：
 *
 * 1. 针法是手工技艺，不是图像风格。界面上不出现「滤镜」「风格」「特效」这类词，
 *    每张针法卡固定提示「数字示意不等于实际手工技艺」（§10.1）。
 * 2. 纹样卡只有在 meaning_status === 'DOCUMENTED' 且有审核过的含义文本时
 *    才展示具体寓意；否则固定显示「当前审核资料没有提供足够依据解释这一
 *    具体纹样的固定文化寓意。」，绝不由画面推断寓意。
 * 3. 题材类别不等于具体传统纹样名称，因此类别卡只作为入口，不做定名。
 * 4. 绣品与针法 / 纹样的对应关系必须有来源 Claim 才存在，界面不暗示
 *    「某绣品就是用某种针法做的」。
 * 5. 传承实践只展示公开资料层面的实践类型，不生成任何传承人人格对白。
 * 6. 卡片状态如实区分：未探索 / 已探索 / 可共创 / 仅展示。
 *    可共创必须同时通过文化审核、权利审核与生成策略审核；
 *    当前第一批内容大多为「仅展示」，界面不美化这一点。
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

const router = useRouter()
const entityStore = useEntityStore()

/* ------------------------------------------------------------------
   scene.workbench：Scene 类型未声明该字段，这里用局部扩展类型读取，
   不改动共享类型文件。scene 为空或没有 workbench 时使用兜底 id 列表（§8.2–8.4）。
   ------------------------------------------------------------------ */

interface WorkbenchData {
  technique_ids?: string[]
  motif_category_ids?: string[]
  object_ids?: string[]
  practice_ids?: string[]
  entry_groups?: { key: string; label: string; entity_ids: string[]; sort_order?: number }[]
  cocreation?: {
    applications?: string[]
    compositions?: string[]
    confirmation_text?: string
    result_label?: string
  }
}

interface SceneWithWorkbench extends Scene {
  workbench?: WorkbenchData | null
}

const workbench = computed<WorkbenchData | null>(
  () => (props.scene as SceneWithWorkbench | null)?.workbench ?? null,
)

/** 兜底 id 列表，严格取自实施规格 §8.2–8.4 */
const FALLBACK = {
  technique: [
    'technique_tiaohua',
    'technique_zhizi',
    'technique_nahua',
    'technique_piehua',
    'technique_gouhua',
  ],
  motif: ['motif_flora', 'motif_fruit', 'motif_birds_animals', 'motif_people', 'motif_geometric'],
  object: [
    'object_apron',
    'object_embroidery_shoes',
    'object_sleeve_cover',
    'object_headscarf',
    'object_sachet',
    'object_insole',
  ],
  practice: [
    'practice_digital_archiving',
    'practice_ich_workshop',
    'practice_school_education',
    'practice_contemporary_design',
    'practice_copyright_protection',
  ],
}

function pickIds(value: string[] | undefined, fallback: string[]): string[] {
  return Array.isArray(value) && value.length ? value : fallback
}

/** 兜底显示名，全部来自已审核内容；不自行编造任何传统纹样名称 */
const FALLBACK_NAMES: Record<string, string> = {
  technique_tiaohua: '架花（挑花）',
  technique_zhizi: '织字（提花）',
  technique_nahua: '纳花（扎花）',
  technique_piehua: '撇花（平绣花）',
  technique_gouhua: '勾花（链子扣）',
  motif_flora: '花草植物',
  motif_category_flora: '花草植物',
  motif_fruit: '蔬果',
  motif_category_fruit: '蔬果',
  motif_birds_animals: '飞禽走兽',
  motif_category_birds_animals: '飞禽走兽',
  motif_people: '人物',
  motif_category_people: '人物',
  motif_geometric: '几何构图',
  motif_category_geometric: '几何构图',
  object_apron: '围腰',
  object_embroidery_shoes: '绣花鞋',
  object_sleeve_cover: '袖套',
  object_headscarf: '头巾',
  object_sachet: '香包',
  object_insole: '鞋垫',
  practice_digital_archiving: '数字化建档',
  practice_ich_workshop: '非遗工坊',
  practice_school_education: '学校课程与研培',
  practice_contemporary_design: '当代文创开发',
  practice_copyright_protection: '版权保护实践',
}

/* ---------------- 实体元数据（用于名称与状态，不做任何推断） ---------------- */

const entities = ref<Record<string, Entity>>({})

onMounted(async () => {
  try {
    const list = await getEntities({ chapter_id: props.chapter.id })
    const next: Record<string, Entity> = {}
    for (const e of list) next[e.id] = e
    entities.value = next
  } catch {
    // 知识卡必须能被浏览：元数据拉取失败不影响工作台显示，名称回退到兜底表
    entities.value = {}
  }
})

function entityOf(id: string): Entity | undefined {
  return entities.value[id]
}

function nameOf(id: string): string {
  const e = entityOf(id)
  return e?.display_name || e?.name || FALLBACK_NAMES[id] || id
}

/** 已探索：用户已经打开过该实体的详情抽屉 */
function isExplored(id: string): boolean {
  return !!entityStore.cache[id] || props.selectedEntityId === id
}

/** 可共创：必须显式通过生成策略审核，默认一律为否 */
function isEligible(id: string): boolean {
  const x = entityOf(id)?.extra
  if (!x) return false
  if (x.is_generation_reference_allowed === true) return true
  const p = typeof x.generation_policy === 'string' ? x.generation_policy : ''
  return p === 'ALLOW_COMBINATION' || p === 'ALLOW_COLOR_VARIATION' || p === 'ALLOW_SCALE_ONLY'
}

/** 仅展示：内容或权利审核明确不允许进入 AI 共创 */
function isDisplayOnly(id: string): boolean {
  const x = entityOf(id)?.extra
  if (!x) return false
  if (x.is_generation_reference_allowed === false) return true
  const p = typeof x.generation_policy === 'string' ? x.generation_policy : ''
  return p === 'DISPLAY_ONLY' || p === 'BLOCKED' || p === 'REVIEW_REQUIRED'
}

type CardState = 'UNSEEN' | 'VIEWED' | 'ELIGIBLE' | 'DISPLAY_ONLY'

function cardState(id: string): CardState {
  if (isEligible(id)) return 'ELIGIBLE'
  if (isExplored(id)) return isDisplayOnly(id) ? 'DISPLAY_ONLY' : 'VIEWED'
  return 'UNSEEN'
}

const STATE_LABEL: Record<CardState, string> = {
  UNSEEN: '未探索',
  VIEWED: '已探索',
  ELIGIBLE: '可共创',
  DISPLAY_ONLY: '仅展示',
}

/* ---------------- 纹样卡：没有 DOCUMENTED 就不展示任何具体寓意 ---------------- */

/** 内容侧未提供依据时的固定文案（与 content 的 fixed_ui_text 完全一致） */
const NO_MEANING_TEXT = '当前审核资料没有提供足够依据解释这一具体纹样的固定文化寓意。'

const HOW_TO_READ_MOTIF = '题材类别不等于具体传统纹样名称，因此本工作台只把它作为入口。'

function meaningStatusOf(id: string): MeaningStatus | undefined {
  const x = entityOf(id)?.extra
  if (!x) return undefined
  return (x.meaning_status as MeaningStatus) ?? (x.default_meaning_status_for_members as MeaningStatus)
}

function documentedMeaning(id: string): string | null {
  const x = entityOf(id)?.extra
  if (!x) return null
  if (meaningStatusOf(id) !== 'DOCUMENTED') return null
  const text = typeof x.meaning_text === 'string' ? x.meaning_text : ''
  return text.length ? text : null
}

/* ---------------- 四宫格数据 ---------------- */

type GroupKey = 'technique' | 'motif' | 'object' | 'practice'

interface Group {
  key: GroupKey
  label: string
  note: string
  ids: string[]
  /** 针法卡必须固定显示的行 */
  fixedNote?: string
}

const groups = computed<Group[]>(() => {
  const wb = workbench.value
  return [
    {
      key: 'technique',
      label: '针法',
      note: '针法是手工技艺，不是图像风格，也不是滤镜或视觉特效。本平台只说明「被官方资料列为常见针法」这一公开事实，不提供完整针法教学，也不做针法鉴定。',
      fixedNote: '数字示意不等于实际手工技艺',
      ids: pickIds(wb?.technique_ids, FALLBACK.technique),
    },
    {
      key: 'motif',
      label: '纹样 / 题材',
      note: HOW_TO_READ_MOTIF + '没有审核过的含义依据时，界面不展示任何具体寓意。',
      ids: pickIds(wb?.motif_category_ids, FALLBACK.motif),
    },
    {
      key: 'object',
      label: '绣品 / 用途',
      note: '绣品与针法、纹样的对应关系必须有来源支撑；第一批资料未提供该对应关系时，本平台不建立这类关系。',
      ids: pickIds(wb?.object_ids, FALLBACK.object),
    },
    {
      key: 'practice',
      label: '传承实践',
      note: '只展示公开资料层面的实践类型，不编写具体单位、人数、产值等信息，也不生成传承人人格对白。',
      ids: pickIds(wb?.practice_ids, FALLBACK.practice),
    },
  ]
})

/* ---------------- Tab / 过滤 ---------------- */

type TabKey = 'technique' | 'motif' | 'object' | 'chat' | 'graph' | 'create'

const TABS: { key: TabKey; label: string; icon: 'needle' | 'palette' | 'artifact' | 'sparkle' | 'nodes' | 'grid' }[] = [
  { key: 'technique', label: '针法', icon: 'needle' },
  { key: 'motif', label: '纹样题材', icon: 'palette' },
  { key: 'object', label: '绣品', icon: 'artifact' },
  { key: 'chat', label: 'AI', icon: 'sparkle' },
  { key: 'graph', label: '图谱', icon: 'nodes' },
  { key: 'create', label: '共创', icon: 'grid' },
]

/** null = 四宫格全部显示 */
const activeFilter = ref<GroupKey | null>(null)
const onlyEligible = ref(false)
const onlyExplored = ref(false)

type FilterTabKey = Extract<TabKey, GroupKey>

function isFilterTab(key: TabKey): key is FilterTabKey {
  return key === 'technique' || key === 'motif' || key === 'object'
}

function onTab(key: TabKey) {
  if (key === 'chat') {
    emit('open-chat')
    return
  }
  if (key === 'graph') {
    emit('open-graph')
    return
  }
  if (key === 'create') {
    goCreate()
    return
  }
  // 再次点击当前分类 → 回到四宫格全部
  activeFilter.value = activeFilter.value === key ? null : key
}

const visibleGroups = computed<Group[]>(() => {
  const list = groups.value
  if (!activeFilter.value) return list
  return list.filter((g) => g.key === activeFilter.value)
})

function visibleIds(g: Group): string[] {
  return g.ids.filter((id) => {
    if (onlyEligible.value && !isEligible(id)) return false
    if (onlyExplored.value && !isExplored(id)) return false
    return true
  })
}

const TOTAL_NODES = computed(() => groups.value.reduce((n, g) => n + g.ids.length, 0))
const exploredCount = computed(
  () => groups.value.reduce((n, g) => n + g.ids.filter(isExplored).length, 0),
)

/** 底部固定提示（§8.1） */
const FOOT_HINT = '先认识元素，再把「可用于共创」的元素加入你的创作篮'

function goCreate() {
  void router.push('/chapter/contemporary/create')
}

function onCard(id: string) {
  emit('select-entity', id)
}
</script>

<template>
  <div class="wk" :class="{ 'is-lens': lensOpen }">
    <!-- ============ 顶部 Tab ============ -->
    <header class="wk__bar">
      <nav class="wk__tabs" aria-label="工坊视图">
        <button
          v-for="t in TABS"
          :key="t.key"
          class="wk__tab"
          :class="{ 'is-on': isFilterTab(t.key) && activeFilter === t.key }"
          type="button"
          @click="onTab(t.key)"
        >
          <DsIcon :name="t.icon" :size="15" />
          <span>{{ t.label }}</span>
        </button>
      </nav>

      <div class="wk__filters">
        <button
          class="wk__chip"
          :class="{ 'is-on': onlyEligible }"
          type="button"
          @click="onlyEligible = !onlyEligible"
        >
          只看可共创
        </button>
        <button
          class="wk__chip"
          :class="{ 'is-on': onlyExplored }"
          type="button"
          @click="onlyExplored = !onlyExplored"
        >
          只看已探索
        </button>
      </div>
    </header>

    <Transition name="wk-lens">
      <p v-if="lensOpen" class="wk__lens-note">
        <DsIcon name="layers" :size="14" />
        <span>来源与权利透镜已开启：只有明确通过文化、权利与生成策略审核的元素会标为“可共创”；未知状态默认不放行。</span>
      </p>
    </Transition>

    <!-- ============ 四宫格 ============ -->
    <div class="wk__body">
      <p v-if="activeFilter === null" class="wk__legend">
        再次点击当前分类可返回四宫格全部视图。
      </p>

      <div class="wk__grid" :class="{ 'is-single': activeFilter !== null }">
        <section v-for="g in visibleGroups" :key="g.key" class="wk__panel">
          <header class="wk__panel-head">
            <h3 class="wk__panel-title">{{ g.label }}</h3>
            <span class="wk__panel-count">{{ visibleIds(g).length }} 个条目</span>
          </header>

          <p class="wk__panel-note">{{ g.note }}</p>

          <!-- 针法卡固定提示：数字示意不等于实际手工技艺 -->
          <p v-if="g.fixedNote" class="wk__panel-fixed">
            <DsIcon name="alert" :size="13" />
            {{ g.fixedNote }}
          </p>

          <ul class="wk__cards">
            <li v-for="id in visibleIds(g)" :key="id">
              <button
                class="wk__card"
                :class="[`is-${cardState(id).toLowerCase()}`, { 'is-current': selectedEntityId === id }]"
                type="button"
                @click="onCard(id)"
              >
                <span class="wk__card-top">
                  <span class="wk__card-name">{{ nameOf(id) }}</span>
                  <span class="wk__card-state" :class="`is-${cardState(id).toLowerCase()}`">
                    {{ STATE_LABEL[cardState(id)] }}
                  </span>
                </span>

                <!-- 纹样 / 题材卡：没有 DOCUMENTED 依据时不展示任何具体寓意 -->
                <template v-if="g.key === 'motif'">
                  <span v-if="documentedMeaning(id)" class="wk__card-meaning">
                    文化含义：{{ documentedMeaning(id) }}
                  </span>
                  <span v-else class="wk__card-meaning is-none">{{ NO_MEANING_TEXT }}</span>
                </template>

                <!-- 针法卡：固定技艺提示 -->
                <span v-else-if="g.key === 'technique'" class="wk__card-note">
                  {{ g.fixedNote }}
                </span>

                <span class="wk__card-cta">
                  <DsIcon name="arrow-right" :size="13" />
                  查看详情
                </span>
              </button>
            </li>

            <li v-if="!visibleIds(g).length" class="wk__cards-empty">
              当前筛选条件下没有条目。
            </li>
          </ul>
        </section>
      </div>
    </div>

    <!-- ============ 底部固定提示 ============ -->
    <footer class="wk__foot">
      <p class="wk__foot-hint">
        <DsIcon name="info" :size="15" />
        <span>{{ FOOT_HINT }}</span>
      </p>

      <div class="wk__foot-right">
        <span class="wk__foot-count">已探索 {{ exploredCount }} 个知识节点</span>
        <span class="wk__foot-total">共 {{ TOTAL_NODES }} 个</span>
        <DsButton variant="primary" size="m" @click="goCreate">
          <span class="wk__foot-btn">
            <DsIcon name="sparkle" :size="15" />
            进入 AI 共创
          </span>
        </DsButton>
      </div>
    </footer>

    <!-- 场景自带的说明（本章声明没有空间场景、不使用任何识别算法） -->
    <p v-if="scene?.disclaimer" class="wk__disclaimer">{{ scene.disclaimer }}</p>
  </div>
</template>

<style scoped>
.wk {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.wk__lens-note {
  flex: none;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 13px;
  border: 1px solid color-mix(in srgb, var(--chapter-accent) 32%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--chapter-accent) 9%, rgba(255,255,255,.72));
  color: var(--color-mineral-800);
  font-size: var(--fs-caption);
  box-shadow: 0 8px 24px rgba(50,92,82,.06);
}
.wk.is-lens .wk__card-state { box-shadow: 0 0 0 1px currentColor; }
.wk-lens-enter-active,.wk-lens-leave-active { transition: opacity 180ms ease, transform 180ms ease; }
.wk-lens-enter-from,.wk-lens-leave-to { opacity: 0; transform: translateY(-4px); }

/* ================= 顶部 ================= */
.wk__bar {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
}
.wk__tabs {
  display: flex;
  gap: var(--sp-2);
  flex-wrap: wrap;
}
.wk__tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: var(--color-panel);
  color: var(--color-ink-700);
  font-size: var(--fs-body-s);
  transition:
    background-color var(--dur-fast) var(--ease-standard),
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.wk__tab:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.wk__tab.is-on {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
  color: #fff;
}
.wk__filters {
  display: flex;
  gap: var(--sp-2);
}
.wk__chip {
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  border: 1px dashed var(--color-border);
  background: transparent;
  color: var(--color-ink-500);
  font-size: var(--fs-caption);
}
.wk__chip:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.wk__chip.is-on {
  border-style: solid;
  border-color: var(--chapter-accent);
  background: color-mix(in srgb, var(--chapter-accent) 12%, transparent);
  color: var(--chapter-accent);
}

/* ================= 四宫格 ================= */
.wk__body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 2px;
}
.wk__legend {
  margin: 0 0 var(--sp-2);
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.wk__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--gap-module);
  align-items: start;
}
.wk__grid.is-single {
  grid-template-columns: minmax(0, 1fr);
}

.wk__panel {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--pad-card);
  box-shadow: var(--shadow-card);
}
.wk__panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-2);
  padding-bottom: var(--sp-2);
  border-bottom: 1px solid var(--color-border);
}
.wk__panel-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  color: var(--color-ink-900);
}
.wk__panel-count {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.wk__panel-note {
  margin: var(--sp-3) 0 0;
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
}
.wk__panel-fixed {
  margin: var(--sp-2) 0 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--evidence-disputed) 14%, transparent);
  color: var(--color-ink-900);
  font-size: var(--fs-caption);
}

/* ---------- 卡片 ---------- */
.wk__cards {
  list-style: none;
  margin: var(--sp-4) 0 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: var(--sp-3);
}
.wk__card {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  text-align: left;
  padding: var(--sp-3);
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: var(--color-paper-50);
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    box-shadow var(--dur-fast) var(--ease-standard),
    transform var(--dur-fast) var(--ease-standard);
}
.wk__card:hover {
  border-color: var(--chapter-accent);
  box-shadow: var(--shadow-card);
  transform: translateY(-1px);
}
.wk__card.is-current {
  border-color: var(--chapter-accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--chapter-accent) 30%, transparent);
}
/* 可共创：唯一带章节色描边的状态 */
.wk__card.is-eligible {
  border-color: color-mix(in srgb, var(--chapter-accent) 55%, transparent);
}
.wk__card.is-display_only {
  background: var(--color-paper-100);
}

.wk__card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-2);
}
.wk__card-name {
  font-size: var(--fs-body-s);
  font-weight: 600;
  color: var(--color-ink-900);
  line-height: var(--lh-body-s);
}
.wk__card-state {
  flex: none;
  padding: 1px 8px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-caption);
  border: 1px solid var(--color-border);
  color: var(--color-ink-500);
  background: var(--color-paper-100);
}
.wk__card-state.is-viewed {
  border-color: color-mix(in srgb, var(--color-jade-600) 45%, transparent);
  color: var(--color-jade-600);
  background: transparent;
}
.wk__card-state.is-eligible {
  border-color: var(--chapter-accent);
  background: var(--chapter-accent);
  color: #fff;
}
.wk__card-state.is-display_only {
  border-style: dashed;
  color: var(--color-ink-500);
  background: transparent;
}

.wk__card-meaning,
.wk__card-note {
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}
.wk__card-meaning.is-none {
  color: var(--color-ink-500);
  font-style: normal;
}
.wk__card-note {
  padding-left: var(--sp-2);
  border-left: 2px solid color-mix(in srgb, var(--evidence-disputed) 55%, transparent);
  color: var(--color-ink-500);
}
.wk__card-cta {
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--fs-caption);
  color: var(--chapter-accent);
}

.wk__cards-empty {
  grid-column: 1 / -1;
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  border: 1px dashed var(--color-border);
  color: var(--color-ink-500);
  font-size: var(--fs-body-s);
}

/* ================= 底部 ================= */
.wk__foot {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  border: 1px solid var(--color-border);
}
.wk__foot-hint {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
}
.wk__foot-hint :deep(svg) {
  color: var(--chapter-accent);
}
.wk__foot-right {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}
.wk__foot-count {
  font-size: var(--fs-body-s);
  color: var(--color-ink-900);
  font-weight: 600;
}
.wk__foot-total {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.wk__foot-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.wk__disclaimer {
  flex: none;
  margin: 0;
  font-size: var(--fs-caption);
  line-height: var(--lh-caption);
  color: var(--color-ink-500);
}

@media (max-width: 1366px) {
  .wk__grid {
    gap: var(--sp-6);
  }
  .wk__panel {
    padding: var(--sp-4);
  }
}
/* 队员二：390×844适配 —— 四宫格改单列 */
@media (max-width: 900px) {
  .wk__grid { grid-template-columns: 1fr; }
  .wk__tab, .wk__chip { min-height: 44px; }
  .wk__cards { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 520px) {
  .wk__cards { grid-template-columns: 1fr; }
}
</style>
