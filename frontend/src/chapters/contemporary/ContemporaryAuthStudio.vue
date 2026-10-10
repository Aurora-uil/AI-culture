<script setup lang="ts">
/** 队员二 C-U01~C-U05 · 针法观察 + 权利卡 + 授权确认 + 受控共创 + Provenance作品卡 */
import { computed, ref } from 'vue'
import GameplayState from '@/components/game/GameplayState.vue'
const emit = defineEmits<{ (e: 'play-complete', p: { card: string; blocked: string[] }): void; (e: 'play-fail', p: { reason: string }): void; (e: 'play-exit'): void }>()
const step = ref(1)
const order = ref<string[]>([])
const PATH = ['穿针', '起针', '行针', '收针']
const mats = ref([
  { id: 'a', t: '本地创作者起针片（已授权·可生成参考）', st: '可生成参考', ok: true },
  { id: 'b', t: '佚名旧纹样照片（权利不清）', st: '不可生成', ok: false },
  { id: 'c', t: '学员练习稿（仅展示）', st: '可展示', ok: false },
  { id: 'd', t: '创作者语音说明（已授权·可学习）', st: '可学习', ok: true },
])
const picked = ref<string[]>(['a'])
const agreed = ref(false)
const msg = ref('')
const blocked = computed(() => picked.value.filter(id => !mats.value.find(m => m.id === id)?.ok))
const canGen = computed(() => step.value === 4 && orderOk.value && blocked.value.length === 0 && agreed.value)
const orderOk = computed(() => JSON.stringify(order.value) === JSON.stringify(PATH))
function togglePath(p: string) { order.value = order.value.includes(p) ? order.value.filter(x => x !== p) : [...order.value, p] }
function submit() {
  if (!orderOk.value) { emit('play-fail', { reason: '针法路径错误' }); msg.value = '请按 穿针→起针→行针→收针 排序，并对照正反面与错误示范。'; return }
  if (blocked.value.length) { emit('play-fail', { reason: `权利不足：${blocked.value.join(',')}` }); msg.value = '权利不清素材不能进入生成流程：已阻断并说明原因。'; return }
  if (!agreed.value) { emit('play-fail', { reason: '未完成授权确认' }); msg.value = '请确认作者、来源、用途、期限、署名与训练范围后继续。'; return }
  emit('play-complete', { card: 'AI辅助文化创意作品·非传统羌绣原作|元素来源/授权/AI步骤/人工修改已列明', blocked: blocked.value }); msg.value = '作品卡已生成并回传剧情层。'
}
</script>
<template>
  <GameplayState state="ready" title="授权共创工作台">
    <div class="co">
      <ol class="co__steps"><li v-for="i in [1, 2, 3, 4]" :key="i" :class="{ on: step === i }"><button type="button" @click="step = i">步骤{{ i }}</button></li></ol>
      <section v-if="step === 1"><h3>针法观察 · 非生成式（局部放大/路径排序/正反对照）</h3>
        <p class="co__note">数字示意不等于实际手工技艺；不要求假装完成真实刺绣。</p>
        <div class="co__opts"><button v-for="p in PATH" :key="p" type="button" :class="{ on: order.includes(p) }" @click="togglePath(p)">{{ order.indexOf(p) + 1 || '·' }} {{ p }}</button></div>
        <div class="co__nav"><button type="button" @click="step = 2">下一步 · 素材权利</button></div>
      </section>
      <section v-if="step === 2"><h3>素材权利状态 · 文字+图标（不只靠颜色）</h3>
        <label v-for="m in mats" :key="m.id" class="co__mat"><input type="checkbox" :value="m.id" v-model="picked" /> <b>{{ m.st }}</b> {{ m.t }}</label>
        <p v-if="blocked.length" class="co__warn">已阻断 {{ blocked.length }} 项权利不足素材：展示授权≠生成/训练授权。</p>
        <div class="co__nav"><button type="button" @click="step = 1">上一步</button><button type="button" @click="step = 3">下一步 · 授权确认</button></div>
      </section>
      <section v-if="step === 3"><h3>授权确认 · 未满足条件时生成按钮不可用</h3>
        <label class="co__mat"><input type="checkbox" v-model="agreed" /> 我确认作者、来源、用途、期限、裁切、署名、训练范围；未满足条件不生成。</label>
        <div class="co__nav"><button type="button" @click="step = 2">上一步</button><button type="button" @click="step = 4">下一步 · 共创摘要</button></div>
      </section>
      <section v-if="step === 4"><h3>受控共创与Provenance作品卡</h3>
        <p class="co__note">已使用：{{ picked.filter(id => !blocked.includes(id)).join(', ') || '无' }}；未使用：{{ blocked.join(', ') || '无' }}；AI仅转写/检索/关系记录，不生成统一传统。</p>
        <p class="co__card">AI辅助文化创意作品 · 非传统羌绣原作（可导出/截图展示）</p>
      </section>
      <p v-if="msg" class="co__msg" role="status">{{ msg }}</p>
      <div class="co__foot"><button class="ghost" type="button" @click="emit('play-exit')">返回剧情</button><button class="primary" type="button" :disabled="!canGen" :title="!canGen ? '权利不足或授权未完成时不可生成' : ''" @click="submit">生成并回传剧情</button></div>
    </div>
  </GameplayState>
</template>
<style scoped>
.co{display:flex;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--color-border);border-radius:var(--radius-card);background:var(--color-panel)}
.co__steps{list-style:none;display:flex;gap:8px;margin:0;padding:0}
.co__steps button{min-height:44px;padding:0 14px;border-radius:var(--radius-pill);border:1px solid var(--color-border);background:#fff}
.co__steps .on button{background:var(--chapter-accent);border-color:var(--chapter-accent);color:#fff}
.co h3{font-size:14px;color:var(--chapter-accent)}
.co__note{font-size:12px;color:var(--color-ink-500);line-height:1.6}
.co__opts{display:flex;gap:8px;flex-wrap:wrap}
.co__opts button{min-height:44px;padding:0 14px;border-radius:8px;border:1px solid var(--color-border);background:#fff}
.co__opts button.on{border-color:var(--chapter-accent);color:var(--chapter-accent)}
.co__mat{display:flex;gap:8px;align-items:flex-start;font-size:13px;line-height:1.6;margin:6px 0}
.co__mat input{width:20px;height:20px}
.co__warn{font-size:12px;color:var(--evidence-disputed);background:color-mix(in srgb,var(--evidence-disputed) 12%,transparent);border-radius:8px;padding:8px 12px}
.co__card{font-size:13px;font-weight:700;background:var(--color-paper-100);border-radius:8px;padding:10px 12px}
.co__msg{font-size:12px}
.co__nav,.co__foot{display:flex;gap:8px;justify-content:flex-end}
.co__nav button{min-height:44px;padding:0 14px;border-radius:8px;border:1px solid var(--color-border);background:#fff}
.primary{min-height:44px;padding:0 18px;border-radius:8px;background:var(--chapter-accent);color:#fff;border:1px solid var(--chapter-accent)}
.primary:disabled{opacity:.45}
.ghost{min-height:44px;padding:0 18px;border-radius:8px;background:#fff;border:1px solid var(--color-border)}
</style>
