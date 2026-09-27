<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { GAME_CATALOG } from '@/game/catalog'
import { useChapterStore } from '@/stores/chapter'
import { useExplorationStore } from '@/stores/exploration'
import { useGameStore } from '@/stores/game'
import type { ChapterSlug } from '@/types'

const chapterStore = useChapterStore()
const exploration = useExplorationStore()
const game = useGameStore()

onMounted(() => {
  game.bootstrap()
  void chapterStore.loadChapters()
  void exploration.refresh()
})

const chapters = computed(() => chapterStore.chapters)
const completed = computed(() => game.completedCount)
const originalVisualSlugs = new Set<ChapterSlug>(['northern-wei', 'tang', 'yuan'])

function progressOf(slug: ChapterSlug, chapterId: string) {
  const server = exploration.progress?.chapters?.find((c) => c.chapter_id === chapterId)?.progress ?? 0
  return Math.max(server, game.progressFor(slug))
}

function routeOf(slug: ChapterSlug) {
  return game.stateFor(slug).started ? `/chapter/${slug}` : `/chapter/${slug}/intro`
}
</script>

<template>
  <div class="archive">
    <div class="archive__grain" aria-hidden="true" />
    <header class="archive__nav">
      <RouterLink to="/" class="archive__brand">同心千年</RouterLink>
      <nav aria-label="全局导航">
        <RouterLink to="/journey">我的史册</RouterLink>
        <RouterLink to="/graph">关系总图</RouterLink>
        <RouterLink to="/about">史料与 AI</RouterLink>
      </nav>
    </header>

    <main class="archive__main">
      <header class="archive__intro">
        <div>
          <p class="archive__eyebrow">千年行卷 · 六个章节</p>
          <h1>选择一段身份<br /><em>进入一段历史处境</em></h1>
        </div>
        <div class="archive__status">
          <span>行旅进度</span>
          <strong>{{ completed }}<small>/ 6</small></strong>
          <p>每一章都会留下不同的记录。<br />重大历史不会改变，你的见闻会。</p>
        </div>
      </header>

      <section class="archive__journey" aria-label="历史章节">
        <div class="archive__line" aria-hidden="true" />
        <article
          v-for="(chapter, index) in chapters"
          :key="chapter.id"
          class="era"
          :class="{ 'era--recommended': chapter.slug === 'yuan' }"
          :data-era="chapter.slug"
          :style="{ '--era-accent': chapter.accent }"
        >
          <RouterLink :to="routeOf(chapter.slug)" class="era__link">
            <div class="era__top">
              <span class="era__number">{{ String(index + 1).padStart(2, '0') }}</span>
              <span class="era__date">{{ chapter.date_label }}</span>
              <span class="era__asset-type">
                {{ originalVisualSlugs.has(chapter.slug) ? '史料原图' : '原创章节视觉' }}
              </span>
              <span v-if="chapter.slug === 'yuan'" class="era__recommend">建议首玩</span>
            </div>

            <div class="era__seal" aria-hidden="true">{{ chapter.keyword.slice(0, 1) }}</div>

            <div class="era__copy">
              <p class="era__dynasty">{{ chapter.era }} · {{ chapter.keyword }}</p>
              <h2>{{ GAME_CATALOG[chapter.slug].gameTitle }}</h2>
              <p class="era__role">你将成为：{{ GAME_CATALOG[chapter.slug].role }}</p>
              <p class="era__mission">{{ GAME_CATALOG[chapter.slug].mission }}</p>
            </div>

            <div class="era__foot">
              <span>{{ GAME_CATALOG[chapter.slug].mechanic }}</span>
              <span>{{ GAME_CATALOG[chapter.slug].duration }}</span>
              <i aria-hidden="true">进入 →</i>
            </div>
            <div class="era__progress" :aria-label="`完成度 ${Math.round(progressOf(chapter.slug, chapter.id))}%`">
              <span :style="{ width: `${progressOf(chapter.slug, chapter.id)}%` }" />
            </div>
          </RouterLink>
        </article>
      </section>

      <footer class="archive__foot">
        <p>相遇 → 交融 → 交流 → 共存 → 归属 → 传承</p>
        <span>每个角色身份均会标注史实、重构与游戏创作的边界</span>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.archive {
  position: relative;
  min-height: 100vh;
  color: #ece3d1;
  background:
    radial-gradient(circle at 14% 8%, rgba(75, 111, 98, .18), transparent 23%),
    radial-gradient(circle at 90% 65%, rgba(117, 65, 49, .12), transparent 27%),
    #0c1413;
}
.archive__grain { position: fixed; inset: 0; pointer-events: none; opacity: .18; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 160 160' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.7' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.18'/%3E%3C/svg%3E"); mix-blend-mode: soft-light; }
.archive__nav { position: relative; z-index: 2; height: 68px; display: flex; align-items: center; justify-content: space-between; padding: 0 clamp(22px, 4vw, 68px); border-bottom: 1px solid rgba(223, 199, 145, .12); }
.archive__brand { font-family: var(--font-display); font-size: 15px; letter-spacing: .3em; color: #dec67f; }
.archive__nav nav { display: flex; gap: 28px; font-size: 12px; color: rgba(236,227,209,.48); }
.archive__nav a:hover { color: #dec67f; }
.archive__main { position: relative; z-index: 1; width: min(1420px, calc(100% - 48px)); margin: 0 auto; padding: clamp(48px, 7vw, 92px) 0 52px; }
.archive__intro { display: flex; align-items: flex-end; justify-content: space-between; gap: 48px; padding: 0 clamp(0px, 3vw, 34px) 52px; }
.archive__eyebrow { font-size: 11px; letter-spacing: .25em; color: #be5a43; }
.archive__intro h1 { margin-top: 12px; font-family: var(--font-display); font-size: clamp(42px, 5.6vw, 78px); line-height: 1.12; font-weight: 500; color: #f0e7d5; }
.archive__intro h1 em { color: rgba(240,231,213,.46); font-style: normal; font-weight: 400; }
.archive__status { flex: 0 0 260px; display: grid; grid-template-columns: 1fr auto; gap: 3px 12px; align-items: end; padding-left: 22px; border-left: 1px solid rgba(222,198,127,.26); }
.archive__status > span { font-size: 10px; letter-spacing: .18em; color: rgba(236,227,209,.42); }
.archive__status strong { grid-row: 1 / 3; grid-column: 2; font-family: var(--font-display); font-size: 48px; line-height: 1; color: #dec67f; font-weight: 400; }
.archive__status strong small { font-size: 14px; color: rgba(236,227,209,.35); }
.archive__status p { font-size: 11px; line-height: 1.7; color: rgba(236,227,209,.4); }

.archive__journey { position: relative; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.archive__line { position: absolute; z-index: -1; top: 50%; left: -8vw; right: -8vw; height: 1px; background: linear-gradient(90deg, transparent, rgba(222,198,127,.25) 12%, rgba(222,198,127,.25) 88%, transparent); }
.era { position: relative; min-height: 370px; }
.era__link { position: relative; height: 100%; display: flex; flex-direction: column; overflow: hidden; padding: 22px 22px 18px; border: 1px solid rgba(229, 211, 175, .14); background: linear-gradient(148deg, rgba(255,255,255,.04), rgba(255,255,255,.012)); transition: transform 220ms ease, border-color 220ms ease, background 220ms ease; }
.era__link::before { content: ''; position: absolute; inset: 0; opacity: .08; background: radial-gradient(circle at 75% 18%, var(--era-accent), transparent 35%); transition: opacity 220ms ease; }
.era__link:hover { transform: translateY(-5px); border-color: color-mix(in srgb, var(--era-accent) 65%, #dec67f); background: linear-gradient(148deg, rgba(255,255,255,.065), rgba(255,255,255,.018)); }
.era__link:hover::before { opacity: .18; }
.era--recommended .era__link { border-color: rgba(222,198,127,.34); box-shadow: inset 0 0 0 1px rgba(222,198,127,.05); }
.era__top { position: relative; display: flex; align-items: center; gap: 12px; min-height: 21px; font-size: 10px; letter-spacing: .12em; color: rgba(236,227,209,.36); }
.era__number { color: color-mix(in srgb, var(--era-accent) 70%, #dec67f); font-family: var(--font-display); font-size: 14px; }
.era__recommend { margin-left: auto; padding: 3px 7px; border: 1px solid rgba(222,198,127,.32); color: #dec67f; }
.era__seal { position: absolute; top: 42px; right: 19px; width: 72px; height: 72px; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--era-accent) 58%, transparent); color: color-mix(in srgb, var(--era-accent) 76%, #dec67f); font-family: var(--font-display); font-size: 31px; opacity: .55; transform: rotate(-3deg); }
.era__seal::after { content: ''; position: absolute; inset: 5px; border: 1px solid currentColor; opacity: .42; }
.era__copy { position: relative; margin-top: 61px; max-width: calc(100% - 25px); }
.era__dynasty { font-size: 11px; letter-spacing: .2em; color: color-mix(in srgb, var(--era-accent) 78%, #dec67f); }
.era h2 { margin-top: 7px; font-family: var(--font-display); font-size: clamp(24px, 2.2vw, 34px); line-height: 1.2; font-weight: 500; color: #f0e7d5; }
.era__role { margin-top: 15px; font-family: var(--font-display); color: rgba(236,227,209,.72); }
.era__mission { margin-top: 10px; font-size: 12px; line-height: 1.72; color: rgba(236,227,209,.43); }
.era__foot { position: relative; display: flex; align-items: center; gap: 10px; margin-top: auto; padding-top: 18px; border-top: 1px solid rgba(229,211,175,.1); color: rgba(236,227,209,.35); font-size: 10px; }
.era__foot span + span::before { content: '·'; margin-right: 10px; }
.era__foot i { margin-left: auto; color: #d8bf78; font-style: normal; font-family: var(--font-display); font-size: 12px; }
.era__progress { position: absolute; left: 0; right: 0; bottom: 0; height: 2px; background: rgba(255,255,255,.025); }
.era__progress span { display: block; height: 100%; background: color-mix(in srgb, var(--era-accent) 72%, #dec67f); transition: width .4s ease; }
.archive__foot { display: flex; justify-content: space-between; gap: 24px; margin-top: 38px; padding: 24px 4px 0; border-top: 1px solid rgba(223,199,145,.1); font-size: 11px; color: rgba(236,227,209,.34); }
.archive__foot p { font-family: var(--font-display); letter-spacing: .13em; color: rgba(222,198,127,.52); }

@media (max-width: 1050px) {
  .archive__journey { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .archive__intro { align-items: flex-start; }
}
@media (max-width: 720px) {
  .archive__nav nav { gap: 14px; }
  .archive__intro { flex-direction: column; align-items: stretch; }
  .archive__status { flex-basis: auto; }
  .archive__journey { grid-template-columns: 1fr; }
  .archive__foot { flex-direction: column; }
}

/* V3 青绿行卷：桌面端固定一屏，章节像摊开的六枚签页。 */
.archive {
  color: var(--color-slate-text);
  background:
    radial-gradient(circle at 12% 12%, rgba(255,255,255,.72), transparent 26%),
    radial-gradient(circle at 90% 72%, rgba(178,81,61,.08), transparent 24%),
    linear-gradient(145deg,#edf3ea,#d8e7de);
}
.archive__grain { opacity:.1;mix-blend-mode:multiply; }
.archive__nav { border-bottom-color:rgba(40,95,97,.16);background:rgba(245,248,241,.42);backdrop-filter:blur(12px); }
.archive__brand { color:var(--color-mineral-800); }
.archive__nav nav { color:rgba(33,76,83,.6); }
.archive__nav a:hover { color:var(--color-scroll-red); }
.archive__eyebrow { color:var(--color-scroll-red); }
.archive__intro h1 { color:var(--color-mineral-800); }
.archive__intro h1 em { color:rgba(41,69,74,.48); }
.archive__status { border-left-color:rgba(40,95,97,.24); }
.archive__status > span,.archive__status p { color:rgba(41,69,74,.5); }
.archive__status strong { color:var(--color-scroll-gold); }
.archive__status strong small { color:rgba(41,69,74,.4); }
.archive__line { background:linear-gradient(90deg,transparent,rgba(40,95,97,.2) 12%,rgba(40,95,97,.2) 88%,transparent); }
.era__link { border-color:rgba(40,95,97,.16);background:linear-gradient(145deg,rgba(255,255,255,.52),rgba(237,244,237,.58));box-shadow:0 12px 32px rgba(50,92,82,.06); }
.era__link:hover { background:rgba(255,255,255,.72);box-shadow:0 18px 42px rgba(50,92,82,.12); }
.era--recommended .era__link { border-color:rgba(178,138,69,.55); }
.era__top { color:rgba(41,69,74,.45); }
.era__recommend { border-color:rgba(178,138,69,.42);color:#8b6a2f;background:rgba(255,250,231,.55); }
.era h2 { color:var(--color-mineral-800); }
.era__role { color:rgba(41,69,74,.76); }
.era__mission { color:rgba(41,69,74,.56); }
.era__foot { border-top-color:rgba(40,95,97,.12);color:rgba(41,69,74,.46); }
.era__foot i { color:var(--color-scroll-red); }
.archive__foot { border-top-color:rgba(40,95,97,.12);color:rgba(41,69,74,.48); }
.archive__foot p { color:rgba(40,95,97,.72); }

@media (min-width:1051px) {
  .archive { height:100dvh;min-height:720px;overflow:hidden; }
  .archive__nav { height:62px; }
  .archive__main { height:calc(100dvh - 62px);min-height:658px;padding:24px 0 18px;display:flex;flex-direction:column; }
  .archive__intro { flex:none;padding:0 24px 20px;align-items:center; }
  .archive__intro h1 { margin-top:6px;font-size:clamp(34px,3.7vw,54px);line-height:1.08; }
  .archive__status { flex-basis:245px; }
  .archive__status strong { font-size:38px; }
  .archive__journey { flex:1;min-height:0;grid-template-rows:repeat(2,minmax(0,1fr)); }
  .era { min-height:0; }
  .era__link { padding:15px 18px 13px; }
  .era__seal { top:34px;width:58px;height:58px;font-size:25px; }
  .era__copy { margin-top:29px; }
  .era h2 { font-size:clamp(21px,1.7vw,29px); }
  .era__role { margin-top:8px;font-size:13px; }
  .era__mission { margin-top:6px;line-height:1.55;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden; }
  .era__foot { padding-top:9px; }
  .archive__foot { flex:none;margin-top:12px;padding-top:10px; }
}

/* V4 角色牌选择：青绿画框、金线掠光、聚焦式悬浮。 */
.archive::before,.archive::after{content:'';position:fixed;z-index:0;pointer-events:none;border:1px solid rgba(178,138,69,.25);width:110px;height:110px}.archive::before{left:18px;top:80px;border-right:0;border-bottom:0}.archive::after{right:18px;bottom:18px;border-left:0;border-top:0}
.archive__journey{perspective:1100px}
.era{transition:opacity 220ms ease,transform 220ms ease,z-index 0s 180ms}
.era:hover,.era:focus-within{z-index:4;transition-delay:0s}
.archive__journey:has(.era:hover) .era:not(:hover),.archive__journey:has(.era:focus-within) .era:not(:focus-within){opacity:.66;transform:scale(.992)}
.era__link{isolation:isolate;transform-origin:50% 70%;outline-offset:5px}
.era__link::before{z-index:0;opacity:.18;background-image:var(--era-art);background-size:var(--era-art-size,cover);background-position:var(--era-art-position,center);background-repeat:no-repeat;filter:saturate(.72) contrast(.92);mask-image:linear-gradient(100deg,transparent 0%,rgba(0,0,0,.18) 28%,#000 72%);transition:opacity 260ms ease,filter 260ms ease,transform 420ms var(--ease-standard)}
.era__link::after{content:'';position:absolute;z-index:1;inset:7px;border:1px solid color-mix(in srgb,var(--era-accent) 22%,rgba(178,138,69,.3));pointer-events:none;box-shadow:18px 0 0 -17px rgba(178,138,69,.65),-18px 0 0 -17px rgba(178,138,69,.65);transition:border-color 220ms ease,box-shadow 220ms ease}
.era__top,.era__seal,.era__copy,.era__foot,.era__progress{z-index:2}
.era__asset-type{margin-left:auto;padding:2px 6px;border:1px solid color-mix(in srgb,var(--era-accent) 28%,rgba(40,95,97,.18));background:rgba(245,249,242,.58);color:rgba(41,69,74,.58);letter-spacing:.08em;white-space:nowrap}
.era__recommend{margin-left:0}
.era[data-era='han']{--era-art:url('/assets/han/han-caravan-v1.png');--era-art-size:cover;--era-art-position:68% center}
.era[data-era='northern-wei']{--era-art:url('/assets/wei/yungang-cave20-original.jpg');--era-art-position:58% center}
.era[data-era='tang']{--era-art:url('/assets/tang/bunian-original.jpg');--era-art-position:66% center}
.era[data-era='yuan']{--era-art:url('/assets/yuan/yuntai-east-wall-original.jpg');--era-art-position:center}
.era[data-era='qing']{--era-art:url('/assets/qing/qing-migration-v1.png');--era-art-size:cover;--era-art-position:70% center}
.era[data-era='contemporary']{--era-art:url('/assets/contemporary/qiang-workshop-v1.png');--era-art-size:cover;--era-art-position:66% center}
.era__copy,.era__seal,.era__foot{transition:transform 260ms var(--ease-standard),opacity 220ms ease}
.era__link:hover,.era__link:focus-visible{transform:translateY(-7px) scale(1.018);border-color:color-mix(in srgb,var(--era-accent) 54%,var(--color-luminous-gold));box-shadow:var(--shadow-game-card),0 0 30px color-mix(in srgb,var(--era-accent) 12%,transparent)}
.era__link:hover::before,.era__link:focus-visible::before{opacity:.34;filter:saturate(.9) contrast(.96);transform:scale(1.025)}
.era__link:hover::after,.era__link:focus-visible::after{border-color:color-mix(in srgb,var(--era-accent) 44%,var(--color-luminous-gold));box-shadow:18px 0 0 -17px var(--color-luminous-gold),-18px 0 0 -17px var(--color-luminous-gold)}
.era__link:hover .era__copy,.era__link:focus-visible .era__copy{transform:translateY(-3px)}
.era__link:hover .era__seal,.era__link:focus-visible .era__seal{opacity:.9;transform:rotate(0deg) scale(1.08);box-shadow:0 0 24px color-mix(in srgb,var(--era-accent) 18%,transparent)}
.era__link:hover .era__foot i,.era__link:focus-visible .era__foot i{transform:translateX(4px)}
.era__foot i{transition:transform 180ms ease}
.era--recommended .era__link{background:linear-gradient(145deg,rgba(255,253,241,.74),rgba(234,242,234,.68))}
.era--recommended .era__recommend{box-shadow:0 0 20px rgba(217,187,115,.18) inset}
@media(prefers-reduced-motion:reduce){.era,.era__link,.era__copy,.era__seal,.era__foot,.era__foot i{transition-duration:1ms}.era__link:hover,.era__link:focus-visible{transform:none}.archive__journey:has(.era:hover) .era:not(:hover),.archive__journey:has(.era:focus-within) .era:not(:focus-within){opacity:1;transform:none}}
</style>
