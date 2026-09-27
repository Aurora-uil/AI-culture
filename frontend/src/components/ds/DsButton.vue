<script setup lang="ts">
/**
 * 按钮（设计系统 §50 / §51）
 *
 * 状态：Default / Hover / Pressed / Disabled / Loading
 * Loading 时按钮文字保持、右侧出现 14px spinner，避免按钮宽度跳变。
 */
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost'
    size?: 'm' | 'l'
    disabled?: boolean
    loading?: boolean
    block?: boolean
    type?: 'button' | 'submit'
  }>(),
  {
    variant: 'primary',
    size: 'm',
    disabled: false,
    loading: false,
    block: false,
    type: 'button',
  },
)

const emit = defineEmits<{ (e: 'click', ev: MouseEvent): void }>()

function onClick(ev: MouseEvent) {
  emit('click', ev)
}
</script>

<template>
  <button
    :type="type"
    class="ds-btn"
    :class="[`ds-btn--${variant}`, `ds-btn--${size}`, { 'is-block': block, 'is-loading': loading }]"
    :disabled="disabled || loading"
    @click="onClick"
  >
    <span class="ds-btn__label"><slot /></span>
    <span v-if="loading" class="ds-btn__spinner" aria-hidden="true" />
  </button>
</template>

<style scoped>
.ds-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  height: var(--btn-h);
  padding: 0 var(--sp-6);
  border-radius: var(--radius-btn);
  border: 1px solid transparent;
  font-size: var(--fs-body);
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  transition:
    background-color var(--dur-fast) var(--ease-standard),
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard),
    transform var(--dur-fast) var(--ease-standard);
}

.ds-btn--l {
  height: var(--btn-h-lg);
  padding: 0 var(--sp-8);
  font-size: var(--fs-body-l);
}

.is-block {
  width: 100%;
}

/* ---------- Primary ---------- */
.ds-btn--primary {
  background: var(--chapter-accent);
  color: #fff;
}
.ds-btn--primary:hover:not(:disabled) {
  filter: brightness(1.08);
}
.ds-btn--primary:active:not(:disabled) {
  transform: translateY(1px);
  filter: brightness(0.96);
}

/* ---------- Secondary ---------- */
.ds-btn--secondary {
  background: rgba(255, 255, 255, 0.9);
  border-color: var(--color-border);
  color: var(--color-ink-900);
}
.ds-btn--secondary:hover:not(:disabled) {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
}
.ds-btn--secondary:active:not(:disabled) {
  transform: translateY(1px);
}

/* ---------- Ghost ---------- */
.ds-btn--ghost {
  background: transparent;
  color: var(--color-ink-500);
}
.ds-btn--ghost:hover:not(:disabled) {
  background: rgba(65, 55, 42, 0.06);
  color: var(--color-ink-900);
}

.ds-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ---------- Loading（宽度不跳变） ---------- */
.ds-btn__label {
  display: inline-block;
}
.is-loading .ds-btn__label {
  opacity: 0.85;
}
.ds-btn__spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-top-color: transparent;
  animation: ds-spin 0.7s linear infinite;
  flex: none;
}
@keyframes ds-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
