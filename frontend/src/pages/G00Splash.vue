<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { GAME_CATALOG } from '@/game/catalog'
import { useGameStore } from '@/stores/game'

const router = useRouter()
const game = useGameStore()
const ready = ref(false)
const chapters = Object.values(GAME_CATALOG)
const completed = computed(() => game.completedCount)
const resetDone = ref(false)

onMounted(() => {
  window.setTimeout(() => (ready.value = true), 720)
})

function enter() {
  void router.push('/timeline')
}

function resetDebugProgress() {
  const confirmed = window.confirm('调试重置将清除六个章节的总进度与元代剧情存档，并从首次进入状态重新开始。确定继续吗？')
  if (!confirmed) return
  game.resetAll()
  localStorage.removeItem('tongxin.yuan.story.v6')
  resetDone.value = true
}
</script>

<template>
  <main class="splash" :class="{ ready }">
    <div class="splash__art" aria-hidden="true" />
    <div class="splash__grain" aria-hidden="true" />
    <svg class="splash__thread" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="threadGold" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#887044" stop-opacity="0" />
          <stop offset=".16" stop-color="#d4b66e" />
          <stop offset=".5" stop-color="#f0d792" />
          <stop offset=".84" stop-color="#d4b66e" />
          <stop offset="1" stop-color="#887044" stop-opacity="0" />
        </linearGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <path class="thread thread--ghost" d="M-80 634 C180 514 303 702 511 563 S821 376 1017 491 1324 658 1680 431" />
      <path class="thread thread--live" d="M-80 634 C180 514 303 702 511 563 S821 376 1017 491 1324 658 1680 431" />
      <g class="thread__knots">
        <circle v-for="(chapter, i) in chapters" :key="chapter.slug" :cx="178 + i * 248" :cy="[571,616,540,435,514,530][i]" r="5" />
      </g>
    </svg>

    <nav class="splash__nav" aria-label="辅助导航">
      <span class="splash__brand">同心千年</span>
      <div>
        <RouterLink to="/about">史料与 AI 说明</RouterLink>
        <span class="splash__progress">已结成 {{ completed }}/6</span>
        <button class="splash__reset" type="button" @click="resetDebugProgress">
          {{ resetDone ? '进度已重置' : '调试 · 重置进度' }}
        </button>
      </div>
    </nav>

    <section class="splash__hero">
      <p class="splash__eyebrow">证据型历史文游 · 第一季</p>
      <h1>
        <span>六段人生</span>
        <em>一条延续千年的相遇之路</em>
      </h1>
      <p class="splash__lead">
        你不能改变已经发生的历史。<br />
        但你可以决定自己看见什么、相信谁，又留下怎样的记录。
      </p>

      <button class="splash__enter" type="button" :disabled="!ready" @click="enter">
        <span>{{ completed ? '继续你的千年行旅' : '领取第一段身份' }}</span>
        <i aria-hidden="true">→</i>
      </button>

      <div class="splash__proof">
        <span>真实史料为边界</span>
        <span>个人经历可分支</span>
        <span>AI 回答可追溯</span>
      </div>
    </section>

    <ol class="splash__chapters" aria-label="六个历史章节">
      <li v-for="(chapter, index) in chapters" :key="chapter.slug">
        <span>{{ String(index + 1).padStart(2, '0') }}</span>
        <strong>{{ chapter.gameTitle }}</strong>
        <small>{{ chapter.role }}</small>
      </li>
    </ol>

    <p class="splash__notice">历史人物与事件依据审核资料；章内玩家角色为明确标注的游戏原创角色。</p>
  </main>
</template>

<style scoped>
.splash {
  position: relative;
  height: 100dvh;
  min-height: 700px;
  overflow: hidden;
  color: var(--color-slate-text);
  background:
    radial-gradient(circle at 74% 25%, rgba(255,255,255,.82), transparent 25%),
    radial-gradient(circle at 12% 90%, rgba(178,81,61,.11), transparent 28%),
    linear-gradient(135deg, #edf3ea 0%, #dbe9e0 55%, #c9ddd2 100%);
}
.splash__art {
  position: absolute;
  z-index: 0;
  inset: 68px 0 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(237,243,234,.98) 0%, rgba(237,243,234,.93) 25%, rgba(232,240,234,.52) 48%, rgba(217,232,222,.06) 76%),
    linear-gradient(0deg, rgba(223,235,226,.38), transparent 48%),
    url('/assets/global/millennia-hero-v1.png') 58% center / cover no-repeat;
  filter: saturate(.84) contrast(.97);
  opacity: 0;
  transform: scale(1.025);
  transition: opacity 1.4s ease .12s, transform 2.2s cubic-bezier(.2,.75,.2,1) .12s;
}
.ready .splash__art { opacity: .9; transform: scale(1); }
.splash__grain { position: absolute; z-index:3; inset: 0; opacity: .12; pointer-events: none; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.18'/%3E%3C/svg%3E"); mix-blend-mode: multiply; }
.splash__thread { position: absolute; z-index:1; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.thread { fill: none; vector-effect: non-scaling-stroke; }
.thread--ghost { stroke: rgba(40, 95, 97, .1); stroke-width: 18; }
.thread--live { stroke: url(#threadGold); stroke-width: 1.6; filter: url(#glow); stroke-dasharray: 1900; stroke-dashoffset: 1900; transition: stroke-dashoffset 2.2s cubic-bezier(.3,.7,.2,1) .25s; }
.ready .thread--live { stroke-dashoffset: 0; }
.thread__knots { fill: #b28a45; opacity: 0; filter: url(#glow); transition: opacity .6s ease 1.8s; }
.ready .thread__knots { opacity: 1; }

.splash__nav { position: relative; z-index: 4; height: 68px; display: flex; align-items: center; justify-content: space-between; padding: 0 clamp(24px, 5vw, 80px); border-bottom: 1px solid rgba(40,95,97,.16); background:rgba(244,248,241,.34); backdrop-filter:blur(12px); }
.splash__brand { font-family: var(--font-display); letter-spacing: .32em; font-size: 15px; color: var(--color-mineral-800); }
.splash__nav div { display: flex; align-items: center; gap: 24px; font-size: 12px; color: rgba(33,76,83,.62); }
.splash__nav a:hover { color: var(--color-scroll-red); }
.splash__progress { padding-left: 24px; border-left: 1px solid rgba(40,95,97,.18); }
.splash__reset { min-height: 30px; border: 1px solid rgba(178,81,61,.34); border-radius: 2px; padding: 0 11px; background: rgba(255,255,255,.28); color: #9b493b; font-size: 10px; letter-spacing: .08em; transition: color .18s ease, border-color .18s ease, background-color .18s ease; }
.splash__reset:hover { border-color: var(--color-scroll-red); background: rgba(255,255,255,.66); color: var(--color-scroll-red); }
.splash__reset:focus-visible { outline: 2px solid rgba(178,81,61,.42); outline-offset: 3px; }

.splash__hero { position: relative; z-index: 4; width: min(1440px, calc(100% - 96px)); margin: clamp(45px, 7vh, 76px) auto 0; padding-right:min(38vw,520px); }
.splash__eyebrow { color: #c76249; font-size: 12px; letter-spacing: .26em; opacity: 0; transform: translateY(10px); transition: .7s ease .15s; }
.splash h1 { max-width: 920px; margin-top: 18px; font-family: var(--font-display); font-weight: 500; line-height: 1.08; }
.splash h1 span { display: block; font-size: clamp(58px, 8vw, 112px); letter-spacing: .08em; color: var(--color-mineral-800); opacity: 0; transform: translateY(18px); transition: .9s cubic-bezier(.2,.8,.2,1) .25s; text-shadow:0 2px 0 rgba(255,255,255,.45); }
.splash h1 em { display: block; margin-top: 10px; font-size: clamp(24px, 2.8vw, 40px); font-style: normal; font-weight: 400; letter-spacing: .08em; color: rgba(41,69,74,.62); opacity: 0; transform: translateY(16px); transition: .8s ease .45s; }
.splash__lead { margin-top: 27px; font-family: var(--font-display); font-size: clamp(15px, 1.35vw, 18px); line-height: 1.9; color: rgba(41,69,74,.72); opacity: 0; transition: opacity .8s ease .7s; }
.ready .splash__eyebrow, .ready h1 span, .ready h1 em { opacity: 1; transform: none; }
.ready .splash__lead { opacity: 1; }

.splash__enter { margin-top: 28px; min-width: 285px; height: 54px; display: inline-flex; align-items: center; justify-content: space-between; gap: 28px; border: 1px solid rgba(40,95,97,.5); border-radius: 2px; padding: 0 20px 0 24px; background: rgba(248,250,244,.55); color: var(--color-mineral-800); box-shadow:0 14px 36px rgba(50,92,82,.1); font-family: var(--font-display); font-size: 16px; letter-spacing: .08em; opacity: 0; transform: translateY(10px); transition: opacity .7s ease .9s, transform .7s ease .9s, background-color .18s ease, border-color .18s ease; }
.ready .splash__enter { opacity: 1; transform: none; }
.splash__enter:not(:disabled):hover { background: rgba(255,255,255,.74); border-color: var(--color-scroll-red); }
.splash__enter i { font-style: normal; color: var(--color-scroll-red); font-family: var(--font-ui); font-size: 20px; }
.splash__proof { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 18px; font-size: 11px; letter-spacing: .08em; color: rgba(41,69,74,.52); }
.splash__proof span::before { content: '◇'; margin-right: 7px; color: var(--color-scroll-gold); }

.splash__chapters { position: absolute; z-index: 4; right: clamp(24px,5vw,80px); bottom: 68px; width: min(450px,34vw); list-style: none; margin: 0; padding: 8px 18px; display: grid; grid-template-columns: 1fr 1fr; border: 1px solid rgba(40,95,97,.16); background:rgba(243,248,241,.62); backdrop-filter:blur(12px); box-shadow:0 18px 50px rgba(50,92,82,.12); }
.splash__chapters li { min-height: 62px; display: grid; grid-template-columns: 28px 1fr; align-content: center; gap: 2px 10px; border-bottom: 1px solid rgba(40,95,97,.12); padding: 8px 10px; }
.splash__chapters li:nth-child(odd) { border-right: 1px solid rgba(40,95,97,.12); }
.splash__chapters span { grid-row: 1 / 3; color: var(--color-scroll-gold); font-family: var(--font-display); }
.splash__chapters strong { font-family: var(--font-display); font-weight: 500; font-size: 14px; color: var(--color-mineral-800); }
.splash__chapters small { font-size: 10px; color: rgba(41,69,74,.54); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.splash__notice { position: absolute; z-index:4; left: clamp(24px,5vw,80px); bottom: 22px; font-size: 10px; color: rgba(41,69,74,.45); }

@media (max-width: 1050px) {
  .splash { height:auto;min-height:100dvh;overflow:visible; }
  .splash__art { position:fixed;inset:68px 0 0;background-position:66% center;opacity:.42!important; }
  .splash__hero { margin-top: 70px; }
  .splash__hero { padding-right:0;width:calc(100% - 48px); }
  .splash__chapters { position: relative; right: auto; bottom: auto; width: calc(100% - 48px); margin: 72px auto 70px; }
  .splash__notice { position: relative; left: auto; bottom: auto; width: calc(100% - 48px); margin: -40px auto 24px; }
}
@media (max-width: 620px) {
  .splash__nav { padding: 0 20px; }
  .splash__nav a, .splash__progress { display: none; }
  .splash__reset { padding: 0 9px; font-size: 9px; }
  .splash__hero { margin-top: 56px; }
  .splash h1 span { font-size: 52px; }
  .splash__chapters { grid-template-columns: 1fr; }
  .splash__chapters li:nth-child(odd) { border-right: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .thread--live { stroke-dashoffset: 0; }
  .splash__eyebrow, .splash h1 span, .splash h1 em, .splash__lead, .splash__enter { opacity: 1; transform: none; }
}

/* V4 开场按钮与行卷画框：一次明确的“进入游戏”聚焦。 */
.splash__enter{position:relative;overflow:hidden;box-shadow:0 16px 38px rgba(50,92,82,.13),0 0 0 4px rgba(255,255,255,.2)}
.splash__enter::before{content:'';position:absolute;inset:-90% -30%;background:linear-gradient(105deg,transparent 41%,rgba(255,255,255,.9) 50%,transparent 59%);transform:translateX(-72%);transition:transform 620ms var(--ease-standard)}
.splash__enter:not(:disabled):hover::before{transform:translateX(72%)}
.splash__enter:not(:disabled):hover{box-shadow:0 20px 48px rgba(50,92,82,.18),0 0 22px rgba(217,187,115,.18)}
.splash__enter span,.splash__enter i{position:relative;z-index:1}
.splash__chapters::before{content:'';position:absolute;inset:7px;pointer-events:none;border:1px solid rgba(178,138,69,.2)}
.splash__chapters li{position:relative;transition:background-color 180ms ease,color 180ms ease}
.splash__chapters li::after{content:'';position:absolute;left:10px;right:10px;bottom:5px;height:1px;transform:scaleX(0);background:linear-gradient(90deg,transparent,var(--color-luminous-gold),transparent);transition:transform 240ms ease}
.splash__chapters li:hover{background:rgba(255,255,255,.24)}.splash__chapters li:hover::after{transform:scaleX(1)}
@media(prefers-reduced-motion:reduce){.splash__enter::before{display:none}}
</style>
