<script setup lang="ts">
import { computed } from 'vue'
import type { VerificationLabel } from '@/types'

/**
 * 史料可信度标签（设计系统 §7 / §81 / §67）
 *
 * 全项目统一文案，不得每章换词。
 * 可访问性要求：**颜色 + 图标 + 文本三重编码**，不能只用颜色表达史料类型。
 * 证据色与章节色严格分离：
 *   章节色 = 用户在哪里；证据色 = 内容是什么性质。
 */
const props = withDefaults(
  defineProps<{
    type: VerificationLabel
    size?: 's' | 'm'
  }>(),
  { size: 's' },
)

interface Meta {
  label: string
  glyph: string
  color: string
  hint: string
}

const META: Record<VerificationLabel, Meta> = {
  historical_fact: {
    label: '史料确认',
    glyph: '●',
    color: 'var(--evidence-fact)',
    hint: '有可靠来源直接支持的内容。',
  },
  scholarly_view: {
    label: '研究观点',
    glyph: '◐',
    color: 'var(--evidence-interpretation)',
    hint: '属于研究解释，不是唯一确定结论。',
  },
  digital_reconstruction: {
    label: '数字复原',
    glyph: '◇',
    color: 'var(--evidence-reconstruction)',
    hint: '为帮助理解而制作的数字化示意，不等同于考古意义上的精确复原。',
  },
  ai_narrative: {
    label: 'AI叙事',
    glyph: '✦',
    color: 'var(--evidence-ai-narrative)',
    hint: '由 AI 基于审核资料生成的第一人称叙事，不是历史人物真实原话。',
  },
  curatorial: {
    label: '策展关联',
    glyph: '┄',
    color: 'var(--evidence-curatorial)',
    hint: '为了帮助理解而建立的主题联系，不是历史事件之间的因果。',
  },
  disputed: {
    label: '存在争议',
    glyph: '!',
    color: 'var(--evidence-disputed)',
    hint: '关于这一点，学界存在不同观点。',
  },
}

const meta = computed(() => META[props.type] ?? META.historical_fact)
</script>

<template>
  <span
    class="ev-badge"
    :class="`ev-badge--${size}`"
    :style="{ '--ev-color': meta.color }"
    :title="meta.hint"
  >
    <span class="ev-badge__glyph" aria-hidden="true">{{ meta.glyph }}</span>
    <span class="ev-badge__label">{{ meta.label }}</span>
  </span>
</template>

<style scoped>
.ev-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px 2px 7px;
  border-radius: var(--radius-pill);
  border: 1px solid color-mix(in srgb, var(--ev-color) 42%, transparent);
  background: color-mix(in srgb, var(--ev-color) 10%, transparent);
  color: var(--ev-color);
  font-size: var(--fs-caption);
  line-height: 1.6;
  white-space: nowrap;
  font-weight: 500;
}

.ev-badge--m {
  font-size: var(--fs-body-s);
  padding: 3px 11px 3px 9px;
}

.ev-badge__glyph {
  font-size: 0.85em;
  line-height: 1;
}
</style>
