<script setup lang="ts">
/** 队员二 Q-U02/Q-U03/Q-U04 · 迁徙资源面板 + 多来源记录册 + 展柜对照 */
import { computed, ref } from 'vue'
import GameplayState from '@/components/game/GameplayState.vue'
const emit = defineEmits<{ (e: 'play-complete', p: { resources: Record<string, number>; records: string; kept: boolean }): void; (e: 'play-fail', p: { reason: string }): void; (e: 'play-exit'): void }>()
const resources = ref<Record<string, number>>({ food: 60, herb: 40, stock: 50, cart: 50, paper: 30 })
const NAMES: Record<string, string> = { food: '食物', herb: '药物', stock: '牲畜', cart: '车具', paper: '记录材料' }
const EFFECT: Record<string, string> = { food: '影响今夜救急', herb: '影响行路损伤', stock: '影响长期生计', cart: '影响转运速度', paper: '影响核名与待核记录' }
const conflicts = ref<Record<string, boolean>>({ range: false, exact: false })
const msg = ref('')
const kept = computed(() => conflicts.value.range && conflicts.value.exact)
function adj(k: string, d: number) { resources.value[k] = Math.max(0, Math.min(100, resources.value[k] + d)) }
function submit() {
  if (!kept.value) { emit('play-fail', { reason: '需保留来源差异' }); msg.value = '至少保留2组冲突记录：不自动合并，逐项勾选并列展示。'; return }
  emit('play-complete', { resources: { ...resources.value }, records: '路线/人数/动机/口述/官方并列', kept: true }); msg.value = '资源与记录册已回传剧情层。'
}
</script>
<template>
  <GameplayState state="ready" title="迁徙资源与记录册">
    <div class="qing2">
      <section><h3>迁徙资源面板 · 数值变化同时说明对人的影响</h3>
        <div v-for="(v, k) in resources" :key="k" class="qing2__res">
          <strong>{{ NAMES[k] }} · {{ v }}</strong><small>{{ EFFECT[k] }}</small>
          <div class="qing2__bar"><i :style="{ width: v + '%' }" /><div class="qing2__btns"><button type="button" @click="adj(k, -10)">−</button><button type="button" @click="adj(k, 10)">＋</button></div></div>
        </div>
      </section>
      <section><h3>多来源记录册 · 不自动合并冲突</h3>
        <label class="qing2__chk"><input type="checkbox" v-model="conflicts.range" /> 保留「约17万人 / 16.8万余 / 三万多户」三种口径并列（来源与统计单位不同）</label>
        <label class="qing2__chk"><input type="checkbox" v-model="conflicts.exact" /> 保留「大部众抵达伊犁 / 首领赴承德」两条路线并列（不是同一条路线）</label>
        <p class="qing2__exhibit">图屏展柜对照：《万法归一图屏》为宫廷叙事视角，不让单件文物代替全部历史；路线精度不高于证据精度。</p>
      </section>
      <p v-if="msg" class="qing2__msg" role="status">{{ msg }}</p>
      <div class="qing2__foot"><button class="ghost" type="button" @click="emit('play-exit')">返回剧情</button><button class="primary" type="button" @click="submit">完成并回传</button></div>
    </div>
  </GameplayState>
</template>
<style scoped>
.qing2{display:flex;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--color-border);border-radius:var(--radius-card);background:var(--color-panel)}
.qing2 h3{font-size:var(--fs-body-s);color:var(--chapter-accent);margin-bottom:8px}
.qing2__res{display:flex;flex-direction:column;gap:4px;border-top:1px solid var(--color-border);padding:8px 0}
.qing2__res small{font-size:12px;color:var(--color-ink-500)}
.qing2__bar{display:flex;align-items:center;gap:8px}
.qing2__bar i{display:block;height:8px;flex:1;border-radius:99px;background:var(--chapter-accent)}
.qing2__btns{display:flex;gap:6px}
.qing2__btns button{min-width:44px;min-height:44px;border-radius:8px;border:1px solid var(--color-border);background:#fff;font-size:18px}
.qing2__chk{display:flex;gap:8px;align-items:flex-start;font-size:13px;line-height:1.6;color:var(--color-ink-700);margin:6px 0}
.qing2__chk input{width:20px;height:20px;margin-top:2px}
.qing2__exhibit{font-size:12px;color:var(--color-ink-500);background:var(--color-paper-100);border-radius:8px;padding:8px 12px;line-height:1.6}
.qing2__msg{font-size:12px}
.qing2__foot{display:flex;justify-content:flex-end;gap:8px}
.primary{min-height:44px;padding:0 18px;border-radius:8px;background:var(--chapter-accent);color:#fff;border:1px solid var(--chapter-accent)}
.ghost{min-height:44px;padding:0 18px;border-radius:8px;background:#fff;border:1px solid var(--color-border)}
</style>
