<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GAME_CATALOG } from '@/game/catalog'
import { getSoundEnabled, playGameCue, setSoundEnabled, type GameCue } from '@/game/audio'
import { useGameStore } from '@/stores/game'
import type { ChapterSlug } from '@/types'
import {
  FIVE_CHAPTER_STORIES,
  isStoryChapterSlug,
  type StoryChallenge,
  type StoryDialogueLine,
  type StoryEvidenceCard,
} from './fiveChapterStories'

interface SavedStoryState {
  sceneIndex: number
  dialogueStep: number
  completedScenes: string[]
  inspected: Record<string, string[]>
  answers: Record<string, string[]>
  classifications: Record<string, Record<string, string>>
  assemblies: Record<string, Record<string, string>>
  decisionId: string | null
  interludesSeen: string[]
  revisionCount: number
}

const route = useRoute()
const router = useRouter()
const game = useGameStore()
const slug = computed(() => route.params.slug as string)
const story = computed(() => isStoryChapterSlug(slug.value) ? FIVE_CHAPTER_STORIES[slug.value] : null)
const meta = computed(() => story.value ? GAME_CATALOG[story.value.slug] : null)

function emptyState(): SavedStoryState {
  return {
    sceneIndex: 0,
    dialogueStep: 0,
    completedScenes: [],
    inspected: {},
    answers: {},
    classifications: {},
    assemblies: {},
    decisionId: null,
    interludesSeen: [],
    revisionCount: 0,
  }
}

const state = reactive<SavedStoryState>(emptyState())
const hydrated = ref(false)
const feedback = ref('')
const archiveOpen = ref(false)
const transitioning = ref(false)
const largeText = ref(false)
const soundEnabled = ref(getSoundEnabled())
const interludeOpen = ref(false)
const pendingDecisionId = ref<string | null>(null)
let transitionTimer: number | undefined

const storageKey = computed(() => `tongxin.${slug.value}.story.v1`)
const currentScene = computed(() => story.value?.scenes[state.sceneIndex] ?? null)
const currentAct = computed(() => {
  if (!story.value || !currentScene.value) return null
  return story.value.acts.find((act) => act.sceneIds.includes(currentScene.value!.id)) ?? null
})
const challenge = computed(() => currentScene.value?.challenge ?? null)
const sceneDecisionId = computed(() => state.decisionId || game.stateFor(slug.value as ChapterSlug).decisionId)
const showDebugAnswers = import.meta.env.DEV

const debugAnswer = computed(() => {
  const task = challenge.value
  if (!task) return ''

  switch (task.kind) {
    case 'inspect':
      return '依次查验全部证据卡'
    case 'single':
    case 'multi':
      return task.correctIds
        .map((id) => task.options.find((option) => option.id === id)?.label ?? id)
        .join('；')
    case 'classify':
      return task.cards
        .map((card) => {
          const bin = task.bins.find((item) => item.id === card.correctBin)
          return `${card.label} → ${bin?.label ?? card.correctBin}`
        })
        .join('；')
    case 'assemble':
      return task.slots
        .map((slot) => {
          const option = slot.options.find((item) => item.id === slot.correctId)
          return `${slot.label} → ${option?.label ?? slot.correctId}`
        })
        .join('；')
    case 'final':
      return '本题无唯一答案；不同选择对应不同保护目标与代价'
  }
})

const effectiveDialogue = computed<StoryDialogueLine[]>(() => {
  const scene = currentScene.value
  if (!scene) return []
  const branch = sceneDecisionId.value ? scene.branchDialogue?.[sceneDecisionId.value] : undefined
  return branch?.length ? [...scene.dialogue, ...branch] : scene.dialogue
})
const currentLine = computed(() => effectiveDialogue.value[Math.min(state.dialogueStep, Math.max(0, effectiveDialogue.value.length - 1))])
const dialogueComplete = computed(() => state.dialogueStep >= effectiveDialogue.value.length - 1)
const sceneComplete = computed(() => currentScene.value ? state.completedScenes.includes(currentScene.value.id) : false)
const progress = computed(() => {
  if (!story.value) return 0
  return Math.round(((state.sceneIndex + (sceneComplete.value ? 1 : 0)) / story.value.scenes.length) * 100)
})
const sceneNumber = computed(() => String(state.sceneIndex + 1).padStart(2, '0'))
const totalScenes = computed(() => String(story.value?.scenes.length ?? 0).padStart(2, '0'))
const currentCharacter = computed(() => {
  if (!story.value || !currentLine.value) return null
  return story.value.characters.find((item) => item.name === currentLine.value?.speaker) ?? {
    name: currentLine.value.speaker,
    role: currentLine.value.role,
    mark: currentLine.value.speaker.slice(0, 1),
    color: story.value.accent,
  }
})
const evidenceCount = computed(() => Object.values(state.inspected).reduce((sum, ids) => sum + ids.length, 0) + state.completedScenes.length)
const isLastScene = computed(() => !!story.value && state.sceneIndex === story.value.scenes.length - 1)

const STORY_INTERLUDES: Record<string, Record<number, { eyebrow: string; title: string; summary: string; connection: string; next: string }>> = {
  han: {
    2: { eyebrow: '第一卷 · 路线已经分开', title: '传奇不是路线图', summary: '你已经把张骞出使、长期交通网络与锦护膊出土信息放回各自年代。它们可以关联，却不能被压缩成一次携带。', connection: '出使、尼雅与织锦仍能共同说明：跨区域联系由不同年代的行动与遗存逐步形成。', next: '下一卷：谁真正走在路上' },
    5: { eyebrow: '第二卷 · 关系强度已校准', title: '网络不属于一个人', summary: '路线由使者、商旅、工匠、地方节点和长期往来共同形成。接下来，你要把复杂证据压进一张短展签。', connection: '人物节点仍然重要，但网络也让匿名参与者、物品流动与长期往来看得见。', next: '下一卷：写下有边界的结论' },
  },
  'northern-wei': {
    2: { eyebrow: '第一卷 · 个案尺度', title: '墓志只替一个人留下文字', summary: '姓名、籍贯与生平线索可以确认墓主个案，却不能让一方墓志代表整个北魏社会。', connection: '一个人的姓名、籍贯与制度背景，仍能成为理解迁都与社会变化的具体入口。', next: '下一卷：让不同材料彼此校正' },
    5: { eyebrow: '第二卷 · 证据并置', title: '变化从来不是同一速度', summary: '石窟、墓志与器物呈现出延续、调整和并存。真正的展陈不必把它们剪成一条整齐路线。', connection: '交融不是单向替代；采用、改造、并存与延续可以同时构成变化。', next: '下一卷：决定主证物如何发言' },
  },
  tang: {
    2: { eyebrow: '第一卷 · 名字走出画框', title: '没有被画下，不等于无关', summary: '你确认了禄东赞在画中的位置，也沿使臣、接见与相关事件连接到画外人物。画面有边界，关系仍能继续。', connection: '一次相见之所以重要，不只因为谁被画下，还因为有人跨越地域，把原本遥远的双方带到彼此面前。', next: '下一卷：让图像、事件与翻译各自发言' },
    5: { eyebrow: '第二卷 · 三种记录', title: '翻译不是替人多说一句', summary: '图像保存相见，文献连接事件，翻译传递已经说出的意思。任何一方都不能用想象补完历史人物的私人心声。', connection: '真正的交流既需要把话送到对岸，也需要承认哪些话没有材料、不能替别人说。', next: '下一卷：相见之后怎样继续' },
  },
  qing: {
    2: { eyebrow: '第一卷 · 河岸第一夜', title: '空白不能替人挨饿', summary: '你没有替受潮名册编造一个完整家庭，也没有让名册空白挡住眼前救急。乌娜一家先被按眼前丁口记录，原册信息保留待核。', connection: '共同生活从具体责任开始：有人说明自己是谁，有人守住记录边界，也有人把物资赶到河岸。', next: '下一卷：分开三条路，看见许多个人' },
    5: { eyebrow: '第二卷 · 四方来援', title: '一碗粮之后，还要有明春', summary: '东归既有故土认同，也有政治、军事和生计等现实背景；抵达后的食衣、茶米、牲畜与牧地又承担不同时间尺度的需要。', connection: '接济不是静止的赏赐清单，而是多地筹措、长途转运、河岸分发和归来者参与重建共同组成的协作网络。', next: '下一卷：共同写下今夜与来日' },
  },
  contemporary: {
    2: { eyebrow: '第一卷 · 旧箱关系已复原', title: '一条重建链，不是单向救助', summary: '公共与社会支援提供条件，本地妇女学习、生产并逐步授艺，帮扶中心、合作社、企业与消费者把作品接入持续生活。', connection: '十几年后，这门技艺仍在不同县域、地区与民族的学习者之间流动。下一步要看清：共同学习怎样既产生连接，又不抹掉各自位置。', next: '下一卷：今天的学习网络' },
    5: { eyebrow: '第二卷 · 接针规则已完成', title: '共同学习，不等于做成同样', summary: '二十四只共创包分别保留作者、作品、问题与允许用途；AI生成的统一“同心纹样”退出，只保留转写、检索和关系记录。', connection: '规则写清还不等于关系发生。第一只试寄包将检验远方学生能否用自己的材料回应，并让问题真正回到工坊。', next: '下一卷：让一只箱子走完来回' },
  },
}

const currentInterlude = computed(() => STORY_INTERLUDES[slug.value]?.[state.sceneIndex] ?? null)

const nextCue = computed(() => {
  if (!dialogueComplete.value) return '点击对话框继续'
  if (challenge.value && !sceneComplete.value) return '完成当前证据操作后继续'
  if (isLastScene.value) return '封存本章记录'
  return '进入下一场'
})

function saveState() {
  if (!hydrated.value) return
  try {
    localStorage.setItem(storageKey.value, JSON.stringify(state))
  } catch {
    // 本地存档失败不阻断体验。
  }
}

function loadState() {
  Object.assign(state, emptyState())
  try {
    const raw = localStorage.getItem(storageKey.value)
    if (!raw) return
    const saved = JSON.parse(raw) as Partial<SavedStoryState>
    Object.assign(state, emptyState(), saved)
    if (story.value) {
      state.sceneIndex = Math.min(Math.max(0, state.sceneIndex), story.value.scenes.length - 1)
      state.dialogueStep = Math.min(Math.max(0, state.dialogueStep), Math.max(0, effectiveDialogue.value.length - 1))
    }
  } catch {
    Object.assign(state, emptyState())
  }
}

function inspectedIds(sceneId: string) {
  return state.inspected[sceneId] ?? (state.inspected[sceneId] = [])
}

function selectedIds(sceneId: string) {
  return state.answers[sceneId] ?? (state.answers[sceneId] = [])
}

function classAssignments(sceneId: string) {
  return state.classifications[sceneId] ?? (state.classifications[sceneId] = {})
}

function slotAssignments(sceneId: string) {
  return state.assemblies[sceneId] ?? (state.assemblies[sceneId] = {})
}

function markSceneComplete(success?: string) {
  const scene = currentScene.value
  const chapter = story.value
  if (!scene || !chapter) return
  if (!state.completedScenes.includes(scene.id)) state.completedScenes.push(scene.id)
  if (scene.evidenceId) game.mark(chapter.slug, 'INSPECT', scene.evidenceId)
  if (scene.marksLens) game.mark(chapter.slug, 'LENS')
  feedback.value = success ?? '本幕证据已记录。'
  playCue('confirm')
}

function inspectCard(card: StoryEvidenceCard) {
  const scene = currentScene.value
  const task = challenge.value
  if (!scene || task?.kind !== 'inspect' || sceneComplete.value) return
  const ids = inspectedIds(scene.id)
  if (!ids.includes(card.id)) ids.push(card.id)
  playCue('paper')
  feedback.value = card.detail
  if (task.cards.every((item) => ids.includes(item.id))) markSceneComplete(task.success)
}

function chooseOption(challengeValue: Extract<StoryChallenge, { kind: 'single' | 'multi' }>, id: string) {
  const scene = currentScene.value
  if (!scene || sceneComplete.value) return
  const ids = selectedIds(scene.id)
  if (challengeValue.kind === 'single') {
    state.answers[scene.id] = [id]
  } else if (ids.includes(id)) {
    state.answers[scene.id] = ids.filter((item) => item !== id)
  } else {
    ids.push(id)
  }
  feedback.value = ''
  playCue('paper')
}

function sameSet(a: string[], b: string[]) {
  return a.length === b.length && [...a].sort().every((value, index) => value === [...b].sort()[index])
}

function validateChoice(challengeValue: Extract<StoryChallenge, { kind: 'single' | 'multi' }>) {
  const scene = currentScene.value
  if (!scene) return
  if (sameSet(selectedIds(scene.id), challengeValue.correctIds)) markSceneComplete(challengeValue.success)
  else {
    state.revisionCount += 1
    feedback.value = challengeValue.retry
    playCue('warning')
  }
}

function assignBin(cardId: string, binId: string) {
  const scene = currentScene.value
  if (!scene || sceneComplete.value) return
  classAssignments(scene.id)[cardId] = binId
  feedback.value = ''
  playCue('paper')
}

function validateClassification(challengeValue: Extract<StoryChallenge, { kind: 'classify' }>) {
  const scene = currentScene.value
  if (!scene) return
  const assignments = classAssignments(scene.id)
  const allCorrect = challengeValue.cards.every((card) => assignments[card.id] === card.correctBin)
  if (allCorrect) markSceneComplete(challengeValue.success)
  else {
    state.revisionCount += 1
    feedback.value = challengeValue.retry
    playCue('warning')
  }
}

function assignSlot(slotId: string, optionId: string) {
  const scene = currentScene.value
  if (!scene || sceneComplete.value) return
  slotAssignments(scene.id)[slotId] = optionId
  feedback.value = ''
  playCue('paper')
}

function validateAssembly(challengeValue: Extract<StoryChallenge, { kind: 'assemble' }>) {
  const scene = currentScene.value
  if (!scene) return
  const assignments = slotAssignments(scene.id)
  const allCorrect = challengeValue.slots.every((slot) => assignments[slot.id] === slot.correctId)
  if (allCorrect) markSceneComplete(challengeValue.success)
  else {
    state.revisionCount += 1
    feedback.value = challengeValue.retry
    playCue('warning')
  }
}

function previewFinal(id: string) {
  if (!story.value || sceneComplete.value) return
  pendingDecisionId.value = id
  const choice = meta.value?.decision.choices.find((item) => item.id === id)
  feedback.value = choice ? `这条路线优先保护：${choice.protects}。你也将接受：${choice.cost}。` : ''
  playCue('paper')
}

function commitFinal() {
  if (!story.value || sceneComplete.value || !pendingDecisionId.value) return
  const id = pendingDecisionId.value
  state.decisionId = id
  game.choose(story.value.slug, id)
  markSceneComplete(meta.value?.decision.choices.find((item) => item.id === id)?.response)
}

function advance() {
  if (transitioning.value || !currentScene.value || !story.value) return
  if (!dialogueComplete.value) {
    state.dialogueStep += 1
    feedback.value = ''
    playCue('paper')
    return
  }
  if (challenge.value && !sceneComplete.value) {
    feedback.value = '先完成画面中央的证据操作。'
    playCue('warning')
    return
  }
  const checkpointKey = currentScene.value.id
  if (currentInterlude.value && !state.interludesSeen.includes(checkpointKey)) {
    state.interludesSeen.push(checkpointKey)
    interludeOpen.value = true
    playCue('transition')
    return
  }
  if (isLastScene.value) {
    game.mark(story.value.slug, 'COMPLETE')
    void router.push(`/chapter/${story.value.slug}/summary`)
    return
  }
  transitioning.value = true
  playCue('transition')
  feedback.value = ''
  transitionTimer = window.setTimeout(() => {
    state.sceneIndex += 1
    state.dialogueStep = 0
    transitioning.value = false
  }, 420)
}

function continueFromInterlude() {
  interludeOpen.value = false
  advance()
}

function onDialogueClick() {
  advance()
}

function onKeydown(event: KeyboardEvent) {
  const target = event.target as HTMLElement
  if (target.closest('button,a,input,select,textarea')) return
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    if (interludeOpen.value) continueFromInterlude()
    else advance()
  }
}

function resetStory() {
  if (!story.value) return
  try { localStorage.removeItem(storageKey.value) } catch { /* noop */ }
  game.resetChapter(story.value.slug)
  Object.assign(state, emptyState())
  archiveOpen.value = false
  interludeOpen.value = false
  pendingDecisionId.value = null
  feedback.value = '本章已从第一幕第一场重新开始。'
}

function toggleLargeText() {
  largeText.value = !largeText.value
  try { localStorage.setItem('tongxin.reading.largeText', largeText.value ? '1' : '0') } catch { /* noop */ }
}

function playCue(kind: GameCue) {
  playGameCue(kind, soundEnabled.value)
}

function toggleSound() {
  soundEnabled.value = !soundEnabled.value
  setSoundEnabled(soundEnabled.value)
  if (soundEnabled.value) playCue('confirm')
}

function challengeKindLabel(kind: StoryChallenge['kind']) {
  return ({ inspect: '证据查验', single: '单项判断', multi: '多项判断', classify: '证据分层', assemble: '结论组装', final: '核心抉择' })[kind]
}

function actForScene(sceneId: string) {
  return story.value?.acts.find((act) => act.sceneIds.includes(sceneId))
}

onMounted(() => {
  game.bootstrap()
  if (!story.value) {
    void router.replace('/timeline')
    return
  }
  loadState()
  try { largeText.value = localStorage.getItem('tongxin.reading.largeText') === '1' } catch { /* noop */ }
  hydrated.value = true
  game.mark(story.value.slug, 'ENTER')
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  if (transitionTimer) window.clearTimeout(transitionTimer)
})

watch(state, saveState, { deep: true })
</script>

<template>
  <div
    v-if="story && currentScene && meta && currentLine"
    class="chapter-story"
    :class="[`chapter-${story.slug}`, `framing-${currentScene.framing}`, `motif-${currentScene.motif}`, { 'is-transitioning': transitioning, 'is-challenge-active': dialogueComplete && challenge && !transitioning, 'is-large-text': largeText }]"
    :style="{ '--story-accent': story.accent, '--story-accent-soft': story.accentSoft, '--story-ink': story.ink }"
  >
    <header class="story-nav">
      <RouterLink to="/timeline" class="story-nav__back">← 千年行卷</RouterLink>
      <div class="story-nav__brand">
        <span>{{ meta.chapterMark }}</span>
        <strong>{{ story.archiveTitle }}</strong>
      </div>
      <div class="story-nav__progress" aria-label="章节剧情进度">
        <div><span>{{ currentAct?.label }} · 第 {{ sceneNumber }} 场</span><em>{{ currentScene.title }}</em></div>
        <ol aria-hidden="true">
          <li
            v-for="(scene, index) in story.scenes"
            :key="scene.id"
            :class="{ 'is-current': index === state.sceneIndex, 'is-done': state.completedScenes.includes(scene.id) }"
          />
        </ol>
        <b>{{ progress }}%</b>
      </div>
      <div class="story-nav__tools">
        <button type="button" class="story-nav__reading" :aria-pressed="largeText" @click="toggleLargeText">{{ largeText ? '标准字' : '大字' }}</button>
        <button type="button" class="story-nav__reading" :aria-pressed="soundEnabled" :title="soundEnabled ? '关闭音效' : '开启音效'" @click="toggleSound">{{ soundEnabled ? '音效开' : '音效关' }}</button>
        <button type="button" class="story-nav__archive" @click="archiveOpen = true">证据卷 <b>{{ evidenceCount }}</b></button>
      </div>
    </header>

    <main class="story-stage" :aria-label="`${currentScene.title}剧情场景`">
      <figure class="story-backdrop" aria-hidden="true">
        <img :key="currentScene.id" :src="currentScene.background" alt="" :style="{ objectPosition: currentScene.position || 'center' }" />
        <div class="story-backdrop__wash" />
        <div class="story-backdrop__signature">
          <i v-for="index in 5" :key="index" />
        </div>
      </figure>

      <div class="story-heading">
        <p><b>{{ sceneNumber }}</b>{{ currentAct?.title }} · {{ currentScene.place }}</p>
        <h1>{{ currentScene.title }}</h1>
        <span>{{ currentScene.objective }}</span>
      </div>

      <section
        v-if="currentCharacter"
        :key="`${currentScene.id}-${state.dialogueStep}-${currentCharacter.name}`"
        class="speaker-presence"
        :class="`is-${currentLine.side || 'left'}`"
        :style="{ '--speaker-color': currentCharacter.color }"
        aria-hidden="true"
      >
        <div class="speaker-presence__halo" />
        <div class="speaker-presence__seal">{{ currentCharacter.mark }}</div>
        <p>{{ currentCharacter.name }}</p>
        <span>{{ currentCharacter.role }}</span>
      </section>

      <section v-if="dialogueComplete && challenge && !transitioning" class="evidence-workbench" :class="`is-${challenge.kind}`">
        <header class="evidence-workbench__head">
          <span>档案工作台 · {{ challengeKindLabel(challenge.kind) }}</span>
          <h2>{{ challenge.title }}</h2>
          <p>{{ challenge.instruction }}</p>
          <small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small>
        </header>

        <div v-if="challenge.kind === 'inspect'" class="inspect-grid">
          <button
            v-for="card in challenge.cards"
            :key="card.id"
            type="button"
            :class="{ 'is-seen': inspectedIds(currentScene.id).includes(card.id) }"
            @click="inspectCard(card)"
          >
            <span>{{ card.stamp }}</span><strong>{{ card.label }}</strong><small class="inspect-card__detail">{{ card.detail }}</small><i>查验</i>
          </button>
        </div>

        <div v-else-if="challenge.kind === 'single' || challenge.kind === 'multi'" class="option-grid">
          <button
            v-for="option in challenge.options"
            :key="option.id"
            type="button"
            :class="{ 'is-selected': selectedIds(currentScene.id).includes(option.id) }"
            @click="chooseOption(challenge, option.id)"
          >
            <i>{{ challenge.kind === 'multi' ? '◇' : '○' }}</i><span><strong>{{ option.label }}</strong><small>{{ option.detail }}</small></span>
          </button>
          <button type="button" class="validate-button" :disabled="selectedIds(currentScene.id).length === 0 || sceneComplete" @click="validateChoice(challenge)">
            {{ sceneComplete ? '判断已记入证据卷' : '核验判断' }}
          </button>
        </div>

        <div v-else-if="challenge.kind === 'classify'" class="classify-board">
          <article v-for="card in challenge.cards" :key="card.id" class="classify-card">
            <div><strong>{{ card.label }}</strong><p>{{ card.detail }}</p></div>
            <div class="classify-card__bins">
              <button
                v-for="bin in challenge.bins"
                :key="bin.id"
                type="button"
                :class="{ 'is-selected': classAssignments(currentScene.id)[card.id] === bin.id }"
                @click="assignBin(card.id, bin.id)"
              >{{ bin.label }}</button>
            </div>
          </article>
          <button type="button" class="validate-button" :disabled="Object.keys(classAssignments(currentScene.id)).length < challenge.cards.length || sceneComplete" @click="validateClassification(challenge)">
            {{ sceneComplete ? '分层已完成' : '统一核验分层' }}
          </button>
        </div>

        <div v-else-if="challenge.kind === 'assemble'" class="assemble-board">
          <article v-for="slot in challenge.slots" :key="slot.id" class="assemble-slot">
            <header><span>{{ slot.label }}</span><strong>{{ slot.prompt }}</strong></header>
            <button
              v-for="option in slot.options"
              :key="option.id"
              type="button"
              :class="{ 'is-selected': slotAssignments(currentScene.id)[slot.id] === option.id }"
              @click="assignSlot(slot.id, option.id)"
            ><strong>{{ option.label }}</strong><small>{{ option.detail }}</small></button>
          </article>
          <button type="button" class="validate-button" :disabled="Object.keys(slotAssignments(currentScene.id)).length < challenge.slots.length || sceneComplete" @click="validateAssembly(challenge)">
            {{ sceneComplete ? '结论链已成立' : '核验完整结论' }}
          </button>
        </div>

        <div v-else-if="challenge.kind === 'final'" class="decision-grid">
          <button
            v-for="choice in meta.decision.choices"
            :key="choice.id"
            type="button"
            :class="{ 'is-selected': (pendingDecisionId || sceneDecisionId) === choice.id }"
            :disabled="sceneComplete && sceneDecisionId !== choice.id"
            @click="previewFinal(choice.id)"
          >
            <span>{{ choice.label }}</span>
            <small class="decision-card__detail">{{ choice.description }}</small>
            <small class="decision-card__tradeoff"><b>保护</b>{{ choice.protects }}<em>代价</em>{{ choice.cost }}</small>
            <i>{{ sceneDecisionId === choice.id ? '已写入' : pendingDecisionId === choice.id ? '待确认' : '查看取舍' }}</i>
          </button>
          <button class="decision-commit" type="button" :disabled="!pendingDecisionId || sceneComplete" @click="commitFinal">
            {{ sceneComplete ? '本次选择已写入档案' : pendingDecisionId ? '确认承担这条路线的后果' : '先选择一条路线，查看它保护什么、又放弃什么' }}
          </button>
        </div>
      </section>

      <div v-if="feedback" class="story-feedback" role="status">{{ feedback }}</div>

      <button
        type="button"
        class="dialogue-panel"
        :class="[`tone-${currentLine.tone || 'normal'}`, { 'is-ready': dialogueComplete && (!challenge || sceneComplete) }]"
        @pointerdown="onDialogueClick"
      >
        <span class="dialogue-panel__name">{{ currentLine.speaker }}</span>
        <span class="dialogue-panel__role">{{ currentLine.role }}</span>
        <span :key="`${currentScene.id}-${state.dialogueStep}`" class="dialogue-panel__text">{{ currentLine.text }}</span>
        <span class="dialogue-panel__cue"><kbd>Enter</kbd>{{ nextCue }} <i>◆</i></span>
      </button>

      <div v-if="transitioning" class="scene-transition" aria-live="polite">
        <span>下一场</span>
        <strong>{{ story.scenes[Math.min(state.sceneIndex + 1, story.scenes.length - 1)]?.title }}</strong>
      </div>
    </main>

    <footer class="story-footnote">
      <span>{{ currentScene.layer }} · {{ currentScene.layerNote }}</span>
      <span>历史图片、AI情境图与剧情重建均按来源类型标注</span>
    </footer>

    <div v-if="interludeOpen && currentInterlude" class="chapter-interlude" role="dialog" aria-modal="true" aria-label="阶段小结">
      <div class="chapter-interlude__thread" aria-hidden="true"><i /><i /><i /></div>
      <section>
        <span>{{ currentInterlude.eyebrow }}</span>
        <h2>{{ currentInterlude.title }}</h2>
        <p>{{ currentInterlude.summary }}</p>
        <aside><span>仍可确认的联系</span><p>{{ currentInterlude.connection }}</p></aside>
        <div><b>{{ evidenceCount }}</b><small>条证据与场景记录已进入本章档案</small></div>
        <button type="button" @click="continueFromInterlude">{{ currentInterlude.next }} <i>→</i></button>
      </section>
    </div>

    <div v-if="archiveOpen" class="archive-overlay" role="dialog" aria-modal="true" aria-label="本章证据卷">
      <button type="button" class="archive-overlay__shade" aria-label="关闭证据卷" @click="archiveOpen = false" />
      <aside class="archive-sheet">
        <header><div><span>{{ meta.chapterMark }}</span><h2>{{ story.archiveTitle }}</h2></div><button type="button" @click="archiveOpen = false">关闭</button></header>
        <p class="archive-sheet__subtitle">{{ story.subtitle }}</p>
        <section><span>本章核心问题</span><p>{{ story.themeQuestion }}</p></section>
        <section><span>玩家身份与任务</span><p>{{ story.playerRole }}</p></section>
        <section><span>剧情前提</span><p>{{ story.premise }}</p></section>
        <section><span>必须守住的边界</span><p>{{ story.boundary }}</p></section>
        <section>
          <span>已完成场景</span>
          <ol>
            <li v-for="scene in story.scenes" :key="scene.id" :class="{ done: state.completedScenes.includes(scene.id) }">
              <b>{{ String(Number(scene.id) + 1).padStart(2, '0') }}</b><em>{{ actForScene(scene.id)?.label }} · {{ scene.title }}</em><i>{{ state.completedScenes.includes(scene.id) ? '已记录' : '未完成' }}</i>
            </li>
          </ol>
        </section>
        <section v-if="sceneDecisionId"><span>核心抉择</span><p>{{ meta.decision.choices.find((item) => item.id === sceneDecisionId)?.label }}</p></section>
        <section><span>修订记录</span><p>本章共修订 {{ state.revisionCount }} 次。修订不是扣分，而是让判断回到证据边界。</p></section>
        <button type="button" class="archive-sheet__reset" @click="resetStory">从头体验本章</button>
      </aside>
    </div>
  </div>
</template>

<style scoped>
:global(html:has(.chapter-story)),:global(body:has(.chapter-story)){overflow:hidden;overscroll-behavior:none}
.chapter-story{height:100dvh;overflow:hidden;color:#f3ead8;background:#101817;font-family:var(--font-ui);--nav-h:64px;--foot-h:25px}
button{font:inherit}
.story-nav{height:var(--nav-h);display:grid;grid-template-columns:145px minmax(190px,.8fr) minmax(260px,1.4fr) 150px;align-items:center;gap:20px;padding:0 26px;border-bottom:1px solid color-mix(in srgb,var(--story-accent) 42%,transparent);background:color-mix(in srgb,var(--story-ink) 92%,#07100f);position:relative;z-index:30}
.story-nav__back{min-height:44px;display:flex;align-items:center;color:rgba(243,234,216,.56);font-size:11px;letter-spacing:.08em}.story-nav__back:hover{color:#fff}
.story-nav__brand{display:flex;align-items:baseline;gap:11px;min-width:0}.story-nav__brand span{font-size:9px;letter-spacing:.18em;color:var(--story-accent-soft)}.story-nav__brand strong{font-family:var(--font-display);font-size:18px;font-weight:500;white-space:nowrap}
.story-nav__progress{display:grid;grid-template-columns:50px 1fr 42px;align-items:center;gap:10px;font-size:9px;letter-spacing:.12em;color:rgba(243,234,216,.48)}.story-nav__progress i{height:3px;background:rgba(255,255,255,.08);overflow:hidden}.story-nav__progress b{display:block;height:100%;background:linear-gradient(90deg,var(--story-accent),var(--story-accent-soft));transition:width .4s ease}.story-nav__progress em{font-style:normal;color:var(--story-accent-soft)}
.story-nav__archive{min-height:40px;border:1px solid color-mix(in srgb,var(--story-accent) 54%,transparent);background:rgba(255,255,255,.025);color:var(--story-accent-soft);font-size:10px;letter-spacing:.09em}.story-nav__archive:hover{border-color:var(--story-accent-soft);color:#fff}
.story-stage{position:relative;height:calc(100dvh - var(--nav-h) - var(--foot-h));overflow:hidden;isolation:isolate}
.story-backdrop{position:absolute;z-index:-4;inset:0;margin:0;background:var(--story-ink);overflow:hidden;pointer-events:none}.story-backdrop img{width:100%;height:100%;object-fit:cover;filter:saturate(.62) contrast(1.08) brightness(.52);transform:scale(1.035);animation:backdrop-in 1.1s ease both}.story-backdrop__wash{position:absolute;inset:0;background:linear-gradient(90deg,color-mix(in srgb,var(--story-ink) 90%,transparent),transparent 43%,color-mix(in srgb,var(--story-ink) 72%,transparent)),linear-gradient(180deg,rgba(5,10,10,.32),transparent 52%,rgba(5,10,10,.83));mix-blend-mode:multiply}.story-backdrop::after{content:'';position:absolute;inset:0;opacity:.12;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 140 140' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.76' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.22'/%3E%3C/svg%3E");mix-blend-mode:screen}
.story-heading{position:absolute;z-index:5;left:28px;top:24px;max-width:340px;padding-left:16px;border-left:2px solid var(--story-accent)}.story-heading p{font-size:9px;letter-spacing:.14em;color:rgba(243,234,216,.48)}.story-heading h1{margin-top:5px;font-family:var(--font-display);font-size:25px;font-weight:500;color:#f4ead5}.story-heading span{display:block;margin-top:5px;font-size:10px;color:rgba(243,234,216,.58)}
.speaker-presence{position:absolute;z-index:2;top:17%;width:min(31vw,390px);height:45%;display:flex;flex-direction:column;align-items:center;justify-content:center;filter:drop-shadow(0 28px 34px rgba(0,0,0,.46));animation:speaker-in .45s ease both}.speaker-presence.is-left{left:4%}.speaker-presence.is-right{right:4%}.speaker-presence__halo{position:absolute;width:270px;aspect-ratio:1;border-radius:50%;border:1px solid color-mix(in srgb,var(--speaker-color) 65%,transparent);background:radial-gradient(circle,color-mix(in srgb,var(--speaker-color) 28%,transparent),transparent 64%);box-shadow:0 0 70px color-mix(in srgb,var(--speaker-color) 12%,transparent)}.speaker-presence__halo::before,.speaker-presence__halo::after{content:'';position:absolute;border-radius:50%;border:1px solid color-mix(in srgb,var(--speaker-color) 28%,transparent)}.speaker-presence__halo::before{inset:16%}.speaker-presence__halo::after{inset:32%}
.speaker-presence__seal{position:relative;width:120px;height:144px;display:grid;place-items:center;border:1px solid color-mix(in srgb,var(--speaker-color) 76%,#e8d6a9);background:linear-gradient(165deg,color-mix(in srgb,var(--speaker-color) 62%,rgba(12,21,20,.72)),rgba(8,13,13,.88));clip-path:polygon(12% 0,88% 0,100% 12%,100% 88%,88% 100%,12% 100%,0 88%,0 12%);font-family:var(--font-display);font-size:62px;color:#f0e1bf;text-shadow:0 2px 14px rgba(0,0,0,.4);box-shadow:inset 0 0 0 7px rgba(255,255,255,.035)}.speaker-presence p{position:relative;margin-top:17px;font-family:var(--font-display);font-size:19px;letter-spacing:.18em}.speaker-presence span{position:relative;margin-top:5px;font-size:9px;letter-spacing:.1em;color:rgba(243,234,216,.45)}
.evidence-workbench{position:absolute;z-index:8;left:50%;top:51%;transform:translate(-50%,-50%);width:min(790px,66vw);max-height:56%;overflow:auto;padding:18px;border:1px solid color-mix(in srgb,var(--story-accent) 55%,transparent);background:linear-gradient(145deg,color-mix(in srgb,var(--story-ink) 91%,rgba(10,15,14,.86)),rgba(15,24,22,.94));box-shadow:0 28px 80px rgba(0,0,0,.52),inset 0 0 0 1px rgba(255,255,255,.035);backdrop-filter:blur(14px);animation:workbench-in .35s ease both;scrollbar-width:thin;scrollbar-color:var(--story-accent) transparent}
.evidence-workbench__head{display:grid;grid-template-columns:90px 1fr;align-items:baseline;gap:3px 12px;padding-bottom:13px;border-bottom:1px solid rgba(255,255,255,.09)}.evidence-workbench__head>span{grid-row:1/3;font-size:8px;letter-spacing:.18em;color:var(--story-accent-soft)}.evidence-workbench__head h2{font-family:var(--font-display);font-size:18px;font-weight:500}.evidence-workbench__head p{font-size:9px;color:rgba(243,234,216,.48)}
.evidence-workbench__head .debug-answer{grid-column:2;display:block;margin-top:3px;font-size:8px;line-height:1.5;font-weight:500;letter-spacing:.03em;color:color-mix(in srgb,var(--story-accent) 78%,#725b31)}
.inspect-grid,.option-grid,.decision-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:13px}.inspect-grid>button,.option-grid>button:not(.validate-button),.decision-grid>button{min-height:126px;padding:14px;text-align:left;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.028);color:rgba(243,234,216,.76);transition:160ms ease}.inspect-grid>button:hover,.option-grid>button:not(.validate-button):hover,.decision-grid>button:hover{border-color:var(--story-accent);transform:translateY(-2px);background:color-mix(in srgb,var(--story-accent) 12%,transparent)}.inspect-grid>button.is-seen,.option-grid>button.is-selected,.decision-grid>button.is-selected{border-color:var(--story-accent-soft);background:color-mix(in srgb,var(--story-accent) 18%,transparent)}
.inspect-grid span{font-size:8px;letter-spacing:.13em;color:var(--story-accent-soft)}.inspect-grid strong{display:block;margin-top:13px;font-family:var(--font-display);font-size:17px;font-weight:500}.inspect-card__detail{display:block;margin-top:7px;font-size:9px;line-height:1.55;color:rgba(243,234,216,.48)}.inspect-grid i{display:block;margin-top:10px;font-style:normal;font-size:8px;color:rgba(243,234,216,.3)}
.option-grid>button:not(.validate-button){display:flex;gap:10px;min-height:94px}.option-grid>button>i{font-style:normal;color:var(--story-accent-soft)}.option-grid span{display:flex;flex-direction:column;gap:7px}.option-grid strong{font-family:var(--font-display);font-size:14px;font-weight:500}.option-grid small{font-size:9px;line-height:1.45;color:rgba(243,234,216,.43)}
.validate-button{grid-column:1/-1;min-height:39px;border:1px solid color-mix(in srgb,var(--story-accent) 58%,transparent);background:color-mix(in srgb,var(--story-accent) 16%,transparent);color:#f3ead8;font-size:10px;letter-spacing:.12em}.validate-button:disabled{opacity:.38}.validate-button:not(:disabled):hover{background:color-mix(in srgb,var(--story-accent) 28%,transparent)}
.classify-board,.assemble-board{display:grid;gap:8px;margin-top:13px}.classify-card{display:grid;grid-template-columns:minmax(150px,1fr) 1.55fr;gap:12px;align-items:center;padding:10px 11px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.025)}.classify-card strong{font-family:var(--font-display);font-size:13px;font-weight:500}.classify-card p{margin-top:3px;font-size:8px;line-height:1.4;color:rgba(243,234,216,.38)}.classify-card__bins{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:5px}.classify-card__bins button{min-height:34px;padding:4px;border:1px solid rgba(255,255,255,.1);background:transparent;color:rgba(243,234,216,.56);font-size:8px}.classify-card__bins button.is-selected{border-color:var(--story-accent-soft);background:color-mix(in srgb,var(--story-accent) 20%,transparent);color:#fff}
.assemble-board{grid-template-columns:repeat(3,1fr)}.assemble-slot{padding:11px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.025)}.assemble-slot header span{font-size:8px;letter-spacing:.13em;color:var(--story-accent-soft)}.assemble-slot header strong{display:block;margin-top:4px;min-height:30px;font-size:10px;font-weight:500;color:rgba(243,234,216,.65)}.assemble-slot>button{width:100%;min-height:64px;margin-top:7px;padding:8px;text-align:left;border:1px solid rgba(255,255,255,.09);background:transparent;color:rgba(243,234,216,.65)}.assemble-slot>button.is-selected{border-color:var(--story-accent-soft);background:color-mix(in srgb,var(--story-accent) 18%,transparent);color:#fff}.assemble-slot>button strong{display:block;font-size:9px;font-weight:500}.assemble-slot>button small{display:block;margin-top:4px;font-size:8px;line-height:1.35;color:rgba(243,234,216,.36)}
.decision-grid>button:not(.decision-commit){min-height:188px;display:flex;flex-direction:column}.decision-grid>button>span{font-family:var(--font-display);font-size:17px}.decision-card__detail{display:block;margin-top:8px;font-size:9px;line-height:1.55;color:rgba(243,234,216,.48)}.decision-card__tradeoff{display:grid;grid-template-columns:30px 1fr;gap:3px 7px;margin-top:10px;padding-top:9px;border-top:1px solid rgba(255,255,255,.08);text-align:left;font-size:8px;line-height:1.4;color:rgba(243,234,216,.53)}.decision-card__tradeoff b,.decision-card__tradeoff em{font-weight:500;font-style:normal;color:var(--story-accent-soft)}.decision-grid i{margin-top:auto;padding-top:10px;font-style:normal;font-size:8px;letter-spacing:.08em;color:var(--story-accent-soft)}.decision-grid button:disabled{opacity:.36}.decision-grid .decision-commit{grid-column:1/-1;min-height:43px;border-color:color-mix(in srgb,var(--story-accent) 68%,#56756d);background:#224f4d;color:#fff5dc;font-family:var(--font-display);font-size:12px}.decision-grid .decision-commit:disabled{background:rgba(35,70,67,.3);color:rgba(35,70,67,.48);border-color:rgba(35,70,67,.18)}
.story-feedback{position:absolute;z-index:12;left:50%;bottom:174px;transform:translateX(-50%);max-width:min(680px,80vw);padding:8px 15px;border:1px solid color-mix(in srgb,var(--story-accent) 50%,transparent);background:rgba(10,18,17,.92);box-shadow:0 8px 30px rgba(0,0,0,.35);font-size:9px;color:var(--story-accent-soft);text-align:center}
.dialogue-panel{position:absolute;z-index:15;left:50%;bottom:24px;transform:translateX(-50%);width:min(900px,calc(100% - 52px));min-height:126px;padding:18px 22px 29px;text-align:left;border:1px solid color-mix(in srgb,var(--story-accent) 50%,transparent);background:linear-gradient(115deg,color-mix(in srgb,var(--story-ink) 96%,rgba(8,14,13,.92)),rgba(13,22,20,.94));box-shadow:0 24px 70px rgba(0,0,0,.5),inset 0 0 0 1px rgba(255,255,255,.025);color:#f3ead8;cursor:pointer}.dialogue-panel>*{pointer-events:none}.dialogue-panel:hover{border-color:var(--story-accent-soft)}.dialogue-panel__name{font-family:var(--font-display);font-size:17px;color:var(--story-accent-soft)}.dialogue-panel__role{margin-left:10px;font-size:8px;letter-spacing:.09em;color:rgba(243,234,216,.36)}.dialogue-panel__text{display:block;margin-top:11px;font-family:var(--font-display);font-size:15px;line-height:1.72;color:rgba(243,234,216,.82);animation:line-in .28s ease both}.dialogue-panel__cue{position:absolute;right:18px;bottom:10px;font-size:8px;letter-spacing:.09em;color:rgba(243,234,216,.35)}.dialogue-panel__cue i{margin-left:7px;font-style:normal;color:var(--story-accent);animation:cue-pulse 1.5s ease infinite}.dialogue-panel.is-ready .dialogue-panel__cue{color:var(--story-accent-soft)}.dialogue-panel.tone-warning{border-left:3px solid #c37553}.dialogue-panel.tone-resolve{border-left:3px solid var(--story-accent-soft)}
.scene-transition{position:absolute;z-index:40;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:linear-gradient(90deg,var(--story-ink),color-mix(in srgb,var(--story-ink) 92%,#1d2d28),var(--story-ink));animation:transition-in .42s ease both}.scene-transition::before,.scene-transition::after{content:'';position:absolute;width:38%;height:1px;background:linear-gradient(90deg,transparent,var(--story-accent),transparent)}.scene-transition::before{top:45%}.scene-transition::after{bottom:43%}.scene-transition span{font-size:8px;letter-spacing:.3em;color:var(--story-accent-soft)}.scene-transition strong{margin-top:10px;font-family:var(--font-display);font-size:28px;font-weight:500}
.story-footnote{position:fixed;z-index:31;left:0;right:0;bottom:0;height:var(--foot-h);display:flex;justify-content:space-between;align-items:center;padding:0 16px;background:#08100f;border-top:1px solid rgba(255,255,255,.05);font-size:7px;letter-spacing:.04em;color:rgba(243,234,216,.28)}
.archive-overlay{position:fixed;z-index:80;inset:0}.archive-overlay__shade{position:absolute;inset:0;width:100%;height:100%;border:0;background:rgba(3,8,7,.7);backdrop-filter:blur(7px)}.archive-sheet{position:absolute;right:0;top:0;bottom:0;width:min(470px,92vw);overflow:auto;padding:25px;background:#eef0e5;color:#263f3e;box-shadow:-28px 0 80px rgba(0,0,0,.36)}.archive-sheet>header{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:16px;border-bottom:1px solid rgba(37,63,62,.16)}.archive-sheet>header span,.archive-sheet section>span{font-size:8px;letter-spacing:.15em;color:#8c6a38}.archive-sheet h2{margin-top:3px;font-family:var(--font-display);font-size:28px;font-weight:500}.archive-sheet>header button,.archive-sheet__reset{min-height:38px;border:1px solid rgba(37,63,62,.18);background:transparent;color:#355b58}.archive-sheet>header button{padding:0 13px}.archive-sheet__subtitle{margin-top:18px;font-family:var(--font-display);font-size:16px;color:#8b5a44}.archive-sheet section{margin-top:22px}.archive-sheet section p{margin-top:7px;font-size:11px;line-height:1.75;color:rgba(38,63,62,.72)}.archive-sheet ol{margin-top:9px;display:grid;gap:5px}.archive-sheet li{display:grid;grid-template-columns:30px 1fr auto;gap:8px;align-items:center;padding:8px;border-bottom:1px solid rgba(37,63,62,.11);opacity:.45}.archive-sheet li.done{opacity:1}.archive-sheet li b{font-size:8px;color:#9a7040}.archive-sheet li em{font-family:var(--font-display);font-style:normal;font-size:12px}.archive-sheet li i{font-style:normal;font-size:8px;color:#62817d}.archive-sheet__reset{width:100%;margin-top:25px}.archive-sheet__reset:hover{border-color:#9c4f42;color:#9c4f42}
.story-backdrop__signature{position:absolute;inset:0;pointer-events:none}.story-backdrop__signature i{position:absolute;display:block;border:1px solid color-mix(in srgb,var(--story-accent) 28%,transparent)}
.chapter-han .story-backdrop__signature i{height:2px;border:0;background:linear-gradient(90deg,transparent,var(--story-accent),transparent);transform:rotate(-7deg)}.chapter-han .story-backdrop__signature i:nth-child(1){width:62%;left:8%;top:29%}.chapter-han .story-backdrop__signature i:nth-child(2){width:48%;left:34%;top:42%;transform:rotate(8deg)}.chapter-han .story-backdrop__signature i:nth-child(3){width:39%;left:18%;top:53%;transform:rotate(-12deg)}.chapter-han .story-backdrop__signature i:nth-child(4),.chapter-han .story-backdrop__signature i:nth-child(5){width:11px;height:11px;border-radius:50%;background:var(--story-accent);box-shadow:0 0 22px var(--story-accent)}.chapter-han .story-backdrop__signature i:nth-child(4){left:33%;top:40%}.chapter-han .story-backdrop__signature i:nth-child(5){right:24%;top:47%}
.chapter-northern-wei .story-backdrop__signature::before{content:'';position:absolute;top:0;bottom:0;left:50%;width:1px;background:linear-gradient(180deg,transparent,var(--story-accent-soft),transparent);box-shadow:0 0 34px var(--story-accent)}.chapter-northern-wei .story-backdrop__signature i{width:34%;height:42%;border-color:color-mix(in srgb,var(--story-accent-soft) 18%,transparent)}.chapter-northern-wei .story-backdrop__signature i:nth-child(1){left:5%;top:18%;clip-path:polygon(4% 0,100% 8%,93% 100%,0 91%)}.chapter-northern-wei .story-backdrop__signature i:nth-child(2){right:5%;top:18%;clip-path:polygon(0 9%,96% 0,100% 90%,7% 100%)}
.chapter-tang .story-backdrop__signature::before,.chapter-tang .story-backdrop__signature::after{content:'';position:absolute;top:11%;bottom:14%;width:13%;border:1px solid color-mix(in srgb,var(--story-accent-soft) 34%,transparent);background:linear-gradient(90deg,rgba(15,12,10,.42),transparent)}.chapter-tang .story-backdrop__signature::before{left:13%;border-right:0}.chapter-tang .story-backdrop__signature::after{right:13%;border-left:0;transform:scaleX(-1)}.chapter-tang .story-backdrop__signature i:first-child{left:31%;top:46%;width:38%;height:2px;border:0;background:linear-gradient(90deg,transparent,var(--story-accent),transparent);box-shadow:0 0 14px var(--story-accent)}
.chapter-qing .story-backdrop__signature i{height:2px;border:0;background:linear-gradient(90deg,transparent,var(--story-accent-soft),transparent);transform-origin:left center}.chapter-qing .story-backdrop__signature i:nth-child(1){width:72%;left:8%;top:31%;transform:rotate(7deg)}.chapter-qing .story-backdrop__signature i:nth-child(2){width:66%;left:12%;top:38%;transform:rotate(-4deg)}.chapter-qing .story-backdrop__signature i:nth-child(3){width:48%;left:32%;top:44%;transform:rotate(12deg)}
.chapter-contemporary .story-backdrop__signature{background-image:linear-gradient(color-mix(in srgb,var(--story-accent) 12%,transparent) 1px,transparent 1px),linear-gradient(90deg,color-mix(in srgb,var(--story-accent) 12%,transparent) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(90deg,transparent,#000 25%,#000 75%,transparent)}.chapter-contemporary .story-backdrop__signature i{width:9px;height:9px;border-radius:50%;background:var(--story-accent);box-shadow:0 0 18px var(--story-accent)}.chapter-contemporary .story-backdrop__signature i:nth-child(1){left:28%;top:27%}.chapter-contemporary .story-backdrop__signature i:nth-child(2){left:43%;top:39%}.chapter-contemporary .story-backdrop__signature i:nth-child(3){left:57%;top:31%}.chapter-contemporary .story-backdrop__signature i:nth-child(4){left:68%;top:45%}
.is-transitioning .story-heading,.is-transitioning .speaker-presence,.is-transitioning .dialogue-panel{opacity:0}
@keyframes backdrop-in{from{opacity:.2;transform:scale(1.08)}to{opacity:1;transform:scale(1.035)}}
@keyframes speaker-in{from{opacity:0;transform:translateX(-16px)}to{opacity:1;transform:none}}
.speaker-presence.is-right{animation-name:speaker-in-right}@keyframes speaker-in-right{from{opacity:0;transform:translateX(16px)}to{opacity:1;transform:none}}
@keyframes workbench-in{from{opacity:0;transform:translate(-50%,-47%) scale(.98)}to{opacity:1;transform:translate(-50%,-50%) scale(1)}}
@keyframes line-in{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
@keyframes cue-pulse{50%{opacity:.38;transform:translateY(2px)}}
@keyframes transition-in{from{opacity:0;clip-path:inset(0 50%)}to{opacity:1;clip-path:inset(0)}}
@media(max-width:900px){
  .story-nav{grid-template-columns:42px 1fr minmax(120px,.8fr) 74px;gap:9px;padding:0 10px}.story-nav__back{font-size:0}.story-nav__back::before{content:'←';font-size:18px}.story-nav__brand span{display:none}.story-nav__brand strong{font-size:15px}.story-nav__progress{grid-template-columns:auto 1fr}.story-nav__progress em{display:none}.story-nav__archive{font-size:0}.story-nav__archive::after{content:'证据卷';font-size:9px}
  .story-heading{left:16px;top:14px;max-width:65vw}.story-heading h1{font-size:20px}.speaker-presence{top:15%;width:48vw;height:35%}.speaker-presence.is-left{left:1%}.speaker-presence.is-right{right:1%}.speaker-presence__halo{width:190px}.speaker-presence__seal{width:90px;height:108px;font-size:45px}.speaker-presence p{font-size:15px;margin-top:10px}.speaker-presence span{display:none}
  .evidence-workbench{top:47%;width:calc(100% - 24px);max-height:52%;padding:12px}.evidence-workbench__head{grid-template-columns:72px 1fr}.inspect-grid,.option-grid,.decision-grid{grid-template-columns:1fr 1fr}.assemble-board{grid-template-columns:1fr}.classify-card{grid-template-columns:1fr}.classify-card__bins{grid-auto-flow:row;grid-template-columns:repeat(3,1fr)}.inspect-grid>button{min-height:106px}.decision-grid>button{min-height:124px}.validate-button{position:sticky;bottom:-12px;z-index:2;background:color-mix(in srgb,var(--story-ink) 90%,var(--story-accent))}
  .dialogue-panel{width:calc(100% - 20px);bottom:14px;min-height:132px;padding:14px 15px 28px}.dialogue-panel__text{font-size:14px;line-height:1.58}.story-feedback{bottom:158px;max-width:92vw}.story-footnote span:last-child{display:none}
}
@media(max-width:520px){
  .chapter-story{--nav-h:56px;--foot-h:21px}.story-nav__progress{font-size:8px}.story-heading span{display:none}.speaker-presence{opacity:.78}.speaker-presence__seal{width:70px;height:84px;font-size:35px}.evidence-workbench{top:45%;max-height:48%}.evidence-workbench__head p{display:none}.evidence-workbench__head .debug-answer{grid-column:1/-1}.inspect-grid,.option-grid,.decision-grid{grid-template-columns:1fr 1fr;gap:6px}.inspect-grid>button,.option-grid>button:not(.validate-button),.decision-grid>button{min-height:88px;padding:9px}.inspect-card__detail,.decision-card__detail{display:none}.option-grid small{font-size:8px}.classify-card{padding:7px}.classify-card__bins{grid-template-columns:1fr}.classify-card__bins button{min-height:30px}.dialogue-panel__role{display:none}.dialogue-panel__text{margin-top:8px}.story-feedback{font-size:8px;padding:6px 10px}
}
@media(prefers-reduced-motion:reduce){.story-backdrop img,.speaker-presence,.evidence-workbench,.dialogue-panel__text,.dialogue-panel__cue i{animation:none}.scene-transition{animation:none}.inspect-grid>button:hover,.option-grid>button:not(.validate-button):hover,.decision-grid>button:hover{transform:none}}

/* V7 商业化剧情舞台：暗场叙事 / 浅色档案工作台 / 九幕脊线。 */
.chapter-story{--nav-h:68px;--foot-h:25px;background:#071412}
.story-nav{grid-template-columns:126px minmax(190px,.8fr) minmax(360px,1.7fr) 220px;gap:18px;padding:0 22px;background:linear-gradient(90deg,color-mix(in srgb,var(--story-ink) 96%,#07110f),color-mix(in srgb,var(--story-ink) 88%,#0b1d19));box-shadow:0 10px 30px rgba(0,0,0,.22)}
.story-nav__brand{flex-direction:column;align-items:flex-start;gap:1px}.story-nav__brand span{font-size:8px}.story-nav__brand strong{font-size:17px}
.story-nav__progress{display:grid;grid-template-columns:114px minmax(150px,1fr) 34px;align-items:center;gap:12px}
.story-nav__progress>div{display:flex;flex-direction:column;min-width:0}.story-nav__progress>div span{font-size:8px;letter-spacing:.13em;color:var(--story-accent-soft)}.story-nav__progress>div em{overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-family:var(--font-display);font-size:11px;font-style:normal;letter-spacing:.04em;color:rgba(255,248,230,.72)}
.story-nav__progress ol{display:grid;grid-template-columns:repeat(9,1fr);gap:4px;list-style:none;margin:0;padding:0}.story-nav__progress li{height:5px;background:rgba(255,255,255,.09);transform:skewX(-14deg);transition:background-color .25s ease,transform .25s ease}.story-nav__progress li.is-done{background:color-mix(in srgb,var(--story-accent) 72%,#d7b768)}.story-nav__progress li.is-current{background:#f0d48a;transform:skewX(-14deg) scaleY(1.65);box-shadow:0 0 12px color-mix(in srgb,var(--story-accent) 60%,transparent)}
.story-nav__progress>b{height:auto;background:none;font-size:9px;font-weight:500;color:rgba(255,244,215,.54)}
.story-nav__tools{display:grid;grid-template-columns:54px 54px 1fr;gap:7px}.story-nav__tools button{min-height:39px}.story-nav__reading{border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.025);color:rgba(243,234,216,.5);font-size:9px;letter-spacing:.08em}.story-nav__reading:hover,.story-nav__reading[aria-pressed='true']{border-color:var(--story-accent-soft);color:#fff3d5}.story-nav__archive{min-height:39px}.story-nav__archive b{display:inline-grid;place-items:center;min-width:21px;height:21px;margin-left:6px;border-radius:50%;background:var(--story-accent);color:#fff;font-size:9px}
.story-backdrop img{filter:saturate(.73) contrast(1.08) brightness(.57)}.story-backdrop__wash{background:linear-gradient(90deg,color-mix(in srgb,var(--story-ink) 88%,transparent),transparent 46%,color-mix(in srgb,var(--story-ink) 60%,transparent)),linear-gradient(180deg,rgba(5,10,10,.24),transparent 48%,rgba(5,10,10,.9))}
.story-heading{left:30px;top:25px;max-width:390px;padding-left:0;border-left:0}.story-heading::before{content:'';position:absolute;left:0;top:0;width:3px;height:100%;background:linear-gradient(var(--story-accent),transparent)}.story-heading>*{margin-left:17px}.story-heading p{display:flex;align-items:center;gap:8px}.story-heading p b{display:grid;place-items:center;width:22px;height:22px;margin-left:-29px;background:var(--story-accent);color:#fff8e9;font-size:8px;font-weight:650;box-shadow:0 0 20px color-mix(in srgb,var(--story-accent) 32%,transparent)}.story-heading h1{font-size:27px;text-shadow:0 3px 18px rgba(0,0,0,.48)}.story-heading span{font-size:11px;color:rgba(255,246,224,.67)}
.speaker-presence__halo{border-style:dashed;opacity:.72}.speaker-presence__seal{width:130px;height:154px;background:linear-gradient(165deg,color-mix(in srgb,var(--speaker-color) 70%,rgba(15,27,24,.82)),rgba(5,12,11,.94));border-width:1px;box-shadow:inset 0 0 0 6px rgba(255,255,255,.025),0 25px 70px rgba(0,0,0,.28)}.speaker-presence__seal::after{content:'口述档案';position:absolute;right:-31px;top:50%;padding:3px 5px;border:1px solid color-mix(in srgb,var(--speaker-color) 48%,transparent);font:7px/1 var(--font-ui);letter-spacing:.16em;color:rgba(255,238,203,.62);transform:rotate(90deg) translateY(-50%)}
.is-challenge-active .speaker-presence{opacity:.16;filter:blur(2px) grayscale(.45);transition:opacity .3s ease,filter .3s ease}.is-challenge-active .story-heading{opacity:.5}.is-challenge-active .story-backdrop img{filter:saturate(.45) contrast(1.08) brightness(.38);transform:scale(1.045)}

.evidence-workbench{width:min(900px,72vw);max-height:62%;padding:20px 22px 22px;color:#203f3f;border:1px solid color-mix(in srgb,var(--story-accent) 52%,#9b8356);background:linear-gradient(142deg,rgba(250,247,232,.98),rgba(225,231,213,.97));box-shadow:0 34px 100px rgba(0,0,0,.62),0 0 0 6px rgba(12,26,23,.36),inset 0 0 0 1px rgba(255,255,255,.8);backdrop-filter:blur(18px)}
.evidence-workbench::before{content:'EVIDENCE / 证据不等于结论';position:absolute;right:22px;top:16px;font-size:7px;letter-spacing:.16em;color:rgba(31,68,65,.42)}
.evidence-workbench__head{grid-template-columns:126px 1fr;padding-bottom:15px;border-bottom-color:rgba(38,82,78,.18)}.evidence-workbench__head>span{color:color-mix(in srgb,var(--story-accent) 82%,#5c4a2f);font-weight:650}.evidence-workbench__head h2{font-size:20px;color:#173f40}.evidence-workbench__head p{font-size:10px;color:rgba(29,65,64,.68)}
.inspect-grid>button,.option-grid>button:not(.validate-button),.decision-grid>button{border-color:rgba(39,79,75,.19);background:rgba(255,255,255,.4);color:#214746;box-shadow:0 5px 16px rgba(43,74,68,.045)}.inspect-grid>button:hover,.option-grid>button:not(.validate-button):hover,.decision-grid>button:hover{border-color:var(--story-accent);background:rgba(255,255,255,.82);box-shadow:0 10px 22px rgba(42,74,68,.09)}.inspect-grid>button.is-seen,.option-grid>button.is-selected,.decision-grid>button.is-selected{border-color:var(--story-accent);background:color-mix(in srgb,var(--story-accent) 10%,rgba(255,255,255,.7));box-shadow:inset 3px 0 0 var(--story-accent)}
.inspect-grid span{color:color-mix(in srgb,var(--story-accent) 84%,#6d5531)}.inspect-grid strong,.option-grid strong,.decision-grid>button>span{color:#173f40}.inspect-card__detail,.option-grid small,.decision-card__detail{color:rgba(32,68,67,.65)}.decision-card__tradeoff{border-top-color:rgba(35,75,70,.13);color:rgba(32,68,67,.65)}.decision-card__tradeoff b,.decision-card__tradeoff em{color:color-mix(in srgb,var(--story-accent) 78%,#6b5330)}.inspect-grid i{color:rgba(31,65,63,.46)}
.validate-button{min-height:43px;border-color:color-mix(in srgb,var(--story-accent) 72%,#5b704f);background:linear-gradient(100deg,color-mix(in srgb,var(--story-accent) 78%,#315e55),color-mix(in srgb,var(--story-accent) 54%,#406e60));color:#fff9e9;font-weight:650;box-shadow:0 10px 24px color-mix(in srgb,var(--story-accent) 16%,transparent)}.validate-button:not(:disabled):hover{background:color-mix(in srgb,var(--story-accent) 82%,#315e55)}.validate-button:disabled{background:rgba(41,75,71,.18);border-color:rgba(41,75,71,.12);color:rgba(30,64,62,.46);box-shadow:none}
.classify-card,.assemble-slot{border-color:rgba(38,78,74,.16);background:rgba(255,255,255,.35)}.classify-card strong,.assemble-slot header strong{color:#214746}.classify-card p{color:rgba(32,67,65,.6)}.classify-card__bins button,.assemble-slot>button{border-color:rgba(38,78,74,.2);background:rgba(255,255,255,.22);color:rgba(30,65,64,.74)}.classify-card__bins button:hover,.assemble-slot>button:hover{border-color:var(--story-accent);background:rgba(255,255,255,.7)}.classify-card__bins button.is-selected,.assemble-slot>button.is-selected{border-color:var(--story-accent);background:color-mix(in srgb,var(--story-accent) 13%,white);color:#173f40;box-shadow:inset 3px 0 0 var(--story-accent)}.assemble-slot header span{color:color-mix(in srgb,var(--story-accent) 84%,#635032)}.assemble-slot>button strong{color:#214746}.assemble-slot>button small{color:rgba(32,67,65,.54)}

.dialogue-panel{pointer-events:auto!important;width:min(980px,calc(100% - 64px));min-height:138px;bottom:22px;padding:24px 28px 31px;border-color:color-mix(in srgb,var(--story-accent) 64%,#aa8a4d);background:linear-gradient(112deg,color-mix(in srgb,var(--story-ink) 97%,#071311),color-mix(in srgb,var(--story-ink) 87%,#122824));box-shadow:0 28px 90px rgba(0,0,0,.62),inset 0 0 0 1px rgba(255,255,255,.035);isolation:isolate;clip-path:polygon(0 0,calc(100% - 15px) 0,100% 15px,100% 100%,15px 100%,0 calc(100% - 15px))}.dialogue-panel::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--story-accent)}.dialogue-panel__name{font-size:19px}.dialogue-panel__role{font-size:9px;color:rgba(243,234,216,.48)}.dialogue-panel__text{margin-top:10px;font-size:17px;line-height:1.68;color:rgba(255,246,226,.9)}.dialogue-panel__cue{right:21px;bottom:10px;display:flex;align-items:center;gap:7px;color:rgba(243,234,216,.48)}.dialogue-panel__cue kbd{padding:2px 5px;border:1px solid rgba(255,255,255,.16);border-radius:2px;background:rgba(255,255,255,.04);font:7px/1 var(--font-ui);letter-spacing:.04em;color:rgba(255,255,255,.5)}
.dialogue-panel>*{pointer-events:auto}
.is-large-text .dialogue-panel__text{font-size:20px;line-height:1.72}.is-large-text .dialogue-panel{min-height:153px}.is-large-text .evidence-workbench{font-size:1.08em}.is-large-text .inspect-card__detail,.is-large-text .option-grid small,.is-large-text .decision-card__detail{font-size:10px}

@media(max-width:1100px){.story-nav{grid-template-columns:108px 160px minmax(280px,1fr) 186px;gap:10px;padding:0 14px}.story-nav__progress{grid-template-columns:92px 1fr 30px}.story-nav__brand strong{font-size:15px}.evidence-workbench{width:min(860px,82vw)}}
@media(max-width:900px){.chapter-story{--nav-h:60px}.story-nav{grid-template-columns:75px 1fr auto}.story-nav__brand{display:none}.story-nav__progress{grid-template-columns:82px 1fr 28px}.story-nav__tools{grid-template-columns:43px 43px 82px}.story-nav__archive{padding:0 6px}.evidence-workbench{width:calc(100% - 24px);max-height:54%;padding:15px}.dialogue-panel{width:calc(100% - 20px);min-height:137px;bottom:12px;padding:18px 17px 29px}.dialogue-panel__text{font-size:15px}.speaker-presence__seal{width:92px;height:108px;font-size:44px}}
@media(max-width:520px){.chapter-story{--nav-h:56px}.story-nav{grid-template-columns:52px 1fr auto;padding:0 6px}.story-nav__back{font-size:0}.story-nav__back::after{content:'← 行卷';font-size:8px}.story-nav__progress{grid-template-columns:52px minmax(78px,1fr);gap:5px}.story-nav__progress>div em,.story-nav__progress>b{display:none}.story-nav__progress ol{gap:2px}.story-nav__tools{grid-template-columns:34px 34px 39px;gap:3px}.story-nav__reading{font-size:7px;letter-spacing:0}.story-nav__archive{font-size:0;padding:0}.story-nav__archive::before{content:'证据';font-size:7px}.story-nav__archive b{display:none}.story-heading{left:17px;top:15px}.story-heading h1{font-size:21px}.story-heading p b{margin-left:-26px}.evidence-workbench{top:44%;max-height:50%;padding:13px 12px}.evidence-workbench::before{display:none}.evidence-workbench__head{grid-template-columns:1fr;gap:2px}.evidence-workbench__head>span{grid-row:auto}.evidence-workbench__head h2{font-size:17px}.evidence-workbench__head p{display:block;font-size:8px}.inspect-grid,.option-grid,.decision-grid{grid-template-columns:1fr 1fr}.inspect-card__detail,.decision-card__detail{display:block;font-size:8px}.dialogue-panel{min-height:140px}.dialogue-panel__name{font-size:16px}.dialogue-panel__text{font-size:14px}.dialogue-panel__cue kbd{display:none}.is-large-text .dialogue-panel__text{font-size:17px}.is-large-text .dialogue-panel{min-height:155px}}

.chapter-interlude{position:fixed;z-index:80;inset:0;display:grid;place-items:center;padding:24px;background:rgba(4,14,13,.86);backdrop-filter:blur(14px);animation:interlude-in .35s ease both}.chapter-interlude::before,.chapter-interlude::after{content:'';position:absolute;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--story-accent),transparent)}.chapter-interlude::before{top:13%}.chapter-interlude::after{bottom:13%}.chapter-interlude section{position:relative;width:min(680px,92vw);padding:38px 55px 34px;border:1px solid color-mix(in srgb,var(--story-accent) 62%,#c5a661);background:linear-gradient(145deg,rgba(250,247,231,.98),rgba(224,232,215,.98));color:#214443;box-shadow:0 34px 110px rgba(0,0,0,.62),0 0 0 8px rgba(255,255,255,.035);text-align:center}.chapter-interlude section>span{font-size:9px;font-weight:650;letter-spacing:.18em;color:color-mix(in srgb,var(--story-accent) 82%,#6a5431)}.chapter-interlude h2{margin-top:12px;font-family:var(--font-display);font-size:34px;font-weight:500;color:#173f40}.chapter-interlude>section>p{max-width:540px;margin:13px auto 0;font-family:var(--font-display);font-size:15px;line-height:1.75;color:rgba(31,65,64,.75)}.chapter-interlude section>aside{max-width:560px;margin:14px auto 0;padding:10px 13px;border:1px solid rgba(39,82,78,.16);background:rgba(255,255,255,.28);text-align:left}.chapter-interlude section>aside span{font-size:8px;letter-spacing:.16em;color:color-mix(in srgb,var(--story-accent) 78%,#6a5431)}.chapter-interlude section>aside p{margin-top:5px;font-family:var(--font-ui);font-size:10px;line-height:1.6;color:rgba(31,65,64,.68)}.chapter-interlude section>div{display:flex;justify-content:center;align-items:center;gap:10px;margin-top:15px}.chapter-interlude section>div b{font-family:var(--font-display);font-size:30px;font-weight:500;color:var(--story-accent)}.chapter-interlude section>div small{max-width:170px;text-align:left;font-size:9px;line-height:1.45;color:rgba(31,65,64,.52)}.chapter-interlude button{min-width:290px;min-height:48px;margin-top:17px;padding:0 17px;border:1px solid color-mix(in srgb,var(--story-accent) 72%,#45665b);background:#224f4d;color:#fff7e7;font-family:var(--font-display);font-size:13px}.chapter-interlude button i{margin-left:13px;font-style:normal;color:#e8c672}.chapter-interlude__thread{position:absolute;left:50%;top:50%;width:min(900px,90vw);height:1px;transform:translate(-50%,-50%);background:linear-gradient(90deg,transparent,rgba(220,190,116,.3),transparent)}.chapter-interlude__thread i{position:absolute;top:50%;width:8px;height:8px;border:1px solid #d8b96f;background:#10201d;transform:translateY(-50%) rotate(45deg)}.chapter-interlude__thread i:nth-child(1){left:8%}.chapter-interlude__thread i:nth-child(2){left:50%}.chapter-interlude__thread i:nth-child(3){right:8%}@keyframes interlude-in{from{opacity:0}to{opacity:1}}@media(max-width:520px){.chapter-interlude{padding:14px}.chapter-interlude section{padding:30px 20px 25px}.chapter-interlude h2{font-size:27px}.chapter-interlude>section>p{font-size:14px}.chapter-interlude section>aside{padding:8px 10px}.chapter-interlude button{width:100%;min-width:0;font-size:12px}}
</style>
