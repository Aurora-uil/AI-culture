<script setup lang="ts">
import { computed, ref } from 'vue'
import DsDrawer from '../ds/DsDrawer.vue'
import DsButton from '../ds/DsButton.vue'
import DsIcon from '../ds/DsIcon.vue'
import EvidenceBadge from '../global/EvidenceBadge.vue'
import { useEntityStore } from '@/stores/entity'

/**
 * 实体详情抽屉（设计系统 §27 / §28）
 *
 * 内容层级只允许四层：
 *   1. 是什么
 *   2. 和当前章节有什么关系
 *   3. 可以继续发现什么
 *   4. 依据是什么
 *
 * 首屏正文 ≤ 220 中文字，更深内容放「展开详细说明」。避免百科式长文。
 */
const props = defineProps<{
  chapterId: string
  /** 「下一个文字 →」等按预设顺序切换 */
  sequence?: string[]
  /** 固定提示，例如历史画证据边界说明 */
  caveat?: string | null
}>()

const emit = defineEmits<{
  (e: 'ask', entityId: string): void
  (e: 'graph', entityId: string): void
  (e: 'sources', entityId: string): void
  (e: 'select', entityId: string): void
  (e: 'close'): void
}>()

const store = useEntityStore()
const entity = computed(() => store.current)

const displayName = computed(() => entity.value?.display_name || entity.value?.name || '')

/** 首屏截断到 220 字，符合 §28 的长度规范 */
const TRUNCATE = 220
const isLong = computed(() => (entity.value?.body_markdown?.length ?? 0) > TRUNCATE)
const expanded = ref(false)
const bodyText = computed(() => {
  const raw = entity.value?.body_markdown || ''
  if (expanded.value || raw.length <= TRUNCATE) return raw
  return raw.slice(0, TRUNCATE) + '……'
})

const nextEntityId = computed(() => {
  if (!props.sequence?.length || !entity.value) return null
  const i = props.sequence.indexOf(entity.value.id)
  if (i < 0) return null
  return props.sequence[(i + 1) % props.sequence.length]
})

const sourceCount = computed(() => entity.value?.source_count ?? 0)
const relatedCount = computed(() => entity.value?.related_entity_count ?? 0)

/** 实体未配图时展示“章节视觉索引”，绝不伪装成该实体原图。 */
const chapterVisual = computed(() => {
  const id = props.chapterId
  if (id.includes('northern_wei')) return 'northern-wei'
  if (id.includes('contemporary')) return 'contemporary'
  if (id.includes('han')) return 'han'
  if (id.includes('tang')) return 'tang'
  if (id.includes('yuan')) return 'yuan'
  if (id.includes('qing')) return 'qing'
  return 'han'
})
const visualIsOriginal = computed(() => ['northern-wei', 'tang', 'yuan'].includes(chapterVisual.value))
</script>

<template>
  <DsDrawer
    :open="store.drawerOpen"
    width="entity"
    :title="displayName"
    :subtitle="entity?.subtitle || entity?.entity_type"
    @close="emit('close')"
  >
    <template v-if="entity">
      <!-- 局部高清图 -->
      <figure v-if="entity.image_url" class="ed__hero">
        <img :src="entity.image_url" :alt="displayName" />
      </figure>
      <div
        v-else
        class="ed__hero ed__hero--index"
        :data-chapter-visual="chapterVisual"
        role="img"
        :aria-label="`${displayName}暂无已核验实体图片，当前显示章节视觉索引`"
      >
        <div class="ed__visual-label">
          <DsIcon :name="entity.entity_type === 'Person' ? 'person' : 'artifact'" :size="18" />
          <span>{{ visualIsOriginal ? '章节史料原图' : '章节AI情境图' }}</span>
          <small>非该实体原图</small>
        </div>
      </div>

      <div class="ed__badges">
        <EvidenceBadge :type="entity.verification_label" size="m" />
        <span v-if="entity.era" class="ed__era">{{ entity.era }}</span>
      </div>

      <!-- 1. 是什么 -->
      <section class="ed__section">
        <p class="ed__summary">{{ entity.short_summary }}</p>
        <p v-if="bodyText" class="ed__body" v-html="bodyText.replace(/\n/g, '<br />')" />
        <button v-if="isLong" class="ed__more" type="button" @click="expanded = !expanded">
          {{ expanded ? '收起' : '展开详细说明' }}
        </button>
      </section>

      <!-- 固定提示：证据边界（如历史画不是现场照片） -->
      <p v-if="caveat" class="ed__caveat">
        <DsIcon name="info" :size="14" />
        <span>{{ caveat }}</span>
      </p>

      <!-- Script 类型：语言与文字关系说明 -->
      <section v-if="entity.extra?.text_language_note" class="ed__section ed__section--note">
        <h3 class="ed__h3">语言与文字的关系</h3>
        <p class="ed__note">{{ entity.extra.text_language_note }}</p>
      </section>

      <!-- 在云台 / 本章中的位置 -->
      <section v-if="entity.extra?.yuntai_usage_note" class="ed__section ed__section--note">
        <h3 class="ed__h3">在本章中的位置</h3>
        <p class="ed__note">{{ entity.extra.yuntai_usage_note }}</p>
      </section>
    </template>

    <template #footer>
      <DsButton variant="primary" @click="entity && emit('ask', entity.id)">
        <DsIcon name="sparkle" :size="15" />
        <span>问它一个问题</span>
      </DsButton>
      <DsButton variant="secondary" @click="entity && emit('graph', entity.id)">
        <DsIcon name="nodes" :size="15" />
        <span>查看它的关系</span>
      </DsButton>
      <DsButton
        v-if="sourceCount"
        variant="secondary"
        @click="entity && emit('sources', entity.id)"
      >
        <DsIcon name="document" :size="15" />
        <span>查看史料来源 {{ sourceCount }}</span>
      </DsButton>
      <DsButton
        v-if="nextEntityId"
        variant="ghost"
        @click="nextEntityId && emit('select', nextEntityId)"
      >
        <span>下一个 →</span>
      </DsButton>
    </template>
  </DsDrawer>
</template>

<style scoped>
.ed__hero {
  margin: 0 0 var(--sp-6);
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-paper-100);
  border: 1px solid var(--color-border);
}
.ed__hero img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}
.ed__hero--empty {
  aspect-ratio: 4 / 3;
  display: grid;
  place-items: center;
  color: var(--color-ink-500);
  opacity: 0.5;
}

.ed__hero--index {
  position: relative;
  aspect-ratio: 4 / 3;
  background-image: var(--ed-visual);
  background-size: var(--ed-visual-size, cover);
  background-position: var(--ed-visual-position, center);
  isolation: isolate;
}
.ed__hero--index::after {
  content: '';
  position: absolute;
  z-index: -1;
  inset: 0;
  background: linear-gradient(180deg, rgba(21,55,58,.04), rgba(21,55,58,.68));
}
.ed__visual-label {
  position: absolute;
  left: var(--sp-4);
  right: var(--sp-4);
  bottom: var(--sp-4);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 8px;
  align-items: center;
  color: #fffdf5;
  text-shadow: 0 1px 10px rgba(0,0,0,.34);
}
.ed__visual-label svg { grid-row: 1 / 3; }
.ed__visual-label span { font-family: var(--font-display); font-size: var(--fs-body-s); }
.ed__visual-label small { font-size: var(--fs-caption); opacity: .76; }
.ed__hero--index[data-chapter-visual='han']{--ed-visual:url('/assets/han/han-route-scene-v2.png');--ed-visual-size:cover;--ed-visual-position:58% center}
.ed__hero--index[data-chapter-visual='northern-wei']{--ed-visual:url('/assets/wei/yungang-cave20-original.jpg')}
.ed__hero--index[data-chapter-visual='tang']{--ed-visual:url('/assets/tang/bunian-original.jpg');--ed-visual-position:62% center}
.ed__hero--index[data-chapter-visual='yuan']{--ed-visual:url('/assets/yuan/yuntai-east-wall-original.jpg')}
.ed__hero--index[data-chapter-visual='qing']{--ed-visual:url('/assets/qing/qing-migration-photoreal-v2.png');--ed-visual-size:cover;--ed-visual-position:center}
.ed__hero--index[data-chapter-visual='contemporary']{--ed-visual:url('/assets/contemporary/qiang-workshop-photoreal-v2.png');--ed-visual-size:cover;--ed-visual-position:center}

.ed__badges {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}
.ed__era {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

.ed__section {
  margin-bottom: var(--sp-6);
}
.ed__section--note {
  padding: var(--sp-4);
  background: var(--color-paper-100);
  border-radius: var(--radius-card);
  border-left: 3px solid color-mix(in srgb, var(--chapter-accent) 60%, transparent);
}

.ed__h3 {
  font-size: var(--fs-body-s);
  font-weight: 600;
  color: var(--color-ink-700);
  margin-bottom: var(--sp-2);
}

.ed__summary {
  font-size: var(--fs-body-l);
  line-height: var(--lh-body-l);
  color: var(--color-ink-900);
  margin-bottom: var(--sp-4);
}

.ed__body,
.ed__note {
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-l);
  color: var(--color-ink-700);
}

.ed__more {
  margin-top: var(--sp-3);
  border: 0;
  background: transparent;
  padding: 0;
  color: var(--chapter-accent);
  font-size: var(--fs-body-s);
}
.ed__more:hover {
  text-decoration: underline;
}

.ed__caveat {
  display: flex;
  gap: var(--sp-2);
  align-items: flex-start;
  padding: var(--sp-3) var(--sp-4);
  margin-bottom: var(--sp-6);
  border-radius: var(--radius-card);
  background: color-mix(in srgb, var(--color-warning) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-warning) 32%, transparent);
  color: var(--color-warning);
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-s);
}
</style>
