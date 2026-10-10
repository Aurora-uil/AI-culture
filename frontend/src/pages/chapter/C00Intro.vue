<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GAME_CATALOG } from '@/game/catalog'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
import { useExplorationStore } from '@/stores/exploration'
import type { ChapterSlug } from '@/types'

const route = useRoute()
const router = useRouter()
const chapterStore = useChapterStore()
const exploration = useExplorationStore()
const slug = computed(() => route.params.slug as ChapterSlug)
const chapter = computed(() => chapterStore.current)
const meta = computed(() => GAME_CATALOG[slug.value])

const CHAPTER_ART: Record<ChapterSlug, { src: string; label: string; fit?: 'cover' | 'contain'; position?: string }> = {
  han: { src: '/assets/han/han-route-scene-v2.png', label: 'AI历史环境重构 · 非史实照片', position: '58% center' },
  'northern-wei': { src: '/assets/wei/yungang-cave20-original.jpg', label: '云冈石窟第20窟 · 历史原图', position: 'center' },
  tang: { src: '/assets/tang/bunian-original.jpg', label: '《步辇图》· 历史原图', position: '64% center' },
  yuan: { src: '/assets/yuan/yuntai-east-wall-original.jpg', label: '居庸关云台东壁 · 历史原图', position: '52% center' },
  qing: { src: '/assets/qing/qing-migration-photoreal-v2.png', label: 'AI历史环境重构 · 非史实照片', position: 'center' },
  contemporary: { src: '/assets/contemporary/qiang-workshop-photoreal-v2.png', label: 'AI当代工坊情境重构 · 非纪实照片', position: 'center' },
}
const art = computed(() => CHAPTER_ART[slug.value])

onMounted(async () => {
  const id = SLUG_TO_ID[slug.value]
  if (id && chapterStore.current?.id !== id) await chapterStore.loadChapter(id)
  if (id) {
    await exploration.ensureSession(id)
    exploration.track('CHAPTER_ENTER', {}, id)
  }
})
</script>

<template>
  <main v-if="chapter" class="intro" :style="{ '--era-accent': chapter.accent }">
    <figure class="intro__art" aria-hidden="true">
      <img :src="art.src" alt="" :style="{ objectFit: art.fit || 'cover', objectPosition: art.position || 'center' }" />
      <figcaption>{{ art.label }}</figcaption>
    </figure>
    <div class="intro__grain" aria-hidden="true" />
    <div class="intro__motes" aria-hidden="true">
      <i v-for="index in 12" :key="index" />
    </div>
    <div class="intro__rings" aria-hidden="true"><i /><i /><i /></div>
    <RouterLink to="/timeline" class="intro__back">← 返回千年行卷</RouterLink>

    <section class="intro__content">
      <p class="intro__chapter">第 {{ String(chapter.sort_order).padStart(2, '0') }} 章 · {{ chapter.era }} · {{ chapter.date_label }}</p>
      <h1>{{ meta.gameTitle }}</h1>
      <p class="intro__keyword">{{ chapter.keyword }}</p>
      <blockquote>“{{ meta.openingLine }}”</blockquote>
      <div class="intro__role">
        <span>本章身份</span>
        <strong>{{ meta.role }}</strong>
        <small>{{ meta.roleNote }}</small>
      </div>
      <div class="intro__anchor">
        <span>主证物</span>
        <strong>{{ meta.storyAnchor.name }}</strong>
        <em>{{ meta.storyAnchor.statusLabel }}</em>
      </div>
      <div class="intro__actions">
        <button type="button" @click="router.push(`/chapter/${slug}`)">
          <span>进入任务简报</span><i aria-hidden="true">→</i>
        </button>
        <button type="button" @click="router.push(`/chapter/${slug}/story`)">直接进入剧情</button>
      </div>
    </section>

    <footer class="intro__foot">
      <span>{{ meta.mechanic }}</span><span>{{ meta.duration }}</span><span>结章信物：{{ meta.artifact }}</span>
    </footer>
  </main>
</template>

<style scoped>
.intro { position: relative; min-height: 100vh; overflow: hidden; display: grid; place-items: center; color: #eee5d2; background: radial-gradient(circle at 50% 48%, color-mix(in srgb, var(--era-accent) 20%, transparent), transparent 32%), #09110f; }
.intro__art{position:absolute;inset:0 0 0 42%;margin:0;overflow:hidden;opacity:.36;mask-image:linear-gradient(90deg,transparent 0,#000 34%,#000 100%)}
.intro__art::after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(227,239,229,.05),rgba(39,77,75,.14))}
.intro__art img{width:100%;height:100%;display:block;filter:saturate(.72) contrast(.96)}
.intro__art figcaption{position:absolute;z-index:1;right:24px;bottom:24px;padding:5px 10px;border:1px solid rgba(255,255,255,.36);border-radius:999px;background:rgba(246,249,242,.76);backdrop-filter:blur(8px);font-size:9px;letter-spacing:.12em;color:rgba(41,69,74,.72)}
.intro__grain { position: absolute; inset: 0; opacity: .2; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 140 140' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.78' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.18'/%3E%3C/svg%3E"); mix-blend-mode: soft-light; }
.intro__rings { position: absolute; width: min(76vw, 850px); aspect-ratio: 1; border-radius: 50%; border: 1px solid color-mix(in srgb, var(--era-accent) 32%, transparent); animation: breathe 7s ease-in-out infinite; }
.intro__rings i { position: absolute; border-radius: 50%; border: 1px solid color-mix(in srgb, var(--era-accent) 18%, transparent); }
.intro__rings i:nth-child(1) { inset: 12%; }.intro__rings i:nth-child(2) { inset: 28%; }.intro__rings i:nth-child(3) { inset: 43%; background: color-mix(in srgb, var(--era-accent) 8%, transparent); }
.intro__back { position: absolute; z-index: 2; left: clamp(22px,4vw,64px); top: 28px; font-size: 11px; letter-spacing: .1em; color: rgba(238,229,210,.42); }
.intro__back:hover { color: #dec67f; }
.intro__content { position: relative; z-index: 1; width: min(720px, calc(100% - 40px)); text-align: center; padding: 70px 0; }
.intro__chapter { font-size: 10px; letter-spacing: .25em; color: color-mix(in srgb, var(--era-accent) 72%, #dec67f); animation: rise .7s both; }
.intro h1 { margin-top: 18px; font-family: var(--font-display); font-size: clamp(55px,9vw,118px); line-height: 1; font-weight: 500; letter-spacing: .08em; color: #f0e7d5; animation: rise .8s .12s both; }
.intro__keyword { margin-top: 12px; font-family: var(--font-display); font-size: 15px; letter-spacing: .6em; color: rgba(238,229,210,.38); animation: rise .8s .2s both; }
.intro blockquote { margin: 38px auto 0; max-width: 560px; font-family: var(--font-display); font-size: clamp(16px,2vw,22px); line-height: 1.8; color: rgba(238,229,210,.68); animation: rise .8s .3s both; }
.intro__role { margin: 32px auto 0; display: flex; flex-direction: column; gap: 4px; animation: rise .8s .4s both; }
.intro__role span { font-size: 9px; letter-spacing: .23em; color: rgba(238,229,210,.34); }.intro__role strong { font-family: var(--font-display); font-size: 21px; font-weight: 500; color: #dec67f; }.intro__role small { color: rgba(238,229,210,.3); }
.intro__actions { margin-top: 32px; display: flex; justify-content: center; gap: 10px; animation: rise .8s .5s both; }
.intro__actions button { height: 50px; padding: 0 19px; border: 1px solid rgba(222,198,127,.2); border-radius: 0; background: transparent; color: rgba(238,229,210,.52); }
.intro__actions button:first-child { min-width: 210px; display: flex; align-items: center; justify-content: space-between; background: color-mix(in srgb, var(--era-accent) 18%, transparent); border-color: color-mix(in srgb, var(--era-accent) 68%, #dec67f); color: #f0e7d5; font-family: var(--font-display); font-size: 15px; }
.intro__actions button:hover { border-color: #dec67f; color: #f0e7d5; }.intro__actions i { font-style: normal; color: #dec67f; }
.intro__foot { position: absolute; z-index: 1; bottom: 28px; display: flex; gap: 24px; font-size: 10px; letter-spacing: .1em; color: rgba(238,229,210,.3); }.intro__foot span + span::before { content: '◇'; margin-right: 24px; color: rgba(222,198,127,.42); }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes breathe { 50% { transform: scale(1.025); opacity: .72; } }
@media (max-width: 620px) { .intro__actions { flex-direction: column; }.intro__foot { display: none; } }
@media (prefers-reduced-motion: reduce) { .intro__rings { animation: none; }.intro__chapter,.intro h1,.intro__keyword,.intro blockquote,.intro__role,.intro__actions { animation: none; } }

/* V3 青绿章节扉页 */
.intro{height:100dvh;min-height:680px;color:var(--color-slate-text);background:radial-gradient(circle at 50% 46%,color-mix(in srgb,var(--era-accent) 14%,white),transparent 34%),linear-gradient(145deg,#edf3ea,#d4e5db)}
.intro__grain{opacity:.09;mix-blend-mode:multiply}
.intro__rings{border-color:color-mix(in srgb,var(--era-accent) 28%,rgba(40,95,97,.2))}
.intro__rings i{border-color:color-mix(in srgb,var(--era-accent) 18%,rgba(40,95,97,.15))}
.intro__back{color:rgba(41,69,74,.56)}
.intro__back:hover{color:var(--color-scroll-red)}
.intro h1{color:var(--color-mineral-800);text-shadow:0 2px 0 rgba(255,255,255,.55)}
.intro__keyword{color:rgba(41,69,74,.45)}
.intro blockquote{color:rgba(41,69,74,.7)}
.intro__role span{color:rgba(41,69,74,.45)}
.intro__role strong{color:color-mix(in srgb,var(--era-accent) 70%,var(--color-mineral-700))}
.intro__role small{color:rgba(41,69,74,.48)}
.intro__actions button{border-color:rgba(40,95,97,.22);color:rgba(41,69,74,.68);background:rgba(248,250,244,.35)}
.intro__actions button:first-child{background:color-mix(in srgb,var(--era-accent) 10%,rgba(255,255,255,.68));border-color:color-mix(in srgb,var(--era-accent) 58%,var(--color-mineral-700));color:var(--color-mineral-800)}
.intro__actions button:hover{border-color:var(--color-scroll-red);color:var(--color-scroll-red)}
.intro__actions i{color:var(--color-scroll-red)}
.intro__foot{color:rgba(41,69,74,.45)}
.intro__foot span + span::before{color:var(--color-scroll-gold)}

/* V4 章节开幕：以“时间镜门”聚焦玩家身份。 */
.intro__content::before,.intro__content::after{content:'';position:absolute;top:50%;width:clamp(70px,12vw,180px);height:1px;background:linear-gradient(90deg,transparent,rgba(178,138,69,.56));pointer-events:none}.intro__content::before{right:calc(100% + 26px)}.intro__content::after{left:calc(100% + 26px);transform:scaleX(-1)}
.intro__role{position:relative;width:min(480px,90%);padding:13px 32px 15px;border-block:1px solid rgba(178,138,69,.34);background:linear-gradient(90deg,transparent,rgba(255,252,235,.72) 18%,rgba(255,252,235,.72) 82%,transparent)}
.intro__role::before,.intro__role::after{content:'◇';position:absolute;top:50%;transform:translateY(-50%);color:var(--color-scroll-gold);font-size:12px}.intro__role::before{left:9px}.intro__role::after{right:9px}
.intro__actions button{position:relative;overflow:hidden;box-shadow:0 10px 28px rgba(42,77,73,.07);transition:border-color 180ms ease,color 180ms ease,background-color 180ms ease,transform 180ms ease,box-shadow 180ms ease}
.intro__actions button:first-child::before{content:'';position:absolute;inset:-90% -35%;background:linear-gradient(105deg,transparent 41%,rgba(255,255,255,.78) 50%,transparent 59%);transform:translateX(-70%);transition:transform 540ms ease}.intro__actions button:first-child:hover::before{transform:translateX(70%)}
.intro__actions button:first-child:hover{box-shadow:0 15px 34px color-mix(in srgb,var(--era-accent) 16%,transparent);transform:translateY(-2px)}
.intro__actions button span,.intro__actions button i{position:relative;z-index:1}
@media(prefers-reduced-motion:reduce){.intro__actions button:first-child::before{display:none}}
@media(max-width:760px){.intro__art{inset:38% 0 0 0;opacity:.19;mask-image:linear-gradient(180deg,transparent,#000 38%)}.intro__art figcaption{display:none}}

/* V5 游戏开幕：借鉴剧情游戏的标题演出，以时代尘光代替宫廷花瓣。 */
.intro::before{
  content:'';
  position:absolute;
  z-index:1;
  inset:14px;
  border:1px solid color-mix(in srgb,var(--era-accent) 22%,rgba(178,138,69,.3));
  pointer-events:none;
  clip-path:polygon(0 0,18% 0,18% 1px,82% 1px,82% 0,100% 0,100% 100%,82% 100%,82% calc(100% - 1px),18% calc(100% - 1px),18% 100%,0 100%);
}
.intro__art img{animation:intro-camera 8s ease-out both}
.intro__motes{position:absolute;z-index:1;inset:0;overflow:hidden;pointer-events:none}
.intro__motes i{position:absolute;width:4px;height:4px;border-radius:50% 0 50% 50%;background:color-mix(in srgb,var(--era-accent) 46%,#e8cd86);box-shadow:0 0 12px rgba(217,187,115,.45);opacity:0;animation:intro-mote 6.5s linear infinite}
.intro__motes i:nth-child(1){left:8%;top:82%;animation-delay:-1s}.intro__motes i:nth-child(2){left:17%;top:64%;animation-delay:-4s}.intro__motes i:nth-child(3){left:28%;top:88%;animation-delay:-2.4s}.intro__motes i:nth-child(4){left:39%;top:73%;animation-delay:-5.1s}.intro__motes i:nth-child(5){left:49%;top:92%;animation-delay:-3.4s}.intro__motes i:nth-child(6){left:57%;top:67%;animation-delay:-.4s}.intro__motes i:nth-child(7){left:66%;top:86%;animation-delay:-4.6s}.intro__motes i:nth-child(8){left:74%;top:72%;animation-delay:-2s}.intro__motes i:nth-child(9){left:83%;top:91%;animation-delay:-5.8s}.intro__motes i:nth-child(10){left:91%;top:61%;animation-delay:-3s}.intro__motes i:nth-child(11){left:34%;top:96%;animation-delay:-6s}.intro__motes i:nth-child(12){left:71%;top:97%;animation-delay:-1.6s}
.intro__actions button:first-child{min-width:230px;box-shadow:0 12px 36px color-mix(in srgb,var(--era-accent) 14%,transparent),0 0 0 1px rgba(255,255,255,.44) inset}
.intro__actions button:first-child i{transition:transform 260ms var(--ease-standard)}
.intro__actions button:first-child:hover i{transform:translateX(6px)}
@keyframes intro-camera{from{transform:scale(1.065);filter:saturate(.58) contrast(.9) blur(2px)}to{transform:scale(1);filter:saturate(.72) contrast(.96)}}
@keyframes intro-mote{0%{opacity:0;transform:translate(0,16px) rotate(10deg) scale(.5)}18%{opacity:.72}78%{opacity:.35}100%{opacity:0;transform:translate(34px,-150px) rotate(220deg) scale(1.1)}}
@media(prefers-reduced-motion:reduce){.intro__art img,.intro__motes i{animation:none}.intro__motes{display:none}}

/* V6 全景式章节开幕：真实场景占据舞台，信息只覆盖在低细节区域。 */
.intro{
  display:block;
  background:#dbe8df;
  color:#fff9e8;
}
.intro__art{inset:0;opacity:1;mask-image:none}
.intro__art::after{
  background:
    linear-gradient(90deg,rgba(18,52,50,.9) 0,rgba(20,56,54,.77) 32%,rgba(20,55,53,.18) 64%,rgba(20,55,53,.04) 100%),
    linear-gradient(0deg,rgba(16,46,44,.72),transparent 32%),
    linear-gradient(180deg,rgba(14,43,42,.42),transparent 24%);
}
.intro__art img{filter:saturate(.9) contrast(1.06) brightness(.9)}
.intro__art figcaption{right:28px;bottom:26px;border-color:rgba(255,246,219,.44);background:rgba(24,58,55,.72);color:#fff8e7;text-shadow:0 1px 8px rgba(0,0,0,.3)}
.intro__grain{opacity:.12;mix-blend-mode:soft-light}
.intro__rings{left:8vw;top:50%;width:min(58vw,760px);border-color:rgba(239,207,130,.2);transform:translateY(-50%)}
.intro__back{z-index:3;color:rgba(255,249,231,.72);text-shadow:0 2px 9px rgba(0,0,0,.3)}
.intro__back:hover{color:#f4ce76}
.intro__content{
  z-index:2;
  width:min(590px,44vw);
  min-height:100dvh;
  margin-left:clamp(54px,7vw,112px);
  padding:clamp(86px,12vh,132px) 0 92px;
  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:flex-start;
  text-align:left;
}
.intro__content::before,.intro__content::after{display:none}
.intro__chapter{padding:7px 11px;border:1px solid rgba(242,207,126,.42);background:rgba(20,55,53,.38);backdrop-filter:blur(8px);color:#f1cd78}
.intro h1{margin-top:22px;font-size:clamp(58px,6.9vw,104px);color:#fff9e8;text-shadow:0 4px 30px rgba(0,0,0,.42)}
.intro__keyword{color:rgba(255,246,219,.66);text-shadow:0 2px 10px rgba(0,0,0,.3)}
.intro blockquote{margin:28px 0 0;max-width:500px;padding-left:18px;border-left:2px solid #e3b959;color:rgba(255,249,232,.9);text-shadow:0 2px 14px rgba(0,0,0,.38)}
.intro__role{width:min(470px,100%);margin:25px 0 0;padding:14px 18px 15px;border:1px solid rgba(244,221,164,.28);background:rgba(22,58,55,.48);backdrop-filter:blur(10px);align-items:flex-start}
.intro__role::before,.intro__role::after{display:none}
.intro__role span{color:rgba(255,246,222,.62)}
.intro__role strong{color:#f3d382}
.intro__role small{color:rgba(255,249,232,.68)}
.intro__actions{margin-top:22px;justify-content:flex-start}
.intro__actions button{border-color:rgba(255,239,197,.32);background:rgba(19,53,51,.46);color:rgba(255,249,232,.76);backdrop-filter:blur(8px)}
.intro__actions button:first-child{background:linear-gradient(90deg,rgba(238,206,128,.92),rgba(218,175,79,.88));border-color:#f0cf80;color:#214f4d;box-shadow:0 14px 36px rgba(7,34,33,.24)}
.intro__actions button:first-child i{color:#984b3b}
.intro__actions button:hover{border-color:#f3cf78;color:#fff9e8}
.intro__actions button:first-child:hover{color:#173f3d}
.intro__foot{z-index:2;left:clamp(54px,7vw,112px);bottom:27px;color:rgba(255,247,226,.58);text-shadow:0 2px 10px rgba(0,0,0,.35)}
@media(max-width:760px){
  .intro{min-height:100dvh}
  .intro__art{inset:0;opacity:1;mask-image:none}
  .intro__art::after{background:linear-gradient(0deg,rgba(14,44,42,.94) 0,rgba(16,48,46,.68) 58%,rgba(15,45,43,.22) 100%)}
  .intro__art figcaption{display:block;right:16px;bottom:14px;max-width:70%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .intro__rings{left:50%;top:48%;width:88vw;transform:translate(-50%,-50%)}
  .intro__content{width:auto;min-height:100dvh;margin:0;padding:94px 24px 72px;justify-content:flex-end;align-items:flex-start;text-align:left}
  .intro h1{font-size:clamp(50px,17vw,76px)}
  .intro blockquote{margin-top:20px}
  .intro__role{width:100%;margin-top:18px}
  .intro__actions{width:100%;flex-direction:column}
  .intro__actions button{width:100%}
}
@media(prefers-reduced-motion:reduce){.intro__art img{animation:none}}

/* V7 开幕信息卡：把主证物与玩家身份一起交代。 */
.intro__role{margin-bottom:0;border-bottom-color:rgba(244,221,164,.14)}
.intro__anchor{width:min(470px,100%);display:grid;grid-template-columns:58px minmax(0,1fr) auto;align-items:center;gap:10px;margin-top:7px;padding:10px 14px;border:1px solid rgba(244,221,164,.24);background:rgba(15,47,45,.58);backdrop-filter:blur(10px);animation:rise .8s .46s both}
.intro__anchor span{font-size:9px;letter-spacing:.18em;color:rgba(255,246,222,.54)}.intro__anchor strong{overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-family:var(--font-display);font-size:13px;font-weight:500;color:#fff5da}.intro__anchor em{padding:3px 6px;border:1px solid rgba(240,205,121,.36);font-size:8px;font-style:normal;letter-spacing:.08em;color:#f1cf7f}
.intro__actions{margin-top:17px}.intro__actions button:first-child{min-width:245px}
@media(max-width:760px){.intro__anchor{width:100%}.intro__anchor strong{font-size:12px}}
</style>
