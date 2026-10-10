<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GAME_CATALOG } from '@/game/catalog'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
import { useExplorationStore } from '@/stores/exploration'
import { useGameStore } from '@/stores/game'
import { getEntities } from '@/api/endpoints'
import type { ChapterSlug, Entity } from '@/types'
import { FIVE_CHAPTER_STORIES, isStoryChapterSlug } from '@/chapters/story/fiveChapterStories'

const route = useRoute()
const router = useRouter()
const chapterStore = useChapterStore()
const exploration = useExplorationStore()
const game = useGameStore()
const slug = computed(() => route.params.slug as ChapterSlug)
const chapter = computed(() => chapterStore.current)
const meta = computed(() => GAME_CATALOG[slug.value])
const state = computed(() => game.stateFor(slug.value))
const visited = ref<Entity[]>([])
const loading = ref(true)

const EVIDENCE_LABELS: Record<string, string> = {
  script_sanskrit_lantsa: '梵文书写系统',
  script_tibetan: '藏文',
  script_phagspa: '八思巴文',
  script_old_uyghur: '回鹘文',
  script_chinese: '汉文',
  script_tangut: '西夏文',
  sample_a: '统一施工校样',
  sample_b: '结构调整校样',
  position_marks: '位置标记',
  scale_baseline: '尺度基准',
  handoff_marks: '交接记号',
  spacing_shift: '间距变化',
  direction_change: '书写方向',
  structure_break: '文本结构断裂',
  water_mark: '纸边水痕',
  fold_line: '折线错位',
  ink_spread: '墨迹扩散',
  version_layers: '两阶段版本关系',
  shared_rules: '三层共同规则',
  script_people_boundary: '文字与人群边界',
  archive_record: '校验后的档案表述',
  decision_chain: '修缮裁决链',
  han_caption_split: '错误展签拆解',
  han_chronology_gap: '人物与文物的年代距离',
  han_dual_route: '人物行程与长期网络',
  han_niya_context: '尼雅出土语境',
  han_network_actors: '长期网络中的多类参与者',
  han_relation_scale: '关系强度刻度',
  han_caption_draft: '三层展签草案',
  wei_scope_split: '个案—制度—社会尺度',
  wei_epitaph_scope: '元羽墓志证据范围',
  wei_move_process: '493—494迁都过程',
  wei_grotto_compare: '云冈—龙门策展对照',
  wei_costume_boundary: '服饰证据边界',
  wei_evidence_types: '制度文本—图像—实物',
  wei_change_model: '采用—改造—并存—延续',
  tang_absent_search: '画中人物名册',
  tang_outside_chain: '画内—事件—画外关系链',
  tang_image_boundary: '历史画证据边界',
  tang_attribution_layers: '作者归属三层证据',
  tang_cast_boundary: '画内／画外人物',
  tang_relation_thread: '有来源的画外关系',
  tang_guide_line: '导览词空位',
  qing_arrival_ledger: '抵达、接济与虚构个案三层记录',
  qing_relief_first: '名册受损时的救急原则',
  qing_route_scopes: '迁徙—觐见—安置三线',
  qing_number_sources: '历史数字来源口径',
  qing_motive_plural: '多重历史背景',
  qing_relief_chain: '食衣—生计—安置接济链',
  qing_settlement_ledger: '今夜—明春双页接济簿',
  contemporary_recovery_chain: '灾后羌绣重建关系链',
  contemporary_many_hands: '支援—生产—协作行动图',
  contemporary_learning_network: '当代跨地学习网络',
  contemporary_exchange_kit: '接针共创包结构',
  contemporary_ai_boundary: 'AI辅助往返边界',
  contemporary_exchange_protocol: '起针—回应—回信协议',
  contemporary_pilot_reply: '首组跨地回信档案',
}

interface YuanStorySummaryState {
  investigationChoice?: string
  knowledgeChoice?: string
  finalChoice?: string
  finalDeductionAttempts?: number
  keepOldVersion?: boolean | null
}

const yuanStoryState = ref<YuanStorySummaryState | null>(null)
const genericRevisionCount = ref(0)

const returnPath = computed(() => `/chapter/${slug.value}/story`)

const decision = computed(() =>
  meta.value.decision.choices.find((choice) => choice.id === state.value.decisionId),
)
const gameProgress = computed(() => game.progressFor(slug.value))
const canComplete = computed(() => gameProgress.value >= 67 && !!state.value.decisionId)
const path = computed(() => visited.value.slice(0, 7))
const chapterOrder = Object.keys(GAME_CATALOG) as ChapterSlug[]
const nextSlug = computed(() => chapterOrder[chapterOrder.indexOf(slug.value) + 1] ?? null)
const nextMeta = computed(() => nextSlug.value ? GAME_CATALOG[nextSlug.value] : null)
const dominantMethod = computed(() => {
  const items = [
    ['求真', state.value.methods.truth],
    ['共情', state.value.methods.empathy],
    ['联结', state.value.methods.connection],
  ] as const
  return [...items].sort((a, b) => b[1] - a[1])[0]?.[0] ?? '求真'
})

const yuanRoute = computed(() => {
  if (slug.value !== 'yuan' || !yuanStoryState.value) return null
  const story = yuanStoryState.value
  const routes = {
    over_simplify: {
      title: '快速推进 · 版本链受损',
      summary: '你让施工按期推进，却把未经证实的版本关系写成了确定结论。档案端保留了这次判断造成的证据缺口。',
    },
    limited_confirm: {
      title: '有限确认 · 协作继续',
      summary: '你只统一得到证据支持的施工外层，同时保留文本差异与版本未知，让行动和证据边界一起进入记录。',
    },
    evidence_insufficient: {
      title: '停工复核 · 工期承压',
      summary: '你最大程度保存了证据，也承担了停工与重排人手的现实成本。谨慎并非没有代价。',
    },
  }
  const route = routes[story.finalChoice as keyof typeof routes] ?? routes.limited_confirm
  return {
    ...route,
    archive: story.keepOldVersion ? '旧版可继续复核' : '旧版未保留，版本链留下缺口',
    trust: story.investigationChoice === 'blame' ? '曾经草率归责，人物信任受损' : '将移动事实与人物归责分开',
    attempts: Math.max(1, story.finalDeductionAttempts ?? 1),
  }
})

const STORY_ROUTE_SUMMARIES: Partial<Record<ChapterSlug, Record<string, { title: string; summary: string }>>> = {
  han: {
    mark_uncertain: { title: '删去直连 · 问题留下', summary: '你删掉了最醒目的传奇，让观众从“为什么仍要并置”开始理解人物事件与长期网络的距离。' },
    ask_travellers: { title: '长期网络 · 历史变大', summary: '你保留张骞的重要节点，同时让尼雅织锦回到跨越多个世纪、由许多人共同形成的交通网络。' },
    follow_fast: { title: '并列年代 · 交出判断', summary: '你没有替观众补写直接关系，而是把出使、断代与出土信息并排交给他们核对。' },
  },
  'northern-wei': {
    compare_first: { title: '明确个案 · 范围站稳', summary: '元羽墓志不再替整个北魏发言，却更准确地说明一个具体人物及其制度背景。' },
    workshop_together: { title: '多证物并列 · 变化分层', summary: '墓志、石窟与陶俑彼此校正，采用、改造、并存与延续得以同时出现。' },
    keep_family_mark: { title: '个人尺度 · 宏大落地', summary: '展签从姓名、籍贯和姓氏写起，并把墓主之外的社会经验明确留作未知。' },
  },
  tang: {
    state_absence: { title: '明示缺席 · 空白可信', summary: '你明确写出文成公主不在画中，再用来源说明她如何与画外事件相连。' },
    follow_envoy: { title: '跟随使臣 · 关系出框', summary: '你从画中禄东赞出发，经由会见与事件走向文成公主，没有把画外人物塞回画里。' },
    keep_multiple_views: { title: '图文并列 · 彼此限定', summary: '图像与文献互相补充，也互相提醒对方不能独自代表全部历史。' },
  },
  qing: {
    record_range: { title: '先救眼前 · 明日续簿', summary: '你让食衣先到达眼前每个人，也把失散复核、牲畜分配与牧地安排明确留作未完责任，没有把第一碗粮写成故事终点。' },
    record_names: { title: '先留住名字 · 安排补发', summary: '你让归来者参与逐户核名，许多失散者没有从簿上消失；与此同时，等待中的人被写入优先补发清单。' },
    follow_route: { title: '双页共写 · 把今夜接到明春', summary: '食衣、家口、牲畜、牧地与责任人进入同一条协作链，归来者不再只是领取物资，也成为重建生活的参与者。' },
  },
  contemporary: {
    remove_asset: { title: '先做档案展 · 联系停在发问', summary: '二十四校看见了灾后支援、本地生产、培训和市场如何相接，也留下许多问题；但没有作品返回工坊，本轮尚不能称作共同创作。' },
    request_review: { title: '先寄问题卡 · 让双方选择', summary: '项目延期一个月，学生先提出关心的问题，创作者再自主选择回应对象；交流不再由平台预先分配，也失去了整齐的首发效果。' },
    use_authorized: { title: '八组先往返 · 十六校等待', summary: '八份不同的起针片收到八种不同材料的回应，并由原作者再次答复；规模缩小了，但每条连接的两端都有人。' },
  },
}

const localStoryRoute = computed(() => {
  if (slug.value === 'yuan' || !state.value.decisionId) return null
  return STORY_ROUTE_SUMMARIES[slug.value]?.[state.value.decisionId] ?? null
})

const storyRecap = computed(() =>
  isStoryChapterSlug(slug.value) ? FIVE_CHAPTER_STORIES[slug.value].recap : null,
)

const routeComparison = computed(() => meta.value.decision.choices.map((choice, index) => ({
  ...choice,
  index: String(index + 1).padStart(2, '0'),
  chosen: choice.id === state.value.decisionId,
  impactLabels: (Object.entries(choice.impact) as Array<[keyof typeof choice.impact, number]>)
    .filter(([, value]) => !!value)
    .map(([key, value]) => `${({ truth: '求真', empathy: '共情', connection: '联结' })[key]} +${value}`),
})))

onMounted(async () => {
  game.bootstrap()
  if (slug.value === 'yuan') {
    try {
      yuanStoryState.value = JSON.parse(localStorage.getItem('tongxin.yuan.story.v6') ?? 'null')
    } catch {
      yuanStoryState.value = null
    }
  } else {
    try {
      const saved = JSON.parse(localStorage.getItem(`tongxin.${slug.value}.story.v1`) ?? 'null') as { revisionCount?: number } | null
      genericRevisionCount.value = saved?.revisionCount ?? 0
    } catch {
      genericRevisionCount.value = 0
    }
  }
  const id = SLUG_TO_ID[slug.value]
  if (!id) return
  if (chapterStore.current?.id !== id) await chapterStore.loadChapter(id)
  if (slug.value !== 'yuan') {
    await exploration.refresh(id)
    const ids = exploration.progress?.visited_entity_ids ?? state.value.evidenceIds
    if (ids.length) {
      try {
        const all = await getEntities()
        visited.value = all.filter((entity) => ids.includes(entity.id))
      } catch { visited.value = [] }
    }
  }
  if (canComplete.value) {
    game.mark(slug.value, 'COMPLETE')
    exploration.track('CHAPTER_COMPLETE', {}, id)
  }
  loading.value = false
  if (slug.value !== 'yuan') void exploration.buildSummary(id)
})

function methodWidth(value: number) {
  return `${Math.min(100, value * 34)}%`
}

function evidenceLabel(id: string) {
  return EVIDENCE_LABELS[id] ?? id.replaceAll('_', ' ')
}

function replayStory() {
  if (slug.value === 'yuan') localStorage.removeItem('tongxin.yuan.story.v6')
  else localStorage.removeItem(`tongxin.${slug.value}.story.v1`)
  game.resetChapter(slug.value)
  void router.push(`/chapter/${slug.value}/story`)
}
</script>

<template>
  <div v-if="chapter" class="ending" :style="{ '--era-accent': chapter.accent }">
    <div class="ending__grain" aria-hidden="true" />
    <header class="ending__nav">
      <RouterLink :to="returnPath">← 返回场景</RouterLink>
      <span>{{ canComplete ? '本章记录已封存' : '本章记录尚未完整' }}</span>
      <RouterLink to="/timeline">千年行卷</RouterLink>
    </header>

    <main class="ending__main">
      <section class="ending__seal">
        <span>{{ chapter.keyword }}</span>
        <i aria-hidden="true" />
      </section>

      <section class="ending__title">
        <p>{{ chapter.era }} · {{ meta.gameTitle }}</p>
        <h1>{{ canComplete ? meta.chapterMark : '未竟之卷' }}</h1>
        <blockquote v-if="decision">“{{ decision.response }}”</blockquote>
        <blockquote v-else>“你已经看见一些证据，但还没有为本章的核心难题作出选择。”</blockquote>
      </section>

      <div class="ending__grid">
        <section class="ending__panel ending__artifact">
          <p class="ending__label">你带回的信物</p>
          <strong>{{ canComplete ? meta.artifact : '尚未获得' }}</strong>
          <span>{{ canComplete ? `这份记录呈现出更强的「${dominantMethod}」倾向。` : `完成至少 4 项任务并作出本章抉择，即可封存「${meta.artifact}」。` }}</span>
        </section>

        <section class="ending__panel ending__methods">
          <p class="ending__label">你的历史方法</p>
          <div><span>求真</span><i><b :style="{ width: methodWidth(state.methods.truth) }" /></i></div>
          <div><span>共情</span><i><b :style="{ width: methodWidth(state.methods.empathy) }" /></i></div>
          <div><span>联结</span><i><b :style="{ width: methodWidth(state.methods.connection) }" /></i></div>
          <small>这不是对价值观的评分，只记录你在本章采用过的方法。</small>
        </section>

        <section class="ending__panel ending__choice">
          <p class="ending__label">你留下的选择</p>
          <strong>{{ decision?.label || '尚未作出本章抉择' }}</strong>
          <span>{{ decision?.description || '回到场景，查验三处证据并开启专属透镜。' }}</span>
          <small v-if="yuanRoute">{{ yuanRoute.trust }} · {{ yuanRoute.archive }}</small>
        </section>

        <section class="ending__panel ending__summary">
          <p class="ending__label">档案助手整理</p>
          <p v-if="yuanRoute"><strong>{{ yuanRoute.title }}</strong><br />{{ yuanRoute.summary }}<small>终局裁决核验 {{ yuanRoute.attempts }} 次。</small></p>
          <p v-else-if="localStoryRoute"><strong>{{ localStoryRoute.title }}</strong><br />{{ localStoryRoute.summary }}</p>
          <p v-else-if="exploration.summary">{{ exploration.summary.summary }}</p>
          <p v-else-if="loading || exploration.summaryLoading">正在依据你的实际路径整理记录……</p>
          <p v-else>继续探索后，档案助手只会使用你真正见过的内容生成总结。</p>
        </section>
      </div>

      <section class="ending__routes" aria-labelledby="route-comparison-title">
        <header>
          <div>
            <p class="ending__label">路线复盘</p>
            <h2 id="route-comparison-title">同一份证据，三种承担方式</h2>
          </div>
          <p>只展开你实际走过的后果；其余路线保留为可重玩的选择，不提前剧透结局。</p>
        </header>
        <div>
          <article
            v-for="routeItem in routeComparison"
            :key="routeItem.id"
            :class="{ 'is-chosen': routeItem.chosen }"
          >
            <span>{{ routeItem.index }} · {{ routeItem.chosen ? '本次路线' : '未走过' }}</span>
            <h3>{{ routeItem.label }}</h3>
            <p>{{ routeItem.chosen ? routeItem.response : routeItem.description }}</p>
            <dl>
              <div><dt>优先保护</dt><dd>{{ routeItem.protects }}</dd></div>
              <div><dt>接受代价</dt><dd>{{ routeItem.cost }}</dd></div>
            </dl>
            <footer>
              <b v-for="impact in routeItem.impactLabels" :key="impact">{{ impact }}</b>
              <small>{{ routeItem.chosen ? '后果已写入本章记录' : '重开本章可体验完整后果' }}</small>
            </footer>
          </article>
        </div>
      </section>

      <section v-if="storyRecap" class="ending__boundaries" aria-labelledby="boundary-recap-title">
        <header>
          <p class="ending__label">史实边界复盘</p>
          <h2 id="boundary-recap-title">故事结束，证据层级仍然保留</h2>
        </header>
        <div>
          <article><span>史料确证</span><p>{{ storyRecap.confirmed }}</p></article>
          <article><span>研究解释</span><p>{{ storyRecap.interpretation }}</p></article>
          <article><span>尚未确认</span><p>{{ storyRecap.unknown }}</p></article>
          <article><span>剧情虚构</span><p>{{ storyRecap.fiction }}</p></article>
        </div>
      </section>

      <section class="ending__path">
        <p class="ending__label">本次查验</p>
        <div v-if="path.length">
          <template v-for="(entity, index) in path" :key="entity.id">
            <RouterLink :to="slug === 'yuan' ? '/chapter/yuan/story' : `/chapter/${slug}/scene?entity=${entity.id}`">{{ entity.display_name || entity.name }}</RouterLink>
            <span v-if="index < path.length - 1">—</span>
          </template>
        </div>
        <div v-else class="ending__ids">
          <template v-for="(id, index) in state.evidenceIds.slice(0, 7)" :key="id">
            <span>{{ evidenceLabel(id) }}</span><b v-if="index < state.evidenceIds.slice(0, 7).length - 1">—</b>
          </template>
        </div>
      </section>

      <p v-if="slug !== 'yuan'" class="ending__revision">本章共修订 {{ genericRevisionCount }} 次。修订不计为失败；它记录你如何让判断重新回到证据边界。</p>

      <div class="ending__actions">
        <button type="button" @click="replayStory">重开本章 · 尝试另一条路线</button>
        <button type="button" @click="router.push('/journey')">查看我的千年史册</button>
        <button
          class="primary"
          type="button"
          @click="router.push(nextSlug ? `/chapter/${nextSlug}/intro` : '/timeline')"
        >
          {{ nextMeta ? `领取下一段身份 · ${nextMeta.gameTitle}` : '把记录带回千年行卷' }} →
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.ending { position: relative; min-height: 100vh; color: #ede4d2; background: radial-gradient(circle at 50% 0, color-mix(in srgb, var(--era-accent) 17%, transparent), transparent 35%), #0b1312; }
.ending__grain { position: fixed; inset: 0; pointer-events: none; opacity: .18; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 160 160' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.72' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.18'/%3E%3C/svg%3E"); mix-blend-mode: soft-light; }
.ending__nav { position: relative; z-index: 2; height: 62px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 0 clamp(20px,4vw,64px); border-bottom: 1px solid rgba(226,207,169,.11); font-size: 10px; letter-spacing: .12em; color: rgba(237,228,210,.4); }.ending__nav a:last-child { justify-self: end; }.ending__nav a:hover { color: #ddc47c; }
.ending__main { position: relative; z-index: 1; width: min(1020px, calc(100% - 40px)); margin: 0 auto; padding: 62px 0 70px; }
.ending__seal { position: relative; width: 92px; height: 92px; margin: 0 auto; display: grid; place-items: center; color: color-mix(in srgb, var(--era-accent) 68%, #d7bf79); border: 1px solid currentColor; font-family: var(--font-display); font-size: 21px; transform: rotate(-3deg); }.ending__seal i { position: absolute; inset: 7px; border: 1px solid currentColor; opacity: .48; }.ending__seal::before,.ending__seal::after { content: ''; position: absolute; background: currentColor; opacity: .24; }.ending__seal::before { width: 140px; height: 1px; }.ending__seal::after { height: 140px; width: 1px; }
.ending__title { margin-top: 28px; text-align: center; }.ending__title > p { font-size: 10px; letter-spacing: .22em; color: rgba(237,228,210,.38); }.ending__title h1 { margin-top: 8px; font-family: var(--font-display); font-size: clamp(48px,7vw,82px); font-weight: 500; color: #f1e7d4; }.ending__title blockquote { max-width: 670px; margin: 20px auto 0; font-family: var(--font-display); font-size: 15px; line-height: 1.9; color: rgba(237,228,210,.62); }
.ending__grid { margin-top: 48px; display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid rgba(226,207,169,.12); border-left: 1px solid rgba(226,207,169,.12); }.ending__panel { min-height: 174px; padding: 23px; border-right: 1px solid rgba(226,207,169,.12); border-bottom: 1px solid rgba(226,207,169,.12); background: rgba(255,255,255,.017); }.ending__label { font-size: 9px !important; letter-spacing: .2em; color: rgba(237,228,210,.34) !important; }
.ending__artifact strong,.ending__choice strong { display: block; margin-top: 17px; font-family: var(--font-display); font-size: 24px; font-weight: 500; color: #dcc47e; }.ending__artifact span,.ending__choice span { display:block; margin-top: 8px; font-size: 11px; line-height: 1.7; color: rgba(237,228,210,.42); }
.ending__choice small{display:block;margin-top:8px;font-size:9px;line-height:1.55;color:rgba(237,228,210,.32)}.ending__summary strong{font-family:var(--font-display);font-weight:500;color:#dcc47e}.ending__summary small{display:block;margin-top:6px;font-family:var(--font-ui);font-size:9px;color:rgba(237,228,210,.32)}
.ending__methods > div { margin-top: 12px; display: grid; grid-template-columns: 42px 1fr; align-items: center; gap: 10px; font-size: 10px; color: rgba(237,228,210,.5); }.ending__methods i { height: 3px; background: rgba(255,255,255,.06); }.ending__methods b { display:block; height:100%; min-width: 5px; background: color-mix(in srgb, var(--era-accent) 65%, #dcc47e); }.ending__methods small { display:block; margin-top: 13px; color: rgba(237,228,210,.28); }
.ending__summary > p:not(.ending__label) { margin-top: 17px; font-family: var(--font-display); line-height: 1.85; color: rgba(237,228,210,.64); }
.ending__path { padding: 24px 0; border-bottom: 1px solid rgba(226,207,169,.12); }.ending__path > div { display:flex; flex-wrap:wrap; gap: 8px; margin-top: 13px; align-items:center; color: rgba(237,228,210,.3); }.ending__path a,.ending__ids span { font-family: var(--font-display); color: rgba(237,228,210,.62); }.ending__path a:hover { color:#dcc47e; }.ending__ids b { font-weight:400; }
.ending__actions { display:flex; justify-content:center; gap:10px; margin-top:32px; }.ending__actions button { height:49px; padding:0 19px; border:1px solid rgba(226,207,169,.18); border-radius:0; background:transparent; color:rgba(237,228,210,.56); }.ending__actions button:hover { border-color:#dcc47e; color:#f1e7d4; }.ending__actions .primary { min-width:270px; background:color-mix(in srgb,var(--era-accent) 18%,transparent); border-color:color-mix(in srgb,var(--era-accent) 68%,#dcc47e); color:#f1e7d4; font-family:var(--font-display); }
.ending__routes{margin-top:34px;padding-top:28px;border-top:1px solid rgba(226,207,169,.14)}.ending__routes>header{display:flex;justify-content:space-between;gap:28px;align-items:end}.ending__routes h2{margin-top:7px;font-family:var(--font-display);font-size:25px;font-weight:500;color:#f1e7d4}.ending__routes>header>p{max-width:390px;font-size:10px;line-height:1.7;color:rgba(237,228,210,.36);text-align:right}.ending__routes>div{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:17px}.ending__routes article{position:relative;min-height:190px;padding:18px;border:1px solid rgba(226,207,169,.12);background:rgba(255,255,255,.015);opacity:.68}.ending__routes article.is-chosen{border-color:color-mix(in srgb,var(--era-accent) 70%,#dcc47e);background:linear-gradient(145deg,color-mix(in srgb,var(--era-accent) 13%,transparent),rgba(255,255,255,.025));opacity:1;box-shadow:0 15px 38px rgba(0,0,0,.16)}.ending__routes article>span{font-size:8px;letter-spacing:.17em;color:rgba(237,228,210,.34)}.ending__routes article.is-chosen>span{color:#dcc47e}.ending__routes h3{margin-top:12px;font-family:var(--font-display);font-size:18px;font-weight:500;color:rgba(241,231,212,.82)}.ending__routes article>p{margin-top:8px;font-size:10px;line-height:1.7;color:rgba(237,228,210,.42)}.ending__routes footer{display:flex;flex-wrap:wrap;gap:5px;margin-top:15px}.ending__routes footer b{padding:3px 6px;border:1px solid rgba(220,196,126,.2);font-size:8px;font-weight:400;color:rgba(220,196,126,.72)}.ending__routes footer small{width:100%;margin-top:5px;font-size:8px;color:rgba(237,228,210,.28)}
@media (max-width:680px) { .ending__grid { grid-template-columns:1fr; }.ending__nav { grid-template-columns:1fr 1fr; }.ending__nav span { display:none; }.ending__actions { flex-direction:column; } }
@media(max-width:760px){.ending__routes>header{align-items:start;flex-direction:column}.ending__routes>header>p{text-align:left}.ending__routes>div{grid-template-columns:1fr}.ending__routes article{min-height:0}.ending__routes article:not(.is-chosen){min-height:148px}}

/* V3 青绿结章卷：桌面端一屏完成“结语—信物—路径—下一章”。 */
.ending{color:var(--color-slate-text);background:radial-gradient(circle at 50% 0,color-mix(in srgb,var(--era-accent) 12%,white),transparent 36%),linear-gradient(145deg,#edf3ea,#d7e6dd)}
.ending__grain{opacity:.08;mix-blend-mode:multiply}
.ending__nav{border-bottom-color:rgba(40,95,97,.15);color:rgba(41,69,74,.52);background:rgba(248,250,244,.3)}
.ending__nav a:hover{color:var(--color-scroll-red)}
.ending__title>p,.ending__label{color:rgba(41,69,74,.48)!important}
.ending__title h1{color:var(--color-mineral-800)}
.ending__title blockquote{color:rgba(41,69,74,.7)}
.ending__grid{border-color:rgba(40,95,97,.15)}
.ending__panel{border-color:rgba(40,95,97,.15);background:rgba(248,250,244,.42)}
.ending__artifact strong,.ending__choice strong{color:#8d6c31}
.ending__artifact span,.ending__choice span{color:rgba(41,69,74,.58)}
.ending__choice small,.ending__summary small{color:rgba(41,69,74,.46)}.ending__summary strong{color:#8d6c31}
.ending__methods>div{color:rgba(41,69,74,.6)}
.ending__methods i{background:rgba(40,95,97,.1)}
.ending__methods small{color:rgba(41,69,74,.45)}
.ending__summary>p:not(.ending__label){color:rgba(41,69,74,.72)}
.ending__path{border-bottom-color:rgba(40,95,97,.15)}
.ending__path>div{color:rgba(41,69,74,.42)}
.ending__path a,.ending__ids span{color:rgba(41,69,74,.7)}
.ending__path a:hover{color:var(--color-scroll-red)}
.ending__actions button{border-color:rgba(40,95,97,.22);background:rgba(255,255,255,.3);color:rgba(41,69,74,.7)}
.ending__actions button:hover{border-color:var(--color-scroll-red);color:var(--color-scroll-red)}
.ending__actions .primary{background:color-mix(in srgb,var(--era-accent) 10%,rgba(255,255,255,.6));border-color:color-mix(in srgb,var(--era-accent) 58%,var(--color-mineral-700));color:var(--color-mineral-800)}

@media(min-width:681px){
  .ending{height:100dvh;min-height:720px;overflow:hidden}
  .ending__main{height:calc(100dvh - 62px);min-height:658px;padding:20px 0 18px;display:flex;flex-direction:column}
  .ending__seal{flex:none;width:62px;height:62px;font-size:17px}
  .ending__seal i{inset:5px}.ending__seal::before{width:100px}.ending__seal::after{height:100px}
  .ending__title{flex:none;margin-top:10px}
  .ending__title h1{margin-top:2px;font-size:clamp(40px,4.6vw,60px);line-height:1.1}
  .ending__title blockquote{margin-top:8px;font-size:13px;line-height:1.6}
  .ending__grid{flex:1;min-height:0;margin-top:15px;grid-template-rows:repeat(2,minmax(0,1fr))}
  .ending__panel{min-height:0;padding:15px 19px}
  .ending__artifact strong,.ending__choice strong{margin-top:8px;font-size:20px}
  .ending__summary>p:not(.ending__label){margin-top:8px;line-height:1.6}
  .ending__methods>div{margin-top:7px}.ending__methods small{margin-top:7px}
  .ending__path{flex:none;padding:10px 0}.ending__path>div{margin-top:5px}
  .ending__actions{flex:none;margin-top:13px}.ending__actions button{height:43px}
}

/* V4 结章仪式：信物与方法像剧情游戏的通关卷轴逐层揭示。 */
.ending__main::before{content:'';position:absolute;z-index:-1;left:50%;top:18px;width:min(780px,80vw);height:210px;transform:translateX(-50%);pointer-events:none;background:radial-gradient(ellipse,rgba(217,187,115,.18),transparent 68%)}
.ending__seal{box-shadow:0 0 0 6px rgba(255,255,255,.2),0 12px 30px rgba(44,82,76,.12);animation:ending-seal 720ms cubic-bezier(.16,.76,.2,1) both}
.ending__title{animation:ending-rise 620ms 120ms var(--ease-standard) both}
.ending__panel{position:relative;overflow:hidden;animation:ending-rise 520ms var(--delay,220ms) var(--ease-standard) both}
.ending__panel:nth-child(2){--delay:300ms}.ending__panel:nth-child(3){--delay:380ms}.ending__panel:nth-child(4){--delay:460ms}
.ending__panel::after{content:'';position:absolute;right:-40px;bottom:-48px;width:120px;height:120px;border:1px solid color-mix(in srgb,var(--era-accent) 18%,transparent);border-radius:50%;box-shadow:0 0 0 14px color-mix(in srgb,var(--era-accent) 5%,transparent)}
.ending__actions button{position:relative;overflow:hidden;transition:border-color 180ms ease,color 180ms ease,box-shadow 180ms ease,transform 180ms ease}
.ending__actions button:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(45,81,76,.12)}
@keyframes ending-seal{from{opacity:0;transform:rotate(-12deg) scale(.55)}to{opacity:1;transform:rotate(-3deg) scale(1)}}
@keyframes ending-rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.ending__seal,.ending__title,.ending__panel{animation:none}.ending__actions button:hover{transform:none}}

/* V8 路线复盘加入后，结章从“一屏奖章”调整为可滚动的通关档案。 */
.ending__routes{border-top-color:rgba(40,95,97,.16)}
.ending__routes h2{color:var(--color-mineral-800)}
.ending__routes>header>p{color:rgba(41,69,74,.56)}
.ending__routes article{border-color:rgba(40,95,97,.15);background:rgba(248,250,244,.42);opacity:.82}
.ending__routes article.is-chosen{border-color:color-mix(in srgb,var(--era-accent) 70%,#94753c);background:linear-gradient(145deg,color-mix(in srgb,var(--era-accent) 9%,white),rgba(255,255,255,.46));box-shadow:0 15px 38px rgba(45,81,76,.1)}
.ending__routes article>span{color:rgba(41,69,74,.47)}
.ending__routes article.is-chosen>span{color:#9a7333}
.ending__routes h3{color:var(--color-mineral-800)}
.ending__routes article>p{color:rgba(41,69,74,.65)}
.ending__routes dl{display:grid;gap:5px;margin-top:12px;padding-top:10px;border-top:1px solid rgba(40,95,97,.11)}.ending__routes dl>div{display:grid;grid-template-columns:50px 1fr;gap:7px;font-size:8px;line-height:1.45}.ending__routes dt{color:#8d6c31}.ending__routes dd{margin:0;color:rgba(41,69,74,.58)}
.ending__routes footer b{border-color:rgba(154,115,51,.27);color:#8d6c31;background:rgba(255,255,255,.26)}
.ending__routes footer small{color:rgba(41,69,74,.43)}
.ending__revision{margin-top:12px;text-align:center;font-size:9px;color:rgba(41,69,74,.48)}
.ending__boundaries{margin-top:28px;padding-top:22px;border-top:1px solid rgba(40,95,97,.16)}
.ending__boundaries>header{display:flex;align-items:end;justify-content:space-between;gap:20px}.ending__boundaries h2{font-family:var(--font-display);font-size:25px;font-weight:500;color:var(--color-mineral-800)}
.ending__boundaries>div{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:14px}.ending__boundaries article{min-height:132px;padding:15px;border:1px solid rgba(40,95,97,.15);background:rgba(248,250,244,.42)}.ending__boundaries article span{font-size:9px;letter-spacing:.13em;color:#8d6c31}.ending__boundaries article p{margin-top:9px;font-size:10px;line-height:1.75;color:rgba(41,69,74,.66)}
@media(max-width:760px){.ending__boundaries>header{display:block}.ending__boundaries h2{margin-top:5px;font-size:21px}.ending__boundaries>div{grid-template-columns:1fr 1fr}.ending__boundaries article{min-height:0}}
@media(min-width:681px){
  .ending{height:auto;min-height:100dvh;overflow:visible}
  .ending__main{height:auto;min-height:0;padding:34px 0 52px;display:block}
  .ending__grid{margin-top:24px;grid-template-rows:none}
  .ending__panel{min-height:155px;padding:18px 21px}
  .ending__routes{margin-top:28px}
  .ending__path{padding:19px 0}
  .ending__actions{margin-top:22px}
}
</style>
