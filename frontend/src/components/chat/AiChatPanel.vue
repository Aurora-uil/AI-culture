<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import DsIcon from '../ds/DsIcon.vue'
import DsButton from '../ds/DsButton.vue'
import DsSkeleton from '../ds/DsSkeleton.vue'
import ChatMessage from './ChatMessage.vue'
import AiStatusIndicator from './AiStatusIndicator.vue'
import EvidenceBadge from '../global/EvidenceBadge.vue'
import { useChatStore } from '@/stores/chat'

/**
 * AI 对话面板（设计系统 §29 / §30 / §33 / §34）
 *
 * 固定显示 AI 身份说明 —— 这是产品可信度的核心，不可省略。
 * 文物角色直接显示文物本身，不给文物画眼睛嘴巴。
 * 当代章节不模拟在世传承人，使用「数字工坊讲述者」。
 */
const props = defineProps<{
  chapterId: string
  characterId: string
  currentEntityId?: string | null
  /** 左栏角色视觉（文物图 / 人物形象） */
  characterImage?: string | null
}>()

const emit = defineEmits<{
  (e: 'source', sourceId: string): void
  (e: 'explore', entityId: string): void
}>()

const chat = useChatStore()
const input = ref('')
const scroller = ref<HTMLElement | null>(null)

watch(
  () => [props.chapterId, props.characterId],
  () => {
    void chat.init(props.chapterId, props.characterId, props.currentEntityId ?? undefined)
  },
  { immediate: true },
)

watch(
  () => props.currentEntityId,
  (id) => {
    chat.currentEntityId = id ?? null
  },
)

watch(
  () => [chat.messages.length, chat.status],
  async () => {
    await nextTick()
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
  },
)

async function send() {
  const q = input.value.trim()
  if (!q) return
  input.value = ''
  await chat.ask(q, props.chapterId)
}

function onKeydown(e: KeyboardEvent) {
  // Enter 发送，Shift+Enter 换行
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    void send()
  }
}

const disclaimer = computed(
  () =>
    chat.character?.disclaimer ||
    '本角色为基于历史资料构建的AI数字叙事角色，其第一人称表达属于数字化叙事重构，并非历史人物真实原话。',
)
</script>

<template>
  <div class="chat">
    <!-- 左栏：角色视觉与说明（4 列） -->
    <aside class="chat__side">
      <div class="chat__portrait">
        <img
          v-if="characterImage"
          :src="characterImage"
          :alt="chat.character?.name || '角色'"
        />
        <div v-else class="chat__portrait-empty">
          <DsIcon
            :name="chat.character?.character_type === 'person' ? 'person' : 'artifact'"
            :size="34"
          />
        </div>
      </div>

      <h2 class="chat__name">{{ chat.character?.name || 'AI数字角色' }}</h2>
      <p v-if="chat.character?.subtitle" class="chat__subtitle">
        {{ chat.character.subtitle }}
      </p>
      <div class="chat__badge">
        <EvidenceBadge type="ai_narrative" size="m" />
      </div>

      <!-- AI 身份说明：固定显示 -->
      <p class="chat__disclaimer">{{ disclaimer }}</p>

      <div v-if="currentEntityId" class="chat__context">
        <span class="chat__context-label">当前上下文</span>
        <span class="chat__context-value">{{ currentEntityId }}</span>
      </div>
    </aside>

    <!-- 右栏：对话（8 列） -->
    <section class="chat__main">
      <header class="chat__toolbar">
        <span class="chat__toolbar-title">与「{{ chat.character?.name || '角色' }}」对话</span>
        <div class="chat__modes" role="group" aria-label="回答模式">
          <button
            class="chat__mode"
            :class="{ 'is-on': chat.answerMode === 'narrative' }"
            type="button"
            @click="chat.setMode('narrative')"
          >
            叙事模式
          </button>
          <button
            class="chat__mode"
            :class="{ 'is-on': chat.answerMode === 'factual' }"
            type="button"
            @click="chat.setMode('factual')"
          >
            史实模式
          </button>
        </div>
      </header>

      <div ref="scroller" class="chat__scroll">
        <!-- 开场 -->
        <div v-if="!chat.messages.length" class="chat__hello">
          <p class="chat__hello-text">
            {{ chat.character?.name || '你好' }}：你可以从我的石刻、文字和历史背景开始问起。
          </p>

          <div v-if="chat.recommended.length" class="chat__chips">
            <p class="chat__chips-label">推荐问题</p>
            <button
              v-for="q in chat.recommended.slice(0, 4)"
              :key="q.id"
              class="chat__chip"
              type="button"
              @click="chat.ask(q.text, chapterId)"
            >
              {{ q.text }}
            </button>
          </div>
        </div>

        <ChatMessage
          v-for="m in chat.messages"
          :key="m.id"
          :message="m"
          :character-name="chat.character?.name"
          @source="emit('source', $event)"
          @explore="emit('explore', $event)"
          @regenerate="chat.regenerate($event)"
        />

        <AiStatusIndicator v-if="chat.isBusy && chat.statusText" :text="chat.statusText" />
        <DsSkeleton v-else-if="chat.streaming" variant="message" />
      </div>

      <!-- 输入区 -->
      <footer class="chat__composer">
        <textarea
          v-model="input"
          class="chat__input"
          rows="1"
          placeholder="输入你想问的问题……"
          :disabled="chat.isBusy"
          @keydown="onKeydown"
        />
        <DsButton
          v-if="chat.streaming"
          variant="secondary"
          @click="chat.stop()"
        >
          <DsIcon name="stop" :size="15" />
          <span>停止</span>
        </DsButton>
        <DsButton
          v-else
          variant="primary"
          :disabled="!input.trim()"
          @click="send"
        >
          <DsIcon name="send" :size="15" />
          <span>发送</span>
        </DsButton>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.chat {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: var(--gap-module);
  height: 100%;
  min-height: 0;
}

/* ---------- 左栏 ---------- */
.chat__side {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  min-width: 0;
  padding-top: var(--sp-2);
}
.chat__portrait {
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-paper-100);
  border: 1px solid var(--color-border);
  aspect-ratio: 1 / 1;
}
.chat__portrait img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.chat__portrait-empty {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: var(--color-ink-500);
  opacity: 0.45;
}

.chat__name {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  line-height: var(--lh-h2);
}
.chat__subtitle {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
}
.chat__badge {
  margin-top: var(--sp-1);
}
.chat__disclaimer {
  font-size: var(--fs-caption);
  line-height: var(--lh-body-s);
  color: var(--color-ink-500);
  padding: var(--sp-3);
  border-radius: var(--radius-btn);
  background: var(--color-paper-100);
  border-left: 3px solid color-mix(in srgb, var(--evidence-ai-narrative) 55%, transparent);
}
.chat__context {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.chat__context-value {
  color: var(--color-ink-700);
}

/* ---------- 右栏 ---------- */
.chat__main {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--color-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
}

.chat__toolbar {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-6);
  border-bottom: 1px solid var(--color-border);
}
.chat__toolbar-title {
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
}

.chat__modes {
  display: flex;
  gap: 2px;
  padding: 2px;
  border-radius: var(--radius-btn);
  background: var(--color-paper-200);
}
.chat__mode {
  border: 0;
  background: transparent;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
  transition:
    background-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.chat__mode.is-on {
  background: #fff;
  color: var(--chapter-accent);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(39, 34, 27, 0.08);
}

.chat__scroll {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-6);
  min-height: 0;
}

.chat__hello {
  margin-bottom: var(--sp-8);
}
.chat__hello-text {
  font-size: var(--fs-body);
  color: var(--color-ink-700);
  margin-bottom: var(--sp-6);
}

.chat__chips-label {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  margin-bottom: var(--sp-3);
}
.chat__chips {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sp-2);
}
.chat__chip {
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  text-align: left;
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.chat__chip:hover {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}

.chat__composer {
  flex: none;
  display: flex;
  align-items: flex-end;
  gap: var(--sp-3);
  padding: var(--sp-4) var(--sp-6);
  border-top: 1px solid var(--color-border);
  background: #fff;
}
.chat__input {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  padding: 11px var(--sp-4);
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: var(--color-paper-50);
  font-family: inherit;
  font-size: var(--fs-body);
  line-height: 1.5;
  color: var(--color-ink-900);
}
.chat__input:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--chapter-accent) 45%, transparent);
  outline-offset: 2px;
  border-color: var(--chapter-accent);
}

@media (max-width: 1200px) {
  .chat {
    grid-template-columns: 1fr;
  }
  .chat__side {
    display: none;
  }
}
</style>
