<script setup lang="ts">
import DsIcon from '../ds/DsIcon.vue'

/**
 * AIGC 内容标识（设计系统 §82 / PRD §16.3）
 *
 * 所有 AI 生成图像 / 历史场景示意必须固定显示此标识，
 * 避免观众误认为是真实历史影像或考古精确复原。
 */
withDefaults(
  defineProps<{
    kind?: 'scene' | 'image' | 'generated'
    /** 覆盖默认文案 */
    text?: string
    /** 是否使用深色底（叠在深色画面上） */
    onDark?: boolean
  }>(),
  { kind: 'scene', onDark: false },
)
</script>

<template>
  <span
    class="ai-badge"
    :class="{ 'is-dark': onDark }"
    :title="
      kind === 'generated'
        ? '该结果为AI辅助文化创意作品，不是传统羌绣原作。'
        : '该画面用于帮助理解空间与氛围，不等同于考古意义上的精确复原。'
    "
  >
    <DsIcon name="sparkle" :size="12" />
    <span>{{
      text || (kind === 'generated' ? 'AI辅助文化创意作品' : 'AI辅助历史场景示意')
    }}</span>
  </span>
</template>

<style scoped>
.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-caption);
  line-height: 1.5;
  color: var(--color-ink-500);
  background: rgba(250, 248, 242, 0.82);
  border: 1px solid var(--color-border);
  backdrop-filter: blur(6px);
  cursor: help;
  white-space: nowrap;
}
.ai-badge.is-dark {
  color: rgba(255, 255, 255, 0.86);
  background: rgba(31, 37, 43, 0.5);
  border-color: rgba(255, 255, 255, 0.18);
}
</style>
