<script setup lang="ts">
/**
 * 加载骨架（设计系统 §64）
 *
 * 实体卡：图像块 / 标题线 / 正文3行 / 按钮
 * 不要整个页面大转圈。
 */
withDefaults(
  defineProps<{
    variant?: 'entity' | 'source' | 'message' | 'text'
    rows?: number
  }>(),
  { variant: 'entity', rows: 3 },
)
</script>

<template>
  <div class="sk" :class="`sk--${variant}`" aria-hidden="true">
    <template v-if="variant === 'entity'">
      <div class="sk__block sk__image" />
      <div class="sk__line sk__line--w60" />
      <div v-for="i in rows" :key="i" class="sk__line" :style="{ width: `${96 - i * 7}%` }" />
      <div class="sk__actions">
        <div class="sk__btn" />
        <div class="sk__btn sk__btn--wide" />
      </div>
    </template>

    <template v-else-if="variant === 'source'">
      <div v-for="i in rows" :key="i" class="sk__source-card">
        <div class="sk__line sk__line--w30" />
        <div class="sk__line sk__line--w70" />
        <div class="sk__line sk__line--w90" />
        <div class="sk__line sk__line--w50" />
      </div>
    </template>

    <template v-else-if="variant === 'message'">
      <div class="sk__line sk__line--w40" />
      <div class="sk__line sk__line--w95" />
      <div class="sk__line sk__line--w80" />
    </template>

    <template v-else>
      <div v-for="i in rows" :key="i" class="sk__line" :style="{ width: `${100 - i * 9}%` }" />
    </template>
  </div>
</template>

<style scoped>
.sk {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.sk__block,
.sk__line,
.sk__btn {
  background: linear-gradient(
    90deg,
    rgba(65, 55, 42, 0.06) 25%,
    rgba(65, 55, 42, 0.11) 37%,
    rgba(65, 55, 42, 0.06) 63%
  );
  background-size: 400% 100%;
  animation: sk-shimmer 1.4s ease-in-out infinite;
  border-radius: 6px;
}

.sk__image {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: var(--radius-card);
  margin-bottom: var(--sp-2);
}

.sk__line {
  height: 12px;
}
.sk__line--w30 {
  width: 30%;
}
.sk__line--w40 {
  width: 40%;
}
.sk__line--w50 {
  width: 50%;
}
.sk__line--w60 {
  width: 60%;
  height: 18px;
}
.sk__line--w70 {
  width: 70%;
}
.sk__line--w80 {
  width: 80%;
}
.sk__line--w90 {
  width: 90%;
}
.sk__line--w95 {
  width: 95%;
}

.sk__actions {
  display: flex;
  gap: var(--sp-2);
  margin-top: var(--sp-2);
}
.sk__btn {
  height: 40px;
  width: 130px;
  border-radius: var(--radius-btn);
}
.sk__btn--wide {
  width: 150px;
}

.sk__source-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  padding: var(--sp-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  margin-bottom: var(--sp-3);
}

@keyframes sk-shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sk__block,
  .sk__line,
  .sk__btn {
    animation: none;
  }
}
</style>
