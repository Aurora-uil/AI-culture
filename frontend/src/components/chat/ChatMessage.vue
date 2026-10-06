<script setup lang="ts">
import { computed } from 'vue'
import DsIcon from '../ds/DsIcon.vue'
import type { ChatMessage } from '@/types'

/**
 * 对话消息（设计系统 §31 / §33）
 *
 * AI 消息固定包含：角色名 → 正文 → 来源 chips → 继续探索 chips
 * 并且必须如实标注这条回答是怎么来的（实时AI / 本地检索 / 演示保障），
 * 绝不把兜底回答伪装成实时 AI。
 */
const props = defineProps<{
  message: ChatMessage
  characterName?: string
}>()

const emit = defineEmits<{
  (e: 'source', sourceId: string): void
  (e: 'explore', entityId: string): void
  (e: 'regenerate', messageId: string): void
}>()

const isUser = computed(() => props.message.role === 'user')

/** 回答来源层级标注 */
const tierInfo = computed(() => {
  switch (props.message.response_tier) {
    case 'live_rag':
      return { label: '已联网搜索 · DeepSeek 归纳', warn: false }
    case 'web_search_fallback':
      return { label: '已联网搜索 · 未经 DeepSeek 归纳', warn: true }
    case 'faq_fallback':
      return { label: '演示保障模式 · 来自已审核问答库', warn: true }
    case 'local_retrieval':
      return { label: '本地资料检索 · 未接入实时大模型', warn: true }
    default:
      return null
  }
})
</script>

<template>
  <!-- 用户消息 -->
  <div v-if="isUser" class="msg msg--user">
    <div class="msg__bubble msg__bubble--user">{{ message.content }}</div>
  </div>

  <!-- AI 消息 -->
  <div v-else class="msg msg--ai">
    <header class="msg__head">
      <span class="msg__who">{{ characterName || 'AI数字角色' }}</span>
      <span class="msg__tag">AI数字叙事角色</span>
    </header>

    <div class="msg__bubble">
      <!-- 无资料：明确承认，不编造 -->
      <div v-if="message.status === 'NO_EVIDENCE'" class="msg__state msg__state--empty">
        <DsIcon name="info" :size="16" />
        <div>
          <p class="msg__state-title">资料不足</p>
          <p class="msg__state-text">
            当前资料库中没有足够可靠的材料支持确定回答这个问题。你可以换个问法，或查看与本章相关的已核验资料。
          </p>
        </div>
      </div>

      <div
        v-else-if="message.status === 'MODEL_TIMEOUT' || message.status === 'NETWORK_ERROR'"
        class="msg__state msg__state--warn"
      >
        <DsIcon name="alert" :size="16" />
        <div>
          <p class="msg__state-title">AI讲述暂时没有完成</p>
          <p class="msg__state-text">你可以重试，或先查看相关史料。</p>
        </div>
      </div>

      <div v-else-if="message.status === 'VALIDATION_FAILED'" class="msg__state msg__state--warn">
        <DsIcon name="alert" :size="16" />
        <div>
          <p class="msg__state-title">这条回答没有通过事实核验</p>
          <p class="msg__state-text">系统不会展示未通过核验的内容，请换个问法再试。</p>
        </div>
      </div>

      <p v-else class="msg__text" v-html="message.content.replace(/\n/g, '<br />')" />
    </div>

    <!-- 来源标注 -->
    <p v-if="tierInfo" class="msg__tier" :class="{ 'is-warn': tierInfo.warn }">
      {{ tierInfo.label }}
    </p>

    <!-- 来源 chips -->
    <div v-if="message.citations?.length" class="msg__cites">
      <span class="msg__cites-label">依据：</span>
      <template v-for="(c, i) in message.citations" :key="c.source_id + i">
        <a
          v-if="c.public_url"
          class="msg__cite"
          :href="c.public_url"
          target="_blank"
          rel="noopener noreferrer"
        >
          <span class="msg__cite-num">{{ i + 1 }}</span>
          <span>{{ c.title }}</span>
        </a>
        <button
          v-else
          class="msg__cite"
          type="button"
          @click="emit('source', c.source_id)"
        >
          <span class="msg__cite-num">{{ i + 1 }}</span>
          <span>{{ c.title }}</span>
        </button>
      </template>
    </div>

    <!-- 继续探索 -->
    <div v-if="message.related_entities?.length" class="msg__related">
      <span class="msg__cites-label">继续探索：</span>
      <button
        v-for="e in message.related_entities"
        :key="e.id"
        class="msg__rel-chip"
        type="button"
        @click="emit('explore', e.id)"
      >
        {{ e.display_name || e.name }}
      </button>
    </div>

    <div v-if="!isUser && message.status === 'DONE'" class="msg__actions">
      <button class="msg__action" type="button" @click="emit('regenerate', message.id)">
        <DsIcon name="refresh" :size="13" />
        <span>重新回答</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.msg {
  margin-bottom: var(--sp-6);
}
.msg--user {
  display: flex;
  justify-content: flex-end;
}

/* ---------- 用户气泡 ---------- */
.msg__bubble--user {
  max-width: 76%;
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-card);
  border-bottom-right-radius: 4px;
  background: color-mix(in srgb, var(--chapter-accent) 12%, #fff);
  border: 1px solid color-mix(in srgb, var(--chapter-accent) 26%, transparent);
  font-size: var(--fs-body);
  line-height: var(--lh-body);
  color: var(--color-ink-900);
}

/* ---------- AI 气泡 ---------- */
.msg--ai {
  max-width: 88%;
}
.msg__head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}
.msg__who {
  font-size: var(--fs-body-s);
  font-weight: 600;
  color: var(--chapter-accent);
}
.msg__tag {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--evidence-ai-narrative) 14%, transparent);
  color: var(--evidence-ai-narrative);
  border: 1px solid color-mix(in srgb, var(--evidence-ai-narrative) 30%, transparent);
}

.msg__bubble {
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  border-top-left-radius: 4px;
  background: #fff;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

.msg__text {
  font-size: var(--fs-body);
  line-height: var(--lh-body-l);
  color: var(--color-ink-900);
}

/* ---------- 异常状态 ---------- */
.msg__state {
  display: flex;
  gap: var(--sp-3);
  align-items: flex-start;
}
.msg__state--empty {
  color: var(--color-ink-500);
}
.msg__state--warn {
  color: var(--color-warning);
}
.msg__state-title {
  font-size: var(--fs-body-s);
  font-weight: 600;
  margin-bottom: 3px;
}
.msg__state-text {
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-s);
  color: var(--color-ink-700);
}

/* ---------- 来源层级标注 ---------- */
.msg__tier {
  margin-top: var(--sp-2);
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  padding-left: var(--sp-1);
}
.msg__tier.is-warn {
  color: var(--color-warning);
}

/* ---------- 引用 chips ---------- */
.msg__cites,
.msg__related {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: var(--sp-3);
}
.msg__cites-label {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.msg__cite,
.msg__rel-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-caption);
  border: 1px solid var(--color-border);
  background: var(--color-paper-50);
  color: var(--color-ink-700);
  text-decoration: none;
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.msg__cite:hover,
.msg__rel-chip:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.msg__cite-num {
  width: 14px;
  height: 14px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--color-paper-200);
  font-size: 9px;
}

.msg__actions {
  margin-top: var(--sp-2);
}
.msg__action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 0;
  background: transparent;
  padding: 2px 0;
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.msg__action:hover {
  color: var(--chapter-accent);
}
</style>
