<script setup lang="ts">
import { computed, ref } from 'vue';
/** 拓片校勘：字形证据 vs 空间证据，永不宣布唯一正确位置。 */
const props = defineProps<{ seenScripts: string[] }>();
const emit = defineEmits<{ (e: 'submit', payload: { choice: string }): void }>();
const zoneA = ref<string>('hs_script_tibetan');
const zoneB = ref<string>('hs_script_phagspa');
const zones = [
  { id: 'hs_script_sanskrit_lantsa', label: '梵文书写系统候选区' },
  { id: 'hs_script_tibetan', label: '藏文候选区' },
  { id: 'hs_script_phagspa', label: '八思巴文候选区' },
  { id: 'hs_script_chinese', label: '汉文候选区' },
];
const glyph = computed(() => ([
  { k: '字符形态', a: true, b: false, note: 'A区笔形更接近拓片' },
  { k: '行列方向', a: true, b: true, note: '两区均为竖列' },
  { k: '版面结构', a: false, b: true, note: 'B区栏界与拓片一致' },
  { k: '字符密度', a: false, b: false, note: '均缺少可比密度样本' },
]));
const spatial = computed(() => ([
  { k: '所在区域', a: true, b: false, note: '' },
  { k: '相邻装饰', a: false, b: true, note: 'B区相邻装饰吻合行距' },
  { k: '行距', a: false, b: true, note: '' },
  { k: '相对位置', a: false, b: false, note: '仍缺相邻题刻比对' },
]));
const confidence = computed(() => '低—中：字形与空间证据指向不同候选区，缺少相邻题刻比对。');
const choice = ref('pending');
const gateMsg = computed(() => {
  if (props.seenScripts.length >= 3) return '';
  return `仍需查验 ${3 - props.seenScripts.length} 处题刻后再提交（当前 ${props.seenScripts.length}/3）。可先选“暂列位置待核”保留证据。`;
});
function confirm() {
  if (choice.value !== 'pending' && props.seenScripts.length < 3) return;
  emit('submit', { choice: choice.value });
}
</script>
<template>
  <div class="rub">
    <h3>错位拓片 · 双证据比对</h3>
    <p class="rub__tip">系统只呈现相符 / 冲突与置信度，不宣布唯一正确位置。</p>
    <div class="rub__zones">
      <label>候选区A <select v-model="zoneA"><option v-for="z in zones" :key="z.id" :value="z.id">{{ z.label }}</option></select></label>
      <label>候选区B <select v-model="zoneB"><option v-for="z in zones" :key="z.id" :value="z.id">{{ z.label }}</option></select></label>
    </div>
    <div class="rub__grid">
      <section><h4>字形证据</h4><ul><li v-for="g in glyph" :key="g.k">{{ g.k }}：A {{ g.a ? '相符' : '冲突' }} / B {{ g.b ? '相符' : '冲突' }}<small>{{ g.note }}</small></li></ul></section>
      <section><h4>空间证据</h4><ul><li v-for="g in spatial" :key="g.k">{{ g.k }}：A {{ g.a ? '相符' : '冲突' }} / B {{ g.b ? '相符' : '冲突' }}<small>{{ g.note }}</small></li></ul></section>
    </div>
    <p class="rub__conf">当前判断：{{ confidence }}</p>
    <div class="rub__choices">
      <label><input type="radio" value="pending" v-model="choice" /> 暂列“位置待核”</label>
      <label><input type="radio" value="compare" v-model="choice" /> 继续比对相邻题刻</label>
      <label><input type="radio" value="submit" v-model="choice" /> 提交初步归位意见（标注不确定性）</label>
    </div>
    <p v-if="gateMsg" class="rub__tip">{{ gateMsg }}</p>
    <button type="button" @click="confirm()">确认校勘选择</button>
  </div>
</template>
<style scoped>
.rub{border:1px solid var(--color-border);border-radius:12px;padding:14px;background:var(--color-panel);font-size:13px;color:var(--color-ink-700)}
.rub__tip{color:var(--color-ink-500);font-size:12px}
.rub__zones{display:flex;gap:12px;margin:8px 0}
.rub__grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.rub__conf{margin-top:8px;font-weight:600;color:var(--chapter-accent)}
.rub__choices{display:flex;flex-direction:column;gap:4px;margin:8px 0}
</style>
