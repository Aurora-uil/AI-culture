<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

defineProps<{
  chapter: number
  era: string
  title: string
  role: string
}>()

const visible = ref(true)
let timer: number | undefined

onMounted(() => {
  timer = window.setTimeout(() => (visible.value = false), 1850)
})

onBeforeUnmount(() => {
  if (timer) window.clearTimeout(timer)
})
</script>

<template>
  <Transition name="scene-reveal">
    <div v-if="visible" class="scene-reveal" aria-hidden="true">
      <div class="scene-reveal__veil" />
      <div class="scene-reveal__rings"><i /><i /><i /></div>
      <div class="scene-reveal__copy">
        <span>第 {{ String(chapter).padStart(2, '0') }} 章 · {{ era }}</span>
        <strong>{{ title }}</strong>
        <small>此刻，你是{{ role }}</small>
      </div>
      <div class="scene-reveal__thread" />
    </div>
  </Transition>
</template>

<style scoped>
.scene-reveal {
  position: absolute;
  z-index: calc(var(--z-hud) + 6);
  inset: 0;
  overflow: hidden;
  display: grid;
  place-items: center;
  pointer-events: none;
  color: #fff9e9;
}
.scene-reveal__veil {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 52% 48%, color-mix(in srgb, var(--chapter-accent) 42%, transparent), transparent 34%),
    linear-gradient(105deg, rgba(20, 48, 48, .92), rgba(28, 63, 58, .79) 48%, rgba(52, 71, 60, .88));
  backdrop-filter: blur(13px) saturate(.72);
}
.scene-reveal__veil::after {
  content: '';
  position: absolute;
  inset: 0;
  opacity: .14;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 120 120' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.72' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.26'/%3E%3C/svg%3E");
  mix-blend-mode: soft-light;
}
.scene-reveal__rings {
  position: absolute;
  width: min(47vw, 530px);
  aspect-ratio: 1;
  border: 1px solid rgba(229, 197, 123, .42);
  border-radius: 50%;
  animation: reveal-ring 1.8s var(--ease-standard) both;
}
.scene-reveal__rings i { position: absolute; border: 1px solid rgba(229, 197, 123, .2); border-radius: 50%; }
.scene-reveal__rings i:nth-child(1) { inset: 12%; }
.scene-reveal__rings i:nth-child(2) { inset: 27%; }
.scene-reveal__rings i:nth-child(3) { inset: 43%; background: rgba(229, 197, 123, .08); }
.scene-reveal__copy {
  position: relative;
  z-index: 1;
  display: grid;
  justify-items: center;
  text-align: center;
  text-shadow: 0 3px 26px rgba(10, 28, 26, .6);
  animation: reveal-copy 1.35s .08s var(--ease-standard) both;
}
.scene-reveal__copy span { font-size: 10px; letter-spacing: .3em; color: rgba(255, 244, 215, .72); }
.scene-reveal__copy strong { margin-top: 12px; font-family: var(--font-display); font-size: clamp(31px, 4.5vw, 62px); font-weight: 500; letter-spacing: .15em; }
.scene-reveal__copy small { margin-top: 15px; font-family: var(--font-display); font-size: 13px; letter-spacing: .12em; color: rgba(255, 248, 226, .72); }
.scene-reveal__thread {
  position: absolute;
  z-index: 1;
  top: 50%;
  left: 50%;
  width: min(72vw, 920px);
  height: 1px;
  transform: translate(-50%, 72px) scaleX(0);
  background: linear-gradient(90deg, transparent, rgba(229, 197, 123, .9), transparent);
  animation: reveal-thread 1.55s .18s var(--ease-standard) both;
}
.scene-reveal-enter-active { transition: opacity 260ms ease; }
.scene-reveal-leave-active { transition: opacity 520ms ease, filter 520ms ease; }
.scene-reveal-enter-from, .scene-reveal-leave-to { opacity: 0; filter: blur(7px); }
@keyframes reveal-copy { from { opacity: 0; transform: translateY(18px) scale(.96); } to { opacity: 1; transform: none; } }
@keyframes reveal-ring { from { opacity: 0; transform: scale(.6) rotate(-8deg); } 48% { opacity: 1; } to { opacity: .62; transform: scale(1.08) rotate(2deg); } }
@keyframes reveal-thread { 45% { transform: translate(-50%, 72px) scaleX(1); } 100% { transform: translate(-50%, 72px) scaleX(.78); opacity: .45; } }
@media (prefers-reduced-motion: reduce) { .scene-reveal__copy,.scene-reveal__rings,.scene-reveal__thread { animation: none; } }
</style>
