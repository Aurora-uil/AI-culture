<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GAME_CATALOG } from '@/game/catalog'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
import { useExplorationStore } from '@/stores/exploration'
import { useGameStore } from '@/stores/game'
import { getEntities } from '@/api/endpoints'
import type { ChapterSlug, Entity } from '@/types'

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
}

interface YuanStorySummaryState {
  investigationChoice?: string
  knowledgeChoice?: string
  finalChoice?: string
  finalDeductionAttempts?: number
  keepOldVersion?: boolean | null
}

const yuanStoryState = ref<YuanStorySummaryState | null>(null)

const returnPath = computed(() => slug.value === 'yuan' ? '/chapter/yuan/story' : `/chapter/${slug.value}/scene`)

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

onMounted(async () => {
  game.bootstrap()
  if (slug.value === 'yuan') {
    try {
      yuanStoryState.value = JSON.parse(localStorage.getItem('tongxin.yuan.story.v6') ?? 'null')
    } catch {
      yuanStoryState.value = null
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
    if (slug.value === 'yuan') exploration.track('YUAN_CHAPTER_COMPLETED', {}, id)
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

function replayYuan() {
  localStorage.removeItem('tongxin.yuan.story.v6')
  game.resetChapter('yuan')
  void router.push('/chapter/yuan/story')
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
          <p v-else-if="exploration.summary">{{ exploration.summary.summary }}</p>
          <p v-else-if="loading || exploration.summaryLoading">正在依据你的实际路径整理记录……</p>
          <p v-else>继续探索后，档案助手只会使用你真正见过的内容生成总结。</p>
        </section>
      </div>

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

      <div class="ending__actions">
        <button v-if="slug === 'yuan'" type="button" @click="replayYuan">重开元代篇 · 尝试另一条路线</button>
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
@media (max-width:680px) { .ending__grid { grid-template-columns:1fr; }.ending__nav { grid-template-columns:1fr 1fr; }.ending__nav span { display:none; }.ending__actions { flex-direction:column; } }

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
</style>
