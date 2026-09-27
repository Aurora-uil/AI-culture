<script setup lang="ts">
import { computed } from 'vue'
import DsIcon from '../ds/DsIcon.vue'
import EvidenceBadge from '../global/EvidenceBadge.vue'
import { useGraphStore } from '@/stores/graph'
import type { ClaimType, VerificationLabel } from '@/types'

/**
 * 「为什么有这条关系？」（设计系统 §37 / PRD Risk 4）
 *
 * 图谱不能只是前端画出来的一堆线 —— 每一条重要边都必须可以追溯来源，
 * 并且明确标注它是史实、解释还是策展关联。
 */
const store = useGraphStore()
const evidence = computed(() => store.evidence)

const claimTypeLabel: Record<ClaimType, string> = {
  fact: '史实',
  interpretation: '研究解释',
  curatorial: '策展关联',
  catalogue_fact: '目录记录',
}

const badgeType = computed<VerificationLabel>(() => {
  switch (evidence.value?.claim_type) {
    case 'interpretation':
      return 'scholarly_view'
    case 'curatorial':
      return 'curatorial'
    default:
      return 'historical_fact'
  }
})
</script>

<template>
  <Transition name="fade">
    <aside v-if="evidence" class="rep">
      <header class="rep__head">
        <h4 class="rep__title">为什么有这条关系？</h4>
        <button class="rep__close" type="button" aria-label="关闭" @click="store.evidence = null">
          <DsIcon name="close" :size="15" />
        </button>
      </header>

      <p class="rep__triple">
        <span class="rep__node">{{ evidence.subject_name }}</span>
        <span class="rep__arrow">→</span>
        <span class="rep__rel">{{ evidence.display_label }}</span>
        <span class="rep__arrow">→</span>
        <span class="rep__node">{{ evidence.object_name }}</span>
      </p>

      <div class="rep__meta">
        <span class="rep__type">类型：{{ claimTypeLabel[evidence.claim_type] }}</span>
        <EvidenceBadge :type="badgeType" />
      </div>

      <p v-if="evidence.claim" class="rep__claim">「{{ evidence.claim }}」</p>

      <div v-if="evidence.sources.length" class="rep__sources">
        <p class="rep__sources-label">支持依据：</p>
        <ul class="rep__list">
          <li v-for="(s, i) in evidence.sources" :key="s.id">
            <span class="rep__num">{{ i + 1 }}</span>
            <span class="rep__src-title">{{ s.title }}</span>
            <span class="rep__src-inst">{{ s.institution }}</span>
          </li>
        </ul>
      </div>

      <p v-else class="rep__nosrc">
        这条关系目前还没有绑定已审核的史料来源。
      </p>
    </aside>
  </Transition>
</template>

<style scoped>
.rep {
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  background: var(--color-paper-50);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

.rep__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sp-3);
}
.rep__title {
  font-size: var(--fs-body-s);
  font-weight: 600;
  color: var(--color-ink-900);
}
.rep__close {
  border: 0;
  background: transparent;
  color: var(--color-ink-500);
  display: grid;
  place-items: center;
  padding: 2px;
}

.rep__triple {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: var(--fs-body-s);
  margin-bottom: var(--sp-3);
}
.rep__node {
  color: var(--color-ink-900);
  font-weight: 500;
}
.rep__rel {
  color: var(--chapter-accent);
  padding: 1px 7px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--chapter-accent) 12%, transparent);
}
.rep__arrow {
  color: var(--color-ink-500);
}

.rep__meta {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}
.rep__type {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

.rep__claim {
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-l);
  color: var(--color-ink-700);
  padding: var(--sp-3);
  background: #fff;
  border-radius: var(--radius-btn);
  margin-bottom: var(--sp-3);
}

.rep__sources-label {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  margin-bottom: var(--sp-2);
}
.rep__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.rep__list li {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
}
.rep__num {
  flex: none;
  width: 16px;
  height: 16px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--color-paper-200);
  font-size: 10px;
  color: var(--color-ink-700);
}
.rep__src-title {
  color: var(--color-ink-900);
}
.rep__src-inst {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

.rep__nosrc {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  font-style: italic;
}
</style>
