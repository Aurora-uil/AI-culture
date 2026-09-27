<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

type Burst = {
  id: number
  x: number
  y: number
  color: string
}

const bursts = ref<Burst[]>([])
let nextId = 0
const timers = new Set<number>()

function isInteractive(target: EventTarget | null): HTMLElement | null {
  if (!(target instanceof Element)) return null
  const element = target.closest<HTMLElement>('button, a, [role="button"], [data-game-interactive]')
  if (!element || element.matches(':disabled, [aria-disabled="true"]')) return null
  return element
}

function onActivate(event: MouseEvent) {
  const element = isInteractive(event.target)
  if (!element) return

  const rect = element.getBoundingClientRect()
  const keyboardClick = event.detail === 0 || (event.clientX === 0 && event.clientY === 0)
  const x = keyboardClick ? rect.left + rect.width / 2 : event.clientX
  const y = keyboardClick ? rect.top + rect.height / 2 : event.clientY
  const color = getComputedStyle(element).getPropertyValue('--chapter-accent').trim() || '#b28a45'
  const id = ++nextId

  bursts.value = [...bursts.value.slice(-4), { id, x, y, color }]
  const timer = window.setTimeout(() => {
    bursts.value = bursts.value.filter((burst) => burst.id !== id)
    timers.delete(timer)
  }, 820)
  timers.add(timer)
}

onMounted(() => window.addEventListener('click', onActivate, { capture: true }))
onBeforeUnmount(() => {
  window.removeEventListener('click', onActivate, { capture: true })
  timers.forEach((timer) => window.clearTimeout(timer))
})
</script>

<template>
  <div class="interaction-fx" aria-hidden="true">
    <span
      v-for="burst in bursts"
      :key="burst.id"
      class="interaction-fx__burst"
      :style="{ left: `${burst.x}px`, top: `${burst.y}px`, '--burst-color': burst.color }"
    >
      <i class="interaction-fx__ring" />
      <i class="interaction-fx__thread" />
      <i v-for="index in 6" :key="index" class="interaction-fx__spark" :style="{ '--spark-index': index }" />
    </span>
  </div>
</template>

<style scoped>
.interaction-fx {
  position: fixed;
  inset: 0;
  z-index: 9999;
  overflow: hidden;
  pointer-events: none;
}
.interaction-fx__burst {
  position: absolute;
  width: 1px;
  height: 1px;
}
.interaction-fx__ring {
  position: absolute;
  left: -10px;
  top: -10px;
  width: 20px;
  height: 20px;
  border: 1px solid color-mix(in srgb, var(--burst-color) 70%, #d7b873);
  border-radius: 50%;
  box-shadow: 0 0 18px color-mix(in srgb, var(--burst-color) 36%, transparent);
  animation: interaction-ring 760ms cubic-bezier(.16,.72,.2,1) both;
}
.interaction-fx__thread {
  position: absolute;
  left: -58px;
  top: -1px;
  width: 116px;
  height: 2px;
  border-radius: 50%;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--burst-color) 45%, #f0d38d), transparent);
  box-shadow: 0 0 13px color-mix(in srgb, var(--burst-color) 32%, transparent);
  animation: interaction-thread 720ms var(--ease-standard) both;
}
.interaction-fx__spark {
  --angle: calc(var(--spark-index) * 60deg);
  position: absolute;
  left: -2px;
  top: -2px;
  width: 4px;
  height: 4px;
  border-radius: 50% 0 50% 50%;
  background: color-mix(in srgb, var(--burst-color) 55%, #d9b77d);
  box-shadow: 0 0 8px color-mix(in srgb, var(--burst-color) 44%, transparent);
  transform: rotate(var(--angle)) translateX(9px) rotate(45deg);
  animation: interaction-spark 680ms cubic-bezier(.12,.72,.22,1) both;
}
@keyframes interaction-ring {
  0% { opacity: .85; transform: scale(.35); }
  72% { opacity: .38; }
  100% { opacity: 0; transform: scale(4.7); }
}
@keyframes interaction-spark {
  0% { opacity: 0; transform: rotate(var(--angle)) translateX(5px) rotate(45deg) scale(.4); }
  20% { opacity: .95; }
  100% { opacity: 0; transform: rotate(var(--angle)) translateX(36px) rotate(135deg) scale(.15); }
}
@keyframes interaction-thread {
  0% { opacity: 0; transform: scaleX(.06) rotate(-7deg); }
  24% { opacity: .9; }
  100% { opacity: 0; transform: scaleX(1.35) rotate(5deg); }
}
@media (prefers-reduced-motion: reduce) {
  .interaction-fx { display: none; }
}
</style>
