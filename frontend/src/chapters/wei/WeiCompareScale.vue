<script setup lang="ts">
/** 队员二 W-U02 · 证据对照尺：延续 / 变化 / 并存 / 未知（每项可展开来源说明） */
import { ref } from 'vue'
import GameplayState from '@/components/game/GameplayState.vue'
const emit = defineEmits<{ (e: 'play-complete', p: { judgments: Record<string, string> }): void; (e: 'play-fail', p: { reason: string }): void; (e: 'play-exit'): void }>()
const props = withDefaults(defineProps<{ items?: { id: string; title: string; source: string }[] }>(), { items: () => [
  { id: 'costume', title: '服饰形制', source: '供养人图像与陶俑：可观察形制，不能直接等同日常穿着。' },
  { id: 'cave', title: '窟形与造像', source: '云冈与龙门分属不同阶段：可比较，不做前后替代。' },
  { id: 'inscription', title: '题记与籍贯', source: '元羽墓志：可证个案与制度背景，不代表全体同步变化。' },
] })
const CATS = [{ id: 'continue', t: '延续' }, { id: 'change', t: '变化' }, { id: 'coexist', t: '并存' }, { id: 'unknown', t: '未知' }]
const pick = ref<Record<string, string>>({})
const open = ref<string | null>(null)
const msg = ref('')
function submit() {
  if (Object.keys(pick.value).length < props.items.length) { emit('play-fail', { reason: '尚有证据未判断' }); msg.value = '每项判断可展开来源和说明，请全部完成后再提交。'; return }
  emit('play-complete', { judgments: { ...pick.value } }); msg.value = '对照完成：结果已回传剧情层。'
}
</script>
<template>
  <GameplayState state="ready" title="证据对照尺">
    <div class="scale">
      <div v-for="it in props.items" :key="it.id" class="scale__row">
        <div class="scale__head"><strong>{{ it.title }}</strong><button type="button" @click="open = open === it.id ? null : it.id">{{ open === it.id ? '收起来源' : '展开来源' }}</button></div>
        <p v-if="open === it.id" class="scale__src">{{ it.source }}</p>
        <div class="scale__cats"><button v-for="c in CATS" :key="c.id" type="button" :class="{ on: pick[it.id] === c.id }" @click="pick[it.id] = c.id">{{ c.t }}</button></div>
      </div>
      <p v-if="msg" class="scale__msg" role="status">{{ msg }}</p>
      <div class="scale__foot"><button class="ghost" type="button" @click="emit('play-exit')">返回剧情</button><button class="primary" type="button" @click="submit">完成对照</button></div>
    </div>
  </GameplayState>
</template>
<style scoped>
.scale{display:flex;flex-direction:column;gap:10px;padding:16px;border:1px solid var(--color-border);border-radius:var(--radius-card);background:var(--color-panel)}
.scale__head{display:flex;justify-content:space-between;align-items:center}
.scale__head button{min-height:44px;background:none;border:0;color:var(--chapter-accent);font-size:var(--fs-caption)}
.scale__src{font-size:var(--fs-caption);color:var(--color-ink-500);background:var(--color-paper-100);border-radius:8px;padding:8px 12px;line-height:1.6}
.scale__cats{display:flex;gap:8px;flex-wrap:wrap}
.scale__cats button{min-height:44px;padding:0 16px;border-radius:var(--radius-pill);border:1px solid var(--color-border);background:#fff}
.scale__cats button.on{background:var(--chapter-accent);border-color:var(--chapter-accent);color:#fff}
.scale__msg{font-size:var(--fs-caption)}
.scale__foot{display:flex;justify-content:flex-end;gap:8px}
.primary{min-height:44px;padding:0 18px;border-radius:8px;background:var(--chapter-accent);color:#fff;border:1px solid var(--chapter-accent)}
.ghost{min-height:44px;padding:0 18px;border-radius:8px;background:#fff;border:1px solid var(--color-border)}
</style>
