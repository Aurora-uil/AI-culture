<script setup lang="ts">
/**
 * 队员二共用：玩法状态壳（加载/空/错误/离线/重试）
 * 供五章核心玩法组件复用，不接管剧情分支逻辑。
 */
withDefaults(defineProps<{
  state?: 'ready' | 'loading' | 'empty' | 'error' | 'offline'
  title?: string
  note?: string
  retryLabel?: string
}>(), {
  state: 'ready', title: '', note: '', retryLabel: '重新尝试',
})
const emit = defineEmits<{ (e: 'retry'): void }>()
</script>
<template>
  <div v-if="state === 'loading'" class="ps" role="status" aria-live="polite">
    <span class="ps__spin" aria-hidden="true" /><p class="ps__t">{{ title || '正在载入玩法…' }}</p>
    <p v-if="note" class="ps__n">{{ note }}</p>
  </div>
  <div v-else-if="state !== 'ready'" class="ps" :class="`is-${state}`" role="alert">
    <p class="ps__t">{{ title || ({ empty: '这里暂时没有内容', error: '玩法加载失败', offline: '网络不可用，仍可继续主线' } as any)[state] }}</p>
    <p v-if="note" class="ps__n">{{ note }}</p>
    <button v-if="state === 'error' || state === 'offline'" type="button" class="ps__btn" @click="emit('retry')">{{ retryLabel }}</button>
  </div>
  <slot v-else />
</template>
<style scoped>
.ps{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;min-height:180px;padding:24px;border:1px dashed var(--color-border);border-radius:var(--radius-card);background:var(--color-paper-100);text-align:center}
.ps__t{font-size:var(--fs-body-s);font-weight:600;color:var(--color-ink-900)}
.ps__n{font-size:var(--fs-caption);color:var(--color-ink-500);max-width:420px;line-height:1.6}
.ps__btn{margin-top:4px;min-height:44px;padding:0 18px;border-radius:var(--radius-btn);border:1px solid var(--chapter-accent);background:#fff;color:var(--chapter-accent);font-size:var(--fs-body-s)}
.ps__spin{width:22px;height:22px;border-radius:50%;border:2px solid var(--color-border);border-top-color:var(--chapter-accent);animation:ps-spin .7s linear infinite}
@keyframes ps-spin{to{transform:rotate(360deg)}}
</style>
