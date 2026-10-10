<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GlobalHeader from '@/components/global/GlobalHeader.vue'
import DsButton from '@/components/ds/DsButton.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
import { useExplorationStore } from '@/stores/exploration'
import {
  createGenerationJob,
  getCocreationElements,
  validateCocreation,
} from '@/api/endpoints'
import type {
  ApplicationType,
  CocreationElement,
  CompositionOption,
  GenerationResult,
} from '@/types'

/**
 * C09 AI 共创工作台（当代章节 §19 / 设计系统 §61 / §62）
 *
 * 流程：元素 → 用途 → 构图 → 来源确认 → 生成 → 结果说明
 *
 * 硬性规则：
 *  - 用户不能跳过「来源确认」直接生成；
 *  - 生成结果永远标注「AI辅助文化创意作品 · 非传统羌绣原作」；
 *  - 权利校验不通过的元素不能进入生成流程；
 *  - 权利接口失败时默认不生成。
 */
const route = useRoute()
const router = useRouter()
const chapterStore = useChapterStore()
const exploration = useExplorationStore()

const chapter = computed(() => chapterStore.current)

const step = ref(1)
const STEPS = ['文化元素', '用途', '构图', '来源确认', '生成'] as const

const elements = ref<CocreationElement[]>([])
const selectedIds = ref<string[]>([])
const application = ref<ApplicationType | ''>('')
const composition = ref<CompositionOption | ''>('')
const confirmed = ref(false)

const validating = ref(false)
const generating = ref(false)
const blockedIds = ref<string[]>([])
const warnings = ref<string[]>([])
const result = ref<GenerationResult | null>(null)
const errorMsg = ref('')
const usingControlledDemo = ref(false)

/**
 * 离线目录只包含 content/contemporary 中同时满足：
 * rights.can_use_for_generation=true + policy=ALLOW_COMBINATION 的项目自绘示意元素。
 * 它不把任何传统纹样或权利未知素材临时放行。
 */
const CONTROLLED_DEMO_ELEMENTS: CocreationElement[] = [
  {
    id: 'pattern_demo_flora_01',
    name: '花草题材（数字示意图）',
    entity_type: 'PatternElement',
    short_summary: '项目自绘的花草题材数字示意图，不代表任何具体传统纹样。',
    meaning_status: 'GENERAL_CATEGORY_ONLY',
    rights_record_id: 'rights_pattern_demo_flora_01',
    generation_policy_id: 'policy_pattern_demo_flora_01',
    policy_type: 'ALLOW_COMBINATION',
    generatable: true,
  },
  {
    id: 'pattern_demo_bird_01',
    name: '飞禽走兽题材（数字示意图）',
    entity_type: 'PatternElement',
    short_summary: '项目自绘的题材类别示意图，不记录传世作品，也不解释固定寓意。',
    meaning_status: 'GENERAL_CATEGORY_ONLY',
    rights_record_id: 'rights_pattern_demo_bird_01',
    generation_policy_id: 'policy_pattern_demo_bird_01',
    policy_type: 'ALLOW_COMBINATION',
    generatable: true,
  },
  {
    id: 'pattern_demo_geometric_01',
    name: '几何构图（数字示意图）',
    entity_type: 'PatternElement',
    short_summary: '平台自绘的通用几何排列示意，不代表任何特定传统纹样。',
    meaning_status: 'GENERAL_CATEGORY_ONLY',
    rights_record_id: 'rights_pattern_demo_geometric_01',
    generation_policy_id: 'policy_pattern_demo_geometric_01',
    policy_type: 'ALLOW_COMBINATION',
    generatable: true,
  },
  {
    id: 'pattern_demo_composite_01',
    name: '组合构图（数字示意图）',
    entity_type: 'PatternElement',
    short_summary: '项目自绘的多元素组合流程示意，不对应具体传统纹样。',
    meaning_status: 'GENERAL_CATEGORY_ONLY',
    rights_record_id: 'rights_pattern_demo_composite_01',
    generation_policy_id: 'policy_pattern_demo_composite_01',
    policy_type: 'ALLOW_COMBINATION',
    generatable: true,
  },
]

const APPLICATIONS: { key: ApplicationType; label: string }[] = [
  { key: 'bookmark', label: '书签' },
  { key: 'poster', label: '海报' },
  { key: 'phone_wallpaper', label: '手机壁纸' },
  { key: 'packaging_concept', label: '包装概念' },
  { key: 'pattern_tile', label: '连续纹样' },
]

const COMPOSITIONS: { key: CompositionOption; label: string; desc: string }[] = [
  { key: 'CENTERED', label: '居中', desc: '主体居中，四周留白' },
  { key: 'BORDER', label: '边框', desc: '纹样沿边缘环绕' },
  { key: 'REPEAT', label: '重复', desc: '单位纹样连续排列' },
  { key: 'SYMMETRIC', label: '对称', desc: '左右或四方对称' },
  { key: 'FREE_MODERN', label: '自由现代', desc: '现代构图，不追求对称' },
]

onMounted(async () => {
  const id = SLUG_TO_ID[route.params.slug as keyof typeof SLUG_TO_ID]
  if (!id) return
  if (chapterStore.current?.id !== id) await chapterStore.loadChapter(id)
  await exploration.ensureSession(id)
  exploration.track('COCREATION_START', {}, id)

  try {
    elements.value = await getCocreationElements(id)
  } catch {
    elements.value = CONTROLLED_DEMO_ELEMENTS
    usingControlledDemo.value = true
  }
})

const selectedElements = computed(() =>
  elements.value.filter((e) => selectedIds.value.includes(e.id)),
)

/**
 * 只有明确允许生成、且权利记录允许的元素才能被选中。
 * `generatable` 由后端依据 generation_policy + rights_record 判定 ——
 * 「知识可以展示」不等于「素材可以用于生成」，这是两套权限。
 */
function canSelect(e: CocreationElement): boolean {
  return e.generatable
}

function toggle(id: string) {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter((x) => x !== id)
  } else {
    selectedIds.value = [...selectedIds.value, id]
  }
}

const canNext = computed(() => {
  switch (step.value) {
    case 1:
      return selectedIds.value.length > 0
    case 2:
      return !!application.value
    case 3:
      return !!composition.value
    case 4:
      return confirmed.value
    default:
      return false
  }
})

function next() {
  if (!canNext.value) return
  step.value = Math.min(5, step.value + 1)
}
function prev() {
  step.value = Math.max(1, step.value - 1)
}

/** 第 5 步：先权利校验，再生成 */
async function generate() {
  if (!application.value || !composition.value) return
  generating.value = true
  errorMsg.value = ''
  blockedIds.value = []
  warnings.value = []
  result.value = null

  try {
    if (usingControlledDemo.value) {
      result.value = {
        asset_id: 'asset_qiang_fallback_sample_v1',
        generation_id: 'controlled-offline-sample-v1',
        image_url: '/assets/contemporary/cocreation-sample-v1.png',
        label: 'AI辅助文化创意作品 · 非传统羌绣原作',
        is_fallback_sample: true,
        used_element_ids: [...selectedIds.value],
        ai_added_note: '现代构图、留白与配色变化；未新增或解释任何传统文化寓意。',
        source_ids: [],
        model_name: '离线演示保障样例',
        prompt_template_version: 'offline-controlled-v1',
      }
      exploration.track(
        'COCREATION_COMPLETE',
        { metadata: { fallback: true, sample: 'offline-controlled-v1' } },
        chapterStore.current?.id,
      )
      return
    }

    const check = await validateCocreation({
      element_ids: selectedIds.value,
      application_type: application.value,
      composition_option: composition.value,
    })

    if (!check.valid) {
      blockedIds.value = check.blocked_element_ids
      warnings.value = check.warning_codes
      errorMsg.value =
        '你选择的一个元素目前仅允许展示，暂不能用于AI共创。请移除后再试。'
      generating.value = false
      return
    }

    const res = await createGenerationJob({
      exploration_session_id: exploration.progress?.session_id,
      element_ids: selectedIds.value,
      application_type: application.value,
      composition_option: composition.value,
    })

    result.value = res
    exploration.track('COCREATION_COMPLETE', {}, chapterStore.current?.id)
  } catch (e: any) {
    // 权利接口失败时默认不生成
    if (e?.response?.status === 403) {
      errorMsg.value = '你选择的一个元素目前仅允许展示，暂不能用于AI共创。'
    } else if (e?.response?.status === 504) {
      errorMsg.value = '生成暂时没有完成。你可以重试，或查看演示保障作品。'
    } else {
      errorMsg.value = '生成暂时没有完成，请稍后重试。'
    }
  } finally {
    generating.value = false
  }
}

function reset() {
  step.value = 1
  selectedIds.value = []
  application.value = ''
  composition.value = ''
  confirmed.value = false
  result.value = null
  errorMsg.value = ''
  blockedIds.value = []
}

const appLabel = computed(
  () => APPLICATIONS.find((a) => a.key === application.value)?.label ?? '',
)
const compLabel = computed(
  () => COMPOSITIONS.find((c) => c.key === composition.value)?.label ?? '',
)
</script>

<template>
  <div v-if="chapter" class="page">
    <GlobalHeader />

    <main class="co page-body">
      <header class="co__head">
        <p class="co__eyebrow">RIGHTS LEDGER · 09 / CONTEMPORARY</p>
        <h1 class="co__title">授权共创工作台</h1>
        <p class="co__sub">
          先核对作品、用途与权利，再启动生成。这里记录的不只是结果，也记录谁允许了什么。
        </p>
      </header>

      <!-- Stepper -->
      <ol class="co__steps">
        <li
          v-for="(s, i) in STEPS"
          :key="s"
          class="co__step"
          :class="{ 'is-on': step === i + 1, 'is-done': step > i + 1 }"
        >
          <span class="co__step-num">
            <DsIcon v-if="step > i + 1" name="check" :size="12" />
            <template v-else>{{ i + 1 }}</template>
          </span>
          <span class="co__step-label">{{ s }}</span>
        </li>
      </ol>

      <!-- 固定警示 -->
      <p class="co__warn">
        <DsIcon name="alert" :size="15" />
        <span>生成结果为AI辅助文化创意作品，不是传统羌绣原作。</span>
      </p>

      <section class="co__body">
        <!-- 1 元素 -->
        <div v-if="step === 1" class="co__pane">
          <h2 class="co__h2">选择文化元素</h2>
          <p class="co__note">
            只有完成来源与权利审核、且允许用于共创的元素才能被选择。
          </p>
          <p v-if="usingControlledDemo" class="co__offline-note">
            当前使用离线演示目录：仅加载内容库中标记“可用于生成”的项目自绘示意元素（内容状态待终审）；传统纹样与权利未知素材均未放行。
          </p>
          <div class="co__grid">
            <button
              v-for="e in elements"
              :key="e.id"
              class="co__card"
              :class="{
                'is-on': selectedIds.includes(e.id),
                'is-blocked': !canSelect(e),
              }"
              type="button"
              :disabled="!canSelect(e)"
              @click="toggle(e.id)"
            >
              <span class="co__card-name">{{ e.name }}</span>
              <span class="co__card-type">{{ e.entity_type }}</span>
              <span v-if="!canSelect(e)" class="co__card-badge co__card-badge--blocked">
                仅可展示
              </span>
              <span v-else-if="selectedIds.includes(e.id)" class="co__card-badge co__card-badge--on">
                已选
              </span>
            </button>
          </div>
          <p v-if="!elements.length" class="co__empty">
            当前没有可用于共创的文化元素。请先确认素材权利记录已审核完成。
          </p>
        </div>

        <!-- 2 用途 -->
        <div v-else-if="step === 2" class="co__pane">
          <h2 class="co__h2">选择用途</h2>
          <div class="co__options">
            <button
              v-for="a in APPLICATIONS"
              :key="a.key"
              class="co__option"
              :class="{ 'is-on': application === a.key }"
              type="button"
              @click="application = a.key"
            >
              {{ a.label }}
            </button>
          </div>
        </div>

        <!-- 3 构图 -->
        <div v-else-if="step === 3" class="co__pane">
          <h2 class="co__h2">选择构图</h2>
          <div class="co__options co__options--grid">
            <button
              v-for="c in COMPOSITIONS"
              :key="c.key"
              class="co__option co__option--card"
              :class="{ 'is-on': composition === c.key }"
              type="button"
              @click="composition = c.key"
            >
              <span class="co__option-title">{{ c.label }}</span>
              <span class="co__option-desc">{{ c.desc }}</span>
            </button>
          </div>
        </div>

        <!-- 4 来源确认 -->
        <div v-else-if="step === 4" class="co__pane">
          <h2 class="co__h2">确认来源与使用范围</h2>
          <p class="co__note">请逐项确认你选择使用的元素及其来源。</p>

          <ul class="co__confirm-list">
            <li v-for="e in selectedElements" :key="e.id" class="co__confirm-item">
              <div class="co__confirm-head">
                <span class="co__confirm-name">{{ e.name }}</span>
                <span class="co__confirm-src">
                  来源：{{ e.policy_type === 'ALLOW_COMBINATION' ? '已审核并授权共创' : '仅可展示' }}
                </span>
              </div>
              <p v-if="e.short_summary" class="co__confirm-desc">{{ e.short_summary }}</p>
              <p class="co__confirm-rights">
                <span class="co__rights-tag">可网页展示</span>
                <span class="co__rights-tag" :class="{ off: !canSelect(e) }">可生成参考</span>
                <span class="co__rights-tag off">模型训练：不允许</span>
              </p>
            </li>
          </ul>

          <label class="co__checkbox">
            <input v-model="confirmed" type="checkbox" />
            <span>我知道生成结果是AI辅助文化创意，不等同于传统羌绣原作。</span>
          </label>
        </div>

        <!-- 5 生成 -->
        <div v-else class="co__pane">
          <h2 class="co__h2">生成</h2>

          <div class="co__summary">
            <p><span>元素：</span>{{ selectedElements.map((e) => e.name).join(' / ') }}</p>
            <p><span>用途：</span>{{ appLabel }}</p>
            <p><span>构图：</span>{{ compLabel }}</p>
          </div>

          <p v-if="errorMsg" class="co__error">
            <DsIcon name="alert" :size="15" />
            <span>{{ errorMsg }}</span>
          </p>

          <!-- 结果卡 -->
          <article v-if="result" class="co__result">
            <div class="co__result-img">
              <img v-if="result.image_url" :src="result.image_url" alt="AI辅助文化创意作品" />
              <div v-else class="co__result-placeholder">
                <DsIcon name="palette" :size="34" />
              </div>
            </div>

            <div class="co__result-body">
              <p class="co__result-label">{{ result.label }}</p>
              <p v-if="result.is_fallback_sample" class="co__result-fallback">
                演示保障样例 · 非本次实时生成
              </p>

              <div class="co__result-rows">
                <p>
                  <span>使用元素：</span>
                  {{ selectedElements.map((e) => e.name).join(' / ') }}
                </p>
                <p v-if="result.ai_added_note">
                  <span>AI新增：</span>{{ result.ai_added_note }}
                </p>
              </div>

              <div class="co__result-actions">
                <DsButton variant="secondary" @click="reset">
                  <DsIcon name="refresh" :size="15" />
                  <span>重新组合</span>
                </DsButton>
                <DsButton variant="ghost" @click="router.push(`/chapter/${route.params.slug}/graph`)">
                  <DsIcon name="nodes" :size="15" />
                  <span>查看文化来源</span>
                </DsButton>
              </div>
            </div>
          </article>

          <div v-else class="co__generate">
            <DsButton size="l" :loading="generating" :disabled="generating" @click="generate">
              <DsIcon v-if="!generating" name="sparkle" :size="17" />
              <span>{{ generating ? '正在生成……' : '开始生成' }}</span>
            </DsButton>
            <p class="co__generate-note">
              生成前会先校验每个元素的使用权限。没有明确授权的元素不会进入生成流程。
            </p>
          </div>
        </div>
      </section>

      <!-- 步骤控制 -->
      <footer class="co__foot">
        <DsButton v-if="step > 1" variant="ghost" @click="prev">
          <DsIcon name="arrow-left" :size="15" />
          <span>上一步</span>
        </DsButton>
        <div class="co__foot-right">
          <DsButton
            v-if="step < 5"
            variant="primary"
            :disabled="!canNext"
            @click="next"
          >
            <span>下一步</span>
            <DsIcon name="arrow-right" :size="15" />
          </DsButton>
        </div>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.co {
  display: flex;
  flex-direction: column;
  gap: var(--sp-5, 20px);
  padding-top: var(--sp-8);
  padding-bottom: var(--sp-12);
  max-width: 1080px;
}
.page{background:radial-gradient(circle at 82% 8%,rgba(195,163,91,.12),transparent 26%),linear-gradient(135deg,#edf2e9,#e4eee7)}
.co__head{position:relative;padding:0 0 19px 18px;border-left:2px solid var(--chapter-accent);border-bottom:1px solid rgba(40,95,97,.14)}
.co__eyebrow{margin-bottom:7px;font-size:8px;letter-spacing:.19em;color:var(--color-scroll-gold)}

.co__title {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  color: var(--color-ink-900);
}
.co__sub {
  margin-top: var(--sp-2);
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  max-width: 660px;
}

/* ---------- Stepper ---------- */
.co__steps {
  display: flex;
  list-style: none;
  margin: var(--sp-4) 0 0;
  padding: 0;
  gap: 6px;
  padding:9px;
  border:1px solid rgba(40,95,97,.14);
  background:rgba(249,250,242,.62);
}
.co__step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding:9px 8px;
  border-bottom: 2px solid rgba(40,95,97,.12);
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
}
.co__step.is-on {
  border-color: var(--chapter-accent);
  color: var(--chapter-accent);
  font-weight: 600;
}
.co__step.is-done {
  border-color: color-mix(in srgb, var(--chapter-accent) 45%, transparent);
  color: var(--color-ink-700);
}
.co__step-num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 11px;
  border: 1.4px solid currentColor;
  flex: none;
}
.co__step.is-done .co__step-num {
  background: var(--chapter-accent);
  border-color: var(--chapter-accent);
  color: #fff;
}

.co__warn {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-card);
  background: color-mix(in srgb, var(--color-warning) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-warning) 32%, transparent);
  color: var(--color-warning);
  font-size: var(--fs-body-s);
}

/* ---------- 内容 ---------- */
.co__body {
  min-height: 320px;
  padding:25px;
  border:1px solid rgba(40,95,97,.16);
  background:rgba(250,250,243,.76);
  box-shadow:0 20px 60px rgba(45,76,70,.08),inset 0 0 0 5px rgba(255,255,255,.26);
}
.co__h2 {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  margin-bottom: var(--sp-3);
}
.co__note {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  margin-bottom: var(--sp-5, 20px);
}
.co__offline-note {
  margin: 0 0 var(--sp-4);
  padding: 8px 12px;
  border-left: 2px solid var(--color-scroll-gold);
  background: rgba(255,255,255,.46);
  color: rgba(41,69,74,.72);
  font-size: var(--fs-caption);
}
.co__empty {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  padding: var(--sp-8) 0;
}

.co__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--sp-3);
}
.co__card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: #fff;
  text-align: left;
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    box-shadow var(--dur-fast) var(--ease-standard);
}
.co__card:hover:not(:disabled) {
  border-color: var(--chapter-accent);
}
.co__card.is-on {
  border-color: var(--chapter-accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--chapter-accent) 20%, transparent);
}
.co__card.is-blocked {
  opacity: 0.5;
  cursor: not-allowed;
}
.co__card-name {
  font-size: var(--fs-body);
  color: var(--color-ink-900);
}
.co__card-type {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.co__card-badge {
  position: absolute;
  top: var(--sp-2);
  right: var(--sp-2);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-pill);
}
.co__card-badge--on {
  background: var(--chapter-accent);
  color: #fff;
}
.co__card-badge--blocked {
  background: rgba(65, 55, 42, 0.1);
  color: var(--color-ink-500);
}

.co__options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}
.co__options--grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}
.co__option {
  padding: 10px 20px;
  border-radius: var(--radius-btn);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.co__option:hover {
  border-color: var(--chapter-accent);
}
.co__option.is-on {
  border-color: var(--chapter-accent);
  background: color-mix(in srgb, var(--chapter-accent) 10%, #fff);
  color: var(--chapter-accent);
  font-weight: 600;
}
.co__option--card {
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: flex-start;
  text-align: left;
  padding: var(--sp-4);
}
.co__option-title {
  font-size: var(--fs-body);
}
.co__option-desc {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

/* ---------- 确认 ---------- */
.co__confirm-list {
  list-style: none;
  margin: 0 0 var(--sp-6);
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.co__confirm-item {
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  background: #fff;
}
.co__confirm-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
}
.co__confirm-name {
  font-size: var(--fs-body);
  color: var(--color-ink-900);
  font-weight: 500;
}
.co__confirm-src {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}
.co__confirm-desc {
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  margin-bottom: var(--sp-3);
}
.co__confirm-rights {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.co__rights-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--color-success) 14%, transparent);
  color: var(--color-success);
}
.co__rights-tag.off {
  background: rgba(65, 55, 42, 0.07);
  color: var(--color-ink-500);
}

.co__checkbox {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  border: 1px solid var(--color-border);
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  cursor: pointer;
}
.co__checkbox input {
  margin-top: 3px;
  accent-color: var(--chapter-accent);
}

/* ---------- 生成 ---------- */
.co__summary {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  margin-bottom: var(--sp-5, 20px);
}
.co__summary span {
  color: var(--color-ink-500);
}

.co__error {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-card);
  background: color-mix(in srgb, var(--color-error) 9%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-error) 30%, transparent);
  color: var(--color-error);
  font-size: var(--fs-body-s);
  margin-bottom: var(--sp-5, 20px);
}

.co__generate {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sp-3);
}
.co__generate-note {
  font-size: var(--fs-caption);
  color: var(--color-ink-500);
}

/* ---------- 结果卡 ---------- */
.co__result {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--sp-6);
  padding: var(--sp-6);
  border-radius: var(--radius-card);
  background: #fff;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}
.co__result-img {
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-paper-100);
  aspect-ratio: 1 / 1;
}
.co__result-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.co__result-placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: var(--color-ink-500);
  opacity: 0.5;
}
.co__result-label {
  font-size: var(--fs-body);
  font-weight: 600;
  color: var(--color-ink-900);
  margin-bottom: var(--sp-1);
}
.co__result-fallback {
  display: inline-block;
  font-size: var(--fs-caption);
  color: var(--color-warning);
  margin-bottom: var(--sp-3);
}
.co__result-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  margin: var(--sp-3) 0 var(--sp-5, 20px);
}
.co__result-rows span {
  color: var(--color-ink-500);
}
.co__result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

/* ---------- 步骤控制 ---------- */
.co__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--color-border);
}
.co__foot-right {
  margin-left: auto;
}
@media(max-width:700px){.co{padding-top:22px}.co__steps{overflow-x:auto}.co__step{min-width:92px}.co__step-label{font-size:10px}.co__body{padding:17px}.co__result{grid-template-columns:1fr}.co__head{padding-left:13px}.co__sub{line-height:1.7}}
</style>
