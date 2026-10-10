<script setup lang="ts">
import { computed, onMounted } from 'vue'
import GlobalHeader from '@/components/global/GlobalHeader.vue'
import { GAME_CATALOG, type MethodKey } from '@/game/catalog'
import { useChapterStore } from '@/stores/chapter'
import { useGameStore } from '@/stores/game'
import type { ChapterSlug } from '@/types'

/** 玩家史册只记录玩家真正做过的事，不做人格、立场或“文化认同”评分。 */
const chapterStore = useChapterStore()
const game = useGameStore()
const slugs = Object.keys(GAME_CATALOG) as ChapterSlug[]

onMounted(() => {
  game.bootstrap()
  void chapterStore.loadChapters()
})

const records = computed(() =>
  slugs.map((slug, index) => {
    const meta = GAME_CATALOG[slug]
    const state = game.stateFor(slug)
    const chapter = chapterStore.chapters.find((item) => item.slug === slug)
    const decision = meta.decision.choices.find((item) => item.id === state.decisionId)
    return {
      index,
      slug,
      meta,
      state,
      decision,
      era: chapter?.era ?? ['汉代', '北魏', '唐代', '元代', '清代', '当代'][index],
      keyword: chapter?.keyword ?? ['相遇', '交融', '交流', '共存', '归属', '传承'][index],
      accent: chapter?.accent ?? '#7c9c8a',
      progress: game.progressFor(slug),
    }
  }),
)

const startedCount = computed(() => records.value.filter((item) => item.state.started).length)
const completedCount = computed(() => records.value.filter((item) => item.state.completed).length)
const evidenceCount = computed(() => records.value.reduce((sum, item) => sum + item.state.evidenceIds.length, 0))
const methodTotals = computed<Record<MethodKey, number>>(() =>
  records.value.reduce(
    (totals, item) => {
      totals.truth += item.state.methods.truth
      totals.empathy += item.state.methods.empathy
      totals.connection += item.state.methods.connection
      return totals
    },
    { truth: 0, empathy: 0, connection: 0 },
  ),
)
const maxMethod = computed(() => Math.max(1, ...Object.values(methodTotals.value)))
const nextRecord = computed(() => {
  const unfinished = records.value
    .filter((item) => item.state.started && !item.state.completed)
    .sort((a, b) => (b.state.updatedAt ?? '').localeCompare(a.state.updatedAt ?? ''))[0]
  if (unfinished) return unfinished

  const latest = records.value
    .filter((item) => item.state.updatedAt)
    .sort((a, b) => (b.state.updatedAt ?? '').localeCompare(a.state.updatedAt ?? ''))[0]
  if (latest) {
    for (let offset = 1; offset <= records.value.length; offset += 1) {
      const candidate = records.value[(latest.index + offset) % records.value.length]
      if (!candidate.state.completed) return candidate
    }
  }

  return records.value.find((item) => item.slug === 'yuan') ?? records.value[0]
})

function routeFor(record: (typeof records.value)[number]) {
  if (record.state.completed) return `/chapter/${record.slug}/summary`
  if (record.state.started) return `/chapter/${record.slug}`
  return `/chapter/${record.slug}/intro`
}

function methodWidth(value: number) {
  return `${Math.max(value ? 8 : 0, Math.round((value / maxMethod.value) * 100))}%`
}
</script>

<template>
  <div class="chronicle">
    <div class="chronicle__grain" aria-hidden="true" />
    <GlobalHeader dark :show-breadcrumb="false" />

    <main class="chronicle__main">
      <header class="chronicle__hero">
        <div>
          <p class="chronicle__eyebrow">个人行旅档案 · 只记录真实操作</p>
          <h1>我的千年史册</h1>
          <p class="chronicle__lead">这里不判断你“是什么样的人”，只保存你查验过的证据、做出的选择，以及带离每个时代的方法。</p>
        </div>
        <RouterLink :to="routeFor(nextRecord)" class="chronicle__continue">
          <span>{{ nextRecord.state.started ? '继续未完章节' : '领取下一段身份' }}</span>
          <strong>{{ nextRecord.era }} · {{ nextRecord.meta.gameTitle }}</strong>
          <i aria-hidden="true">→</i>
        </RouterLink>
      </header>

      <section class="chronicle__summary" aria-label="行旅概况">
        <div><strong>{{ completedCount }}</strong><span>已封存章节</span></div>
        <div><strong>{{ startedCount }}</strong><span>经历过的身份</span></div>
        <div><strong>{{ evidenceCount }}</strong><span>亲自查验的证据</span></div>
        <p>完成一章并不会获得“历史正确分”。你获得的是一件信物，以及一段能够说明依据的个人记录。</p>
      </section>

      <div class="chronicle__layout">
        <section class="ledger" aria-labelledby="ledger-title">
          <header class="ledger__head"><p>六份证据责任</p><h2 id="ledger-title">你的章节记录</h2></header>
          <ol class="ledger__list">
            <li
              v-for="record in records"
              :key="record.slug"
              class="record"
              :class="{ 'is-started': record.state.started, 'is-complete': record.state.completed }"
              :style="{ '--record-accent': record.accent }"
            >
              <span class="record__knot" aria-hidden="true"><i /></span>
              <RouterLink :to="routeFor(record)" class="record__body">
                <div class="record__index"><span>{{ String(record.index + 1).padStart(2, '0') }}</span><small>{{ record.era }} · {{ record.keyword }}</small></div>
                <div class="record__title"><h3>{{ record.meta.gameTitle }}</h3><p>{{ record.meta.role }}</p></div>
                <div class="record__result">
                  <template v-if="record.state.completed"><span>已获得</span><strong>{{ record.meta.artifact }}</strong></template>
                  <template v-else-if="record.state.started"><span>当前进度</span><strong>{{ record.progress }}%</strong></template>
                  <template v-else><span>尚未进入</span><strong>{{ record.meta.duration }}</strong></template>
                </div>
                <div class="record__choice"><span>{{ record.decision ? '你留下的选择' : '本章核心抉择' }}</span><p>{{ record.decision?.label ?? record.meta.decision.title }}</p></div>
                <span class="record__arrow" aria-hidden="true">→</span>
                <div class="record__progress"><i :style="{ width: `${record.progress}%` }" /></div>
              </RouterLink>
            </li>
          </ol>
        </section>

        <aside class="methods">
          <div class="methods__seal" aria-hidden="true">史</div>
          <p class="methods__eyebrow">跨章节记录</p>
          <h2>你采用过的历史方法</h2>
          <p class="methods__intro">这些刻度来自具体选择，不是人格测试，也不会给出高低评价。</p>
          <div class="methods__bars">
            <div><header><strong>求真</strong><span>{{ methodTotals.truth }} 次</span></header><i><b :style="{ width: methodWidth(methodTotals.truth) }" /></i><p>标明未知、比较来源、拒绝让推测冒充事实。</p></div>
            <div><header><strong>共情</strong><span>{{ methodTotals.empathy }} 次</span></header><i><b :style="{ width: methodWidth(methodTotals.empathy) }" /></i><p>记住数字背后的人，也承认不同处境中的有限视角。</p></div>
            <div><header><strong>联结</strong><span>{{ methodTotals.connection }} 次</span></header><i><b :style="{ width: methodWidth(methodTotals.connection) }" /></i><p>把人物、器物、道路与制度放回关系中理解。</p></div>
          </div>
          <blockquote v-if="completedCount">“你已封存 {{ completedCount }} 段记录。它们不会合成唯一结论，却会在关系图中留下不同入口。”</blockquote>
          <blockquote v-else>“第一段记录尚未封存。建议从元代云台的校勘任务开始。”</blockquote>
          <RouterLink to="/graph" class="methods__link">查看这些记录之间的联系 <span>→</span></RouterLink>
        </aside>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chronicle{position:relative;min-height:100vh;color:#ece3d1;background:radial-gradient(circle at 87% 16%,rgba(61,111,99,.16),transparent 27%),#0a1211}.chronicle__grain{position:fixed;inset:0;pointer-events:none;opacity:.17;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 160 160' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.72' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.18'/%3E%3C/svg%3E");mix-blend-mode:soft-light}.chronicle__main{position:relative;z-index:1;width:min(1320px,calc(100% - 48px));margin:0 auto;padding:clamp(52px,7vw,92px) 0 76px}.chronicle__hero{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:64px;align-items:end}.chronicle__eyebrow,.methods__eyebrow,.ledger__head p{font-size:10px;letter-spacing:.22em;color:#bc6049}.chronicle__hero h1{margin-top:12px;font-family:var(--font-display);font-size:clamp(48px,6.5vw,86px);line-height:1;font-weight:500;color:#f1e7d4}.chronicle__lead{max-width:660px;margin-top:24px;font-family:var(--font-display);font-size:15px;line-height:1.9;color:rgba(236,227,209,.54)}.chronicle__continue{position:relative;display:grid;gap:5px;padding:20px 48px 20px 20px;border:1px solid rgba(218,193,126,.32);background:rgba(218,193,126,.055);transition:border-color .18s ease,background .18s ease}.chronicle__continue:hover{border-color:#d8bf78;background:rgba(218,193,126,.1)}.chronicle__continue span{font-size:9px;letter-spacing:.16em;color:rgba(236,227,209,.4)}.chronicle__continue strong{font-family:var(--font-display);font-size:17px;font-weight:500;color:#dfc981}.chronicle__continue i{position:absolute;right:19px;top:50%;transform:translateY(-50%);color:#dfc981;font-style:normal}.chronicle__summary{display:grid;grid-template-columns:150px 150px 170px 1fr;margin-top:55px;border-top:1px solid rgba(226,207,169,.12);border-bottom:1px solid rgba(226,207,169,.12)}.chronicle__summary>div{display:flex;flex-direction:column;justify-content:center;min-height:110px;padding:18px;border-right:1px solid rgba(226,207,169,.12)}.chronicle__summary strong{font-family:var(--font-display);font-size:36px;font-weight:400;color:#d9c17d}.chronicle__summary span{margin-top:3px;font-size:10px;color:rgba(236,227,209,.38)}.chronicle__summary>p{align-self:center;max-width:520px;padding:20px 0 20px 32px;font-size:11px;line-height:1.8;color:rgba(236,227,209,.36)}.chronicle__layout{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:54px;margin-top:64px}.ledger__head h2,.methods h2{margin-top:7px;font-family:var(--font-display);font-size:28px;font-weight:500;color:#eee4d1}.ledger__list{position:relative;list-style:none;margin:32px 0 0;padding:0}.ledger__list::before{content:'';position:absolute;left:18px;top:15px;bottom:15px;width:1px;background:linear-gradient(#d8bf78,rgba(216,191,120,.12))}.record{position:relative;display:grid;grid-template-columns:38px 1fr}.record__knot{position:relative;z-index:2;width:37px;display:grid;place-items:center}.record__knot i{width:9px;height:9px;border:1px solid rgba(216,191,120,.34);background:#0a1211;transform:rotate(45deg)}.record.is-started .record__knot i{border-color:color-mix(in srgb,var(--record-accent) 72%,#d8bf78);box-shadow:0 0 18px color-mix(in srgb,var(--record-accent) 40%,transparent)}.record.is-complete .record__knot i{background:color-mix(in srgb,var(--record-accent) 65%,#d8bf78)}.record__body{position:relative;display:grid;grid-template-columns:105px minmax(190px,1.35fr) 120px minmax(180px,1fr) 24px;gap:18px;align-items:center;min-height:118px;padding:18px 16px;border-bottom:1px solid rgba(226,207,169,.1);transition:background .18s ease}.record__body:hover{background:rgba(255,255,255,.025)}.record__index{display:flex;flex-direction:column;gap:5px}.record__index>span{font-family:var(--font-display);color:color-mix(in srgb,var(--record-accent) 68%,#d8bf78)}.record__index small,.record__result span,.record__choice span{font-size:9px;letter-spacing:.1em;color:rgba(236,227,209,.32)}.record__title h3{font-family:var(--font-display);font-size:21px;font-weight:500;color:rgba(241,231,212,.88)}.record__title p{margin-top:5px;font-size:10px;color:rgba(236,227,209,.38)}.record__result,.record__choice{display:flex;flex-direction:column;gap:5px}.record__result strong{font-family:var(--font-display);font-size:14px;font-weight:500;color:#d9c17d}.record__choice p{font-size:11px;line-height:1.5;color:rgba(236,227,209,.55)}.record__arrow{color:rgba(216,191,120,.5)}.record__progress{position:absolute;left:16px;right:16px;bottom:-1px;height:1px}.record__progress i{display:block;height:100%;background:color-mix(in srgb,var(--record-accent) 70%,#d8bf78)}.methods{position:sticky;top:calc(var(--header-h) + 28px);align-self:start;padding:30px;border:1px solid rgba(226,207,169,.14);background:linear-gradient(145deg,rgba(255,255,255,.032),rgba(255,255,255,.012))}.methods__seal{float:right;width:52px;height:52px;display:grid;place-items:center;margin:-3px -3px 12px 18px;border:1px solid rgba(97,145,131,.44);color:#7fa292;font-family:var(--font-display);font-size:19px;transform:rotate(3deg)}.methods__intro{clear:both;margin-top:18px;font-size:11px;line-height:1.75;color:rgba(236,227,209,.39)}.methods__bars{display:grid;gap:24px;margin-top:29px}.methods__bars header{display:flex;justify-content:space-between;align-items:baseline}.methods__bars strong{font-family:var(--font-display);font-weight:500;color:#e5d8c0}.methods__bars header span{font-size:9px;color:rgba(236,227,209,.32)}.methods__bars>div>i{display:block;height:3px;margin-top:9px;background:rgba(255,255,255,.055)}.methods__bars b{display:block;height:100%;background:linear-gradient(90deg,#668d7e,#d8bf78);transition:width .4s ease}.methods__bars p{margin-top:8px;font-size:10px;line-height:1.6;color:rgba(236,227,209,.34)}.methods blockquote{margin-top:31px;padding:17px 0;border-top:1px solid rgba(226,207,169,.1);border-bottom:1px solid rgba(226,207,169,.1);font-family:var(--font-display);font-size:13px;line-height:1.8;color:rgba(236,227,209,.54)}.methods__link{display:flex;justify-content:space-between;margin-top:21px;font-size:11px;color:#d8bf78}.methods__link:hover{color:#f0dfaa}
@media(max-width:1050px){.chronicle__layout{grid-template-columns:1fr}.methods{position:relative;top:auto}.record__body{grid-template-columns:90px 1fr 110px minmax(150px,.8fr) 20px}.chronicle__summary{grid-template-columns:repeat(3,1fr)}.chronicle__summary>p{grid-column:1/-1;padding:18px 0}}
@media(max-width:720px){.chronicle__main{width:min(100% - 32px,1320px);padding-top:42px}.chronicle__hero{grid-template-columns:1fr;gap:28px}.chronicle__continue{width:100%}.chronicle__summary{grid-template-columns:repeat(3,1fr);margin-top:36px}.chronicle__summary>div{min-height:86px;padding:12px}.chronicle__summary strong{font-size:29px}.record{grid-template-columns:25px 1fr}.ledger__list::before{left:12px}.record__knot{width:25px}.record__body{grid-template-columns:1fr auto;gap:10px;min-height:145px;padding:16px 10px}.record__index{grid-column:1}.record__title{grid-column:1/-1}.record__result{grid-column:2;grid-row:1}.record__choice{grid-column:1/-1}.record__arrow{position:absolute;right:8px;bottom:17px}.methods{padding:22px}}
@media(prefers-reduced-motion:reduce){.methods__bars b{transition:none}}

/* V3 青绿史册：低饱和卷面，不使用黑底；桌面六章同时可见。 */
.chronicle{color:var(--color-slate-text);background:radial-gradient(circle at 86% 15%,rgba(255,255,255,.68),transparent 25%),linear-gradient(145deg,#eaf2e9,#d4e4da)}
.chronicle__grain{opacity:.09;mix-blend-mode:multiply}
.chronicle__hero h1{color:var(--color-mineral-800)}
.chronicle__lead{color:rgba(41,69,74,.62)}
.chronicle__continue{border-color:rgba(40,95,97,.28);background:rgba(248,250,244,.56);box-shadow:0 14px 36px rgba(50,92,82,.08)}
.chronicle__continue:hover{border-color:var(--color-scroll-red);background:rgba(255,255,255,.75)}
.chronicle__continue span{color:rgba(41,69,74,.48)}
.chronicle__continue strong{color:var(--color-mineral-700)}
.chronicle__continue i{color:var(--color-scroll-red)}
.chronicle__summary{border-color:rgba(40,95,97,.16);background:rgba(248,250,244,.28)}
.chronicle__summary>div{border-right-color:rgba(40,95,97,.14)}
.chronicle__summary strong{color:var(--color-scroll-gold)}
.chronicle__summary span,.chronicle__summary>p{color:rgba(41,69,74,.52)}
.ledger__head h2,.methods h2{color:var(--color-mineral-800)}
.ledger__list::before{background:linear-gradient(var(--color-scroll-gold),rgba(40,95,97,.14))}
.record__knot i{background:#e1ebe3;border-color:rgba(40,95,97,.3)}
.record__body{border-bottom-color:rgba(40,95,97,.13)}
.record__body:hover{background:rgba(255,255,255,.4)}
.record__index small,.record__result span,.record__choice span{color:rgba(41,69,74,.45)}
.record__title h3{color:var(--color-mineral-800)}
.record__title p{color:rgba(41,69,74,.52)}
.record__result strong{color:#8d6c31}
.record__choice p{color:rgba(41,69,74,.68)}
.methods{border-color:rgba(40,95,97,.18);background:rgba(248,250,244,.58);box-shadow:0 18px 48px rgba(50,92,82,.08)}
.methods__intro,.methods__bars p{color:rgba(41,69,74,.53)}
.methods__bars strong{color:var(--color-mineral-800)}
.methods__bars header span{color:rgba(41,69,74,.42)}
.methods__bars>div>i{background:rgba(40,95,97,.1)}
.methods blockquote{border-color:rgba(40,95,97,.13);color:rgba(41,69,74,.68)}
.methods__link{color:var(--color-scroll-red)}

@media(min-width:1051px){
  .chronicle{height:100dvh;min-height:720px;overflow:hidden}
  .chronicle__main{height:calc(100dvh - var(--header-h));min-height:648px;padding:22px 0 20px;display:flex;flex-direction:column}
  .chronicle__hero{flex:none;grid-template-columns:minmax(0,1fr) 320px;gap:44px;align-items:center}
  .chronicle__hero h1{font-size:clamp(42px,4.2vw,62px)}
  .chronicle__lead{margin-top:12px;font-size:13px;line-height:1.7}
  .chronicle__continue{padding-top:15px;padding-bottom:15px}
  .chronicle__summary{flex:none;margin-top:18px;grid-template-columns:125px 125px 145px 1fr}
  .chronicle__summary>div{min-height:64px;padding:10px 15px}
  .chronicle__summary strong{font-size:27px}
  .chronicle__summary>p{padding:10px 0 10px 24px;line-height:1.6}
  .chronicle__layout{flex:1;min-height:0;margin-top:18px;gap:34px;grid-template-columns:minmax(0,1fr) 330px}
  .ledger{min-height:0;display:flex;flex-direction:column}
  .ledger__head h2{font-size:22px}
  .ledger__list{flex:1;min-height:0;margin-top:9px;display:grid;grid-template-rows:repeat(6,minmax(0,1fr))}
  .record{min-height:0}
  .record__body{min-height:0;height:100%;padding:8px 12px;grid-template-columns:90px minmax(170px,1.2fr) 105px minmax(160px,1fr) 20px;gap:12px}
  .record__title h3{font-size:18px}
  .record__title p{margin-top:2px}
  .methods{top:auto;height:100%;overflow:hidden;padding:21px 24px}
  .methods h2{font-size:24px}
  .methods__intro{margin-top:10px}
  .methods__bars{gap:14px;margin-top:18px}
  .methods__bars p{margin-top:4px;line-height:1.45}
  .methods blockquote{margin-top:16px;padding:11px 0;font-size:12px;line-height:1.6}
  .methods__link{margin-top:13px}
}
</style>
