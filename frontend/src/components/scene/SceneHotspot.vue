<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Hotspot } from '@/types'

/**
 * 场景热点（设计系统 §24 / §25）
 *
 * idle:    直径 18px / 30% accent / 微弱环形呼吸
 * hover:   直径 22px / tooltip
 * visited: 实心小点 + ✓
 * selected:外圈 32px
 *
 * 动效：2.4 秒呼吸周期，opacity .55 → .9，scale 1 → 1.12 → 1
 * 禁止：疯狂闪烁 / 大范围粒子爆炸 / 持续旋转
 */
const props = withDefaults(
  defineProps<{
    hotspot: Hotspot
    status?: 'UNSEEN' | 'SEEN' | 'SELECTED'
    /** 影像场景用绝对百分比定位；地图场景由父级决定 */
    positioned?: boolean
  }>(),
  { status: 'UNSEEN', positioned: true },
)

const emit = defineEmits<{ (e: 'select', hotspot: Hotspot): void }>()

const hovering = ref(false)

/** 多边形的质心即热点圆心 */
const center = computed<{ x: number; y: number }>(() => {
  const pts = props.hotspot.normalized_points
  if (!pts || !Array.isArray(pts) || pts.length === 0) return { x: 0.5, y: 0.5 }
  // point 形态：[[x, y]] 或 [x, y]
  if (typeof pts[0] === 'number') {
    const [x, y] = pts as unknown as number[]
    return { x, y }
  }
  const arr = pts as number[][]
  const sx = arr.reduce((s, p) => s + p[0], 0) / arr.length
  const sy = arr.reduce((s, p) => s + p[1], 0) / arr.length
  return { x: sx, y: sy }
})

/** 地图像素尺寸下，热点按视觉大小做半径补偿 */
const styleVars = computed(() => ({
  left: `${center.value.x * 100}%`,
  top: `${center.value.y * 100}%`,
}))
</script>

<template>
  <div
    v-if="positioned"
    class="hs"
    :class="[`hs--${status.toLowerCase()}`]"
    :style="styleVars"
    role="button"
    tabindex="0"
    :aria-label="`${hotspot.label || '热点'}${status === 'SEEN' ? '，已探索' : '，未探索'}`"
    @click.stop="emit('select', hotspot)"
    @keydown.enter.prevent="emit('select', hotspot)"
    @keydown.space.prevent="emit('select', hotspot)"
    @mouseenter="hovering = true"
    @mouseleave="hovering = false"
  >
    <span class="hs__ring" aria-hidden="true" />
    <span class="hs__dot" aria-hidden="true" />
    <span v-if="status === 'SEEN'" class="hs__check" aria-hidden="true">✓</span>

    <Transition name="fade">
      <span v-if="hovering" class="hs__tip" role="tooltip">
        <span class="hs__tip-title">{{ hotspot.label || '未命名节点' }}</span>
        <span class="hs__tip-state">{{ status === 'SEEN' ? '已探索' : '未探索' }}</span>
        <span class="hs__tip-cta">点击了解 →</span>
      </span>
    </Transition>
  </div>
</template>

<style scoped>
.hs {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: var(--z-hotspot);
  cursor: pointer;
  display: grid;
  place-items: center;
}

/* ---------- 呼吸环 ---------- */
.hs__ring {
  position: absolute;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1.5px solid color-mix(in srgb, var(--chapter-accent) 55%, transparent);
  animation: hs-breathe 2.4s ease-in-out infinite;
}

/* ---------- 实心点 ---------- */
.hs__dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--chapter-accent) 30%, transparent);
  border: 1.5px solid color-mix(in srgb, var(--chapter-accent) 75%, transparent);
  transition:
    width var(--dur-fast) var(--ease-standard),
    height var(--dur-fast) var(--ease-standard),
    background-color var(--dur-fast) var(--ease-standard);
}

.hs:hover .hs__dot,
.hs:focus-visible .hs__dot {
  width: 22px;
  height: 22px;
  background: color-mix(in srgb, var(--chapter-accent) 55%, transparent);
}

/* ---------- 已访问：实心小点 + ✓，不再强闪 ---------- */
.hs--seen .hs__ring {
  animation: none;
  opacity: 0.35;
  width: 24px;
  height: 24px;
}
.hs--seen .hs__dot {
  width: 14px;
  height: 14px;
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
}
.hs__check {
  position: absolute;
  font-size: 9px;
  line-height: 1;
  color: #fff;
  font-weight: 700;
  pointer-events: none;
}

/* ---------- 选中：外圈 32px ---------- */
.hs--selected .hs__ring {
  animation: none;
  width: 32px;
  height: 32px;
  border-width: 2px;
  opacity: 1;
}
.hs--selected .hs__dot {
  width: 20px;
  height: 20px;
  background: var(--chapter-accent);
}

@keyframes hs-breathe {
  0%,
  100% {
    opacity: 0.55;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.12);
  }
}

/* ---------- Tooltip（180–240px，Hover 延迟 150ms） ---------- */
.hs__tip {
  position: absolute;
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  width: 190px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: var(--radius-card);
  background: var(--color-paper-50);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  z-index: var(--z-tooltip);
  pointer-events: none;
  transition-delay: 150ms;
}
.hs__tip-title {
  font-size: var(--fs-body-s);
  font-weight: 600;
  color: var(--color-ink-900);
}
.hs__tip-state {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.hs__tip-cta {
  font-size: var(--fs-caption);
  color: var(--chapter-accent);
  margin-top: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .hs__ring {
    animation: none;
  }
}
</style>
