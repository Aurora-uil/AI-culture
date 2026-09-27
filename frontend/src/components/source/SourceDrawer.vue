<script setup lang="ts">
import DsDrawer from '../ds/DsDrawer.vue'
import DsSkeleton from '../ds/DsSkeleton.vue'
import SourceCard from './SourceCard.vue'
import { useEntityStore } from '@/stores/entity'

/**
 * 史料证据抽屉（设计系统 §35）
 * 宽度 520px，可叠在实体抽屉之上；关闭后回到实体（§54 / §85）。
 */
const store = useEntityStore()
</script>

<template>
  <!--
    close-on-back=false：来源抽屉是叠在实体抽屉之上的次级抽屉（设计系统 §54）。
    实体抽屉已经占了一条 history 记录，这里再 pushState 会让浏览器 Back
    需要按两次才能退出，比赛演示时容易让操作者困惑。
  -->
  <DsDrawer
    :open="store.sourceDrawerOpen"
    width="source"
    title="史料依据"
    stacked
    :close-on-back="false"
    @close="store.closeSources()"
  >
    <template v-if="store.sourcesLoading">
      <DsSkeleton variant="source" :rows="2" />
    </template>

    <template v-else-if="store.sources.length">
      <p class="sd__count">
        当前内容：{{ store.current?.display_name || store.current?.name }}
        <span class="sd__count-sep">·</span>
        共 {{ store.sources.length }} 条资料
      </p>

      <SourceCard
        v-for="(s, i) in store.sources"
        :key="s.id"
        :source="s"
        :index="i + 1"
      />
    </template>

    <!-- 空状态（设计系统 §63）：简洁图标 + 一句解释 + 一个下一步 -->
    <div v-else class="sd__empty">
      <p class="sd__empty-text">这段内容暂时没有绑定已审核的史料来源。</p>
      <p class="sd__empty-sub">你可以返回继续探索其它节点。</p>
    </div>
  </DsDrawer>
</template>

<style scoped>
.sd__count {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  margin-bottom: var(--sp-5, 20px);
}
.sd__count-sep {
  margin: 0 6px;
}

.sd__empty {
  padding: var(--sp-12) var(--sp-6);
  text-align: center;
}
.sd__empty-text {
  font-size: var(--fs-body);
  color: var(--color-ink-700);
  margin-bottom: var(--sp-2);
}
.sd__empty-sub {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
}
</style>
