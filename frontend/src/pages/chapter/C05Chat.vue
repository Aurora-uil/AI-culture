<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GlobalHeader from '@/components/global/GlobalHeader.vue'
import AiChatPanel from '@/components/chat/AiChatPanel.vue'
import SourceDrawer from '@/components/source/SourceDrawer.vue'
import EntityDrawer from '@/components/entity/EntityDrawer.vue'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
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
const chapter = computed(() => chapterStore.current)
const contextEntityId = ref<string | null>(null)

onMounted(async () => {
  const id = SLUG_TO_ID[slug.value as keyof typeof SLUG_TO_ID]
  if (!id) return
  if (chapterStore.current?.id !== id) await chapterStore.loadChapter(id)
  await exploration.ensureSession(id)
  game.mark(slug.value as ChapterSlug, 'CHAT')

  const q = route.query.entity
  if (typeof q === 'string' && q) contextEntityId.value = q
})

function backToScene() {
  void router.push({
    path: `/chapter/${slug.value}/scene`,
    query: contextEntityId.value ? { entity: contextEntityId.value } : undefined,
  })
}

function onSource(sourceId: string) {
  const entityId = contextEntityId.value || chapterStore.selectedEntityId
  if (entityId) void entityStore.openSources(entityId, chapter.value?.id)
}

function onExplore(entityId: string) {
  void entityStore.load(entityId, chapter.value?.id)
}

const characterImage = computed(() => {
  // 文物角色直接显示文物本身，不给文物画眼睛嘴巴
  return entityStore.current?.image_url ?? null
})
</script>

<template>
  <div v-if="chapter" class="page">
    <GlobalHeader dark />

    <main class="cc page-body">
      <header class="cc__bar">
        <div class="cc__identity">
          <span>ARCHIVE DIALOGUE · 05</span>
          <strong>向档案发问</strong>
        </div>
        <div class="cc__actions">
          <span class="cc__hint">回答基于已审核史料检索生成 · 来源可追溯</span>
          <button class="cc__back" type="button" @click="backToScene">
            <span aria-hidden="true">←</span>
            <span>返回场景</span>
          </button>
        </div>
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
  padding-top: 18px;
  padding-bottom: 18px;
  height: calc(100vh - var(--header-h));
  min-height: 0;
}

.cc__bar {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  min-height: 54px;
  padding: 0 2px 13px;
  border-bottom: 1px solid rgba(40,95,97,.14);
}
.cc__identity{display:flex;align-items:baseline;gap:13px}.cc__identity span{font-size:8px;letter-spacing:.17em;color:var(--color-scroll-gold)}.cc__identity strong{font-family:var(--font-display);font-size:22px;font-weight:500;color:var(--color-mineral-800)}
.cc__actions{display:flex;align-items:center;gap:18px}
.cc__back {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  border: 1px solid rgba(40,95,97,.2);
  background: rgba(255,255,255,.5);
  padding: 7px 11px;
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
  overflow:hidden;
  border:1px solid rgba(40,95,97,.18);
  background:rgba(250,249,241,.72);
  box-shadow:0 18px 55px rgba(45,76,70,.09),inset 0 0 0 5px rgba(255,255,255,.28);
}
.page{background:radial-gradient(circle at 88% 2%,rgba(195,163,91,.11),transparent 28%),linear-gradient(135deg,#edf2e9,#e2ece5)}
@media(max-width:720px){.cc__identity span,.cc__hint{display:none}.cc__identity strong{font-size:18px}.cc__actions{gap:8px}.cc{padding-top:10px;padding-bottom:10px}}
</style>
