<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GlobalHeader from '@/components/global/GlobalHeader.vue'
import KnowledgeGraph from '@/components/graph/KnowledgeGraph.vue'
import RelationEvidencePanel from '@/components/source/RelationEvidencePanel.vue'
import EntityDrawer from '@/components/entity/EntityDrawer.vue'
import SourceDrawer from '@/components/source/SourceDrawer.vue'
import DsButton from '@/components/ds/DsButton.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
import { useGraphStore } from '@/stores/graph'
import { useEntityStore } from '@/stores/entity'
import { useExplorationStore } from '@/stores/exploration'
import { useGameStore } from '@/stores/game'
import type { ChapterSlug } from '@/types'

/**
 * C07 关系图谱页（设计系统 §38 / §41）
 *
 * 默认以当前实体为中心显示 1-hop。
 * 左侧 9 列画布，右侧 3 列节点信息。
 * 「为什么有这条关系？」是本页可信度的关键功能。
 */
const route = useRoute()
const router = useRouter()
const chapterStore = useChapterStore()
const graphStore = useGraphStore()
const entityStore = useEntityStore()
const exploration = useExplorationStore()
const game = useGameStore()

const slug = computed(() => route.params.slug as string)
const chapter = computed(() => chapterStore.current)
/** 模板里 chapter 可能为 null，单独取一份非空的 chapter id 供抽屉调用 */
const chapterId = computed(() => chapter.value?.id ?? '')
const loading = ref(true)

const centerId = computed(() => {
  const q = route.query.entity
  if (typeof q === 'string' && q) return q
  return chapterStore.selectedEntityId || chapter.value?.core_entity_ids?.[0] || ''
})

const selectedNode = computed(
  () => graphStore.nodes.find((n) => n.id === graphStore.selectedNodeId) ?? null,
)

/** 当前选中节点相关的边 —— 用于展示「为什么有这条关系？」 */
const selectedEdge = computed(() => {
  const id = graphStore.selectedNodeId
  if (!id) return null
  return graphStore.edges.find((e) => e.source === id || e.target === id) ?? null
})

onMounted(async () => {
  const id = SLUG_TO_ID[slug.value as keyof typeof SLUG_TO_ID]
  if (!id) return
  if (chapterStore.current?.id !== id) await chapterStore.loadChapter(id)
  await exploration.ensureSession(id)
  game.mark(slug.value as ChapterSlug, 'GRAPH')
  if (slug.value === 'yuan') exploration.track('YUAN_GRAPH_OPENED', {}, id)

  if (centerId.value) {
    try {
      await graphStore.load(centerId.value, id)
    } finally {
      loading.value = false
    }
  } else {
    loading.value = false
  }
})

watch(
  () => route.query.entity,
  (id) => {
    if (typeof id === 'string' && id && id !== graphStore.centerId) {
      graphStore.reset()
      void graphStore.load(id, chapter.value?.id)
    }
  },
)

function backToScene() {
  void router.push({
    path: `/chapter/${slug.value}/scene`,
    query: graphStore.selectedNodeId ? { entity: graphStore.selectedNodeId } : undefined,
  })
}

async function onNodeSelect(id: string) {
  graphStore.selectNode(id)
  if (selectedEdge.value) {
    await graphStore.loadEvidence(selectedEdge.value.id, chapter.value?.id)
    if (slug.value === 'yuan') {
      exploration.track('YUAN_RELATION_EVIDENCE_VIEWED', { relation_id: selectedEdge.value.id }, chapter.value?.id)
    }
  }
  void router.replace({ query: { ...route.query, entity: id } })
}

async function onExpand(id: string) {
  await graphStore.expand(id, chapter.value?.id)
}

async function openDetail(id: string) {
  await entityStore.load(id, chapter.value?.id)
}
</script>

<template>
  <div v-if="chapter" class="page">
    <GlobalHeader dark />

    <main class="cg page-body">
      <header class="cg__bar">
        <button class="cg__back" type="button" @click="backToScene">
          <span aria-hidden="true">←</span>
          <span>返回场景</span>
        </button>
        <span class="cg__hint">点击节点查看关系，双击展开一层</span>
        <div class="cg__tools">
          <button
            class="cg__tool"
            :class="{ 'is-on': graphStore.onlyMine }"
            type="button"
            @click="graphStore.onlyMine = !graphStore.onlyMine"
          >
            <DsIcon name="compass" :size="14" />
            <span>仅看我的节点</span>
          </button>
          <button class="cg__tool" type="button" @click="graphStore.reset(centerId)">
            <DsIcon name="refresh" :size="14" />
            <span>重置视图</span>
          </button>
        </div>
      </header>

      <div class="cg__layout">
        <div class="cg__canvas">
          <div v-if="loading" class="cg__state">正在加载关系图谱……</div>
          <div v-else-if="!graphStore.nodes.length" class="cg__state cg__state--empty">
            <p>这个节点暂时没有可展开的关系。</p>
            <DsButton variant="secondary" @click="backToScene">返回场景</DsButton>
          </div>
          <KnowledgeGraph
            v-else
            @select="onNodeSelect"
            @dblclick="onExpand"
          />
        </div>

        <aside class="cg__side">
          <template v-if="selectedNode">
            <p class="cg__node-type">{{ selectedNode.type }}</p>
            <h2 class="cg__node-name">{{ selectedNode.name }}</h2>
            <p v-if="selectedNode.short_summary" class="cg__node-summary">
              {{ selectedNode.short_summary }}
            </p>

            <div class="cg__node-actions">
              <DsButton variant="secondary" block @click="openDetail(selectedNode.id)">
                <span>查看详情</span>
              </DsButton>
              <DsButton variant="ghost" block @click="onExpand(selectedNode.id)">
                <DsIcon name="layers" :size="15" />
                <span>展开一层</span>
              </DsButton>
            </div>

            <RelationEvidencePanel />
          </template>

          <div v-else class="cg__side-empty">
            <DsIcon name="nodes" :size="26" />
            <p>点击任意节点，查看它的信息与关系依据</p>
          </div>
        </aside>
      </div>
    </main>

    <EntityDrawer
      :chapter-id="chapter.id"
      @ask="$router.push(`/chapter/${slug}/chat?entity=${selectedNode?.id || ''}`)"
      @graph="(id) => onNodeSelect(id)"
      @sources="(id) => entityStore.openSources(id, chapterId)"
      @select="openDetail"
      @close="entityStore.close()"
    />
    <SourceDrawer />
  </div>
</template>

<style scoped>
.cg {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding-top: var(--sp-4);
  padding-bottom: var(--sp-4);
  height: calc(100vh - var(--header-h));
  min-height: 0;
}

.cg__bar {
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--sp-4);
}
.cg__back {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  border: 0;
  background: transparent;
  padding: 4px 0;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  flex: none;
}
.cg__back:hover {
  color: var(--chapter-accent);
}
.cg__hint {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.cg__tools {
  margin-left: auto;
  display: flex;
  gap: var(--sp-2);
}
.cg__tool {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
}
.cg__tool:hover,
.cg__tool.is-on {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}

.cg__layout {
  flex: 1;
  display: grid;
  grid-template-columns: 9fr 3fr;
  /* 必须显式声明行高：默认 grid 行是 auto，会缩到内容高度，
     导致画布只占页面一半、下方留出大片空白。
     minmax(0, 1fr) 里的 0 是必需的，否则子元素 min-height 会把行撑开。 */
  grid-template-rows: minmax(0, 1fr);
  gap: var(--gap-module);
  min-height: 0;
}

.cg__canvas {
  position: relative;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
  min-height: 0;
}

.cg__state {
  height: 100%;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: var(--sp-4);
  color: var(--color-ink-500);
  font-size: var(--fs-body-s);
  text-align: center;
}

.cg__side {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-paper-50);
  overflow-y: auto;
}
.cg__node-type {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  letter-spacing: 0.08em;
}
.cg__node-name {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  line-height: var(--lh-h2);
}
.cg__node-summary {
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-l);
  color: var(--color-ink-700);
}
.cg__node-actions {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.cg__side-empty {
  margin: auto;
  text-align: center;
  color: var(--color-ink-500);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-3);
  font-size: var(--fs-body-s);
}

@media (max-width: 1200px) {
  .cg__layout {
    grid-template-columns: 1fr;
  }
}
</style>
