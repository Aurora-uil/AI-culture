<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GlobalHeader from '@/components/global/GlobalHeader.vue'
import ChapterProgress from '@/components/global/ChapterProgress.vue'
import SceneViewer from '@/components/scene/SceneViewer.vue'
import EntityDrawer from '@/components/entity/EntityDrawer.vue'
import SourceDrawer from '@/components/source/SourceDrawer.vue'
import DsButton from '@/components/ds/DsButton.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import GameQuestDock from '@/components/game/GameQuestDock.vue'
import GameSceneReveal from '@/components/game/GameSceneReveal.vue'
import { GAME_CATALOG } from '@/game/catalog'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
import { useEntityStore } from '@/stores/entity'
import { useExplorationStore } from '@/stores/exploration'
import { useGameStore } from '@/stores/game'
import { getCocreationElements } from '@/api/endpoints'
import type { ChapterSlug, Entity, Hotspot } from '@/types'

/**
 * C02 核心探索场景（设计系统 §22 / §23）
 *
 * 场景始终保留：
 *   左上：章节上下文
 *   右上：核心工具
 *   底部：当前任务 + 探索进度
 *
 * 六章共用本页骨架，差异由各章专属组件（透镜 / 地图 / 画卷 / 工坊）提供。
 */
const route = useRoute()
const router = useRouter()
const chapterStore = useChapterStore()
const entityStore = useEntityStore()
const exploration = useExplorationStore()
const game = useGameStore()

const slug = computed(() => route.params.slug as string)
const chapterSlug = computed(() => slug.value as ChapterSlug)
const chapter = computed(() => chapterStore.current)
const scene = computed(() => chapterStore.scene)
const meta = computed(() => GAME_CATALOG[chapterSlug.value])
const storyProgress = computed(() => game.progressFor(chapterSlug.value))
const isExploreMode = computed(() => route.query.module === 'explore')
const discovery = ref('')
let discoveryTimer: number | undefined
const STORY_VISIT_STORAGE_KEY = 'tongxin.chapter.story.visits.v1'

function markStoryVisited(value: ChapterSlug) {
  try {
    const visits = JSON.parse(localStorage.getItem(STORY_VISIT_STORAGE_KEY) ?? '{}') as Partial<Record<ChapterSlug, boolean>>
    visits[value] = true
    localStorage.setItem(STORY_VISIT_STORAGE_KEY, JSON.stringify(visits))
  } catch {
    // 本地进度不可用时不阻断剧情。
  }
}

function showDiscovery(label: string) {
  discovery.value = label
  if (discoveryTimer) window.clearTimeout(discoveryTimer)
  discoveryTimer = window.setTimeout(() => (discovery.value = ''), 1450)
}

onBeforeUnmount(() => {
  if (discoveryTimer) window.clearTimeout(discoveryTimer)
})

/** 各章专属交互组件注册表（设计系统 §76 Interaction Registry） */
const CHAPTER_COMPONENTS: Record<string, ReturnType<typeof defineAsyncComponent>> = {
  han: defineAsyncComponent(() => import('@/chapters/han/HanRouteMap.vue')),
  'northern-wei': defineAsyncComponent(() => import('@/chapters/wei/WeiEvidenceCompare.vue')),
  tang: defineAsyncComponent(() => import('@/chapters/tang/TangScrollViewer.vue')),
  yuan: defineAsyncComponent(() => import('@/chapters/yuan/YuanYuntaiScene.vue')),
  qing: defineAsyncComponent(() => import('@/chapters/qing/QingMigrationMap.vue')),
  contemporary: defineAsyncComponent(
    () => import('@/chapters/contemporary/QiangKnowledgeWorkbench.vue'),
  ),
}

const chapterComponent = computed(() => CHAPTER_COMPONENTS[slug.value] ?? null)

const LENS_LABELS: Record<string, string> = {
  han: '路线证据透镜',
  'northern-wei': '文化证据对照尺',
  tang: '画内 / 画外透镜',
  yuan: '六体文字透镜',
  qing: '路线精度透镜',
  contemporary: '来源与权利透镜',
}
const lensLabel = computed(() => LENS_LABELS[slug.value] ?? '证据透镜')
const canShowLens = computed(() => Boolean(chapterComponent.value))

/** 六体文字等按预设顺序切换 */
const entitySequence = ref<string[]>([])

const guides = ref<string[]>([])
const guideIndex = ref(0)
const guideClosed = ref(false)

onMounted(async () => {
  const id = SLUG_TO_ID[slug.value as keyof typeof SLUG_TO_ID]
  if (!id) return
  if (chapterStore.current?.id !== id) await chapterStore.loadChapter(id)
  await exploration.ensureSession(id)
  exploration.track('SCENE_ENTER', {}, id)
  game.mark(slug.value as ChapterSlug, 'ENTER')
  if (route.query.module === 'explore') {
    chapterStore.setLens(true)
    exploration.track('LENS_OPEN', { metadata: { entry: 'task_hall' } }, id)
    game.mark(slug.value as ChapterSlug, 'LENS')
  } else {
    markStoryVisited(slug.value as ChapterSlug)
  }
  if (slug.value === 'yuan') {
    exploration.track('YUAN_SCENE_ENTERED', {}, id)
    try {
      const raw = localStorage.getItem('tongxin.yuan.task.v1')
      if (!raw) localStorage.setItem('tongxin.yuan.task.v1', JSON.stringify({ phase: 'SCENE_ENTERED', sceneEntered: true, seenScripts: [] }))
    } catch { /* 本地记录失败不阻断 */ }
  }

  // 元代按六体文字顺序切换
  if (slug.value === 'yuan') {
    entitySequence.value = [
      'script_sanskrit_lantsa',
      'script_tibetan',
      'script_phagspa',
      'script_old_uyghur',
      'script_chinese',
      'script_tangut',
    ]
  }

  guides.value = buildGuides(slug.value)
})

function buildGuides(s: string): string[] {
  const common = '点击发光区域，看看同一历史空间里留下了哪些内容'
  switch (s) {
    case 'yuan':
      return [
        '点击发光区域，看看同一历史空间里留下了哪些文字',
        '试试「六体文字透镜」，可以同时看到六处标注',
        '选一处文字，打开详情后可以直接向它提问',
      ]
    case 'han':
      return [
        '点击地图上的节点，看看道路连接了哪些地方',
        '用「路线透镜」查看路线的可信度分级',
        '选择一件物品，看看它从哪里来、经过哪里',
      ]
    case 'qing':
      return [
        '沿着时间轴推进，理解迁徙的整个过程',
        '路线的可信度是分级的，请留意图例',
        '「抵达以后」会展示接应、赈济与安置',
      ]
    case 'tang':
      return [
        '横向拖动画卷，查看画面中的每个人物',
        '点击禄东赞，可以从画中走到画外',
        '文成公主不在画面里，她需要经由历史事件展开',
      ]
    case 'northern-wei':
      return [
        '左右两处石窟可以对照查看',
        '选择「服饰」「雕塑」等类别，两侧会同步高亮',
        '每条证据都标明了「能支持什么」与「不能推出什么」',
      ]
    default:
      return [
        '先认识针法，再了解纹样题材与绣品用途',
        '把可用于共创的元素加入创作篮',
        '完成来源与使用确认后，才能进入 AI 生成',
      ]
  }
}

const currentGuide = computed(() => guides.value[guideIndex.value] ?? '')

function nextGuide() {
  if (!guides.value.length) return
  guideIndex.value = (guideIndex.value + 1) % guides.value.length
}
function prevGuide() {
  if (!guides.value.length) return
  guideIndex.value = (guideIndex.value - 1 + guides.value.length) % guides.value.length
}

/** 热点点击：选中 → 上报 → 打开详情 → 标记已访问 */
async function onHotspot(h: Hotspot) {
  chapterStore.selectEntity(h.entity_id)
  chapterStore.markSeen(h.id)
  void router.replace({
    query: { ...route.query, entity: h.entity_id },
  })
  const entity = await entityStore.load(h.entity_id, chapter.value?.id, { source_page: 'C02' })
  showDiscovery(entity.display_name || entity.name || h.label || '新线索')
  game.mark(slug.value as ChapterSlug, 'INSPECT', h.entity_id)
  if (slug.value === 'yuan') {
    exploration.track('YUAN_HOTSPOT_OPENED', { entity_id: h.entity_id }, chapter.value?.id)
    exploration.track('ENTITY_VIEW', { entity_id: h.entity_id }, chapter.value?.id)
    try {
      const raw = localStorage.getItem('tongxin.yuan.task.v1')
      const st = raw ? JSON.parse(raw) : { seenScripts: [] }
      const scripts = ['script_sanskrit_lantsa','script_tibetan','script_phagspa','script_old_uyghur','script_chinese','script_tangut']
      if (scripts.includes(h.entity_id) && !st.seenScripts.includes(h.entity_id)) {
        st.seenScripts.push(h.entity_id)
        localStorage.setItem('tongxin.yuan.task.v1', JSON.stringify(st))
        if (st.seenScripts.length === 3) exploration.track('YUAN_THREE_SCRIPTS_OPENED', {}, chapter.value?.id)
        if (st.seenScripts.length >= 6) exploration.track('YUAN_ALL_SCRIPTS_OPENED', {}, chapter.value?.id)
      }
    } catch { /* ignore */ }
  }
}

async function onSelectEntity(entityId: string) {
  const hotspot = chapterStore.hotspots.find((h) => h.entity_id === entityId)
  if (hotspot) {
    chapterStore.selectHotspot(hotspot.id)
    chapterStore.markSeen(hotspot.id)
  }
  const entity = await entityStore.load(entityId, chapter.value?.id)
  showDiscovery(entity.display_name || entity.name || '新线索')
  game.mark(slug.value as ChapterSlug, 'INSPECT', entityId)
}

function toggleLens() {
  const next = !chapterStore.lensOpen
  chapterStore.setLens(next)
  if (next) {
    exploration.track('LENS_OPEN', {}, chapter.value?.id)
    game.mark(slug.value as ChapterSlug, 'LENS')
    if (slug.value === 'yuan') {
      exploration.track('YUAN_SCRIPT_LENS_USED', {}, chapter.value?.id)
    }
  }
}

/** 六体文字透镜：只显示未探索 */
const onlyUnseen = ref(false)
const lensFilter = computed(() => {
  if (!chapterStore.lensOpen) return undefined
  if (!onlyUnseen.value) return () => true
  return (h: Hotspot) => (chapterStore.hotspotStatus[h.id] ?? 'UNSEEN') === 'UNSEEN'
})

const seenCount = computed(() => chapterStore.seenHotspotIds.length)
const totalCount = computed(() => chapterStore.hotspots.length)

function closeEntity() {
  entityStore.close()
  const q = { ...route.query }
  delete q.entity
  void router.replace({ query: q })
}

function goChat(entityId?: string) {
  game.mark(slug.value as ChapterSlug, 'CHAT')
  void router.push({
    path: `/chapter/${slug.value}/chat`,
    query: entityId ? { entity: entityId } : undefined,
  })
}

function goGraph(entityId?: string) {
  game.mark(slug.value as ChapterSlug, 'GRAPH')
  void router.push({
    path: `/chapter/${slug.value}/graph`,
    query: { entity: entityId || chapterStore.selectedEntityId || '' },
  })
}

function openSources(entityId: string) {
  void entityStore.openSources(entityId, chapter.value?.id)
}

/* ---- 元代拓片校勘 ---- */
const showRubbing = ref(false)
const YuanRubbingCompare = defineAsyncComponent(
  () => import('@/chapters/yuan/YuanRubbingCompare.vue'),
)
/** 已查验的六体文字 id（供拓片比对门槛判断） */
const yuanSeenScripts = computed(() => {
  const scripts = ['script_sanskrit_lantsa','script_tibetan','script_phagspa','script_old_uyghur','script_chinese','script_tangut']
  return game.stateFor('yuan').evidenceIds.filter((id) => scripts.includes(id))
})
function onRubbingSubmit(payload: { choice: string }) {  exploration.track('YUAN_DECISION_SUBMITTED', { entity_id: payload.choice }, chapter.value?.id)
  const map: Record<string, string> = { pending: 'leave_pending', compare: 'compare_neighbours', submit: 'submit_preliminary' }
  game.choose(chapterSlug.value, map[payload.choice] ?? 'leave_pending')
  showRubbing.value = false
}

watch(
  () => route.query.entity,
  (id) => {
    if (id && typeof id === 'string' && id !== entityStore.current?.id) {
      void onSelectEntity(id)
    }
  },
)
</script>

<template>
  <div v-if="chapter" class="page game-scene-page">
    <GlobalHeader dark />

    <main class="cs page-body">
      <!-- 工具栏 -->
      <header class="cs__bar">
        <div class="cs__bar-left">
          <button class="cs__hub-link" type="button" @click="router.push(`/chapter/${slug}`)">
            <span aria-hidden="true">←</span>
            <span>返回任务大厅</span>
          </button>
          <span class="cs__era">{{ chapter.era }}</span>
          <span class="cs__title">{{ chapter.title }}</span>
        </div>

        <div class="cs__status" aria-label="本章剧情进度">
          <span>剧情推进</span>
          <i><b :style="{ width: `${storyProgress}%` }" /></i>
          <strong>{{ storyProgress }}%</strong>
        </div>

        <div class="cs__tools">
          <button
            v-if="canShowLens"
            class="cs__tool"
            :class="{ 'is-on': chapterStore.lensOpen }"
            type="button"
            @click="toggleLens"
          >
            <DsIcon name="layers" :size="15" />
            <span>{{ lensLabel }}</span>
          </button>
          <button class="cs__tool" type="button" @click="goChat()">
            <DsIcon name="sparkle" :size="15" />
            <span>AI对话</span>
          </button>
          <button class="cs__tool" type="button" @click="goGraph()">
            <DsIcon name="nodes" :size="15" />
            <span>关系图谱</span>
          </button>
          <button v-if="slug === 'yuan'" class="cs__tool" type="button" @click="showRubbing = true">
            <DsIcon name="document" :size="15" />
            <span>拓片比对</span>
          </button>
        </div>
      </header>

      <!-- 场景主体 -->
      <section class="cs__stage">
        <GameSceneReveal
          :chapter="chapter.sort_order"
          :era="chapter.era"
          :title="meta.gameTitle"
          :role="meta.role"
        />
        <GameQuestDock v-if="!isExploreMode" :slug="chapterSlug" />
        <component
          v-if="chapterComponent"
          :is="chapterComponent"
          :chapter="chapter"
          :scene="scene"
          :hotspot-status="chapterStore.hotspotStatus"
          :lens-open="chapterStore.lensOpen"
          :selected-entity-id="chapterStore.selectedEntityId"
          @select-hotspot="onHotspot"
          @select-entity="onSelectEntity"
          @open-chat="goChat"
          @open-graph="goGraph"
        />

        <Transition name="discovery-cue">
          <div v-if="discovery" class="cs__discovery" role="status" aria-live="polite">
            <span>线索已记入见闻录</span>
            <strong>{{ discovery }}</strong>
          </div>
        </Transition>
      </section>

      <!-- 引导条 -->
      <footer class="cs__guide" v-if="!guideClosed && currentGuide">
        <span class="cs__guide-label">探索提示</span>
        <span class="cs__guide-text">{{ currentGuide }}</span>
        <div class="cs__guide-actions">
          <button class="cs__guide-btn" type="button" @click="prevGuide">上一提示</button>
          <button class="cs__guide-btn" type="button" @click="nextGuide">下一提示</button>
          <button class="cs__guide-btn" type="button" @click="guideClosed = true">关闭</button>
        </div>
        <span class="cs__guide-count">已探索 {{ seenCount }}/{{ totalCount }}</span>
      </footer>
    </main>

    <ChapterProgress
      :era="chapter.era"
      :progress="exploration.progress?.progress ?? 0"
    />

    <!-- 双 Drawer -->
    <EntityDrawer
      :chapter-id="chapter.id"
      :sequence="entitySequence"
      @ask="goChat"
      @graph="goGraph"
      @sources="openSources"
      @select="onSelectEntity"
      @close="closeEntity"
    />
    <SourceDrawer />
    <div v-if="slug === 'yuan' && showRubbing" class="cs__dialogue-overlay" role="dialog" aria-label="拓片校勘">
      <div class="cs__dialogue-box">
        <Suspense>
          <YuanRubbingCompare :seen-scripts="yuanSeenScripts" @submit="onRubbingSubmit" />
          <template #fallback><p>校勘面板加载中……</p></template>
        </Suspense>
        <button class="cs__guide-btn" type="button" @click="showRubbing = false">返回场景（状态保留）</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cs {
  flex: none;
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding-top: var(--sp-4);
  padding-bottom: 0;
  height: calc(100dvh - var(--header-h) - var(--status-h));
  min-height: 0;
  color: #eee5d2;
  background: #0c1413;
}

.game-scene-page { height: 100dvh; overflow: hidden; background: #0c1413; }

/* 元代拓片浮层：覆盖但不销毁场景组件，返回后缩放热点透镜保持 */
.cs__dialogue-overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  background: rgba(8, 14, 13, 0.55);
  padding: 20px;
}
.cs__dialogue-box {
  width: min(720px, 100%);
  max-height: 88dvh;
  overflow: auto;
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 16px;
}

.cs__bar {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-6);
}
.cs__bar-left {
  display: flex;
  align-items: baseline;
  gap: var(--sp-3);
  min-width: 0;
}
.cs__hub-link{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border:1px solid rgba(226,207,169,.17);border-radius:var(--radius-btn);background:rgba(255,255,255,.035);color:rgba(238,229,210,.66);font-size:11px;white-space:nowrap}
.cs__hub-link:hover,.cs__hub-link:focus-visible{border-color:var(--color-luminous-gold);color:#f5e8c8}
.cs__era {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  color: var(--chapter-accent);
}
.cs__title {
  font-size: var(--fs-body-s);
  color: rgba(238, 229, 210, 0.46);
}

.cs__tools {
  display: flex;
  gap: var(--sp-2);
  flex: none;
}
.cs__status {
  margin-left: auto;
  display: grid;
  grid-template-columns: auto clamp(90px, 10vw, 150px) 34px;
  align-items: center;
  gap: 9px;
  padding: 5px 11px;
  border: 1px solid rgba(40,95,97,.16);
  border-radius: 999px;
  background: rgba(248,250,244,.5);
  color: rgba(41,69,74,.52);
  font-size: 10px;
  letter-spacing: .08em;
}
.cs__status i { height: 3px; overflow: hidden; border-radius: 999px; background: rgba(40,95,97,.12); }
.cs__status b { display: block; height: 100%; min-width: 3px; border-radius: inherit; background: linear-gradient(90deg,var(--chapter-accent),var(--color-luminous-gold)); box-shadow: 0 0 12px color-mix(in srgb,var(--chapter-accent) 42%,transparent); transition: width 520ms var(--ease-standard); }
.cs__status strong { color: var(--color-mineral-700); font-size: 10px; }
.cs__tool {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: var(--radius-btn);
  border: 1px solid rgba(226, 207, 169, 0.17);
  background: rgba(255, 255, 255, 0.035);
  font-size: var(--fs-body-s);
  color: rgba(238, 229, 210, 0.62);
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard),
    background-color var(--dur-fast) var(--ease-standard);
}
.cs__tool:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.cs__tool.is-on {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
  color: #fff;
}

.cs__stage {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
}
.cs__discovery {
  position: absolute;
  z-index: calc(var(--z-hud) + 5);
  left: 50%;
  top: 22px;
  min-width: 220px;
  padding: 9px 32px 10px;
  transform: translateX(-50%);
  text-align: center;
  color: #fff8e7;
  background: linear-gradient(90deg,transparent,rgba(26,64,60,.86) 15%,rgba(26,64,60,.9) 85%,transparent);
  text-shadow: 0 2px 12px rgba(0,0,0,.35);
  pointer-events: none;
}
.cs__discovery::before,.cs__discovery::after { content: '◇'; position: absolute; top: 50%; transform: translateY(-50%); color: var(--color-luminous-gold); }
.cs__discovery::before { left: 12px; }.cs__discovery::after { right: 12px; }
.cs__discovery span { display: block; font-size: 9px; letter-spacing: .2em; color: rgba(255,239,202,.68); }
.cs__discovery strong { display: block; margin-top: 1px; font-family: var(--font-display); font-size: 16px; font-weight: 500; letter-spacing: .08em; }
.discovery-cue-enter-active,.discovery-cue-leave-active { transition: opacity 280ms ease, transform 420ms var(--ease-standard), filter 280ms ease; }
.discovery-cue-enter-from,.discovery-cue-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px) scale(.94); filter: blur(4px); }

.cs__guide {
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-4);
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(226, 207, 169, 0.15);
  font-size: var(--fs-body-s);
  margin-bottom: var(--sp-3);
}
.cs__guide-label {
  flex: none;
  color: var(--chapter-accent);
  font-weight: 600;
}
.cs__guide-text {
  color: rgba(238, 229, 210, 0.62);
  min-width: 0;
}
.cs__guide-actions {
  margin-left: auto;
  display: flex;
  gap: var(--sp-2);
  flex: none;
}
.cs__guide-btn {
  border: 0;
  background: transparent;
  font-size: var(--fs-caption);
  color: rgba(238, 229, 210, 0.42);
  padding: 3px 8px;
  border-radius: var(--radius-btn);
}
.cs__guide-btn:hover {
  background: rgba(238, 229, 210, 0.07);
  color: #eee5d2;
}
.cs__guide-count {
  flex: none;
  font-size: var(--fs-caption);
  color: rgba(238, 229, 210, 0.38);
  padding-left: var(--sp-3);
  border-left: 1px solid rgba(226, 207, 169, 0.15);
}

/* V3 青绿场景框：历史场景保留自身色彩，操作界面改为雾青卷面。 */
.cs{color:var(--color-slate-text);background:linear-gradient(145deg,#eaf2e9,#d5e5dc)}
.game-scene-page{background:#dbe8df}
.cs__title{color:rgba(41,69,74,.55)}
.cs__tool{border-color:rgba(40,95,97,.2);background:rgba(248,250,244,.62);color:rgba(41,69,74,.7)}
.cs__tool:hover{background:rgba(255,255,255,.84)}
.cs__tool.is-on{color:#fff}
.cs__guide{background:rgba(248,250,244,.72);border-color:rgba(40,95,97,.18);box-shadow:0 8px 24px rgba(50,92,82,.06)}
.cs__guide-text{color:rgba(41,69,74,.7)}
.cs__guide-btn{color:rgba(41,69,74,.55)}
.cs__guide-btn:hover{background:rgba(40,95,97,.08);color:var(--color-mineral-800)}
.cs__guide-count{color:rgba(41,69,74,.5);border-left-color:rgba(40,95,97,.16)}

/* V4 沉浸式历史舞台：场景成为被青铜金线框住的一帧，而不是普通内容容器。 */
.cs__stage{isolation:isolate;border:1px solid rgba(178,138,69,.4);border-radius:12px;box-shadow:0 24px 54px rgba(42,77,73,.16),0 0 0 5px rgba(246,249,242,.52);overflow:hidden}
.cs__stage::before{content:'';position:absolute;z-index:calc(var(--z-hud) + 1);inset:10px;pointer-events:none;border:1px solid rgba(255,245,210,.27);border-radius:7px;box-shadow:22px 0 0 -21px var(--color-luminous-gold),-22px 0 0 -21px var(--color-luminous-gold)}
.cs__stage::after{content:'';position:absolute;z-index:calc(var(--z-hud) + 1);left:50%;top:9px;width:72px;height:8px;pointer-events:none;transform:translateX(-50%);border-top:1px solid rgba(217,187,115,.7);border-bottom:1px solid rgba(217,187,115,.28);background:radial-gradient(circle,var(--color-luminous-gold) 0 2px,transparent 3px)}
.cs__tool{position:relative;overflow:hidden;box-shadow:0 5px 16px rgba(44,83,77,.05)}
.cs__tool::after{content:'';position:absolute;inset:-70% -30%;background:linear-gradient(105deg,transparent 40%,rgba(255,255,255,.7) 50%,transparent 60%);transform:translateX(-75%);transition:transform 460ms ease}
.cs__tool:hover::after{transform:translateX(75%)}
.cs__tool>*{position:relative;z-index:1}
.cs__guide{position:relative;overflow:hidden;border-radius:4px 4px 10px 10px}
.cs__guide::before{content:'◇';flex:none;color:var(--color-luminous-gold);font-size:10px}
@media(prefers-reduced-motion:reduce){.cs__tool::after{display:none}}
@media(max-width:900px){.cs__status{display:none}.cs__tool span{display:none}.cs__tool{padding:8px}}

/* V5 叙事对白条：保留一屏布局，同时让提示像剧情游戏的旁白卷。 */
.cs__guide{
  min-height:52px;
  padding:10px 20px;
  border-color:rgba(178,138,69,.28);
  background:linear-gradient(90deg,rgba(225,235,224,.74),rgba(255,250,232,.92) 12%,rgba(249,247,229,.92) 88%,rgba(225,235,224,.74));
  box-shadow:0 12px 28px rgba(48,84,78,.09),0 0 24px rgba(217,187,115,.1) inset;
  clip-path:polygon(7px 0,calc(100% - 7px) 0,100% 50%,calc(100% - 7px) 100%,7px 100%,0 50%);
}
.cs__guide::after{content:'';position:absolute;left:18%;right:18%;top:0;height:1px;background:linear-gradient(90deg,transparent,var(--color-luminous-gold),transparent);opacity:.7}
.cs__guide-label{font-family:var(--font-display);letter-spacing:.12em;color:var(--color-scroll-red)}
.cs__guide-text{font-family:var(--font-display);font-size:13px;letter-spacing:.025em}
.cs__guide-btn{transition:background-color 160ms ease,color 160ms ease,transform 160ms ease}
.cs__guide-btn:hover{transform:translateY(-1px)}
</style>
