<script setup lang="ts">
/** 队员二 T-U03/T-U04 · 名册校对 + 120字展签编辑器（越界提示，不只判对错） */
import { computed, ref } from 'vue'
import GameplayState from '@/components/game/GameplayState.vue'
const emit = defineEmits<{ (e: 'play-complete', p: { roster: Record<string, string>; caption: string }): void; (e: 'play-fail', p: { reason: string }): void; (e: 'play-exit'): void }>()
const rows = ref([
  { id: 'ludongzan', name: '禄东赞', guess: '吐蕃使臣', fix: '', note: '应写：吐蕃使臣禄东赞（画中可确认）' },
  { id: 'wencheng', name: '文成公主', guess: '画中宫女', fix: '', note: '纠正：不在画中，经由641年事件进入画外关系' },
  { id: 'taizong', name: '唐太宗', guess: '唐太宗', fix: '', note: '画中核心人物，坐于步辇之上' },
])
const caption = ref('')
const BANNED = ['现场照片', '亲历', '永久和平', '一定是', '证明全部']
const warn = computed(() => BANNED.find(w => caption.value.includes(w)) || '')
const mustHave = computed(() => [
  { k: '画面', ok: /画|人物|相见|步辇/.test(caption.value) },
  { k: '关联史实', ok: /634|641|使|事件|禄东赞/.test(caption.value) },
  { k: '归属判断', ok: /归属|编目|阎立本|传/.test(caption.value) },
  { k: '未知项', ok: /未知|不能|不在画/.test(caption.value) },
])
const msg = ref('')
function submit() {
  if (rows.value.some(r => !r.fix)) { emit('play-fail', { reason: '名册尚有未校对行' }); msg.value = '名册至少纠正1个名称/身份问题：请为每行选择正确归属。'; return }
  if (caption.value.length > 120) { emit('play-fail', { reason: '展签超120字' }); msg.value = `展签${caption.value.length}字，已超120字上限。`; return }
  if (warn.value) { emit('play-fail', { reason: `越界表述：${warn.value}` }); msg.value = `发现越界表述「${warn.value}」：历史画不是现场照片，一次相见不能概括全部历史。`; return }
  const missing = mustHave.value.filter(m => !m.ok)
  if (missing.length) { emit('play-fail', { reason: `缺少：${missing.map(m => m.k).join('、')}` }); msg.value = `展签必含画面、关联史实、归属判断、未知项，缺少：${missing.map(m => m.k).join('、')}。`; return }
  emit('play-complete', { roster: Object.fromEntries(rows.value.map(r => [r.id, r.fix])), caption: caption.value }); msg.value = '名册与展签已回传剧情层。'
}
</script>
<template>
  <GameplayState state="ready" title="名册校对与展签">
    <div class="tang2">
      <section><h3>名册校对 · 说明原因而非只判对错</h3>
        <div v-for="r in rows" :key="r.id" class="tang2__row">
          <strong>{{ r.name }} · 原写：{{ r.guess }}</strong>
          <div class="tang2__opts"><button v-for="o in ['画内人物', '画外关系人物']" :key="o" type="button" :class="{ on: r.fix === o }" @click="r.fix = o; msg = r.note">{{ o }}</button></div>
        </div>
      </section>
      <section><h3>120字展签 · {{ caption.length }}/120</h3>
        <textarea v-model="caption" rows="4" maxlength="140" placeholder="必含：画面内容、关联史实、归属判断、未知边界" aria-label="展签编辑" />
        <ul class="tang2__must"><li v-for="m in mustHave" :key="m.k" :class="{ ok: m.ok }">{{ m.ok ? '✓' : '○' }}{{ m.k }}</li></ul>
        <p v-if="warn" class="tang2__warn">越界提示：「{{ warn }}」请改为有边界的表述。</p>
      </section>
      <p v-if="msg" class="tang2__msg" role="status">{{ msg }}</p>
      <div class="tang2__foot"><button class="ghost" type="button" @click="emit('play-exit')">返回剧情</button><button class="primary" type="button" @click="submit">完成并回传</button></div>
    </div>
  </GameplayState>
</template>
<style scoped>
.tang2{display:flex;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--color-border);border-radius:var(--radius-card);background:var(--color-panel)}
.tang2 h3{font-size:var(--fs-body-s);color:var(--chapter-accent);margin-bottom:8px}
.tang2__row{border-top:1px solid var(--color-border);padding:8px 0;display:flex;flex-direction:column;gap:6px}
.tang2__opts{display:flex;gap:8px}
.tang2__opts button{min-height:44px;padding:0 16px;border-radius:var(--radius-pill);border:1px solid var(--color-border);background:#fff}
.tang2__opts button.on{background:var(--chapter-accent);border-color:var(--chapter-accent);color:#fff}
textarea{width:100%;border:1px solid var(--color-border);border-radius:8px;padding:10px;font-size:14px;line-height:1.6;min-height:96px}
.tang2__must{list-style:none;display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--color-ink-500);margin:8px 0 0;padding:0}
.tang2__must .ok{color:var(--evidence-fact)}
.tang2__warn{font-size:12px;color:var(--evidence-disputed);background:color-mix(in srgb,var(--evidence-disputed) 12%,transparent);border-radius:8px;padding:8px 12px}
.tang2__msg{font-size:12px}
.tang2__foot{display:flex;justify-content:flex-end;gap:8px}
.primary{min-height:44px;padding:0 18px;border-radius:8px;background:var(--chapter-accent);color:#fff;border:1px solid var(--chapter-accent)}
.ghost{min-height:44px;padding:0 18px;border-radius:8px;background:#fff;border:1px solid var(--color-border)}
</style>
