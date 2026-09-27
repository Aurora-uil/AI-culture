<script setup lang="ts">
import { computed } from 'vue'
import DsIcon from '../ds/DsIcon.vue'
import type { Source } from '@/types'

/**
 * 来源卡片（设计系统 §36）
 *
 * 必须区分三件事，不能只列参考文献名字：
 *   1. 来源是什么
 *   2. 来源支持哪条事实
 *   3. 这条内容是史实还是解释
 *
 * UI 只显示「官方资料 / 学术研究 / 专业资料」，不向用户暴露 S/A/B 内部评级。
 */
const props = defineProps<{
  source: Source
  index?: number
}>()

const typeLabel = computed(() => {
  switch (props.source.source_type) {
    case 'official':
      return '官方资料'
    case 'academic':
      return '学术研究'
    case 'book':
      return '专业著作'
    default:
      return '专业资料'
  }
})

const isCourtSource = computed(() => props.source.source_perspective === 'qing_court')
</script>

<template>
  <article class="sc">
    <header class="sc__head">
      <span class="sc__type">{{ typeLabel }}</span>
      <span v-if="index" class="sc__index">{{ index }}</span>
    </header>

    <h4 class="sc__title">{{ source.title }}</h4>
    <p class="sc__inst">
      {{ source.institution }}
      <template v-if="source.author"> · {{ source.author }}</template>
      <template v-if="source.publication_year"> · {{ source.publication_year }}</template>
    </p>

    <!-- 来源视角：清代御制文献等必须标明 -->
    <p v-if="isCourtSource" class="sc__perspective">
      <DsIcon name="info" :size="13" />
      <span>清代官方文献记载与表述，带有其作者与政治语境。</span>
    </p>

    <!-- 支持了哪些具体事实 —— 这是本组件的核心，不是只列书名 -->
    <div v-if="source.claims?.length" class="sc__claims">
      <p class="sc__claims-label">支持事实：</p>
      <ul class="sc__claims-list">
        <li v-for="c in source.claims" :key="c.claim_id">「{{ c.text }}」</li>
      </ul>
    </div>

    <p v-if="source.bibliography" class="sc__biblio">{{ source.bibliography }}</p>

    <a
      v-if="source.public_url"
      class="sc__link"
      :href="source.public_url"
      target="_blank"
      rel="noopener noreferrer"
    >
      <span>查看来源</span>
      <DsIcon name="external-link" :size="13" />
    </a>
    <p v-else class="sc__nolink">该来源暂无公开链接，以上为书目信息。</p>
  </article>
</template>

<style scoped>
.sc {
  padding: var(--sp-4) var(--sp-4) var(--sp-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: #fff;
  margin-bottom: var(--sp-4);
}

.sc__head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}
.sc__type {
  font-size: var(--fs-caption);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--color-blue-600) 12%, transparent);
  color: var(--color-blue-800);
}
.sc__index {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

.sc__title {
  font-size: var(--fs-body);
  font-weight: 600;
  line-height: var(--lh-h3);
  color: var(--color-ink-900);
  margin-bottom: 2px;
}

.sc__inst {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  margin-bottom: var(--sp-3);
}

.sc__perspective {
  display: flex;
  gap: 6px;
  align-items: flex-start;
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-warning);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-btn);
  background: color-mix(in srgb, var(--color-warning) 9%, transparent);
  margin-bottom: var(--sp-3);
}

.sc__claims {
  padding: var(--sp-3);
  background: var(--color-paper-100);
  border-radius: var(--radius-btn);
  margin-bottom: var(--sp-3);
}
.sc__claims-label {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  margin-bottom: 4px;
}
.sc__claims-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sc__claims-list li {
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}

.sc__biblio {
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
  margin-bottom: var(--sp-3);
}

.sc__link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--fs-body-s);
  color: var(--chapter-accent);
}
.sc__link:hover {
  text-decoration: underline;
}

.sc__nolink {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  font-style: italic;
}
</style>
