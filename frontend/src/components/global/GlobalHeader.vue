<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import DsIcon from '../ds/DsIcon.vue'
import { useChapterStore } from '@/stores/chapter'
import { useSessionStore } from '@/stores/session'

/**
 * 全局顶部导航（设计系统 §14）
 *
 * 左侧：Logo + 项目名 + 章节面包屑
 * 右侧：全局知识图谱 / 我的探索 / 项目说明 / 全屏
 *
 * 不放：登录 / 商城 / 消息 / 个人头像 —— 比赛版不需要。
 */
withDefaults(defineProps<{ showBreadcrumb?: boolean; dark?: boolean }>(), {
  showBreadcrumb: true,
  dark: false,
})

const router = useRouter()
const chapterStore = useChapterStore()
const session = useSessionStore()

const breadcrumb = computed(() => {
  const c = chapterStore.current
  if (!c) return null
  return { era: c.era, keyword: c.keyword, title: c.title }
})

function toggleFullscreen() {
  if (!document.fullscreenElement) void document.documentElement.requestFullscreen?.()
  else void document.exitFullscreen?.()
}
</script>

<template>
  <header class="g-header" :class="{ 'g-header--dark': dark }">
    <div class="g-header__left">
      <RouterLink to="/timeline" class="g-header__brand">
        <span class="g-header__mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" width="26" height="26">
            <circle cx="16" cy="16" r="10.5" fill="none" stroke="currentColor" stroke-width="1.6" />
            <circle cx="16" cy="16" r="5.5" fill="none" stroke="currentColor" stroke-width="1.4" />
            <circle cx="16" cy="16" r="2" fill="currentColor" />
            <path
              d="M16 3.5v5M16 23.5v5M3.5 16h5M23.5 16h5"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
            />
          </svg>
        </span>
        <span class="g-header__name">同心千年</span>
      </RouterLink>

      <nav v-if="showBreadcrumb && breadcrumb" class="g-header__crumb" aria-label="章节位置">
        <DsIcon name="chevron-right" :size="14" class="g-header__crumb-sep" />
        <span class="g-header__crumb-era">{{ breadcrumb.era }}</span>
        <span class="g-header__crumb-dot">·</span>
        <span class="g-header__crumb-keyword">{{ breadcrumb.keyword }}</span>
        <span class="g-header__crumb-sep-text">/</span>
        <span class="g-header__crumb-title">{{ breadcrumb.title }}</span>
      </nav>
    </div>

    <div class="g-header__right">
      <span
        v-if="session.health && session.demoFallback"
        class="g-header__mode"
        title="未配置大模型 API Key，AI 回答来自已审核的预设问答库。"
      >
        演示保障模式
      </span>
      <span
        v-else-if="session.healthChecked && !session.health"
        class="g-header__mode g-header__mode--offline"
        title="内容服务未连接。章节目录、元代场景和游戏存档正在使用内置演示数据。"
      >
        本地演示
      </span>

      <RouterLink to="/graph" class="g-header__link">
        <DsIcon name="nodes" :size="16" />
        <span>知识图谱</span>
      </RouterLink>
      <RouterLink to="/journey" class="g-header__link">
        <DsIcon name="compass" :size="16" />
        <span>我的探索</span>
      </RouterLink>
      <RouterLink to="/about" class="g-header__link">
        <DsIcon name="info" :size="16" />
        <span>项目说明</span>
      </RouterLink>

      <button class="g-header__icon-btn" type="button" aria-label="全屏" @click="toggleFullscreen">
        <DsIcon name="grid" :size="16" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.g-header {
  position: sticky;
  top: 0;
  z-index: var(--z-hud);
  height: var(--header-h);
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-6);
  padding: 0 var(--pad-page-x);
  background: rgba(250, 248, 242, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
}

.g-header__left,
.g-header__right {
  display: flex;
  align-items: center;
  gap: var(--sp-6);
  min-width: 0;
}

.g-header__brand {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex: none;
}
.g-header__mark {
  color: var(--color-cinnabar-700);
  display: grid;
  place-items: center;
}
.g-header__name {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  letter-spacing: 0.16em;
  color: var(--color-ink-900);
  white-space: nowrap;
}

.g-header__crumb {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  min-width: 0;
}
.g-header__crumb-sep {
  color: var(--color-ink-500);
}
.g-header__crumb-era {
  color: var(--chapter-accent);
  font-weight: 600;
}
.g-header__crumb-dot {
  color: var(--color-ink-500);
}
.g-header__crumb-keyword {
  color: var(--chapter-accent);
  letter-spacing: 0.08em;
}
.g-header__crumb-sep-text {
  color: var(--color-ink-500);
}
.g-header__crumb-title {
  color: var(--color-ink-500);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.g-header__mode {
  flex: none;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--color-warning) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-warning) 40%, transparent);
  color: var(--color-warning);
  font-size: var(--fs-caption);
  cursor: help;
}

.g-header__link {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  padding: 6px 10px;
  border-radius: var(--radius-btn);
  transition:
    background-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.g-header__link:hover {
  background: rgba(65, 55, 42, 0.06);
  color: var(--color-ink-900);
}

.g-header__icon-btn {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-btn);
  background: transparent;
  color: var(--color-ink-500);
  transition: color var(--dur-fast) var(--ease-standard);
}
.g-header__icon-btn:hover {
  color: var(--color-ink-900);
}
.g-header__mode--offline {
  border-color: rgba(111, 151, 137, .38);
  background: rgba(111, 151, 137, .1);
  color: #6f9789;
}

.g-header--dark {
  background: rgba(229, 238, 231, 0.94);
  border-bottom-color: rgba(40, 95, 97, 0.18);
  box-shadow: 0 8px 28px rgba(47, 88, 83, .08);
}
.g-header--dark .g-header__mark,
.g-header--dark .g-header__crumb-era,
.g-header--dark .g-header__crumb-keyword {
  color: color-mix(in srgb, var(--chapter-accent) 68%, var(--color-mineral-700));
}
.g-header--dark .g-header__name { color: var(--color-mineral-800); }
.g-header--dark .g-header__crumb,
.g-header--dark .g-header__crumb-sep,
.g-header--dark .g-header__crumb-dot,
.g-header--dark .g-header__crumb-title,
.g-header--dark .g-header__crumb-sep-text,
.g-header--dark .g-header__link,
.g-header--dark .g-header__icon-btn { color: rgba(33, 76, 83, 0.66); }
.g-header--dark .g-header__link:hover,
.g-header--dark .g-header__icon-btn:hover {
  color: var(--color-mineral-800);
  background: rgba(40, 95, 97, 0.08);
}
.g-header--dark .g-header__icon-btn { border-color: rgba(40, 95, 97, 0.2); }

@media (max-width: 1366px) {
  .g-header__crumb-title,
  .g-header__link span {
    display: none;
  }
}
</style>
