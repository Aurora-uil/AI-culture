<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { GAME_CATALOG } from '@/game/catalog'
import { useGameStore } from '@/stores/game'
import type { ChapterSlug } from '@/types'

const props = defineProps<{
  slug: ChapterSlug
}>()

const game = useGameStore()
const router = useRouter()
const open = ref(true)
const decisionOpen = ref(false)
const resultChoiceId = ref('')
const resultOpen = ref(false)
let resultTimer: number | undefined

const meta = computed(() => GAME_CATALOG[props.slug])
const state = computed(() => game.stateFor(props.slug))
const progress = computed(() => game.progressFor(props.slug))
const canDecide = computed(
  () => state.value.evidenceIds.length >= 3 && !!state.value.actions.LENS,
)
const chosen = computed(() =>
  meta.value.decision.choices.find((choice) => choice.id === state.value.decisionId),
)
const resultChoice = computed(() =>
  meta.value.decision.choices.find((choice) => choice.id === resultChoiceId.value),
)

const DECISION_ART: Record<ChapterSlug, string> = {
  han: '/assets/han/han-route-scene-v2.png',
  'northern-wei': '/assets/wei/yungang-cave20-original.jpg',
  tang: '/assets/tang/bunian-original.jpg',
  yuan: '/assets/yuan/yuntai-east-wall-original.jpg',
  qing: '/assets/qing/qing-migration-v1.png',
  contemporary: '/assets/contemporary/qiang-workshop-v1.png',
}
const decisionStyle = computed(() => ({
  '--decision-art': `url("${DECISION_ART[props.slug]}")`,
}))

function choose(id: string) {
  game.choose(props.slug, id)
  decisionOpen.value = false
  resultChoiceId.value = id
  resultOpen.value = true
  if (resultTimer) window.clearTimeout(resultTimer)
  resultTimer = window.setTimeout(() => (resultOpen.value = false), 2300)
}

function openSummary() {
  router.push(`/chapter/${props.slug}/summary`)
}

onBeforeUnmount(() => {
  if (resultTimer) window.clearTimeout(resultTimer)
})
</script>

<template>
  <aside class="quest" :class="{ 'is-open': open }" aria-label="本章任务">
    <button class="quest__handle" type="button" :aria-expanded="open" @click="open = !open">
      <span class="quest__seal" aria-hidden="true">任</span>
      <span class="quest__handle-copy">
        <span>当前任务</span>
        <strong>{{ progress }}%</strong>
      </span>
      <span class="quest__chevron" aria-hidden="true">{{ open ? '‹' : '›' }}</span>
    </button>

    <Transition name="quest-slide">
      <div v-if="open" class="quest__body">
        <div class="quest__role">
          <span>你的身份</span>
          <strong>{{ meta.role }}</strong>
        </div>
        <div class="quest__anchor" :class="`is-${meta.storyAnchor.status}`">
          <span>剧情锚点</span>
          <strong>{{ meta.storyAnchor.name }}</strong>
          <small>{{ meta.storyAnchor.statusLabel }}</small>
        </div>
        <p class="quest__mission">{{ meta.mission }}</p>

        <ol class="quest__steps">
          <li
            v-for="(objective, index) in meta.objectives"
            :key="objective.action"
            :class="{
              done: game.objectiveDone(slug, objective.action, objective.target),
              current:
                !game.objectiveDone(slug, objective.action, objective.target) &&
                meta.objectives
                  .slice(0, index)
                  .every((item) => game.objectiveDone(slug, item.action, item.target)),
            }"
          >
            <span class="quest__step-mark" aria-hidden="true">
              {{ game.objectiveDone(slug, objective.action, objective.target) ? '✓' : index + 1 }}
            </span>
            <span>{{ objective.label }}</span>
            <small v-if="objective.action === 'INSPECT'">
              {{ Math.min(state.evidenceIds.length, objective.target ?? 1) }}/{{ objective.target }}
            </small>
          </li>
        </ol>

        <button
          v-if="!state.decisionId"
          class="quest__decision"
          type="button"
          :disabled="!canDecide"
          @click="decisionOpen = true"
        >
          <span>{{ canDecide ? meta.decision.eyebrow : '抉择尚未解锁' }}</span>
          <strong>{{ canDecide ? '进入本章抉择' : '先查验 3 处证据并开启透镜' }}</strong>
        </button>
        <div v-else class="quest__result">
          <span>你留下的选择</span>
          <strong>{{ chosen?.label }}</strong>
          <button type="button" @click="openSummary">整理本章记录 <span aria-hidden="true">→</span></button>
        </div>
      </div>
    </Transition>
  </aside>

  <Teleport to="body">
    <Transition name="decision-fade">
      <div
        v-if="decisionOpen"
        class="decision"
        :style="decisionStyle"
        role="dialog"
        aria-modal="true"
        :aria-label="meta.decision.title"
      >
        <button class="decision__backdrop" type="button" aria-label="关闭抉择" @click="decisionOpen = false" />
        <section class="decision__sheet">
          <header class="decision__head">
            <div>
              <p>{{ meta.decision.eyebrow }}</p>
              <h2>{{ meta.decision.title }}</h2>
            </div>
            <button type="button" @click="decisionOpen = false">暂不决定</button>
          </header>
          <p class="decision__context">{{ meta.decision.context }}</p>
          <div class="decision__choices">
            <button
              v-for="(choice, index) in meta.decision.choices"
              :key="choice.id"
              type="button"
              @click="choose(choice.id)"
            >
              <span class="decision__index">{{ ['甲', '乙', '丙'][index] }}</span>
              <span class="decision__copy">
                <strong>{{ choice.label }}</strong>
                <small>{{ choice.description }}</small>
              </span>
              <span class="decision__arrow" aria-hidden="true">→</span>
            </button>
          </div>
          <p class="decision__note">历史结果不会因这次选择改变；它会改变你留下的记录与本章结语。</p>
        </section>
      </div>
    </Transition>
    <Transition name="result-reveal">
      <div v-if="resultOpen && resultChoice" class="choice-result" role="status" aria-live="polite">
        <div class="choice-result__halo" aria-hidden="true" />
        <div class="choice-result__scroll">
          <span>本章记录已写入</span>
          <strong>{{ resultChoice.label }}</strong>
          <p>{{ resultChoice.response }}</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.quest {
  position: absolute;
  z-index: var(--z-hud);
  top: 18px;
  left: 18px;
  display: flex;
  align-items: flex-start;
  filter: drop-shadow(0 18px 36px rgba(2, 10, 10, 0.28));
}

.quest__handle {
  width: 78px;
  min-height: 94px;
  border: 1px solid rgba(222, 202, 161, 0.34);
  border-radius: 4px 0 0 4px;
  background: rgba(12, 20, 19, 0.94);
  color: #eee5d2;
  padding: 10px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  backdrop-filter: blur(16px);
}
.quest:not(.is-open) .quest__handle { border-radius: 4px; }
.quest__seal {
  width: 29px;
  height: 29px;
  display: grid;
  place-items: center;
  border: 1px solid #ba5a43;
  color: #d36a4e;
  font-family: var(--font-display);
  font-size: 15px;
}
.quest__handle-copy { display: flex; flex-direction: column; font-size: 10px; letter-spacing: .08em; }
.quest__handle-copy strong { font-family: var(--font-display); font-size: 16px; color: #d8bb7c; }
.quest__chevron { color: rgba(238, 229, 210, .52); }

.quest__body {
  width: min(330px, calc(100vw - 116px));
  max-height: min(610px, calc(100vh - 190px));
  overflow: auto;
  border: 1px solid rgba(222, 202, 161, 0.34);
  border-left: 0;
  border-radius: 0 4px 4px 0;
  background:
    linear-gradient(rgba(16, 25, 24, .95), rgba(16, 25, 24, .98)),
    repeating-linear-gradient(0deg, transparent 0 25px, rgba(216, 187, 124, .04) 26px);
  color: #eee5d2;
  padding: 18px;
  backdrop-filter: blur(18px);
}
.quest__role { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
.quest__role span { font-size: 10px; color: rgba(238, 229, 210, .5); letter-spacing: .16em; }
.quest__role strong { font-family: var(--font-display); font-size: 16px; font-weight: 500; color: #d8bb7c; }
.quest__anchor{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:7px;margin-top:11px;padding:8px 9px;border:1px solid rgba(216,187,124,.15);border-left:2px solid #d8bb7c;background:rgba(216,187,124,.045)}
.quest__anchor span{font-size:8px;letter-spacing:.12em;color:rgba(238,229,210,.42)}
.quest__anchor strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:var(--font-display);font-size:12px;font-weight:500;color:#eee5d2}
.quest__anchor small{font-size:8px;color:#9bbba4}
.quest__anchor.is-rights{border-left-color:#c85b43}
.quest__anchor.is-rights small{color:#d37460}
.quest__mission { margin-top: 10px; font-size: 13px; line-height: 1.72; color: rgba(238, 229, 210, .76); }
.quest__steps { list-style: none; padding: 14px 0 0; margin: 14px 0 0; border-top: 1px solid rgba(222, 202, 161, .16); display: grid; gap: 4px; }
.quest__steps li { min-height: 34px; display: grid; grid-template-columns: 24px 1fr auto; align-items: center; gap: 8px; padding: 4px 6px; color: rgba(238, 229, 210, .42); font-size: 12px; border-left: 1px solid transparent; }
.quest__steps li.current { color: #f2ead9; border-left-color: #d8bb7c; background: rgba(216, 187, 124, .07); }
.quest__steps li.done { color: rgba(238, 229, 210, .66); }
.quest__step-mark { width: 20px; height: 20px; display: grid; place-items: center; border: 1px solid rgba(222, 202, 161, .22); border-radius: 50%; font-size: 10px; }
.done .quest__step-mark { color: #9bbba4; border-color: rgba(117, 166, 135, .5); }
.quest__steps small { color: #d8bb7c; }
.quest__decision, .quest__result { width: 100%; margin-top: 14px; padding: 12px; border: 1px solid rgba(216, 187, 124, .25); border-radius: 3px; background: rgba(216, 187, 124, .08); text-align: left; color: #eee5d2; display: flex; flex-direction: column; gap: 2px; }
.quest__decision:not(:disabled):hover { border-color: #d8bb7c; background: rgba(216, 187, 124, .13); }
.quest__decision:disabled { cursor: not-allowed; opacity: .48; }
.quest__decision span, .quest__result span { font-size: 10px; letter-spacing: .12em; color: rgba(238, 229, 210, .48); }
.quest__decision strong, .quest__result strong { font-family: var(--font-display); font-weight: 500; color: #d8bb7c; }
.quest__result { border-color: rgba(117, 166, 135, .35); }
.quest__result button { margin-top: 9px; padding: 9px 0 0; border: 0; border-top: 1px solid rgba(117, 166, 135, .22); background: transparent; color: #a8cbb1; text-align: left; font-size: 12px; letter-spacing: .06em; }
.quest__result button span { float: right; color: #a8cbb1; font-size: 14px; }
.quest__result button:hover { color: #d8eadc; }

.quest-slide-enter-active, .quest-slide-leave-active { transition: opacity 180ms ease, transform 180ms ease; }
.quest-slide-enter-from, .quest-slide-leave-to { opacity: 0; transform: translateX(-10px); }

.decision { position: fixed; inset: 0; z-index: var(--z-dialog); display: grid; place-items: center; padding: 24px; }
.decision__backdrop { position: absolute; inset: 0; border: 0; background: rgba(2, 8, 8, .72); backdrop-filter: blur(8px); }
.decision__sheet { position: relative; width: min(840px, 100%); color: #ece4d3; border: 1px solid rgba(216, 187, 124, .36); background: #121c1a; box-shadow: 0 32px 100px rgba(0,0,0,.5); padding: 30px; }
.decision__sheet::before { content: ''; position: absolute; inset: 8px; pointer-events: none; border: 1px solid rgba(216, 187, 124, .09); }
.decision__head { position: relative; display: flex; justify-content: space-between; gap: 24px; }
.decision__head p { font-size: 11px; color: #c85b43; letter-spacing: .2em; }
.decision__head h2 { margin-top: 6px; font-family: var(--font-display); font-size: clamp(25px, 3vw, 38px); font-weight: 500; color: #f0e6d1; }
.decision__head button { align-self: flex-start; border: 0; background: transparent; color: rgba(236, 228, 211, .55); font-size: 12px; }
.decision__context { position: relative; max-width: 680px; margin-top: 20px; line-height: 1.8; color: rgba(236, 228, 211, .72); }
.decision__choices { position: relative; display: grid; gap: 9px; margin-top: 26px; }
.decision__choices button { display: grid; grid-template-columns: 38px 1fr auto; align-items: center; gap: 14px; padding: 16px; border: 1px solid rgba(216, 187, 124, .18); background: rgba(255,255,255,.025); color: inherit; text-align: left; transition: border-color 160ms ease, background 160ms ease, transform 160ms ease; }
.decision__choices button:hover { transform: translateX(4px); border-color: rgba(216, 187, 124, .72); background: rgba(216, 187, 124, .07); }
.decision__index { width: 31px; height: 31px; display: grid; place-items: center; border: 1px solid rgba(216, 187, 124, .3); color: #d8bb7c; font-family: var(--font-display); }
.decision__copy { display: flex; flex-direction: column; gap: 4px; }
.decision__copy strong { font-family: var(--font-display); font-size: 17px; font-weight: 500; }
.decision__copy small { color: rgba(236, 228, 211, .55); }
.decision__arrow { color: #d8bb7c; }
.decision__note { position: relative; margin-top: 18px; font-size: 11px; color: rgba(236, 228, 211, .42); }
.decision-fade-enter-active, .decision-fade-leave-active { transition: opacity 200ms ease; }
.decision-fade-enter-from, .decision-fade-leave-to { opacity: 0; }

@media (max-width: 760px) {
  .quest { left: 8px; top: 8px; }
  .quest__handle { width: 58px; }
  .decision { padding: 10px; align-items: end; }
  .decision__sheet { padding: 22px 18px; max-height: 88vh; overflow: auto; }
}

/* V3 卷册任务条 */
.quest{filter:drop-shadow(0 16px 34px rgba(50,92,82,.18))}
.quest__handle{border-color:rgba(40,95,97,.28);background:rgba(237,244,237,.94);color:var(--color-mineral-800)}
.quest__handle-copy strong{color:#8d6c31}
.quest__chevron{color:rgba(41,69,74,.5)}
.quest__body{border-color:rgba(40,95,97,.28);background:linear-gradient(rgba(246,248,241,.97),rgba(235,243,236,.98)),repeating-linear-gradient(0deg,transparent 0 25px,rgba(40,95,97,.04) 26px);color:var(--color-slate-text)}
.quest__role span{color:rgba(41,69,74,.48)}
.quest__role strong{color:var(--color-mineral-700)}
.quest__anchor{border-color:rgba(40,95,97,.14);border-left-color:var(--color-scroll-gold);background:rgba(255,255,255,.3)}
.quest__anchor span{color:rgba(41,69,74,.45)}
.quest__anchor strong{color:var(--color-mineral-800)}
.quest__anchor small{color:#50765b}
.quest__anchor.is-rights{border-left-color:var(--color-scroll-red)}
.quest__anchor.is-rights small{color:var(--color-scroll-red)}
.quest__mission{color:rgba(41,69,74,.72)}
.quest__steps{border-top-color:rgba(40,95,97,.15)}
.quest__steps li{color:rgba(41,69,74,.43)}
.quest__steps li.current{color:var(--color-mineral-800);border-left-color:var(--color-scroll-gold);background:rgba(178,138,69,.08)}
.quest__steps li.done{color:rgba(41,69,74,.65)}
.quest__step-mark{border-color:rgba(40,95,97,.2)}
.quest__decision,.quest__result{border-color:rgba(40,95,97,.2);background:rgba(40,95,97,.055);color:var(--color-slate-text)}
.quest__decision:not(:disabled):hover{border-color:var(--color-scroll-red);background:rgba(178,81,61,.06)}
.quest__decision span,.quest__result span{color:rgba(41,69,74,.5)}
.quest__decision strong,.quest__result strong{color:var(--color-mineral-700)}
.quest__result button,.quest__result button span{color:var(--color-mineral-700)}
.decision__backdrop{background:rgba(43,72,70,.35)}
.decision__sheet{color:var(--color-slate-text);border-color:rgba(40,95,97,.32);background:#edf3ea;box-shadow:0 32px 100px rgba(50,92,82,.28);overscroll-behavior:contain}
.decision__sheet::before{border-color:rgba(40,95,97,.1)}
.decision__head h2{color:var(--color-mineral-800)}
.decision__head button{color:rgba(41,69,74,.55)}
.decision__context{color:rgba(41,69,74,.7)}
.decision__choices button{border-color:rgba(40,95,97,.17);background:rgba(255,255,255,.35)}
.decision__choices button:hover{border-color:var(--color-scroll-red);background:rgba(178,81,61,.055)}
.decision__index,.decision__arrow{color:var(--color-scroll-red);border-color:rgba(178,81,61,.34)}
.decision__copy small{color:rgba(41,69,74,.56)}
.decision__note{color:rgba(41,69,74,.45)}

/* V4 电影式抉择与结果卷轴 */
.decision__sheet{
  overflow:hidden;
  background:
    radial-gradient(circle at 92% 6%,color-mix(in srgb,var(--chapter-accent) 15%,transparent),transparent 32%),
    linear-gradient(145deg,#f4f6ee,#e4eee6);
  box-shadow:0 34px 110px rgba(35,75,71,.34),0 0 0 1px rgba(255,255,255,.72) inset;
}
.decision__sheet::after{
  content:'';
  position:absolute;
  inset:0;
  pointer-events:none;
  background:
    linear-gradient(135deg,var(--color-luminous-gold),transparent 17%) top left/68px 68px no-repeat,
    linear-gradient(315deg,var(--color-luminous-gold),transparent 17%) bottom right/68px 68px no-repeat;
  opacity:.22;
}
.decision__choices button{position:relative;overflow:hidden;box-shadow:0 8px 22px rgba(42,77,73,.04)}
.decision__choices button::after{content:'';position:absolute;inset:-80% -30%;background:linear-gradient(100deg,transparent 38%,rgba(255,255,255,.72) 50%,transparent 62%);transform:translateX(-65%) rotate(8deg);transition:transform 520ms var(--ease-standard)}
.decision__choices button:hover{transform:translateX(8px);box-shadow:0 14px 30px rgba(42,77,73,.11)}
.decision__choices button:hover::after{transform:translateX(65%) rotate(8deg)}
.decision__copy,.decision__index,.decision__arrow{position:relative;z-index:1}

.choice-result{position:fixed;inset:0;z-index:calc(var(--z-dialog) + 4);display:grid;place-items:center;pointer-events:none;background:rgba(46,76,72,.16);backdrop-filter:blur(5px)}
.choice-result__halo{position:absolute;width:min(720px,80vw);aspect-ratio:1;border-radius:50%;background:radial-gradient(circle,rgba(217,187,115,.24),rgba(115,169,155,.09) 38%,transparent 68%);animation:result-halo 2.2s ease-out both}
.choice-result__scroll{position:relative;width:min(760px,calc(100% - 38px));padding:32px 68px 30px;text-align:center;color:var(--color-mineral-800);background:linear-gradient(90deg,rgba(224,235,224,.82),#fff8df 13%,#fbf7e8 50%,#fff8df 87%,rgba(224,235,224,.82));border-block:1px solid rgba(178,138,69,.55);box-shadow:0 24px 70px rgba(43,76,69,.26),0 0 35px rgba(217,187,115,.18) inset;clip-path:polygon(4% 0,96% 0,100% 50%,96% 100%,4% 100%,0 50%)}
.choice-result__scroll::before,.choice-result__scroll::after{content:'◇';position:absolute;top:50%;transform:translateY(-50%);color:var(--color-scroll-gold);font-size:22px}.choice-result__scroll::before{left:25px}.choice-result__scroll::after{right:25px}
.choice-result__scroll>span{font-size:10px;letter-spacing:.28em;color:var(--color-scroll-red)}
.choice-result__scroll>strong{display:block;margin-top:6px;font-family:var(--font-display);font-size:clamp(24px,3.2vw,38px);font-weight:500;letter-spacing:.08em}
.choice-result__scroll>p{max-width:620px;margin:10px auto 0;font-family:var(--font-display);font-size:14px;line-height:1.75;color:rgba(41,69,74,.68)}
.result-reveal-enter-active,.result-reveal-leave-active{transition:opacity 300ms ease}.result-reveal-enter-active .choice-result__scroll{animation:result-scroll 620ms cubic-bezier(.16,.78,.18,1) both}.result-reveal-enter-from,.result-reveal-leave-to{opacity:0}
@keyframes result-scroll{0%{opacity:0;transform:scaleX(.08) scaleY(.72)}55%{opacity:1}100%{transform:scale(1)}}
@keyframes result-halo{0%{opacity:0;transform:scale(.55)}32%{opacity:1}100%{opacity:0;transform:scale(1.15)}}
@media(max-width:620px){.choice-result__scroll{padding:26px 38px}.choice-result__scroll::before{left:14px}.choice-result__scroll::after{right:14px}}
@media(prefers-reduced-motion:reduce){.decision__choices button::after{display:none}.choice-result__halo{display:none}.result-reveal-enter-active .choice-result__scroll{animation:none}}

/* V5 电影化抉择：历史场景留在背后，选项像游戏对白浮于下三分之一。 */
.decision{
  align-items:end;
  padding:clamp(24px,5vh,54px) clamp(18px,5vw,72px);
  isolation:isolate;
  overflow:hidden;
}
.decision::before{
  content:'';
  position:absolute;
  z-index:-2;
  inset:-3%;
  background-image:var(--decision-art);
  background-size:cover;
  background-position:center;
  filter:saturate(.76) contrast(1.04) brightness(.68) blur(2px);
  transform:scale(1.035);
  animation:decision-camera 9s ease-out both;
}
.decision::after{
  content:'';
  position:absolute;
  z-index:-1;
  inset:0;
  background:
    linear-gradient(180deg,rgba(23,47,45,.2),rgba(22,49,47,.28) 38%,rgba(28,53,48,.56)),
    radial-gradient(circle at 50% 76%,rgba(217,187,115,.13),transparent 42%);
  pointer-events:none;
}
.decision__backdrop{z-index:-1;background:rgba(26,54,51,.18);backdrop-filter:none}
.decision__sheet{
  width:min(1080px,100%);
  padding:22px 26px 20px;
  border-color:rgba(226,198,132,.55);
  border-radius:5px;
  background:
    linear-gradient(90deg,rgba(222,231,215,.9),rgba(255,248,221,.97) 10%,rgba(249,244,221,.97) 90%,rgba(222,231,215,.9)),
    #f5efd9;
  box-shadow:0 28px 80px rgba(16,38,36,.44),0 0 0 1px rgba(255,255,255,.56) inset,0 0 42px rgba(217,187,115,.14) inset;
  clip-path:polygon(1.2% 0,98.8% 0,100% 8%,100% 92%,98.8% 100%,1.2% 100%,0 92%,0 8%);
  animation:decision-sheet-in 560ms cubic-bezier(.16,.78,.18,1) both;
}
.decision__sheet::before{inset:7px;border-color:rgba(157,115,51,.2)}
.decision__head h2{font-size:clamp(23px,2.5vw,34px);letter-spacing:.04em}
.decision__context{margin-top:12px;max-width:860px;line-height:1.65}
.decision__choices{grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:17px}
.decision__choices button{
  min-height:92px;
  grid-template-columns:34px 1fr auto;
  padding:13px;
  border-color:rgba(146,107,51,.25);
  background:linear-gradient(145deg,rgba(255,255,255,.52),rgba(226,238,224,.45));
  box-shadow:0 8px 24px rgba(42,77,73,.07);
}
.decision__choices button:hover{transform:translateY(-5px);border-color:var(--color-scroll-red);box-shadow:0 17px 34px rgba(42,77,73,.18)}
.decision__copy strong{font-size:16px}.decision__copy small{line-height:1.55}
.decision__note{margin-top:12px;text-align:center}
@keyframes decision-sheet-in{from{opacity:0;transform:translateY(36px) scale(.98)}to{opacity:1;transform:none}}
@keyframes decision-camera{from{transform:scale(1.08)}to{transform:scale(1.035)}}
@media(max-width:820px){
  .decision{padding:10px;align-items:end}
  .decision__sheet{max-height:88dvh;overflow:auto;padding:20px 16px}
  .decision__choices{grid-template-columns:1fr}
  .decision__choices button{min-height:unset}
}
@media(prefers-reduced-motion:reduce){.decision::before,.decision__sheet{animation:none}}
</style>
