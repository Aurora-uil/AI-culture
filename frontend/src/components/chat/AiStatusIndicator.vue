<script setup lang="ts">
/**
 * AI 状态提示（设计系统 §32）
 *
 * 只显示：正在查找史料…… / 正在组织回答…… / 正在核验引用……
 * 不显示「大模型思考中」「Chain of Thought」—— 不暴露内部推理。
 */
defineProps<{ text: string }>()
</script>

<template>
  <Transition name="fade">
    <div v-if="text" class="ai-status" role="status" aria-live="polite">
      <span class="ai-status__dots" aria-hidden="true">
        <i /><i /><i />
      </span>
      <span class="ai-status__text">{{ text }}</span>
    </div>
  </Transition>
</template>

<style scoped>
.ai-status {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  border: 1px solid var(--color-border);
  margin-bottom: var(--sp-6);
}
.ai-status__text {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
}
.ai-status__dots {
  display: inline-flex;
  gap: 4px;
}
.ai-status__dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--chapter-accent);
  opacity: 0.4;
  animation: ai-dot 1.2s ease-in-out infinite;
}
.ai-status__dots i:nth-child(2) {
  animation-delay: 0.18s;
}
.ai-status__dots i:nth-child(3) {
  animation-delay: 0.36s;
}

@keyframes ai-dot {
  0%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-2px);
  }
}
</style>
