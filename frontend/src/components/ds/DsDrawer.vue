<script setup lang="ts">
import { watch, onBeforeUnmount } from 'vue'
import DsIcon from './DsIcon.vue'

/**
 * 抽屉（设计系统 §27 / §53 / §54）
 *
 * - 对象详情 → 右侧抽屉
 * - 来源 → 次级抽屉（可叠在实体抽屉之上，关闭后回实体）
 *
 * §85 返回逻辑：浏览器 Back 应回到上一个产品状态，而不是回首页。
 * 这里通过 pushState 让 Esc / Back 都能关闭抽屉。
 */
const props = withDefaults(
  defineProps<{
    open: boolean
    title?: string
    subtitle?: string
    /** 实体抽屉 420px；来源抽屉 520px */
    width?: 'entity' | 'source'
    /** 次级抽屉：叠在另一个抽屉之上，背景更暗 */
    stacked?: boolean
    closeOnBack?: boolean
  }>(),
  {
    width: 'entity',
    stacked: false,
    closeOnBack: true,
  },
)

const emit = defineEmits<{ (e: 'close'): void }>()

function close() {
  emit('close')
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.open) {
    e.stopPropagation()
    close()
  }
}

watch(
  () => props.open,
  (open) => {
    if (open) {
      document.addEventListener('keydown', onKeydown)
      if (props.closeOnBack) {
        // 让浏览器 Back 关闭抽屉而不是退出页面
        history.pushState({ drawer: true }, '')
        window.addEventListener('popstate', close, { once: true })
      }
    } else {
      document.removeEventListener('keydown', onKeydown)
    }
  },
)

onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer-backdrop">
      <div v-if="open" class="ds-drawer-backdrop" :class="{ 'is-stacked': stacked }" @click="close" />
    </Transition>
    <Transition name="drawer-panel">
      <aside
        v-if="open"
        class="ds-drawer"
        :class="[`ds-drawer--${width}`, { 'is-stacked': stacked }]"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <header v-if="title || $slots.header" class="ds-drawer__head">
          <slot name="header">
            <div class="ds-drawer__titles">
              <p v-if="subtitle" class="ds-drawer__subtitle">{{ subtitle }}</p>
              <h2 class="ds-drawer__title">{{ title }}</h2>
            </div>
          </slot>
          <button class="ds-drawer__close" type="button" aria-label="关闭" @click="close">
            <DsIcon name="close" :size="18" />
          </button>
        </header>

        <div class="ds-drawer__body">
          <slot />
        </div>

        <footer v-if="$slots.footer" class="ds-drawer__foot">
          <slot name="footer" />
        </footer>
      </aside>
    </Transition>
  </Teleport>
</template>

<style scoped>
.ds-drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(31, 37, 43, 0.32);
  z-index: var(--z-drawer-backdrop);
}
.ds-drawer-backdrop.is-stacked {
  z-index: calc(var(--z-drawer-backdrop) + 2);
  background: rgba(31, 37, 43, 0.22);
}

.ds-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: var(--drawer-w);
  display: flex;
  flex-direction: column;
  background: var(--color-paper-50);
  border-left: 1px solid var(--color-border);
  box-shadow: var(--shadow-floating);
  z-index: var(--z-drawer);
}
.ds-drawer--source {
  width: var(--source-drawer-w);
}
.ds-drawer.is-stacked {
  z-index: calc(var(--z-drawer) + 2);
}

.ds-drawer__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: var(--pad-drawer) var(--pad-drawer) var(--sp-4);
  border-bottom: 1px solid var(--color-border);
  flex: none;
}

.ds-drawer__titles {
  min-width: 0;
}
.ds-drawer__subtitle {
  font-size: var(--fs-caption);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-ink-500);
  margin-bottom: var(--sp-1);
}
.ds-drawer__title {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  line-height: var(--lh-h2);
}

.ds-drawer__close {
  flex: none;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: var(--radius-btn);
  background: transparent;
  color: var(--color-ink-500);
  transition: background-color var(--dur-fast) var(--ease-standard);
}
.ds-drawer__close:hover {
  background: rgba(65, 55, 42, 0.08);
  color: var(--color-ink-900);
}

.ds-drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--pad-drawer);
}

.ds-drawer__foot {
  flex: none;
  padding: var(--sp-4) var(--pad-drawer) var(--pad-drawer);
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

/* 过渡 */
.drawer-backdrop-enter-active,
.drawer-backdrop-leave-active {
  transition: opacity var(--dur-normal) var(--ease-standard);
}
.drawer-backdrop-enter-from,
.drawer-backdrop-leave-to {
  opacity: 0;
}

.drawer-panel-enter-active,
.drawer-panel-leave-active {
  transition: transform var(--dur-normal) var(--ease-standard);
}
.drawer-panel-enter-from,
.drawer-panel-leave-to {
  transform: translateX(100%);
}
</style>
