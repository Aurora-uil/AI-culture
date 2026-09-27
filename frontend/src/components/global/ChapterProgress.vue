<script setup lang="ts">
import { computed } from 'vue'
import DsIcon from '../ds/DsIcon.vue'

/**
 * 章节进度条（设计系统 §15）—— 固定在页面底部 HUD
 *
 * 原则：
 *  - 不做游戏经验值、不做积分，用「探索进度」；
 *  - 进度可跳跃，不强迫线性通关；
 *  - §89：状态文字比百分比更重要（未探索 / 探索中 / 已完成核心路径 / 深度探索）。
 */
const props = withDefaults(
  defineProps<{
    era: string
    progress: number
    nodes?: { label: string; done: boolean; current?: boolean }[]
    hint?: string
    showDisclaimer?: boolean
  }>(),
  { progress: 0, showDisclaimer: true },
)

const statusText = computed(() => {
  const p = props.progress
  if (p <= 0) return '未探索'
  if (p >= 90) return '深度探索'
  if (p >= 60) return '已完成核心路径'
  return '探索中'
})

const clamped = computed(() => Math.max(0, Math.min(100, Math.round(props.progress))))
</script>

<template>
  <footer class="ch-progress">
    <div class="ch-progress__left">
      <span class="ch-progress__era">{{ era }}探索</span>
      <span class="ch-progress__pct">{{ clamped }}%</span>
      <span class="ch-progress__status">{{ statusText }}</span>

      <ol v-if="nodes?.length" class="ch-progress__nodes">
        <li
          v-for="n in nodes"
          :key="n.label"
          class="ch-progress__node"
          :class="{ 'is-done': n.done, 'is-current': n.current }"
        >
          <span class="ch-progress__node-dot" aria-hidden="true">
            <DsIcon v-if="n.done" name="check" :size="9" />
          </span>
          <span class="ch-progress__node-label">{{ n.label }}</span>
        </li>
      </ol>
    </div>

    <div class="ch-progress__right">
      <span v-if="hint" class="ch-progress__hint">{{ hint }}</span>
      <span v-if="showDisclaimer" class="ch-progress__disclaimer">
        史料说明 / AI说明
      </span>
    </div>
  </footer>
</template>

<style scoped>
.ch-progress {
  position: sticky;
  bottom: 0;
  z-index: var(--z-hud);
  flex: none;
  height: var(--status-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-6);
  padding: 0 var(--pad-page-x);
  background: rgba(250, 248, 242, 0.92);
  backdrop-filter: blur(12px);
  border-top: 1px solid var(--color-border);
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

.ch-progress__left,
.ch-progress__right {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  min-width: 0;
}

.ch-progress__era {
  color: var(--color-ink-700);
}
.ch-progress__pct {
  font-weight: 600;
  color: var(--chapter-accent);
}
.ch-progress__status {
  padding: 1px 8px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--chapter-accent) 12%, transparent);
  color: var(--chapter-accent);
}

.ch-progress__nodes {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  list-style: none;
  margin: 0 0 0 var(--sp-4);
  padding: 0;
  min-width: 0;
  overflow: hidden;
}
.ch-progress__node {
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}
.ch-progress__node-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1.4px solid var(--color-ink-500);
  display: grid;
  place-items: center;
  color: #fff;
  flex: none;
}
.ch-progress__node.is-done .ch-progress__node-dot {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
}
.ch-progress__node.is-current .ch-progress__node-dot {
  border-color: var(--chapter-accent);
  border-width: 2px;
}
.ch-progress__node.is-done .ch-progress__node-label {
  color: var(--color-ink-700);
}

.ch-progress__hint {
  color: var(--color-ink-700);
}
.ch-progress__disclaimer {
  opacity: 0.75;
}

@media (max-width: 1366px) {
  .ch-progress__nodes {
    display: none;
  }
}
</style>
