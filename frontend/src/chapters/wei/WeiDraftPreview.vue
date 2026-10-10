<script setup lang="ts">
/**
 * 队员二 W-U03 · 北魏营造推演样稿（明确标注“推演样稿，非复原件”）
 * emits: play-complete { elements } / play-fail / play-exit
 */
import { ref, computed } from 'vue'
import GameplayState from '@/components/game/GameplayState.vue'
const emit = defineEmits<{ (e: 'play-complete', p: { elements: Record<string, string> }): void; (e: 'play-fail', p: { reason: string }): void; (e: 'play-exit'): void }>()
const groups = [
  { id: 'fold', label: '衣褶', options: [{ id: 'keep', t: '延续旧式' }, { id: 'adapt', t: '改造并存' }] },
  { id: 'decor', label: '装饰', options: [{ id: 'keep', t: '延续旧式' }, { id: 'adapt', t: '改造并存' }] },
  { id: 'text', label: '文字', options: [{ id: 'keep', t: '延续旧式' }, { id: 'adapt', t: '改造并存' }] },
  { id: 'craft', label: '工艺', options: [{ id: 'keep', t: '延续旧式' }, { id: 'adapt', t: '改造并存' }] },
]
const pick = ref<Record<string, string>>({})
const level = ref<Record<string, string>>({})
const msg = ref('')
const done = computed(() => groups.every(g => pick.value[g.id] && level.value[g.id]))
function submit() {
  if (!done.value) { emit('play-fail', { reason: '每项需选择来源层级' }); msg.value = '每项需选择：直接证据 / 类比推断 / 创作选择，否则不能定稿。'; return }
  emit('play-complete', { elements: { ...pick.value } }); msg.value = '样稿已生成（推演样稿，非复原件）。'
}
</script>
<template>
  <GameplayState state="ready" title="营造推演">
    <div class="wei2">
      <p class="wei2__tag">推演样稿 · 不伪装复原件 · 每个元素可反查依据</p>
      <div v-for="g in groups" :key="g.id" class="wei2__row">
        <strong>{{ g.label }}</strong>
        <div class="wei2__opts"><button v-for="o in g.options" :key="o.id" :class="{ on: pick[g.id] === o.id }" type="button" @click="pick[g.id] = o.id">{{ o.t }}</button></div>
        <div class="wei2__opts"><button v-for="l in ['直接证据', '类比推断', '创作选择']" :key="l" :class="{ on: level[g.id] === l }" type="button" @click="level[g.id] = l">{{ l }}</button></div>
      </div>
      <div class="wei2__preview" aria-label="样稿预览">样稿预览：{{ groups.map(g => `${g.label}·${pick[g.id] === 'keep' ? '延续' : pick[g.id] === 'adapt' ? '改造' : '未选'}(${level[g.id] || '未标来源'})`).join(' / ') }}</div>
      <p v-if="msg" class="wei2__msg" role="status">{{ msg }}</p>
      <div class="wei2__foot"><button class="ghost" type="button" @click="emit('play-exit')">返回剧情</button><button class="primary" type="button" @click="submit">完成推演</button></div>
    </div>
  </GameplayState>
</template>
<style scoped>
.wei2{display:flex;flex-direction:column;gap:10px;padding:16px;border:1px solid var(--color-border);border-radius:var(--radius-card);background:var(--color-panel)}
.wei2__tag{font-size:var(--fs-caption);color:var(--evidence-disputed)}
.wei2__row{display:flex;flex-direction:column;gap:6px;border-top:1px solid var(--color-border);padding-top:8px}
.wei2__opts{display:flex;gap:8px;flex-wrap:wrap}
.wei2__opts button{min-height:44px;padding:0 14px;border-radius:var(--radius-pill);border:1px solid var(--color-border);background:#fff;font-size:var(--fs-body-s)}
.wei2__opts button.on{border-color:var(--chapter-accent);background:var(--chapter-accent);color:#fff}
.wei2__preview{font-size:var(--fs-caption);background:var(--color-paper-100);border-radius:var(--radius-btn);padding:8px 12px;color:var(--color-ink-700)}
.wei2__msg{font-size:var(--fs-caption);color:var(--color-ink-700)}
.wei2__foot{display:flex;justify-content:flex-end;gap:8px}
.primary{min-height:44px;padding:0 18px;border-radius:var(--radius-btn);background:var(--chapter-accent);color:#fff;border:1px solid var(--chapter-accent)}
.ghost{min-height:44px;padding:0 18px;border-radius:var(--radius-btn);background:#fff;border:1px solid var(--color-border)}
</style>
