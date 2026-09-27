<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import GlobalHeader from '@/components/global/GlobalHeader.vue'
import KnowledgeGraph from '@/components/graph/KnowledgeGraph.vue'
import RelationEvidencePanel from '@/components/source/RelationEvidencePanel.vue'
import DsButton from '@/components/ds/DsButton.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import { useGraphStore } from '@/stores/graph'
import { getGraphOverview } from '@/api/endpoints'

/**
 * G02 总知识图谱（设计系统 §42 / §43）
 *
 * 总图谱不是把六章全部节点一次铺开。
 * 第一层只显示：六章 + 每章 3–5 个核心节点 + 跨时代策展主题。
 * 中心「中华文化长期联系」是 curatorial node，不是古代历史实体 —— 必须通过图例明确。
 */
const store = useGraphStore()
const loading = ref(true)
const failed = ref(false)

onMounted(async () => {
  try {
    const overview = await getGraphOverview()
    store.nodes = overview.nodes.map((n) => ({ ...n, is_center: n.id === overview.center_entity_id }))
    store.edges = overview.edges
    store.centerId = overview.center_entity_id
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
})

const selected = computed(() => store.nodes.find((n) => n.id === store.selectedNodeId) ?? null)

function onSelect(id: string) {
  store.selectNode(id)
}

function onExpand(id: string) {
  void store.expand(id)
}

/** 点击某章跳进该章图谱 */
function openChapterGraph(id: string) {
  const node = store.nodes.find((n) => n.id === id)
  if (node?.type === 'Period') {
    const slug = id.replace('period_', '').replace('_yuntai', '')
    window.location.href = `/chapter/${slug}/graph?entity=${id}`
  }
}
</script>

<template>
  <div class="page">
    <GlobalHeader />

    <main class="tg page-body">
      <header class="tg__head">
        <div>
          <h1 class="tg__title tt-h1">中华文化关系图谱</h1>
          <p class="tg__sub">
            六章内容在此汇合。中心节点「中华文化长期联系」是策展关联，不是古代历史实体。
          </p>
        </div>
        <div class="tg__tools">
          <DsButton variant="ghost" @click="store.reset()">
            <DsIcon name="refresh" :size="15" />
            <span>重置视图</span>
          </DsButton>
        </div>
      </header>

      <div class="tg__layout">
        <div class="tg__canvas-wrap">
          <div v-if="loading" class="tg__state">正在加载图谱……</div>
          <div v-else-if="failed" class="tg__state tg__state--empty">
            <p class="tg__state-title">图谱加载失败</p>
            <p class="tg__state-text">请确认后端服务已启动，然后重试。</p>
            <DsButton variant="secondary" @click="$router.go(0)">重新加载</DsButton>
          </div>
          <KnowledgeGraph v-else @select="onSelect" @dblclick="onExpand" />
        </div>

        <!-- 右栏 3 列：当前节点 -->
        <aside class="tg__side">
          <template v-if="selected">
            <p class="tg__side-type">{{ selected.type }}</p>
            <h2 class="tg__side-title">{{ selected.name }}</h2>
            <p v-if="selected.short_summary" class="tg__side-summary">
              {{ selected.short_summary }}
            </p>

            <div class="tg__side-actions">
              <DsButton
                variant="secondary"
                block
                @click="$router.push(`/chapter/${(selected as any).chapter_slug || ''}/graph?entity=${selected.id}`)"
              >
                <span>进入该章图谱</span>
              </DsButton>
              <DsButton variant="ghost" block @click="onExpand(selected.id)">
                <DsIcon name="layers" :size="15" />
                <span>展开一层</span>
              </DsButton>
            </div>

            <RelationEvidencePanel class="tg__evidence" />
          </template>

          <div v-else class="tg__side-empty">
            <DsIcon name="nodes" :size="26" />
            <p>点击任意节点查看它的信息与关系</p>
          </div>
        </aside>
      </div>
    </main>
  </div>
</template>

<style scoped>
.tg {
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  padding-top: var(--sp-8);
  padding-bottom: var(--sp-8);
  min-height: calc(100vh - var(--header-h));
}

.tg__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-6);
}
.tg__title {
  color: var(--color-ink-900);
}
.tg__sub {
  margin-top: var(--sp-2);
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  max-width: 620px;
}
.tg__tools {
  display: flex;
  gap: var(--sp-2);
  flex: none;
}

.tg__layout {
  flex: 1;
  display: grid;
  grid-template-columns: 9fr 3fr;
  /* 同上：显式行高，否则画布会被内容高度决定，撑不满页面 */
  grid-template-rows: minmax(0, 1fr);
  gap: var(--gap-module);
  min-height: 0;
}

.tg__canvas-wrap {
  position: relative;
  min-height: 520px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-paper-100);
}

.tg__state {
  height: 100%;
  display: grid;
  place-items: center;
  gap: var(--sp-3);
  color: var(--color-ink-500);
  font-size: var(--fs-body-s);
  align-content: center;
}
.tg__state-title {
  font-size: var(--fs-body);
  color: var(--color-ink-700);
}
.tg__state-text {
  font-size: var(--fs-body-s);
  margin-bottom: var(--sp-4);
}

/* ---------- 右栏 ---------- */
.tg__side {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-paper-50);
  overflow-y: auto;
}

.tg__side-type {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
  letter-spacing: 0.08em;
}
.tg__side-title {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  line-height: var(--lh-h2);
}
.tg__side-summary {
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-l);
  color: var(--color-ink-700);
}
.tg__side-actions {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  margin-top: var(--sp-2);
}
.tg__evidence {
  margin-top: var(--sp-2);
}

.tg__side-empty {
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
  .tg__layout {
    grid-template-columns: 1fr;
  }
}
</style>
