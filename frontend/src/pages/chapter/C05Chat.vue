<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GlobalHeader from '@/components/global/GlobalHeader.vue'
import AiChatPanel from '@/components/chat/AiChatPanel.vue'
import SourceDrawer from '@/components/source/SourceDrawer.vue'
import EntityDrawer from '@/components/entity/EntityDrawer.vue'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
import { useChatStore } from '@/stores/chat'
import { useEntityStore } from '@/stores/entity'
import { useExplorationStore } from '@/stores/exploration'
import { useGameStore } from '@/stores/game'
import type { ChapterSlug } from '@/types'

/**
 * C05 AI 对话页（设计系统 §29）
 *
 * 布局：左 4 列角色视觉与说明，右 8 列聊天。
 * 从实体详情「问它一个问题」进入时，当前实体作为上下文带入。
 */
const route = useRoute()
const router = useRouter()
const chapterStore = useChapterStore()
const entityStore = useEntityStore()
const exploration = useExplorationStore()
const game = useGameStore()

const slug = computed(() => route.params.slug as string)
const chapterId = computed(
  () => SLUG_TO_ID[slug.value as keyof typeof SLUG_TO_ID] ?? null,
)
// 路由切章时 chapterStore 可能短暂保留上一章；此时不渲染旧章聊天面板，
// 避免上一章消息在新章节加载完成前闪现。
const chapter = computed(() =>
  chapterStore.current?.id === chapterId.value ? chapterStore.current : null,
)
const contextEntityId = ref<string | null>(null)
const chat = useChatStore()
const yuanAiTracked = ref(false)
const taskHallPath = computed(() => `/chapter/${slug.value}`)
const backLabel = computed(() => `返回${chapter.value?.era ?? ''}任务大厅`)

const CHAPTER_CHAT_IMAGES: Record<ChapterSlug, string> = {
  han: '/assets/han/han-route-scene-v2.png',
  'northern-wei': '/assets/wei/yungang-cave20-original.jpg',
  tang: '/assets/tang/bunian-original.jpg',
  yuan: '/assets/yuan/yuntai-east-wall-original.jpg',
  qing: '/assets/qing/qing-migration-photoreal-v2.png',
  contemporary: '/assets/contemporary/qiang-workshop-photoreal-v2.png',
}

/** 元代：第一条 AI 完成回答即记为自由追问完成（只记一次，不读回答内容） */
watch(
  () => chat.messages.length,
  () => {
    if (slug.value !== 'yuan' || yuanAiTracked.value) return
    const done = chat.messages.some((m: any) => m.role === 'assistant' && (m.status === 'DONE' || (m.content && m.content.length > 0)))
    if (done) {
      yuanAiTracked.value = true
      exploration.track('YUAN_AI_QUESTION_COMPLETED', {}, chapter.value?.id)
    }
  },
)

onMounted(async () => {
  const id = chapterId.value
  if (!id) return
  if (chapterStore.current?.id !== id) await chapterStore.loadChapter(id)
  await exploration.ensureSession(id)
  game.mark(slug.value as ChapterSlug, 'CHAT')

  const q = route.query.entity
  if (typeof q === 'string' && q) contextEntityId.value = q
})

function backToScene() {
  void router.push(taskHallPath.value)
}

function onSource(sourceId: string) {
  const entityId = contextEntityId.value || chapterStore.selectedEntityId
  if (entityId) void entityStore.openSources(entityId, chapter.value?.id)
  if (slug.value === 'yuan') exploration.track('YUAN_SOURCE_VIEWED', { entity_id: sourceId }, chapter.value?.id)
}

function onExplore(entityId: string) {
  void entityStore.load(entityId, chapter.value?.id)
}

const characterImage = computed(() => {
  // 文物角色直接显示文物本身，不给文物画眼睛嘴巴
  if (contextEntityId.value && entityStore.current?.id === contextEntityId.value) {
    return entityStore.current.image_url ?? CHAPTER_CHAT_IMAGES[slug.value as ChapterSlug] ?? null
  }
  return CHAPTER_CHAT_IMAGES[slug.value as ChapterSlug] ?? null
})
</script>

<template>
  <div v-if="chapter" class="page">
    <GlobalHeader dark />

    <main class="cc page-body">
      <header class="cc__bar">
        <button class="cc__back" type="button" @click="backToScene">
          <span aria-hidden="true">←</span>
          <span>{{ backLabel }}</span>
        </button>
        <span class="cc__hint">
          回答会先联网检索，再结合已审核史料整理，可点击来源查看依据
        </span>
      </header>

      <section class="cc__body">
        <AiChatPanel
          :chapter-id="chapter.id"
          :character-id="chapter.ai_character_id"
          :current-entity-id="contextEntityId"
          :character-image="characterImage"
          @source="onSource"
          @explore="onExplore"
        />
      </section>
    </main>

    <SourceDrawer />
    <EntityDrawer :chapter-id="chapter.id" @close="entityStore.close()" />
  </div>
</template>

<style scoped>
.cc {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding-top: var(--sp-4);
  height: calc(100vh - var(--header-h));
  min-height: 0;
}

.cc__bar {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
}
.cc__back {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  border: 0;
  background: transparent;
  padding: 4px 0;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
}
.cc__back:hover {
  color: var(--chapter-accent);
}
.cc__hint {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

.cc__body {
  flex: 1;
  min-height: 0;
}
</style>
