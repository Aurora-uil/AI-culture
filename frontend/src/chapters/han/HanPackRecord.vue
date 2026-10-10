<script setup lang="ts">
/**
 * 队员二 H-U02/H-U03/H-U04 · 汉代行囊·路线·见闻记录
 * 约定接口（供1号剧情组件接入）：
 * props: initialPack / initialRoute / initialRecords（可空，由剧情状态传入）
 * emits: play-complete { pack, route, records } / play-fail { reason } / play-exit
 * 不硬编码第二份历史数据：所有文案由 props.fallback 传入或使用默认教学文案。
 */
import { computed, ref } from 'vue'
import GameplayState from '@/components/game/GameplayState.vue'

const props = withDefaults(defineProps<{
  loading?: boolean; offline?: boolean; error?: string | null
  initialPack?: string[]; initialRoute?: string | null
}>(), { loading: false, offline: false, error: null, initialPack: () => [], initialRoute: null })
const emit = defineEmits<{
  (e: 'play-complete', p: { pack: string[]; route: string; records: Record<string, string> }): void
  (e: 'play-fail', p: { reason: string }): void
  (e: 'play-exit'): void
}>()

interface Supply { id: string; name: string; use: string; cost: string }
const SUPPLIES: Supply[] = [
  { id: 'gift', name: '礼物', use: '用于交涉，打开一次对话', cost: '占用1格行囊' },
  { id: 'food', name: '食物', use: '支撑一次远行选择', cost: '每段路消耗1份' },
  { id: 'slip', name: '简牍', use: '记录见闻，可校勘', cost: '需防潮保存' },
  { id: 'herb', name: '药物', use: '应对一次行路损伤', cost: '仅够一人份' },
  { id: 'horse', name: '马具', use: '加快一段行程', cost: '需配合食物' },
]
const ROUTES = [
  { id: 'fast_unknown', name: '快但未知', desc: '信息不完整，省时但需承担不确定', need: 'food' },
  { id: 'slow_checked', name: '慢但可核', desc: '可逐站核对，耗时但边界清楚', need: 'slip' },
]
const pack = ref<string[]>([...props.initialPack])
const route = ref<string | null>(props.initialRoute)
const records = ref<Record<string, string>>({ place: '', person: '', item: '', confidence: '不确定' })
const msg = ref('')

const state = computed(() => props.loading ? 'loading' : props.error ? 'error' : props.offline ? 'offline' : 'ready')
function toggle(id: string) {
  if (pack.value.includes(id)) pack.value = pack.value.filter(x => x !== id)
  else { if (pack.value.length >= 3) { msg.value = '行囊最多带3样：每种物资至少影响一次后续选择。'; return } pack.value.push(id) }
  msg.value = ''
}
function submit() {
  if (pack.value.length === 0) { emit('play-fail', { reason: '行囊为空：至少携带1样物资才能出发' }); msg.value = '行囊为空：至少携带1样物资才能出发。'; return }
  if (!route.value) { emit('play-fail', { reason: '尚未选择路线' }); msg.value = '请先选择一条路线：选择前信息不完整，选择后反馈清楚。'; return }
  const need = ROUTES.find(r => r.id === route.value)?.need
  if (need && !pack.value.includes(need)) { emit('play-fail', { reason: `该路线需要「${SUPPLIES.find(s => s.id === need)?.name}」` }); msg.value = `该路线需要「${SUPPLIES.find(s => s.id === need)?.name}」，请调整行囊或更换路线。`; return }
  emit('play-complete', { pack: [...pack.value], route: route.value, records: { ...records.value } })
  msg.value = '已记录：物资、路线与见闻卡将回传剧情层。'
}
</script>
<template>
  <GameplayState :state="state" title="汉代行囊与路线" note="物资与交涉关联；允许保留不确定" @retry="emit('play-exit')">
    <div class="hanplay">
      <section class="hanplay__block" aria-label="行囊取舍">
        <h3>行囊取舍 · 最多3样</h3>
        <ul class="hanplay__grid">
          <li v-for="s in SUPPLIES" :key="s.id">
            <button type="button" :class="{ on: pack.includes(s.id) }" :aria-pressed="pack.includes(s.id)" @click="toggle(s.id)">
              <strong>{{ s.name }}</strong><small>{{ s.use }}</small><small class="cost">{{ s.cost }}</small>
            </button>
          </li>
        </ul>
      </section>
      <section class="hanplay__block" aria-label="路线选择">
        <h3>路线选择 · 亲见实线 / 转述虚线 / 推测雾线</h3>
        <ul class="hanplay__grid">
          <li v-for="r in ROUTES" :key="r.id">
            <button type="button" :class="{ on: route === r.id }" :aria-pressed="route === r.id" @click="route = r.id">
              <strong>{{ r.name }}</strong><small>{{ r.desc }}</small>
            </button>
          </li>
        </ul>
      </section>
      <section class="hanplay__block" aria-label="见闻记录">
        <h3>见闻记录卡 · 允许保留“不确定”</h3>
        <div class="hanplay__form">
          <label>地名<input v-model="records.place" placeholder="如：敦煌 / 关隘区域" /></label>
          <label>人物<input v-model="records.person" placeholder="如：向导、译者" /></label>
          <label>物品<input v-model="records.item" placeholder="如：织锦、马具" /></label>
          <label>置信度
            <select v-model="records.confidence"><option>亲见</option><option>转述</option><option>推测</option><option>不确定</option></select>
          </label>
        </div>
      </section>
      <p v-if="msg" class="hanplay__msg" role="status">{{ msg }}</p>
      <div class="hanplay__foot">
        <button type="button" class="ghost" @click="emit('play-exit')">返回剧情</button>
        <button type="button" class="primary" @click="submit">完成并回传剧情</button>
      </div>
    </div>
  </GameplayState>
</template>
<style scoped>
.hanplay{display:flex;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--color-border);border-radius:var(--radius-card);background:var(--color-panel)}
.hanplay__block h3{font-size:var(--fs-body-s);color:var(--chapter-accent);margin-bottom:8px}
.hanplay__grid{list-style:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin:0;padding:0}
.hanplay__grid button{width:100%;min-height:44px;text-align:left;padding:10px;border:1px solid var(--color-border);border-radius:var(--radius-btn);background:#fff;color:var(--color-ink-700);display:flex;flex-direction:column;gap:2px}
.hanplay__grid button.on{border-color:var(--chapter-accent);box-shadow:inset 3px 0 0 var(--chapter-accent)}
.hanplay__grid small{font-size:var(--fs-caption);color:var(--color-ink-500)} .cost{color:var(--evidence-disputed)}
.hanplay__form{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
.hanplay__form label{display:flex;flex-direction:column;gap:4px;font-size:var(--fs-caption);color:var(--color-ink-500)}
.hanplay__form input,.hanplay__form select{min-height:44px;border:1px solid var(--color-border);border-radius:var(--radius-btn);padding:0 10px;font-size:var(--fs-body-s)}
.hanplay__msg{font-size:var(--fs-caption);color:var(--color-ink-700);background:var(--color-paper-100);border-radius:var(--radius-btn);padding:8px 12px}
.hanplay__foot{display:flex;justify-content:flex-end;gap:8px}
.primary{min-height:44px;padding:0 18px;border-radius:var(--radius-btn);background:var(--chapter-accent);color:#fff;border:1px solid var(--chapter-accent)}
.ghost{min-height:44px;padding:0 18px;border-radius:var(--radius-btn);background:#fff;border:1px solid var(--color-border);color:var(--color-ink-700)}
@media (max-width:900px){.hanplay{padding:12px}.hanplay__grid{grid-template-columns:1fr 1fr}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
