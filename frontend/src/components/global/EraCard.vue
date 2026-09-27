<script setup lang="ts">
import { computed } from 'vue'
import DsIcon from '../ds/DsIcon.vue'
import type { Chapter } from '@/types'

/**
 * 章节卡片（设计系统 §19）
 *
 * 结构：朝代 / 年代 / 章节图 / 关键词 / 一句话 / 进度
 * Hover：卡片上移 4px、背景轻微放大 1.02、出现主问题。
 * 不使用翻转卡片。
 *
 * §89：状态文字比百分比更重要（未探索/探索中/已完成核心路径/深度探索）。
 */
const props = withDefaults(
  defineProps<{
    chapter: Chapter
    progress?: number
    index?: number
  }>(),
  { progress: 0 },
)

const statusText = computed(() => {
  const p = props.progress
  if (p <= 0) return '未探索'
  if (p >= 90) return '深度探索'
  if (p >= 60) return '已完成核心路径'
  return '探索中'
})

/** 每章封面意象（设计系统 §49：一张封面只表达一个核心意象） */
const COVER_GLYPH: Record<string, string> = {
  han: '道路与行旅',
  'northern-wei': '石窟造像',
  tang: '横向画卷',
  yuan: '券洞石刻文字',
  qing: '迁徙与大地',
  contemporary: '手与刺绣纹样',
}
</script>

<template>
  <RouterLink
    :to="`/chapter/${chapter.slug}`"
    class="era-card"
    :style="{ '--chapter-accent': chapter.accent }"
  >
    <div class="era-card__media">
      <!-- 章节封面意象（SVG 占位，可被真实图片替换） -->
      <div class="era-card__cover" :data-glyph="chapter.slug">
        <span class="era-card__cover-label">{{ COVER_GLYPH[chapter.slug] }}</span>
      </div>
      <span class="era-card__index">{{ String((index ?? 0) + 1).padStart(2, '0') }}</span>
    </div>

    <div class="era-card__body">
      <div class="era-card__head">
        <span class="era-card__era">{{ chapter.era }}</span>
        <span class="era-card__date">{{ chapter.date_label }}</span>
      </div>

      <p class="era-card__keyword tt-keyword">{{ chapter.keyword }}</p>
      <p class="era-card__desc">{{ chapter.title }}</p>

      <!-- Hover 出现主问题 -->
      <p class="era-card__question">{{ chapter.guiding_question }}</p>

      <div class="era-card__foot">
        <span class="era-card__status" :class="{ 'is-none': progress <= 0 }">
          {{ statusText }}
        </span>
        <span class="era-card__pct">{{ Math.round(progress) }}%</span>
        <DsIcon name="arrow-right" :size="14" class="era-card__go" />
      </div>
    </div>
  </RouterLink>
</template>

<style scoped>
.era-card {
  position: relative;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: #fff;
  overflow: hidden;
  box-shadow: var(--shadow-card);
  transition:
    transform var(--dur-normal) var(--ease-standard),
    box-shadow var(--dur-normal) var(--ease-standard);
}
.era-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-floating);
}

.era-card__media {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--color-paper-100);
}

.era-card__cover {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 30% 30%, color-mix(in srgb, var(--chapter-accent) 26%, transparent), transparent 62%),
    radial-gradient(circle at 72% 74%, color-mix(in srgb, var(--chapter-accent) 16%, transparent), transparent 58%),
    var(--color-paper-100);
  transition: transform var(--dur-slow) var(--ease-standard);
}
.era-card:hover .era-card__cover {
  transform: scale(1.02);
}

.era-card__cover-label {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  letter-spacing: 0.2em;
  color: color-mix(in srgb, var(--chapter-accent) 78%, #1f252b);
  opacity: 0.72;
}

.era-card__index {
  position: absolute;
  top: var(--sp-3);
  left: var(--sp-4);
  font-family: var(--font-display);
  font-size: var(--fs-body-s);
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 1px 6px rgba(31, 37, 43, 0.4);
}

.era-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--sp-4) var(--sp-4) var(--sp-3);
}

.era-card__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}
.era-card__era {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  color: var(--chapter-accent);
  letter-spacing: 0.08em;
}
.era-card__date {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

.era-card__keyword {
  font-size: var(--fs-h2);
  color: var(--color-ink-900);
  margin-bottom: 2px;
}

.era-card__desc {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 主问题默认收起，Hover 展开 */
.era-card__question {
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition:
    max-height var(--dur-normal) var(--ease-standard),
    opacity var(--dur-normal) var(--ease-standard),
    margin-top var(--dur-normal) var(--ease-standard);
}
.era-card:hover .era-card__question {
  max-height: 60px;
  opacity: 1;
  margin-top: var(--sp-2);
}

.era-card__foot {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-top: auto;
  padding-top: var(--sp-3);
}
.era-card__status {
  font-size: var(--fs-caption);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--chapter-accent) 12%, transparent);
  color: var(--chapter-accent);
}
.era-card__status.is-none {
  background: rgba(65, 55, 42, 0.06);
  color: var(--color-ink-500);
}
.era-card__pct {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.era-card__go {
  margin-left: auto;
  color: var(--chapter-accent);
  transition: transform var(--dur-fast) var(--ease-standard);
}
.era-card:hover .era-card__go {
  transform: translateX(3px);
}
</style>
