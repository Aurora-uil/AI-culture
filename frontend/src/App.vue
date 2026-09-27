<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { useGameStore } from '@/stores/game'
import GameInteractionFx from '@/components/game/GameInteractionFx.vue'

const route = useRoute()
const session = useSessionStore()
const game = useGameStore()

/** 章节色通过 data-chapter 下发（设计系统 §6） */
const chapterKey = computed(() => (route.meta.chapterKey as string) || '')

onMounted(() => {
  session.bootstrap()
  game.bootstrap()
})
</script>

<template>
  <div class="app-root" :data-chapter="chapterKey || undefined">
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <RouterView v-slot="{ Component }">
      <Transition name="fade" mode="out-in">
        <div id="main-content" :key="route.path" class="app-view" tabindex="-1">
          <component :is="Component" />
        </div>
      </Transition>
    </RouterView>
    <GameInteractionFx />
  </div>
</template>

<style scoped>
/*
 * #app 的高度是 100%，但 .app-root 若只写 min-height: 100%，
 * 子元素再写 min-height: 100% 会因为「百分比高度遇到不确定的父高度」而失效，
 * 表现为整页只有内容高、图谱/场景类页面撑不满视口。
 * 因此这里建立一条确定的高度链：.app-root 撑满视口并作为纵向 flex 容器，
 * .page 用 flex: 1 继承剩余高度。
 */
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}
.app-view {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.skip-link {
  position: fixed;
  z-index: 10002;
  top: 10px;
  left: 12px;
  padding: 9px 14px;
  border: 1px solid var(--color-scroll-gold);
  border-radius: 4px;
  background: var(--color-paper-50);
  color: var(--color-mineral-800);
  box-shadow: var(--shadow-card);
  transform: translateY(-160%);
  transition: transform var(--dur-fast) ease;
}
.skip-link:focus-visible { transform: translateY(0); }
</style>
