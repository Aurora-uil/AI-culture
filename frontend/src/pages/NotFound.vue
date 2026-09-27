<script setup lang="ts">
import { useRouter } from 'vue-router'
import DsButton from '@/components/ds/DsButton.vue'

/**
 * 404（设计系统 §65）
 *
 * 文化项目文案，不写 Oops! / Something went wrong!
 */
const router = useRouter()
</script>

<template>
  <main class="nf">
    <h1 class="nf__title">这段内容暂时没有完成数字化整理</h1>
    <p class="nf__sub">你可以返回时间轴，从六个时代重新进入。</p>
    <div class="nf__actions">
      <DsButton variant="primary" @click="router.push('/timeline')">
        返回历史时间轴
      </DsButton>
      <DsButton variant="ghost" @click="router.back()">返回上一页</DsButton>
    </div>
  </main>
</template>

<style scoped>
.nf {
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  text-align: center;
  padding: var(--sp-16);
}
.nf__title {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  color: var(--color-ink-900);
}
.nf__sub {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
}
.nf__actions {
  display: flex;
  gap: var(--sp-3);
  margin-top: var(--sp-6);
}
</style>
