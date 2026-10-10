<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '@/stores/game'
import { getSoundEnabled, playGameCue, setSoundEnabled, type GameCue } from '@/game/audio'
import {
  ARCHIVE_CHECKS,
  CONSTRUCTION_CLUES,
  RAIN_CLUES,
  RECOMMENDED_ARCHIVE_TEXT,
  RULE_CARDS,
  RULE_GROUPS,
  TEXT_CLUES,
  YUAN_STORY_SCENES,
  type RuleGroup,
  type YuanDialogueLine,
} from './yuanStory'
import {
  COMPARISON_OPTIONS,
  FINAL_DEDUCTION_STAGES,
  LAYOUT_CONTROLS,
  PEOPLE_INFERENCES,
  PEOPLE_INFERENCE_OPTIONS,
  RAIN_RELATIONS,
  RELATION_OPTIONS,
  RELAY_STEPS,
  SAMPLE_COMPARE_ROWS,
  type ComparisonAnswer,
  type FinalDeductionSlot,
  type LayoutChoice,
  type RelationAnswer,
} from './yuanMiniGames'

type ArchiveAnswer = 'supported' | 'partial' | 'unsupported'

interface SavedStoryState {
  sceneIndex: number
  dialogueStep: number
  evidenceIds: string[]
  inspectedIds: string[]
  investigationChoice: string
  twistRevealed: boolean
  ruleAssignments: Record<string, RuleGroup>
  rulesChecked: boolean
  knowledgeInferences: Record<string, RelationAnswer>
  knowledgeChecked: boolean
  knowledgeChoice: string
  finalChoice: string
  finalDeduction: Partial<Record<FinalDeductionSlot, string>>
  finalDeductionChecked: boolean
  finalDeductionAttempts: number
  archiveAnswers: Record<string, ArchiveAnswer>
  keepOldVersion: boolean | null
  comparisonAnswers: Record<string, ComparisonAnswer>
  comparisonChecked: boolean
  relayOrder: string[]
  relayChecked: boolean
  layoutChoices: Record<string, LayoutChoice>
  layoutChecked: boolean
  rainRelations: Record<string, RelationAnswer>
  relationsChecked: boolean
  overlapOffset: number
  interludesSeen: string[]
}

const STORAGE_KEY = 'tongxin.yuan.story.v6'
const router = useRouter()
const game = useGameStore()

const sceneIndex = ref(0)
const dialogueStep = ref(0)
const evidenceIds = ref<string[]>([])
const inspectedIds = ref<string[]>([])
const investigationChoice = ref('')
const twistRevealed = ref(false)
const ruleAssignments = ref<Record<string, RuleGroup>>({})
const rulesChecked = ref(false)
const ruleStep = ref(0)
const knowledgeInferences = ref<Record<string, RelationAnswer>>({})
const knowledgeChecked = ref(false)
const knowledgeStep = ref(0)
const knowledgeChoice = ref('')
const finalChoice = ref('')
const finalDeduction = ref<Partial<Record<FinalDeductionSlot, string>>>({})
const finalDeductionChecked = ref(false)
const finalDeductionAttempts = ref(0)
const deductionStep = ref(0)
const archiveAnswers = ref<Record<string, ArchiveAnswer>>({})
const keepOldVersion = ref<boolean | null>(null)
const comparisonAnswers = ref<Record<string, ComparisonAnswer>>({})
const comparisonChecked = ref(false)
const relayOrder = ref<string[]>([])
const relayChecked = ref(false)
const layoutChoices = ref<Record<string, LayoutChoice>>({})
const layoutChecked = ref(false)
const rainRelations = ref<Record<string, RelationAnswer>>({})
const relationsChecked = ref(false)
const overlapOffset = ref(20)
const compareStep = ref(0)
const layoutStep = ref(0)
const relationStep = ref(0)
const archiveStep = ref(0)
const evidencePage = ref(0)
const evidenceOpen = ref(false)
const feedback = ref('')
const soundEnabled = ref(getSoundEnabled())
const largeText = ref(localStorage.getItem('tongxin.reading.largeText') === '1')
const interludeOpen = ref(false)
const interludesSeen = ref<string[]>([])
const transitionKey = ref(0)
type SceneTransitionPhase = 'idle' | 'cover' | 'reveal'
const transitionPhase = ref<SceneTransitionPhase>('idle')
const transitionScene = ref<(typeof YUAN_STORY_SCENES)[number] | null>(null)
const transitionSceneNumber = computed(() => {
  const index = transitionScene.value
    ? YUAN_STORY_SCENES.findIndex((scene) => scene.id === transitionScene.value?.id)
    : -1
  return index >= 0 ? String(index + 1).padStart(2, '0') : '--'
})
const transitionTimers: number[] = []

const currentScene = computed(() => YUAN_STORY_SCENES[sceneIndex.value])
const branchDialogue = computed<YuanDialogueLine[]>(() => {
  if (currentScene.value.id === '09') {
    const trustLine = investigationChoice.value === 'blame'
      ? '你先把雨水的错写在我头上，现在又要一张纸替所有混乱负责？'
      : '你刚才没有把雨水都算在我头上。也别让这一张纸替所有人背错。'

    if (finalChoice.value === 'over_simplify') return [
      { speaker: '现场负责人', text: '照第二份继续。第一份撤下，不再占地方。', tone: 'tense' },
      { speaker: '帖木儿', text: '石头赶上了工期，可你把“不能确认”写成了“已经判错”。', tone: 'quiet' },
      { speaker: '陈砺', text: trustLine, tone: 'tense' },
      { speaker: '桑结', text: '一张纸离开木案，也会从后来人的证据里消失。', tone: 'turn' },
    ]
    if (finalChoice.value === 'evidence_insufficient') return [
      { speaker: '现场负责人', text: '停一天，后面的石料和人手都得重排。你要把这个代价也记清楚。', tone: 'tense' },
      { speaker: '陈砺', text: '我去把所有交接记号再核一次。但能继续的地方，不该陪着一起停。' },
      { speaker: '帖木儿', text: '谨慎救下了证据，也可能把已经确定的部分困在原地。', tone: 'quiet' },
      { speaker: '桑结', text: '未知需要被保留，行动也需要与证据强度相称。', tone: 'turn' },
    ]
    return [
      { speaker: '现场负责人', text: '共同编号照走；内部结构分区复核。两张纸都签记留存。' },
      { speaker: '陈砺', text: investigationChoice.value === 'blame' ? '你后来改了判断。下次，别先从最容易归责的人开始。' : '这样我能把石料接着送下去，也不用假装看懂我不懂的字。' },
      { speaker: '帖木儿', text: '我负责在每个改动旁留下理由。不是为了证明谁赢，是让下一双手看得见。' },
      { speaker: '桑结', text: '他们没有得到一个整齐答案，却得到了一套能继续合作的办法。', tone: 'turn' },
    ]
  }

  if (currentScene.value.id === '10') {
    const consequence = finalChoice.value === 'over_simplify'
      ? '检测到第一版在后续记录中缺失：施工完成，版本链却断了一段。'
      : finalChoice.value === 'evidence_insufficient'
        ? '检测到停工复核记录：版本证据完整，但工序发生了可见延误。'
        : '检测到两份签记校样：施工判断与证据边界一并保存。'
    const knowledge = knowledgeChoice.value === 'count_people'
      ? '你曾把文字数量直接对应人群；这条推断需要在档案中重新拆开。'
      : '你已把文字、语言、文本与人群分层记录。'
    return [
      { speaker: '同心', text: consequence, tone: finalChoice.value === 'limited_confirm' ? 'system' : 'tense' },
      { speaker: '同心', text: knowledge, tone: 'system' },
      { speaker: 'AI 草稿', text: '“云台六种文字反映了六个不同民族在此共同融合……”', tone: 'system' },
      { speaker: '系统警告', text: '该表述包含未经证据支持的一一对应关系。', tone: 'tense' },
      { speaker: '同心', text: '生成语言和证据校验是两个不同过程。最后仍需要你判断。', tone: 'turn' },
    ]
  }

  if (currentScene.value.id === '11') {
    const fieldResult = finalChoice.value === 'over_simplify'
      ? '现场选择了快速确定；档案端已标出由此损失的版本链。'
      : finalChoice.value === 'evidence_insufficient'
        ? '现场选择了停工复核；档案同时保留证据与延误成本。'
        : '现场采用有限确认：可执行部分继续，未知部分没有被补写。'
    const archiveResult = keepOldVersion.value
      ? '旧版已作为版本证据保留，未来仍可复核。'
      : '旧版未被保留，这段版本关系将无法再次独立复核。'
    return [
      { speaker: '同心', text: fieldResult, tone: 'system' },
      { speaker: '同心', text: archiveResult, tone: keepOldVersion.value ? 'system' : 'tense' },
      { speaker: '你', text: '还是有不知道的。这次不用补成一个整齐故事。' },
      { speaker: '章节结语', text: '共同留下，并不意味着变得相同。', tone: 'turn' },
    ]
  }

  return currentScene.value.dialogue
})
const isTransitioning = computed(() => transitionPhase.value !== 'idle')
const isArchive = computed(() => currentScene.value.period === '当代')
const dialogueComplete = computed(
  () => dialogueStep.value >= branchDialogue.value.length - 1,
)
const currentLine = computed(() => branchDialogue.value[Math.min(dialogueStep.value, branchDialogue.value.length - 1)])
const progress = computed(() => Math.round(((sceneIndex.value + 1) / YUAN_STORY_SCENES.length) * 100))

const YUAN_INTERLUDES: Record<number, { eyebrow: string; title: string; summary: string; connection: string; next: string }> = {
  2: { eyebrow: '第一卷 · 两份校样', title: '都用过，不等于有一份错', summary: '你已经确认两份校样承担过真实工作，也看见了共同施工基准。版本先后仍然未知，不能用整齐故事填上空白。', connection: '两份版本共同证明：不同文字的营造者曾在同一工程中协作，并共享可执行的定位规则。', next: '下一卷：检查被统一的结构' },
  5: { eyebrow: '第二卷 · 归责链拆解', title: '水痕不能替人认错', summary: '受潮、移动与版本冲突可以发生关联，却不足以证明是谁放错旧稿。两份校样更可能属于不同工作阶段。', connection: '版本差异没有切断协作；它记录了现场如何在调整中继续传递尺度、位置与工序。', next: '下一卷：共同规则与文字边界' },
  8: { eyebrow: '第三卷 · 现场裁决', title: '行动必须与证据强度相称', summary: '你已分开共同施工规则、文字自身结构与仍然未知的版本关系。接下来，现场决定会在人物之间产生真正后果。', connection: '共同规则使协作成为可能，而保留文字自身结构，才让共存不等于被磨成相同。', next: '下一卷：让决定接受时间检验' },
}

const currentInterlude = computed(() => YUAN_INTERLUDES[sceneIndex.value] ?? null)
const activeComparison = computed(() => SAMPLE_COMPARE_ROWS[compareStep.value])
const activeLayoutControl = computed(() => LAYOUT_CONTROLS[layoutStep.value])
const activeRainRelation = computed(() => RAIN_RELATIONS[relationStep.value])
const activeArchiveCheck = computed(() => ARCHIVE_CHECKS[archiveStep.value])
const activeRuleCard = computed(() => RULE_CARDS[ruleStep.value])
const activePeopleInference = computed(() => PEOPLE_INFERENCES[knowledgeStep.value])
const evidencePageSize = 8
const evidencePageCount = computed(() => Math.max(1, Math.ceil(evidenceIds.value.length / evidencePageSize)))
const visibleEvidence = computed(() => evidenceIds.value.slice(
  evidencePage.value * evidencePageSize,
  (evidencePage.value + 1) * evidencePageSize,
))
const alignmentAccuracy = computed(() => Math.max(0, 100 - Math.abs(overlapOffset.value - 50) * 2))
const activeDeductionStage = computed(() => FINAL_DEDUCTION_STAGES[deductionStep.value])
const finalDeductionComplete = computed(() =>
  FINAL_DEDUCTION_STAGES.every((stage) => !!finalDeduction.value[stage.id]),
)
const finalDeductionCorrect = computed(() =>
  FINAL_DEDUCTION_STAGES.every((stage) => finalDeduction.value[stage.id] === stage.answer),
)

interface SceneVisual {
  base: string
  mid?: string
  foreground?: string
  effect?: string
  framing: string
}

const SCENE_VISUALS: Record<string, SceneVisual> = {
  '00': { base: '/assets/yuan/yuntai-east-wall-original.jpg', mid: '/assets/yuan/story/trade_relay_props.png', framing: 'archive-desk' },
  '01': { base: '/assets/yuan/story/mural_anchor.png', foreground: '/assets/yuan/story/foreground_stone_reliefs.png', framing: 'wide-arrival' },
  '02': { base: '/assets/yuan/story/background_empty.png', mid: '/assets/yuan/story/mid_cloud_platform.png', foreground: '/assets/yuan/story/trade_relay_props.png', framing: 'work-yard' },
  '03': { base: '/assets/yuan/story/mural_anchor.png', mid: '/assets/yuan/story/six_gold_lines_fx.png', framing: 'wall-close' },
  '04': { base: '/assets/yuan/story/background_empty.png', mid: '/assets/yuan/story/mid_cloud_platform.png', effect: 'rain', framing: 'rain-table' },
  '05': { base: '/assets/yuan/story/trade_relay_props.png', mid: '/assets/yuan/story/background_empty.png', framing: 'paper-close' },
  '06': { base: '/assets/yuan/story/mid_cloud_platform.png', foreground: '/assets/yuan/story/trade_relay_props.png', framing: 'shared-table' },
  '07': { base: '/assets/yuan/story/mural_anchor.png', mid: '/assets/yuan/story/six_gold_lines_fx.png', framing: 'inscription-wall' },
  '08': { base: '/assets/yuan/story/mural_anchor.png', foreground: '/assets/yuan/story/foreground_stone_reliefs.png', framing: 'decision-stage' },
  '09': { base: '/assets/yuan/story/far_pass_road.png', mid: '/assets/yuan/story/mid_cloud_platform.png', foreground: '/assets/yuan/story/foreground_stone_reliefs.png', framing: 'road-passage' },
  '10': { base: '/assets/yuan/yuntai-east-wall-original.jpg', mid: '/assets/yuan/story/six_gold_lines_fx.png', framing: 'archive-review' },
  '11': { base: '/assets/yuan/yuntai-east-wall-original.jpg', mid: '/assets/yuan/story/six_gold_lines_fx.png', framing: 'archive-graph' },
}

const currentVisual = computed(() => SCENE_VISUALS[currentScene.value.id])

interface SpeakerVisual {
  key: string
  role: string
  side: 'left' | 'right' | 'center'
  src?: string
}

const SPEAKER_VISUALS: Record<string, SpeakerVisual> = {
  '陈砺': { key: 'chen', role: '石作协调者', side: 'left', src: '/assets/yuan/characters/chen-li-v2.png' },
  '帖木儿': { key: 'temur', role: '文字与版面校勘者', side: 'right', src: '/assets/yuan/characters/temur-v2.png' },
  '桑结': { key: 'sangjie', role: '文本校勘者', side: 'right', src: '/assets/yuan/characters/sangjie-v2.png' },
  '现场负责人': { key: 'foreman', role: '营造现场负责人', side: 'left', src: '/assets/yuan/characters/foreman-v2.png' },
  '你': { key: 'player', role: '校勘助手', side: 'left', src: '/assets/yuan/characters/temur-composite.png' },
  '路人甲': { key: 'passer-a', role: '经过云台的行旅', side: 'left', src: '/assets/yuan/characters/chen-li-composite.png' },
  '路人乙': { key: 'passer-b', role: '经过云台的行旅', side: 'right', src: '/assets/yuan/characters/sangjie-composite.png' },
}

const currentSpeaker = computed<SpeakerVisual>(() => {
  const speaker = currentLine.value?.speaker ?? '同心'
  if (SPEAKER_VISUALS[speaker]) return SPEAKER_VISUALS[speaker]
  if (speaker.includes('同心') || speaker.includes('系统') || speaker.includes('AI')) {
    return { key: 'ai', role: '数字档案助手', side: 'right' }
  }
  return { key: 'narrator', role: '证据剧场旁白', side: 'center' }
})

const advanceHint = computed(() => {
  if (!dialogueComplete.value) return '点击对话框继续'
  if (!canAdvance.value) return '完成当前场景操作后继续'
  if (currentScene.value.id === '00') return '点击进入证据剧场'
  if (currentScene.value.id === '11') return '点击封存本章记录'
  return '点击继续剧情'
})

const evidenceLabels: Record<string, string> = {
  sample_a: '施工校样',
  sample_b: '结构校样',
  position_marks: '位置标记',
  scale_baseline: '尺度基准',
  handoff_marks: '交接记号',
  spacing_shift: '间距变化',
  direction_change: '书写方向',
  structure_break: '文本结构断裂',
  water_mark: '纸边水痕',
  fold_line: '折线错位',
  ink_spread: '墨迹扩散',
  version_layers: '两阶段版本关系',
  shared_rules: '三层共同规则',
  script_people_boundary: '文字与人群边界',
  decision_chain: '修缮裁决链',
  archive_record: '校验后的档案表述',
}

const finalChoices = [
  {
    id: 'over_simplify',
    index: '甲',
    label: '采用第二版，第一版是错误旧稿',
    description: '施工可以继续，但把尚未证实的版本关系写成确定结论。',
    result: '施工判断：基本可执行；历史叙述：过度确定。',
  },
  {
    id: 'limited_confirm',
    index: '乙',
    label: '有限确认，并保留两份版本',
    description: '沿用共同标准，保留文本差异，也保留前一版作为版本证据。',
    result: '施工继续；证据边界与旧版价值都被保留。',
  },
  {
    id: 'evidence_insufficient',
    index: '丙',
    label: '证据不足，暂缓施工',
    description: '避免草率判断，但需要承担工期延误的现实成本。',
    result: '证据保存最完整；施工进度因此延后。',
  },
]

const resolutionProfile = computed(() => {
  const profiles = {
    over_simplify: {
      label: '快速推进 · 版本链受损',
      tone: 'risk',
      schedule: 100,
      evidence: 45,
      trust: investigationChoice.value === 'blame' ? 28 : 42,
      note: '工期被保住，但未经证实的判断进入施工记录，第一版的证据价值随之降低。',
    },
    limited_confirm: {
      label: '有限确认 · 协作继续',
      tone: 'balanced',
      schedule: 84,
      evidence: 94,
      trust: investigationChoice.value === 'blame' ? 72 : 92,
      note: '共同标准继续运转，文字差异与版本未知被明确保留。',
    },
    evidence_insufficient: {
      label: '停工复核 · 工期承压',
      tone: 'delay',
      schedule: 36,
      evidence: 100,
      trust: investigationChoice.value === 'blame' ? 50 : 66,
      note: '证据保存最完整，但已被支持的施工环节也被迫等待。',
    },
  }
  return profiles[finalChoice.value as keyof typeof profiles] ?? profiles.limited_confirm
})

const knowledgeChoices = [
  { id: 'count_people', label: '六种文字，就有六种人？', response: '可以数文字，但不能顺手把人也数出来。' },
  { id: 'separate_layers', label: '不能直接对应', response: '文字、语言、文本与历史人群必须分层记录。' },
  { id: 'admit_unknown', label: '我们不知道所有经过这里的人是谁', response: '承认未知，比编出一个整齐答案更接近证据。' },
]

const archiveOptions: { id: ArchiveAnswer; label: string }[] = [
  { id: 'supported', label: '证据支持' },
  { id: 'partial', label: '部分确认' },
  { id: 'unsupported', label: '不能推出' },
]

const showDebugAnswers = import.meta.env.DEV
const debugAnswer = computed(() => {
  switch (currentScene.value.id) {
    case '01':
      return COMPARISON_OPTIONS.find((option) => option.id === activeComparison.value.answer)?.label ?? ''
    case '02':
      return RELAY_STEPS.map((step) => step.label).join(' → ')
    case '03': {
      const control = activeLayoutControl.value
      return control.answer === 'shared' ? control.sharedLabel : control.preserveLabel
    }
    case '04':
      if (relationsChecked.value && rainRelationsCorrect.value) return '阶段判断：记录嫌疑，但暂不归责'
      return RELATION_OPTIONS.find((option) => option.id === activeRainRelation.value.answer)?.label ?? ''
    case '05':
      return '将滑块移至中点 50，使共同定位角重合'
    case '06':
      return RULE_GROUPS.find((group) => group.id === activeRuleCard.value.answer)?.label ?? ''
    case '07':
      if (knowledgeChecked.value && knowledgeInferencesCorrect.value) return '回应无唯一答案；推荐“不能直接对应”'
      return PEOPLE_INFERENCE_OPTIONS.find((option) => option.id === activePeopleInference.value.answer)?.label ?? ''
    case '08': {
      if (finalDeductionChecked.value && finalDeductionCorrect.value) return '现实裁决无唯一答案；推荐“有限确认，并保留两份版本”'
      const stage = activeDeductionStage.value
      return stage.options.find((option) => option.id === stage.answer)?.label ?? ''
    }
    case '10':
      if (archiveCorrect.value) return '推荐：作为版本证据保留'
      return archiveOptions.find((option) => option.id === activeArchiveCheck.value.answer)?.label ?? ''
    default:
      return ''
  }
})

const rulesCorrect = computed(() =>
  RULE_CARDS.every((card) => ruleAssignments.value[card.id] === card.answer),
)
const archiveCorrect = computed(() =>
  ARCHIVE_CHECKS.every((item) => archiveAnswers.value[item.id] === item.answer),
)
const comparisonCorrect = computed(() =>
  SAMPLE_COMPARE_ROWS.every((row) => comparisonAnswers.value[row.id] === row.answer),
)
const relayCorrect = computed(() =>
  RELAY_STEPS.every((step, index) => relayOrder.value[index] === step.id),
)
const layoutCorrect = computed(() =>
  LAYOUT_CONTROLS.every((control) => layoutChoices.value[control.id] === control.answer),
)
const rainRelationsCorrect = computed(() =>
  RAIN_RELATIONS.every((relation) => rainRelations.value[relation.id] === relation.answer),
)
const knowledgeInferencesCorrect = computed(() =>
  PEOPLE_INFERENCES.every((item) => knowledgeInferences.value[item.id] === item.answer),
)

const canAdvance = computed(() => {
  if (!dialogueComplete.value) return false
  switch (currentScene.value.id) {
    case '01': return comparisonChecked.value && comparisonCorrect.value
    case '02': return relayCorrect.value && CONSTRUCTION_CLUES.every((item) => evidenceIds.value.includes(item.id))
    case '03': return layoutChecked.value && layoutCorrect.value
    case '04': return relationsChecked.value && rainRelationsCorrect.value && !!investigationChoice.value
    case '05': return twistRevealed.value
    case '06': return rulesChecked.value && rulesCorrect.value
    case '07': return knowledgeChecked.value && knowledgeInferencesCorrect.value && !!knowledgeChoice.value
    case '08': return finalDeductionChecked.value && finalDeductionCorrect.value && !!finalChoice.value
    case '10': return archiveCorrect.value && keepOldVersion.value !== null
    default: return true
  }
})

function save() {
  const state: SavedStoryState = {
    sceneIndex: sceneIndex.value,
    dialogueStep: dialogueStep.value,
    evidenceIds: evidenceIds.value,
    inspectedIds: inspectedIds.value,
    investigationChoice: investigationChoice.value,
    twistRevealed: twistRevealed.value,
    ruleAssignments: ruleAssignments.value,
    rulesChecked: rulesChecked.value,
    knowledgeInferences: knowledgeInferences.value,
    knowledgeChecked: knowledgeChecked.value,
    knowledgeChoice: knowledgeChoice.value,
    finalChoice: finalChoice.value,
    finalDeduction: finalDeduction.value,
    finalDeductionChecked: finalDeductionChecked.value,
    finalDeductionAttempts: finalDeductionAttempts.value,
    archiveAnswers: archiveAnswers.value,
    keepOldVersion: keepOldVersion.value,
    comparisonAnswers: comparisonAnswers.value,
    comparisonChecked: comparisonChecked.value,
    relayOrder: relayOrder.value,
    relayChecked: relayChecked.value,
    layoutChoices: layoutChoices.value,
    layoutChecked: layoutChecked.value,
    rainRelations: rainRelations.value,
    relationsChecked: relationsChecked.value,
    overlapOffset: overlapOffset.value,
    interludesSeen: interludesSeen.value,
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function restore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const state = JSON.parse(raw) as Partial<SavedStoryState>
    sceneIndex.value = Math.min(Math.max(state.sceneIndex ?? 0, 0), YUAN_STORY_SCENES.length - 1)
    evidenceIds.value = state.evidenceIds ?? []
    inspectedIds.value = state.inspectedIds ?? []
    investigationChoice.value = state.investigationChoice ?? ''
    twistRevealed.value = state.twistRevealed ?? false
    ruleAssignments.value = state.ruleAssignments ?? {}
    rulesChecked.value = state.rulesChecked ?? false
    knowledgeInferences.value = state.knowledgeInferences ?? {}
    knowledgeChecked.value = state.knowledgeChecked ?? false
    knowledgeChoice.value = state.knowledgeChoice ?? ''
    finalChoice.value = state.finalChoice ?? ''
    finalDeduction.value = state.finalDeduction ?? {}
    finalDeductionChecked.value = state.finalDeductionChecked ?? false
    finalDeductionAttempts.value = state.finalDeductionAttempts ?? 0
    archiveAnswers.value = state.archiveAnswers ?? {}
    keepOldVersion.value = state.keepOldVersion ?? null
    comparisonAnswers.value = state.comparisonAnswers ?? {}
    comparisonChecked.value = state.comparisonChecked ?? false
    relayOrder.value = state.relayOrder ?? []
    relayChecked.value = state.relayChecked ?? false
    layoutChoices.value = state.layoutChoices ?? {}
    layoutChecked.value = state.layoutChecked ?? false
    rainRelations.value = state.rainRelations ?? {}
    relationsChecked.value = state.relationsChecked ?? false
    overlapOffset.value = state.overlapOffset ?? 20
    interludesSeen.value = state.interludesSeen ?? []

    dialogueStep.value = Math.min(
      Math.max(state.dialogueStep ?? 0, 0),
      branchDialogue.value.length - 1,
    )

    compareStep.value = Math.max(0, SAMPLE_COMPARE_ROWS.findIndex((row) => !comparisonAnswers.value[row.id]))
    layoutStep.value = Math.max(0, LAYOUT_CONTROLS.findIndex((control) => !layoutChoices.value[control.id]))
    relationStep.value = Math.max(0, RAIN_RELATIONS.findIndex((relation) => !rainRelations.value[relation.id]))
    archiveStep.value = Math.max(0, ARCHIVE_CHECKS.findIndex((check) => !archiveAnswers.value[check.id]))
    ruleStep.value = Math.max(0, RULE_CARDS.findIndex((card) => !ruleAssignments.value[card.id]))
    knowledgeStep.value = Math.max(0, PEOPLE_INFERENCES.findIndex((item) => !knowledgeInferences.value[item.id]))
    deductionStep.value = Math.max(0, FINAL_DEDUCTION_STAGES.findIndex((stage) => !finalDeduction.value[stage.id]))
  } catch {
    localStorage.removeItem(STORAGE_KEY)
  }
}

function addEvidence(id: string) {
  if (!evidenceIds.value.includes(id)) evidenceIds.value.push(id)
  if (!inspectedIds.value.includes(id)) inspectedIds.value.push(id)
  game.mark('yuan', 'INSPECT', id)
}

type YuanTelemetryEvent = 'chapter_entered' | 'scene_entered' | 'puzzle_wrong_attempt' | 'puzzle_solved' | 'decision_committed'

function track(event: YuanTelemetryEvent, detail: Record<string, string | number | boolean> = {}) {
  try {
    const key = 'tongxin.yuan.telemetry.v1'
    const existing = JSON.parse(localStorage.getItem(key) ?? '[]') as unknown[]
    const next = [...existing.slice(-119), {
      event,
      scene: currentScene.value.id,
      at: new Date().toISOString(),
      detail,
    }]
    localStorage.setItem(key, JSON.stringify(next))
  } catch {
    // 本地体验数据只用于调试；写入失败不能阻断剧情。
  }
}

function playCue(kind: GameCue) {
  playGameCue(kind, soundEnabled.value)
}

function toggleSound() {
  soundEnabled.value = !soundEnabled.value
  setSoundEnabled(soundEnabled.value)
  if (soundEnabled.value) playCue('confirm')
}

function toggleLargeText() {
  largeText.value = !largeText.value
  localStorage.setItem('tongxin.reading.largeText', largeText.value ? '1' : '0')
}

function inspect(id: string) {
  addEvidence(id)
  feedback.value = `${evidenceLabels[id] ?? '线索'}已记入证据卷`
  window.setTimeout(() => {
    if (feedback.value.includes('已记入')) feedback.value = ''
  }, 1500)
}

function answerComparison(rowId: string, value: ComparisonAnswer) {
  playCue('paper')
  comparisonAnswers.value = { ...comparisonAnswers.value, [rowId]: value }
  comparisonChecked.value = false
  const index = SAMPLE_COMPARE_ROWS.findIndex((item) => item.id === rowId)
  feedback.value = '判断已压入证据槽；完成三项后统一核验。'
  if (index >= 0 && index < SAMPLE_COMPARE_ROWS.length - 1) compareStep.value = index + 1
}

function verifyComparison() {
  comparisonChecked.value = true
  if (comparisonCorrect.value) {
    addEvidence('sample_a')
    addEvidence('sample_b')
    feedback.value = '对读完成：两份都用过、整理逻辑不同、先后仍无法确认。'
    playCue('confirm')
    track('puzzle_solved', { puzzle: 'comparison' })
    return
  }
  const brokenAt = SAMPLE_COMPARE_ROWS.findIndex((item) => comparisonAnswers.value[item.id] !== item.answer)
  compareStep.value = Math.max(0, brokenAt)
  feedback.value = '证据链没有闭合：回到亮起的判断槽，把“观察结果”和“版本推断”分开。'
  playCue('warning')
  track('puzzle_wrong_attempt', { puzzle: 'comparison', node: brokenAt + 1 })
}

function selectRelayStep(stepId: string) {
  if (relayOrder.value.includes(stepId) || relayOrder.value.length >= RELAY_STEPS.length) return
  relayOrder.value = [...relayOrder.value, stepId]
  relayChecked.value = false
  feedback.value = `已放入第 ${relayOrder.value.length} 道工序`
}

function removeRelayStep(index: number) {
  relayOrder.value = relayOrder.value.filter((_, itemIndex) => itemIndex !== index)
  relayChecked.value = false
}

function verifyRelay() {
  relayChecked.value = true
  if (!relayCorrect.value) {
    const brokenAt = RELAY_STEPS.findIndex((step, index) => relayOrder.value[index] !== step.id)
    feedback.value = `工序在第 ${Math.max(1, brokenAt + 1)} 环断开：先建立共同基准，再让记号跨工种传递。`
    playCue('warning')
    track('puzzle_wrong_attempt', { puzzle: 'relay', node: brokenAt + 1 })
    return
  }
  CONSTRUCTION_CLUES.forEach((clue) => addEvidence(clue.id))
  feedback.value = '工序接力成立：统一编号不是为了抹平差异，而是让协作能够继续。'
  playCue('confirm')
  track('puzzle_solved', { puzzle: 'relay' })
}

function setLayoutChoice(controlId: string, value: LayoutChoice) {
  layoutChoices.value = { ...layoutChoices.value, [controlId]: value }
  layoutChecked.value = false
  const index = LAYOUT_CONTROLS.findIndex((item) => item.id === controlId)
  feedback.value = '参数已暂存；观察版面变化，再完成下一项。'
  if (index >= 0 && index < LAYOUT_CONTROLS.length - 1) layoutStep.value = index + 1
}

function verifyLayout() {
  layoutChecked.value = true
  if (layoutCorrect.value) {
    TEXT_CLUES.forEach((clue) => addEvidence(clue.id))
    feedback.value = '版面校准完成：统一外部定位，保留内部间距与原有方向。'
    playCue('confirm')
    track('puzzle_solved', { puzzle: 'layout' })
    return
  }
  const brokenAt = LAYOUT_CONTROLS.findIndex((item) => layoutChoices.value[item.id] !== item.answer)
  layoutStep.value = Math.max(0, brokenAt)
  feedback.value = '校准造成了结构损失：亮起的参数正在把“施工方便”误当成“文本一致”。'
  playCue('warning')
  track('puzzle_wrong_attempt', { puzzle: 'layout', node: brokenAt + 1 })
}

function setRainRelation(relationId: string, value: RelationAnswer) {
  rainRelations.value = { ...rainRelations.value, [relationId]: value }
  relationsChecked.value = false
  investigationChoice.value = ''
  const index = RAIN_RELATIONS.findIndex((item) => item.id === relationId)
  feedback.value = '关系强度已暂存；完成后再判断整条归责链。'
  if (index >= 0 && index < RAIN_RELATIONS.length - 1) relationStep.value = index + 1
}

function verifyRelations() {
  relationsChecked.value = true
  if (rainRelationsCorrect.value) {
    RAIN_CLUES.forEach((clue) => addEvidence(clue.id))
    feedback.value = '关系链已校准：可以确认受潮与移动，不能据此确定版本先后。'
    playCue('confirm')
    track('puzzle_solved', { puzzle: 'relations' })
    return
  }
  const brokenAt = RAIN_RELATIONS.findIndex((item) => rainRelations.value[item.id] !== item.answer)
  relationStep.value = Math.max(0, brokenAt)
  feedback.value = '归责链跨过了证据空白：回到亮起的节点，降低这条连线的确定程度。'
  playCue('warning')
  track('puzzle_wrong_attempt', { puzzle: 'relations', node: brokenAt + 1 })
}

function toggleEvidence() {
  evidenceOpen.value = !evidenceOpen.value
  if (evidenceOpen.value) evidencePage.value = evidencePageCount.value - 1
}

function nextDialogue() {
  if (!dialogueComplete.value) {
    dialogueStep.value += 1
    playCue('paper')
  }
}

function advanceFromDialogue() {
  if (isTransitioning.value) return
  if (!dialogueComplete.value) {
    nextDialogue()
    return
  }
  if (!canAdvance.value) {
    feedback.value = '先完成画面中的调查或选择，再继续剧情。'
    return
  }
  if (currentScene.value.id === '11') {
    finishChapter()
    return
  }
  if (currentInterlude.value && !interludesSeen.value.includes(currentScene.value.id)) {
    interludesSeen.value = [...interludesSeen.value, currentScene.value.id]
    interludeOpen.value = true
    playCue('transition')
    return
  }
  nextScene()
}

function continueFromInterlude() {
  interludeOpen.value = false
  nextScene()
}

function onStoryKeydown(event: KeyboardEvent) {
  if (evidenceOpen.value || isTransitioning.value || event.repeat) return
  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault()
    if (interludeOpen.value) continueFromInterlude()
    else advanceFromDialogue()
  }
}

function clearTransitionTimers() {
  transitionTimers.splice(0).forEach((timer) => window.clearTimeout(timer))
}

function scheduleTransition(callback: () => void, delay: number) {
  transitionTimers.push(window.setTimeout(callback, delay))
}

function nextScene() {
  if (!canAdvance.value || isTransitioning.value) return
  if (currentScene.value.id === '08' && finalChoice.value) {
    game.choose('yuan', finalChoice.value)
  }
  if (currentScene.value.id === '06') {
    addEvidence('shared_rules')
    game.mark('yuan', 'LENS')
  }
  if (currentScene.value.id === '07') {
    addEvidence('script_people_boundary')
    game.mark('yuan', 'CHAT')
  }
  if (currentScene.value.id === '10') {
    addEvidence('archive_record')
    game.mark('yuan', 'GRAPH')
  }
  if (sceneIndex.value < YUAN_STORY_SCENES.length - 1) {
    const nextIndex = sceneIndex.value + 1
    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
    const coverDelay = reducedMotion ? 40 : 360
    const finishDelay = reducedMotion ? 160 : 980

    clearTransitionTimers()
    playCue('transition')
    transitionScene.value = YUAN_STORY_SCENES[nextIndex]
    transitionPhase.value = 'cover'

    scheduleTransition(() => {
      sceneIndex.value = nextIndex
      dialogueStep.value = 0
      compareStep.value = 0
      layoutStep.value = 0
      relationStep.value = 0
      archiveStep.value = 0
      feedback.value = ''
      transitionKey.value += 1
      transitionPhase.value = 'reveal'
      track('scene_entered', { index: nextIndex + 1 })
    }, coverDelay)

    scheduleTransition(() => {
      transitionPhase.value = 'idle'
      transitionScene.value = null
      clearTransitionTimers()
    }, finishDelay)
  }
}

function revealTwist() {
  if (Math.abs(overlapOffset.value - 50) > 6) {
    feedback.value = '两个定位角还没有对齐；移动校样，让共同边缘落在同一条基线上。'
    return
  }
  twistRevealed.value = true
  addEvidence('version_layers')
  feedback.value = '原有解释被推翻：两份校样可能属于不同阶段'
  playCue('confirm')
  track('puzzle_solved', { puzzle: 'overlap' })
}

function assignRule(cardId: string, group: RuleGroup) {
  ruleAssignments.value = { ...ruleAssignments.value, [cardId]: group }
  rulesChecked.value = false
  const index = RULE_CARDS.findIndex((item) => item.id === cardId)
  if (index >= 0 && index < RULE_CARDS.length - 1) ruleStep.value = index + 1
  feedback.value = '规则已放入对应层；六项完成后统一检查，避免凭单项反馈猜答案。'
  playCue('paper')
}

function verifyRules() {
  rulesChecked.value = true
  if (rulesCorrect.value) {
    feedback.value = '规则矩阵闭合：共同标准连接工序，协调规则处理相邻关系，文字结构得到保留。'
    playCue('confirm')
    track('puzzle_solved', { puzzle: 'rule_matrix' })
    return
  }
  const brokenAt = RULE_CARDS.findIndex((card) => ruleAssignments.value[card.id] !== card.answer)
  ruleStep.value = Math.max(0, brokenAt)
  feedback.value = '矩阵中有一项越过了权限：检查亮起的规则，它究竟服务于共同施工，还是属于文字自身。'
  playCue('warning')
  track('puzzle_wrong_attempt', { puzzle: 'rule_matrix', node: brokenAt + 1 })
}

function setKnowledgeInference(id: string, value: RelationAnswer) {
  knowledgeInferences.value = { ...knowledgeInferences.value, [id]: value }
  knowledgeChecked.value = false
  knowledgeChoice.value = ''
  const index = PEOPLE_INFERENCES.findIndex((item) => item.id === id)
  if (index >= 0 && index < PEOPLE_INFERENCES.length - 1) knowledgeStep.value = index + 1
  feedback.value = '证据强度已记录；三条推断完成后再回答陈砺。'
  playCue('paper')
}

function verifyKnowledgeInferences() {
  knowledgeChecked.value = true
  if (knowledgeInferencesCorrect.value) {
    feedback.value = '边界审查完成：空间共存可确认，协作只能有限说明，人群数量不能由文字数量推出。'
    playCue('confirm')
    track('puzzle_solved', { puzzle: 'people_inference' })
    return
  }
  const brokenAt = PEOPLE_INFERENCES.findIndex((item) => knowledgeInferences.value[item.id] !== item.answer)
  knowledgeStep.value = Math.max(0, brokenAt)
  feedback.value = '这条推断把“看见的文字”替换成了“没有直接记录的人”。回到亮起的关系重新判断。'
  playCue('warning')
  track('puzzle_wrong_attempt', { puzzle: 'people_inference', node: brokenAt + 1 })
}

function chooseKnowledge(id: string) {
  knowledgeChoice.value = id
  feedback.value = knowledgeChoices.find((item) => item.id === id)?.response ?? ''
}

function chooseFinalDeduction(slot: FinalDeductionSlot, optionId: string) {
  finalDeduction.value = { ...finalDeduction.value, [slot]: optionId }
  finalDeductionChecked.value = false
  finalChoice.value = ''
  const stageIndex = FINAL_DEDUCTION_STAGES.findIndex((stage) => stage.id === slot)
  if (stageIndex >= 0 && stageIndex < FINAL_DEDUCTION_STAGES.length - 1) deductionStep.value = stageIndex + 1
  feedback.value = '论据已压入裁决卷；三层齐备后再检查整条结论。'
  playCue('paper')
}

function verifyFinalDeduction() {
  finalDeductionChecked.value = true
  finalDeductionAttempts.value += 1
  if (finalDeductionCorrect.value) {
    addEvidence('decision_chain')
    feedback.value = '裁决链闭合：事实、行动与未知各在自己的证据边界内。现在决定由谁承担哪种代价。'
    playCue('confirm')
    track('puzzle_solved', { puzzle: 'final_deduction', attempts: finalDeductionAttempts.value })
    return
  }
  const brokenAt = FINAL_DEDUCTION_STAGES.findIndex((stage) => finalDeduction.value[stage.id] !== stage.answer)
  deductionStep.value = Math.max(0, brokenAt)
  const brokenStage = FINAL_DEDUCTION_STAGES[deductionStep.value]
  feedback.value = `${brokenStage.label}越过了证据边界：检查亮起的裁决层，不要用完整故事替代缺失证据。`
  playCue('warning')
  track('puzzle_wrong_attempt', { puzzle: 'final_deduction', node: brokenAt + 1 })
}

function chooseFinal(id: string) {
  if (!finalDeductionChecked.value || !finalDeductionCorrect.value) return
  finalChoice.value = id
  feedback.value = finalChoices.find((item) => item.id === id)?.result ?? ''
  playCue(id === 'limited_confirm' ? 'confirm' : 'warning')
  track('decision_committed', { decision: id, deductionAttempts: finalDeductionAttempts.value })
}

function setArchiveAnswer(id: string, value: ArchiveAnswer) {
  archiveAnswers.value = { ...archiveAnswers.value, [id]: value }
  const item = ARCHIVE_CHECKS.find((check) => check.id === id)
  feedback.value = item?.answer === value ? item.result : '这项判断超出了当前证据，请重新检查。'
  const index = ARCHIVE_CHECKS.findIndex((check) => check.id === id)
  if (index >= 0 && index < ARCHIVE_CHECKS.length - 1) archiveStep.value = index + 1
}

function finishChapter() {
  game.mark('yuan', 'COMPLETE')
  void router.push('/chapter/yuan/summary')
}

function resetStory() {
  clearTransitionTimers()
  transitionPhase.value = 'idle'
  transitionScene.value = null
  localStorage.removeItem(STORAGE_KEY)
  game.resetChapter('yuan')
  sceneIndex.value = 0
  dialogueStep.value = 0
  evidenceIds.value = []
  inspectedIds.value = []
  investigationChoice.value = ''
  twistRevealed.value = false
  ruleAssignments.value = {}
  rulesChecked.value = false
  ruleStep.value = 0
  knowledgeInferences.value = {}
  knowledgeChecked.value = false
  knowledgeStep.value = 0
  knowledgeChoice.value = ''
  finalChoice.value = ''
  finalDeduction.value = {}
  finalDeductionChecked.value = false
  finalDeductionAttempts.value = 0
  deductionStep.value = 0
  archiveAnswers.value = {}
  keepOldVersion.value = null
  comparisonAnswers.value = {}
  comparisonChecked.value = false
  relayOrder.value = []
  relayChecked.value = false
  layoutChoices.value = {}
  layoutChecked.value = false
  rainRelations.value = {}
  relationsChecked.value = false
  overlapOffset.value = 20
  compareStep.value = 0
  layoutStep.value = 0
  relationStep.value = 0
  archiveStep.value = 0
  evidencePage.value = 0
  interludesSeen.value = []
  interludeOpen.value = false
  feedback.value = ''
}

watch(
  [sceneIndex, dialogueStep, evidenceIds, inspectedIds, investigationChoice, twistRevealed, ruleAssignments, rulesChecked, knowledgeInferences, knowledgeChecked, knowledgeChoice, finalChoice, finalDeduction, finalDeductionChecked, finalDeductionAttempts, archiveAnswers, keepOldVersion, comparisonAnswers, comparisonChecked, relayOrder, relayChecked, layoutChoices, layoutChecked, rainRelations, relationsChecked, overlapOffset, interludesSeen],
  save,
  { deep: true },
)

onMounted(() => {
  game.bootstrap()
  restore()
  game.mark('yuan', 'ENTER')
  track('chapter_entered', { restoredScene: sceneIndex.value + 1 })
  window.addEventListener('keydown', onStoryKeydown)
})

onBeforeUnmount(() => {
  clearTransitionTimers()
  window.removeEventListener('keydown', onStoryKeydown)
})
</script>

<template>
  <div class="yuan-story" :class="{ 'is-archive': isArchive, 'is-large-text': largeText }">
    <header class="story-nav">
      <RouterLink to="/timeline">← 千年行卷</RouterLink>
      <div class="story-brand">
        <span>元代篇 · 证据剧场</span>
        <strong>石壁上的六种声音</strong>
      </div>
      <div class="story-progress" aria-label="章节剧情进度">
        <div><span>第 {{ String(sceneIndex + 1).padStart(2, '0') }} 幕</span><em>{{ currentScene.title }}</em></div>
        <ol aria-hidden="true"><li v-for="(scene, index) in YUAN_STORY_SCENES" :key="scene.id" :class="{ 'is-current': index === sceneIndex, 'is-done': index < sceneIndex }" /></ol>
        <b>{{ progress }}%</b>
      </div>
      <div class="story-nav-actions">
        <button type="button" :aria-pressed="largeText" @click="toggleLargeText">{{ largeText ? '标准字' : '大字' }}</button>
        <button type="button" :aria-label="soundEnabled ? '关闭音效' : '开启音效'" :title="soundEnabled ? '关闭音效' : '开启音效'" @click="toggleSound">{{ soundEnabled ? '音效开' : '音效关' }}</button>
        <button type="button" @click="toggleEvidence">证据卷 <b>{{ evidenceIds.length }}</b></button>
      </div>
    </header>

    <main class="story-stage" :class="[`scene-${currentScene.id}`, `framing-${currentVisual.framing}`]">
      <div class="story-backdrop" :key="transitionKey" aria-hidden="true">
        <img class="story-backdrop__main" :src="currentVisual.base" alt="" width="1920" height="1080" />
        <img v-if="currentVisual.mid" class="story-backdrop__mid" :src="currentVisual.mid" alt="" width="1920" height="1080" />
        <img v-if="currentVisual.foreground" class="story-backdrop__foreground" :src="currentVisual.foreground" alt="" width="1920" height="1080" />
        <div v-if="currentVisual.effect === 'rain'" class="story-backdrop__rain" />
      </div>
      <div class="story-shade" aria-hidden="true" />

      <section :key="`heading-${transitionKey}`" class="scene-heading">
        <p>{{ currentScene.period }} · {{ currentScene.location }}</p>
        <h1>{{ currentScene.title }}</h1>
      </section>

      <aside :key="`objective-${transitionKey}`" class="scene-objective">
        <span>当前目标</span>
        <strong>{{ currentScene.objective }}</strong>
      </aside>

      <Transition name="portrait" mode="out-in">
        <figure
          :key="`${currentScene.id}-${dialogueStep}-${currentSpeaker.key}`"
          class="speaker-portrait"
          :class="[`is-${currentSpeaker.side}`, `speaker-${currentSpeaker.key}`, { 'is-working': dialogueComplete }]"
          aria-hidden="true"
        >
          <div v-if="currentSpeaker.src" class="speaker-portrait__image" :style="{ '--portrait-image': `url(${currentSpeaker.src})` }" />
          <div v-else class="speaker-portrait__sigil"><i /><b>同</b><span>心</span></div>
          <figcaption>{{ currentLine.speaker }} · {{ currentSpeaker.role }}</figcaption>
        </figure>
      </Transition>

      <Transition name="workbench" mode="out-in">
        <section v-if="dialogueComplete" :key="currentScene.id" class="workbench" :class="`interaction-${currentScene.id}`">
          <template v-if="currentScene.id === '00'">
            <div class="archive-conflict">
              <div><span>空间匹配</span><strong>较高</strong></div>
              <div><span>文本结构</span><strong class="warn">异常</strong></div>
              <p>同一块拓片，两种证据给出不同方向。</p>
            </div>
          </template>

          <template v-else-if="currentScene.id === '01'">
            <div class="case-table compare-game">
              <header class="game-head">
                <div><span>证据台 01 · 双稿对读</span><strong>逐项观察，最后一次性提交推断</strong><small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small></div>
                <em>{{ Object.keys(comparisonAnswers).length }} / {{ SAMPLE_COMPARE_ROWS.length }}</em>
              </header>
              <nav class="case-tabs" aria-label="双稿观察项目">
                <button
                  v-for="(row, index) in SAMPLE_COMPARE_ROWS"
                  :key="row.id"
                  :class="{ active: compareStep === index, done: comparisonAnswers[row.id], error: comparisonChecked && comparisonAnswers[row.id] !== row.answer }"
                  type="button"
                  @click="compareStep = index"
                ><i>{{ String(index + 1).padStart(2, '0') }}</i><span>{{ row.label }}</span><b>{{ comparisonAnswers[row.id] ? '◆' : '◇' }}</b></button>
              </nav>
              <Transition name="puzzle-card" mode="out-in">
                <div :key="activeComparison.id" class="compare-stage">
                  <div class="sample-card sample-a"><span>校样 A</span><strong>{{ activeComparison.clueA }}</strong><i class="scan-line" /></div>
                  <div class="comparison-lens"><span>{{ activeComparison.label }}</span><b>⇄</b><small>只判断这一层证据</small></div>
                  <div class="sample-card sample-b"><span>校样 B</span><strong>{{ activeComparison.clueB }}</strong><i class="scan-line" /></div>
                </div>
              </Transition>
              <div class="verdict-deck" aria-label="判断两份校样的关系">
                <button
                  v-for="option in COMPARISON_OPTIONS"
                  :key="option.id"
                  :class="{ selected: comparisonAnswers[activeComparison.id] === option.id }"
                  type="button"
                  :aria-label="option.label"
                  @click="answerComparison(activeComparison.id, option.id)"
                ><i>{{ option.id === 'same' ? '＝' : option.id === 'different' ? '≠' : '？' }}</i><span>{{ option.label }}</span></button>
              </div>
              <button v-if="!comparisonChecked || !comparisonCorrect" class="game-confirm" type="button" :disabled="Object.keys(comparisonAnswers).length !== SAMPLE_COMPARE_ROWS.length" @click="verifyComparison">合拢证据，提交推断</button>
              <p v-else class="game-resolution">证据合拢：两份都曾使用、整理逻辑不同，但版本先后仍不可确认。</p>
            </div>
          </template>

          <template v-else-if="currentScene.id === '02'">
            <div class="case-table relay-game">
              <header class="game-head">
                <div><span>证据台 02 · 工序接力</span><strong>让同一条定位信号穿过四个工种</strong><small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small></div>
                <em>{{ relayOrder.length }} / {{ RELAY_STEPS.length }}</em>
              </header>
              <div class="relay-signal" :style="{ '--relay-progress': `${relayOrder.length * 25}%` }"><i /><span>定位信号</span><b>{{ relayChecked && relayCorrect ? '链路稳定' : '等待闭合' }}</b></div>
              <div class="relay-slots" aria-label="施工顺序">
                <button
                  v-for="slotIndex in RELAY_STEPS.length"
                  :key="slotIndex"
                  :class="{ filled: relayOrder[slotIndex - 1], wrong: relayChecked && relayOrder[slotIndex - 1] !== RELAY_STEPS[slotIndex - 1].id }"
                  type="button"
                  @click="relayOrder[slotIndex - 1] && removeRelayStep(slotIndex - 1)"
                >
                  <span>{{ String(slotIndex).padStart(2, '0') }}</span>
                  <strong>{{ RELAY_STEPS.find((step) => step.id === relayOrder[slotIndex - 1])?.label ?? '等待放入工序' }}</strong>
                  <small>{{ relayOrder[slotIndex - 1] ? '点击撤回' : '—' }}</small>
                </button>
              </div>
              <div class="relay-pool">
                <button v-for="step in RELAY_STEPS" :key="step.id" :disabled="relayOrder.includes(step.id)" type="button" @click="selectRelayStep(step.id)">
                  <i>{{ step.short }}</i><span><strong>{{ step.label }}</strong><small>{{ step.note }}</small></span>
                </button>
              </div>
              <button class="game-confirm" type="button" :disabled="relayOrder.length !== RELAY_STEPS.length" @click="verifyRelay">核对工序链</button>
              <p v-if="canAdvance" class="game-resolution">信息已经从校样传到石料、工序与最终复核。</p>
            </div>
          </template>

          <template v-else-if="currentScene.id === '03'">
            <div class="case-table layout-game">
              <header class="game-head">
                <div><span>证据台 03 · 版面校准</span><strong>每动一个参数，都观察结构是否被改写</strong><small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small></div>
                <em>{{ Object.keys(layoutChoices).length }} / {{ LAYOUT_CONTROLS.length }}</em>
              </header>
              <nav class="case-tabs layout-tabs" aria-label="版面校准项目">
                <button
                  v-for="(control, index) in LAYOUT_CONTROLS"
                  :key="control.id"
                  :class="{ active: layoutStep === index, done: layoutChoices[control.id], error: layoutChecked && layoutChoices[control.id] !== control.answer }"
                  type="button"
                  @click="layoutStep = index"
                ><i>{{ String(index + 1).padStart(2, '0') }}</i><span>{{ control.label }}</span><b>{{ layoutChoices[control.id] ? '◆' : '◇' }}</b></button>
              </nav>
              <div
                class="layout-preview"
                :class="{
                  'outer-shared': layoutChoices.outer_anchor === 'shared',
                  'spacing-shared': layoutChoices.inner_spacing === 'shared',
                  'flow-shared': layoutChoices.writing_flow === 'shared',
                }"
                aria-label="抽象版面预览，不呈现未经校对的古文字"
              >
                <div class="layout-frame frame-a"><i v-for="n in 5" :key="`a-${n}`" /></div>
                <div class="layout-frame frame-b"><i v-for="n in 5" :key="`b-${n}`" /></div>
                <b class="calibration-reticle"><i /><i /></b>
                <span>{{ activeLayoutControl.label }} · 抽象组块预览</span>
              </div>
              <div class="layout-console">
                <span>正在调整</span><strong>{{ activeLayoutControl.label }}</strong>
                <div>
                  <button :class="{ selected: layoutChoices[activeLayoutControl.id] === 'shared' }" type="button" @click="setLayoutChoice(activeLayoutControl.id, 'shared')">{{ activeLayoutControl.sharedLabel }}</button>
                  <button :class="{ selected: layoutChoices[activeLayoutControl.id] === 'preserve' }" type="button" @click="setLayoutChoice(activeLayoutControl.id, 'preserve')">{{ activeLayoutControl.preserveLabel }}</button>
                </div>
                <small>施工需要共同基准，但共同基准不等于内部结构全部相同。</small>
              </div>
              <button v-if="!layoutChecked || !layoutCorrect" class="game-confirm" type="button" :disabled="Object.keys(layoutChoices).length !== LAYOUT_CONTROLS.length" @click="verifyLayout">压印校准结果</button>
              <p v-else class="game-resolution">校准成立：外框共享，内部间距与书写方向保持各自结构。</p>
            </div>
          </template>

          <template v-else-if="currentScene.id === '04'">
            <div class="case-table relation-game">
              <header class="game-head">
                <div><span>证据台 04 · 关系链审查</span><strong>给每条因果线标注强度，再决定是否归责</strong><small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small></div>
                <em>{{ Object.keys(rainRelations).length }} / {{ RAIN_RELATIONS.length }}</em>
              </header>
              <nav class="case-tabs relation-tabs" aria-label="关系链节点">
                <button
                  v-for="(relation, index) in RAIN_RELATIONS"
                  :key="relation.id"
                  :class="{ active: relationStep === index, done: rainRelations[relation.id], error: relationsChecked && rainRelations[relation.id] !== relation.answer }"
                  type="button"
                  @click="relationStep = index"
                ><i>{{ String(index + 1).padStart(2, '0') }}</i><span>关系 {{ index + 1 }}</span><b>{{ rainRelations[relation.id] ? '◆' : '◇' }}</b></button>
              </nav>
              <Transition name="puzzle-card" mode="out-in">
                <div :key="activeRainRelation.id" class="relation-stage">
                  <div class="relation-node"><span>已知</span><strong>{{ activeRainRelation.from }}</strong></div>
                  <div class="relation-wire"><i /><b>证据强度</b><i /></div>
                  <div class="relation-node is-conclusion"><span>推断</span><strong>{{ activeRainRelation.to }}</strong></div>
                </div>
              </Transition>
              <div v-if="!relationsChecked || !rainRelationsCorrect" class="relation-options">
                  <button
                    v-for="option in RELATION_OPTIONS"
                    :key="option.id"
                    :class="{ selected: rainRelations[activeRainRelation.id] === option.id }"
                    type="button"
                    :aria-label="option.label"
                    @click="setRainRelation(activeRainRelation.id, option.id)"
                  ><i>{{ option.id === 'supported' ? '实' : option.id === 'partial' ? '疑' : '断' }}</i><span>{{ option.label }}</span></button>
              </div>
              <button v-if="(!relationsChecked || !rainRelationsCorrect)" class="game-confirm" type="button" :disabled="Object.keys(rainRelations).length !== RAIN_RELATIONS.length" @click="verifyRelations">审查整条关系链</button>
              <div v-else class="micro-choice relation-verdict">
                <span>关系强度已经分开。现在写下你的阶段性判断：</span>
                <button :class="{ selected: investigationChoice === 'blame' }" type="button" @click="investigationChoice = 'blame'; feedback = '这个解释完整，却仍缺少版本先后的直接证据。'">据此认定陈砺放错旧稿</button>
                <button :class="{ selected: investigationChoice === 'hold' }" type="button" @click="investigationChoice = 'hold'; feedback = '你把“动过纸”与“造成版本冲突”暂时分开。'">记录嫌疑，但暂不归责</button>
              </div>
            </div>
          </template>

          <template v-else-if="currentScene.id === '05'">
            <div class="case-table overlap-game">
              <header class="game-head">
                <div><span>证据台 05 · 双稿叠合</span><strong>借助透光台寻找共同定位角，而不是对齐所有内容</strong><small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small></div>
                <em>{{ twistRevealed ? '已锁定' : `吻合 ${alignmentAccuracy}%` }}</em>
              </header>
              <div class="overlap-board" :class="{ solved: twistRevealed }">
                <div class="paper paper-a"><span>A · 施工定位</span><i /><i /><i /><i /></div>
                <div class="paper paper-b" :style="{ '--overlap-shift': `${(overlapOffset - 50) * 3}px` }"><span>B · 结构调整</span><i /><i /><i /><i /></div>
                <b class="overlap-axis" />
                <div class="registration-mark"><i /><b /></div>
                <output>{{ alignmentAccuracy > 88 ? '定位角正在吸附' : '寻找共同边缘' }}</output>
              </div>
              <label class="overlap-control">
                <span>左移</span>
                <input v-model.number="overlapOffset" type="range" min="0" max="100" :disabled="twistRevealed" aria-label="移动结构校样" />
                <span>右移</span>
              </label>
              <button class="game-confirm" type="button" :disabled="twistRevealed || alignmentAccuracy < 70" @click="revealTwist">固定重合点</button>
              <p v-if="twistRevealed" class="game-resolution">重合后仍有局部修改落在不同层级：两份纸可能承担不同阶段的功能；帖木儿的修改也早于雨水。</p>
            </div>
          </template>

          <template v-else-if="currentScene.id === '06'">
            <div class="case-table rule-game">
              <header class="game-head">
                <div><span>证据台 06 · 规则权限矩阵</span><strong>给每条规则划定权限，最后统一核验</strong><small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small></div>
                <em>{{ Object.keys(ruleAssignments).length }} / {{ RULE_CARDS.length }}</em>
              </header>
              <nav class="case-tabs rule-tabs" aria-label="规则权限项目">
                <button
                  v-for="(card, index) in RULE_CARDS"
                  :key="card.id"
                  :class="{ active: ruleStep === index, done: ruleAssignments[card.id], error: rulesChecked && ruleAssignments[card.id] !== card.answer }"
                  type="button"
                  @click="ruleStep = index"
                ><i>{{ String(index + 1).padStart(2, '0') }}</i><span>{{ card.label }}</span><b>{{ ruleAssignments[card.id] ? '◆' : '◇' }}</b></button>
              </nav>
              <div class="rule-stage">
                <div><span>正在划定权限</span><strong>{{ activeRuleCard.label }}</strong><small>这条规则应该统一所有工序、协调相邻区域，还是保护文字自身？</small></div>
                <div class="rule-options">
                  <button v-for="group in RULE_GROUPS" :key="group.id" :class="{ selected: ruleAssignments[activeRuleCard.id] === group.id }" type="button" @click="assignRule(activeRuleCard.id, group.id)">
                    <strong>{{ group.label }}</strong><small>{{ group.note }}</small>
                  </button>
                </div>
              </div>
              <button v-if="!rulesChecked || !rulesCorrect" class="game-confirm" type="button" :disabled="Object.keys(ruleAssignments).length !== RULE_CARDS.length" @click="verifyRules">核验规则权限</button>
              <p v-else class="game-resolution">矩阵闭合：共同标准连接工序，协调规则处理相邻关系，文字自身结构得到保留。</p>
            </div>
          </template>

          <template v-else-if="currentScene.id === '07'">
            <div class="case-table people-game">
              <header class="game-head">
                <div><span>证据台 07 · 人群推断边界</span><strong>{{ knowledgeChecked && knowledgeInferencesCorrect ? '用自己的话回应陈砺' : '判断每句话离证据还有多远' }}</strong><small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small></div>
                <em>{{ knowledgeChecked && knowledgeInferencesCorrect ? '边界成立' : `${Object.keys(knowledgeInferences).length} / ${PEOPLE_INFERENCES.length}` }}</em>
              </header>
              <template v-if="!knowledgeChecked || !knowledgeInferencesCorrect">
                <nav class="case-tabs people-tabs" aria-label="人群推断项目">
                  <button
                    v-for="(item, index) in PEOPLE_INFERENCES"
                    :key="item.id"
                    :class="{ active: knowledgeStep === index, done: knowledgeInferences[item.id], error: knowledgeChecked && knowledgeInferences[item.id] !== item.answer }"
                    type="button"
                    @click="knowledgeStep = index"
                  ><i>{{ String(index + 1).padStart(2, '0') }}</i><span>推断 {{ index + 1 }}</span><b>{{ knowledgeInferences[item.id] ? '◆' : '◇' }}</b></button>
                </nav>
                <div class="people-stage">
                  <div><span>依据</span><strong>{{ activePeopleInference.basis }}</strong></div>
                  <i>能否推出</i>
                  <div><span>陈述</span><strong>{{ activePeopleInference.claim }}</strong></div>
                </div>
                <div class="people-options">
                  <button v-for="option in PEOPLE_INFERENCE_OPTIONS" :key="option.id" :class="{ selected: knowledgeInferences[activePeopleInference.id] === option.id }" type="button" @click="setKnowledgeInference(activePeopleInference.id, option.id)"><i>{{ option.mark }}</i><span>{{ option.label }}</span></button>
                </div>
                <button class="game-confirm" type="button" :disabled="Object.keys(knowledgeInferences).length !== PEOPLE_INFERENCES.length" @click="verifyKnowledgeInferences">审查三条推断</button>
              </template>
              <div v-else class="knowledge-response">
                <div class="boundary-seal"><span>可确认</span><strong>共同空间</strong><i /> <span>有限说明</span><strong>实际协作</strong><i /> <span>不能推出</span><strong>固定人群</strong></div>
                <div class="choice-list compact">
                  <button v-for="choice in knowledgeChoices" :key="choice.id" :class="{ selected: knowledgeChoice === choice.id }" type="button" @click="chooseKnowledge(choice.id)">
                    <strong>{{ choice.label }}</strong><small>{{ knowledgeChoice === choice.id ? choice.response : '选择这句话回应陈砺' }}</small>
                  </button>
                </div>
              </div>
            </div>
          </template>

          <template v-else-if="currentScene.id === '08'">
            <div class="case-table final-deduction">
              <header class="game-head">
                <div><span>终局推演 · 修缮裁决卷</span><strong>{{ finalDeductionCorrect && finalDeductionChecked ? '选择要承担的现实代价' : '用已查验证据组成一条可执行结论' }}</strong><small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small></div>
                <em>{{ finalDeductionChecked && finalDeductionCorrect ? '裁决成立' : `${Object.keys(finalDeduction).length} / 3` }}</em>
              </header>

              <template v-if="!finalDeductionChecked || !finalDeductionCorrect">
                <nav class="case-tabs deduction-tabs" aria-label="终局裁决层级">
                  <button
                    v-for="(stage, index) in FINAL_DEDUCTION_STAGES"
                    :key="stage.id"
                    :class="{ active: deductionStep === index, done: finalDeduction[stage.id], error: finalDeductionChecked && finalDeduction[stage.id] !== stage.answer }"
                    type="button"
                    @click="deductionStep = index"
                  ><i>{{ stage.index }}</i><span>{{ stage.label }}</span><b>{{ finalDeduction[stage.id] ? '◆' : '◇' }}</b></button>
                </nav>
                <div class="deduction-question"><span>{{ activeDeductionStage.index }} · {{ activeDeductionStage.label }}</span><strong>{{ activeDeductionStage.prompt }}</strong></div>
                <div class="deduction-options">
                  <button
                    v-for="option in activeDeductionStage.options"
                    :key="option.id"
                    :class="{ selected: finalDeduction[activeDeductionStage.id] === option.id }"
                    type="button"
                    @click="chooseFinalDeduction(activeDeductionStage.id, option.id)"
                  >
                    <strong>{{ option.label }}</strong>
                    <small>{{ option.evidenceIds.map((id) => evidenceLabels[id]).join(' · ') }}</small>
                  </button>
                </div>
                <button class="game-confirm" type="button" :disabled="!finalDeductionComplete" @click="verifyFinalDeduction">压印整条裁决链</button>
              </template>

              <div v-else class="decision-consequences">
                <div class="deduction-seal"><span>事实</span><i>阶段版本</i><span>行动</span><i>外同内异</i><span>边界</span><i>保留未知</i></div>
                <div class="choice-list final">
                  <button v-for="choice in finalChoices" :key="choice.id" :class="{ selected: finalChoice === choice.id }" type="button" @click="chooseFinal(choice.id)">
                    <span>{{ choice.index }}</span><strong>{{ choice.label }}</strong><small>{{ choice.description }}</small>
                  </button>
                </div>
              </div>
            </div>
          </template>

          <template v-else-if="currentScene.id === '09'">
            <div class="consequence-board" :class="`tone-${resolutionProfile.tone}`">
              <header><span>现场后果</span><strong>{{ resolutionProfile.label }}</strong></header>
              <div class="consequence-meters">
                <label><span>工期</span><i><b :style="{ width: `${resolutionProfile.schedule}%` }" /></i><em>{{ resolutionProfile.schedule }}</em></label>
                <label><span>证据</span><i><b :style="{ width: `${resolutionProfile.evidence}%` }" /></i><em>{{ resolutionProfile.evidence }}</em></label>
                <label><span>协作</span><i><b :style="{ width: `${resolutionProfile.trust}%` }" /></i><em>{{ resolutionProfile.trust }}</em></label>
              </div>
              <p>{{ resolutionProfile.note }}</p>
            </div>
          </template>

          <template v-else-if="currentScene.id === '10'">
            <div class="archive-editor">
              <div class="draft-warning">
                <span>AI 草稿校验</span>
                <strong>发现未经支持的一一对应关系</strong>
                <small v-if="showDebugAnswers && debugAnswer" class="debug-answer">调试答案：{{ debugAnswer }}</small>
              </div>
              <nav v-if="!archiveCorrect" class="case-tabs archive-tabs" aria-label="档案校验项目">
                <button v-for="(check, index) in ARCHIVE_CHECKS" :key="check.id" :class="{ active: archiveStep === index, done: archiveAnswers[check.id] }" type="button" @click="archiveStep = index">
                  <i>{{ String(index + 1).padStart(2, '0') }}</i><span>陈述 {{ index + 1 }}</span><b>{{ archiveAnswers[check.id] ? '◆' : '◇' }}</b>
                </button>
              </nav>
              <div v-if="!archiveCorrect" class="archive-row archive-card">
                <p>{{ activeArchiveCheck.label }}</p>
                <div>
                  <button v-for="option in archiveOptions" :key="option.id" :class="{ selected: archiveAnswers[activeArchiveCheck.id] === option.id }" type="button" @click="setArchiveAnswer(activeArchiveCheck.id, option.id)">{{ option.label }}</button>
                </div>
              </div>
              <blockquote v-if="archiveCorrect">{{ RECOMMENDED_ARCHIVE_TEXT }}</blockquote>
              <div v-if="archiveCorrect" class="keep-version">
                <span>旧版校样如何处理？</span>
                <button :class="{ selected: keepOldVersion === false }" type="button" @click="keepOldVersion = false">删除旧版</button>
                <button :class="{ selected: keepOldVersion === true }" type="button" @click="keepOldVersion = true">作为版本证据保留</button>
              </div>
            </div>
          </template>

          <template v-else-if="currentScene.id === '11'">
            <div class="evidence-graph" :class="`ending-${resolutionProfile.tone}`">
              <div class="graph-core">{{ keepOldVersion ? '证据可复核' : '版本链缺口' }}<br /><small>{{ resolutionProfile.label }}</small></div>
              <span v-for="(label, index) in ['施工位置', '文本结构', '版本关系', '人物记录', '相邻证据']" :key="label" :style="{ '--i': index }">{{ label }}</span>
            </div>
          </template>
        </section>
      </Transition>

      <Transition name="notice">
        <div v-if="feedback" class="story-feedback" role="status">{{ feedback }}</div>
      </Transition>

      <button
        type="button"
        class="dialogue-panel"
        :class="[`tone-${currentLine.tone || 'normal'}`, { 'is-blocked': dialogueComplete && !canAdvance }]"
        :aria-label="`${currentLine.speaker}说：${currentLine.text}。${advanceHint}`"
        @click="advanceFromDialogue"
      >
        <span class="dialogue-name">{{ currentLine.speaker }}</span>
        <span class="dialogue-role">{{ currentSpeaker.role }}</span>
        <Transition name="line-change" mode="out-in">
          <span :key="`${currentScene.id}-${dialogueStep}`" class="dialogue-text">{{ currentLine.text }}</span>
        </Transition>
        <span class="dialogue-cue">
          <kbd>Enter</kbd>
          <span>{{ advanceHint }}</span>
          <i :class="{ paused: dialogueComplete && !canAdvance }">◆</i>
        </span>
      </button>

      <div
        v-if="isTransitioning"
        class="scene-transition"
        :class="`phase-${transitionPhase}`"
        aria-hidden="true"
      >
        <div class="transition-sheet transition-sheet--left"><i /><b /></div>
        <div class="transition-sheet transition-sheet--right"><i /><b /></div>
        <div class="transition-seam"><i /></div>
        <div class="transition-title">
          <span>SCENE {{ transitionSceneNumber }} / {{ YUAN_STORY_SCENES.length }}</span>
          <strong>{{ transitionScene?.title }}</strong>
          <small>{{ transitionScene?.period }} · {{ transitionScene?.location }}</small>
        </div>
      </div>

      <Transition name="drawer">
        <aside v-if="evidenceOpen" class="evidence-drawer">
          <header><div><span>随身证据卷</span><strong>{{ evidenceIds.length }} 条记录</strong></div><button type="button" aria-label="关闭证据卷" @click="evidenceOpen = false">×</button></header>
          <ol>
            <li v-for="(id, index) in visibleEvidence" :key="id"><span>{{ String(evidencePage * evidencePageSize + index + 1).padStart(2, '0') }}</span><strong>{{ evidenceLabels[id] ?? id }}</strong></li>
          </ol>
          <nav v-if="evidencePageCount > 1" class="drawer-pages" aria-label="证据卷分页">
            <button type="button" :disabled="evidencePage === 0" @click="evidencePage -= 1">上一页</button>
            <span>{{ evidencePage + 1 }} / {{ evidencePageCount }}</span>
            <button type="button" :disabled="evidencePage >= evidencePageCount - 1" @click="evidencePage += 1">下一页</button>
          </nav>
          <p>这些记录只代表你在本次体验中实际查验过的材料。</p>
          <button class="reset" type="button" @click="resetStory">从头体验本章</button>
        </aside>
      </Transition>
    </main>

    <footer class="story-footnote">
      <span>{{ isArchive ? '历史遗址照片用于当代档案情境' : '剧情场景美术 · 非史实照片或精确建筑复原' }}</span>
      <span>不展示未经专家校对的古文字字形</span>
    </footer>

    <div v-if="interludeOpen && currentInterlude" class="yuan-interlude" role="dialog" aria-modal="true" aria-label="阶段小结">
      <section>
        <span>{{ currentInterlude.eyebrow }}</span>
        <h2>{{ currentInterlude.title }}</h2>
        <p>{{ currentInterlude.summary }}</p>
        <aside><span>仍可确认的联系</span><p>{{ currentInterlude.connection }}</p></aside>
        <div class="yuan-interlude__ledger"><b>{{ evidenceIds.length }}</b><small>条现场证据已归入云台校勘卷</small></div>
        <button type="button" @click="continueFromInterlude">{{ currentInterlude.next }} <i>→</i></button>
      </section>
    </div>
  </div>
</template>

<style scoped>
:global(html:has(.yuan-story)),:global(body:has(.yuan-story)){overflow:hidden;overscroll-behavior:none}
.yuan-story{height:100dvh;overflow:hidden;color:#eee6d5;background:#101817;font-family:var(--font-ui)}
button{font:inherit}.story-nav{height:66px;display:grid;grid-template-columns:150px 1fr minmax(270px,420px) 170px;align-items:center;gap:20px;padding:0 28px;border-bottom:1px solid rgba(221,193,133,.24);background:rgba(12,20,19,.97);position:relative;z-index:20}
.story-nav>a{min-height:44px;display:flex;align-items:center;color:rgba(238,230,213,.62);font-size:12px;text-decoration:none}.story-nav>a:hover{color:#fff}.story-nav-actions{display:flex;justify-content:flex-end;align-items:center;gap:7px}.story-nav-actions button{min-height:44px;border:0;background:transparent;color:#ddbf7b}.story-nav-actions button:first-child{width:44px;min-height:44px;border:1px solid rgba(221,191,123,.24);border-radius:50%;font-family:var(--font-display)}.story-nav-actions button:hover{color:#fff;border-color:rgba(221,191,123,.58)}
.story-brand{display:flex;align-items:baseline;gap:13px}.story-brand span{font-size:9px;letter-spacing:.18em;color:#bda167}.story-brand strong{font-family:var(--font-display);font-size:18px;font-weight:500}
.story-progress{display:grid;grid-template-columns:auto 1fr 35px;align-items:center;gap:9px;font-size:9px;letter-spacing:.12em;color:rgba(238,230,213,.5)}.story-progress i{height:3px;background:rgba(255,255,255,.09);overflow:hidden}.story-progress b{display:block;height:100%;background:linear-gradient(90deg,#4d98a9,#d9bb73);transition:width .5s ease}.story-progress em{font-style:normal;color:#d9bb73}
.story-stage{position:relative;height:calc(100dvh - 92px - env(safe-area-inset-bottom));overflow:hidden;isolation:isolate}.story-backdrop,.story-shade{position:absolute;inset:0}.story-backdrop{z-index:-3;animation:scene-in .8s ease both}.story-backdrop img{position:absolute;width:100%;height:100%;object-fit:cover}.story-backdrop__main{filter:saturate(.7) contrast(1.04) brightness(.63);transform:scale(1.025)}.is-archive .story-backdrop__main{filter:saturate(.55) contrast(1.03) brightness(.5)}.story-backdrop__lines{opacity:.18;mix-blend-mode:screen}.story-backdrop__foreground{object-fit:fill!important;top:auto!important;height:28%!important;bottom:0;opacity:.7}.story-shade{z-index:-2;background:linear-gradient(90deg,rgba(8,15,14,.78),transparent 35%,transparent 68%,rgba(8,15,14,.68)),linear-gradient(180deg,rgba(5,11,10,.26),transparent 40%,rgba(5,10,9,.2) 55%,rgba(5,10,9,.92) 80%)}
.scene-heading{position:absolute;left:clamp(24px,4vw,68px);top:30px;max-width:540px;text-shadow:0 3px 18px #000}.scene-heading p{font-size:10px;letter-spacing:.18em;color:#d8bd81}.scene-heading h1{margin-top:5px;font-family:var(--font-display);font-size:clamp(34px,4vw,57px);font-weight:500;line-height:1.08}
.scene-objective{position:absolute;right:34px;top:30px;width:min(330px,28vw);padding:13px 16px;border-right:3px solid #d9bb73;background:linear-gradient(90deg,transparent,rgba(10,20,19,.72));text-align:right}.scene-objective span{font-size:9px;letter-spacing:.18em;color:#bf9e5e}.scene-objective strong{display:block;margin-top:3px;font-family:var(--font-display);font-size:14px;font-weight:500}
.workbench{position:absolute;left:50%;top:47%;width:min(920px,74vw);max-height:42vh;transform:translate(-50%,-50%);overflow:hidden;padding:18px;border:1px solid rgba(217,187,115,.38);background:linear-gradient(135deg,rgba(18,28,26,.89),rgba(28,36,32,.84));box-shadow:0 22px 70px rgba(0,0,0,.38),0 0 0 7px rgba(255,255,255,.025);backdrop-filter:blur(10px)}
.samples,.clue-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.samples button,.clue-grid button,.version-overlap button{min-height:128px;padding:18px;border:1px solid rgba(219,190,128,.25);background:linear-gradient(145deg,rgba(241,227,193,.12),rgba(255,255,255,.035));color:#eee6d5;text-align:left}.samples button:hover,.clue-grid button:hover,.version-overlap button:hover{border-color:#d9bb73}.samples button.inspected,.clue-grid button.inspected{border-color:#88b9a2;background:rgba(90,145,118,.15)}.samples span,.clue-grid span,.version-overlap span{display:block;font-size:9px;letter-spacing:.17em;color:#d6b66e}.samples strong,.clue-grid strong,.version-overlap strong{display:block;margin-top:8px;font-family:var(--font-display);font-size:21px;font-weight:500}.samples small,.clue-grid small,.version-overlap small{display:block;margin-top:8px;color:rgba(238,230,213,.58);line-height:1.6}.clue-grid{grid-template-columns:repeat(3,1fr)}.clue-grid button{min-height:142px}.micro-choice{display:flex;gap:8px;margin-top:12px}.micro-choice button,.keep-version button{flex:1;padding:11px;border:1px solid rgba(217,187,115,.22);background:transparent;color:rgba(238,230,213,.7)}.micro-choice button.selected,.keep-version button.selected{border-color:#d9bb73;background:rgba(217,187,115,.12);color:#fff}
.archive-conflict{display:grid;grid-template-columns:1fr 1fr;gap:12px}.archive-conflict div{padding:20px;border:1px solid rgba(217,187,115,.2);background:rgba(0,0,0,.24)}.archive-conflict span{font-size:10px;color:rgba(238,230,213,.5)}.archive-conflict strong{display:block;margin-top:5px;font-family:var(--font-display);font-size:28px;color:#8fc4ad}.archive-conflict strong.warn{color:#e3ac69}.archive-conflict p{grid-column:1/-1;text-align:center;color:#d9bb73}
.version-overlap{text-align:center}.version-overlap button{width:min(420px,100%);text-align:center}.version-overlap p{margin-top:15px;color:#efc777;font-family:var(--font-display)}
.case-table{--game-line:rgba(217,187,115,.2);--game-paper:rgba(243,230,196,.075);display:grid;gap:10px;color:#eee6d5}
.game-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;padding:0 2px 11px;border-bottom:1px solid var(--game-line)}.game-head span{display:block;font-size:9px;letter-spacing:.18em;color:#d8b96f}.game-head strong{display:block;margin-top:4px;font-family:var(--font-display);font-size:17px;font-weight:500}.game-head em{min-width:60px;padding:6px 9px;border:1px solid rgba(217,187,115,.26);color:#ddc17d;font-size:10px;font-style:normal;text-align:center}.game-resolution{padding:9px 12px;border-left:3px solid #78aa91;background:rgba(87,144,114,.13);color:#bfe0ce;font-family:var(--font-display);font-size:12px;line-height:1.5}
.debug-answer{display:block;margin-top:4px;font-size:8px;line-height:1.45;font-weight:500;letter-spacing:.03em;color:#90c9b0}.draft-warning .debug-answer{margin-top:6px;color:#9fd1bb}
.compare-row{display:grid;grid-template-columns:78px minmax(0,1fr) minmax(0,1fr) 250px;gap:8px;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06)}.compare-row>strong{font-family:var(--font-display);font-weight:500;color:#efd18a}.compare-row>p{min-height:40px;display:flex;align-items:center;gap:8px;padding:7px 9px;background:var(--game-paper);font-size:10px;color:rgba(238,230,213,.68)}.compare-row>p i{width:19px;height:19px;display:grid;place-items:center;flex:none;border:1px solid rgba(217,187,115,.32);color:#d8b96f;font-style:normal}.compare-row>div{display:grid;grid-template-columns:repeat(3,1fr);gap:4px}.compare-row button,.layout-controls button,.relation-row button{min-height:34px;border:1px solid rgba(255,255,255,.13);background:transparent;color:rgba(238,230,213,.56);font-size:9px}.compare-row button:hover,.layout-controls button:hover,.relation-row button:hover{border-color:#d8b96f;color:#fff}.compare-row button.selected,.layout-controls button.selected,.relation-row button.selected{border-color:#c79555;background:rgba(199,149,85,.12);color:#fff}.compare-row button.correct,.layout-controls button.correct,.relation-row button.correct{border-color:#78aa91;background:rgba(87,144,114,.18);color:#c9e6d6}.compare-row button.wrong{border-color:#b45d4a;background:rgba(180,93,74,.14);color:#efbaa9}
.relay-slots{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}.relay-slots button{position:relative;min-height:72px;padding:10px;border:1px dashed rgba(217,187,115,.24);background:rgba(0,0,0,.15);color:rgba(238,230,213,.42);text-align:left}.relay-slots button::after{content:'›';position:absolute;right:-7px;top:50%;z-index:2;transform:translateY(-50%);color:#d8b96f}.relay-slots button:last-child::after{display:none}.relay-slots button.filled{border-style:solid;background:rgba(217,187,115,.08);color:#eee6d5}.relay-slots button.wrong{border-color:#b45d4a;background:rgba(180,93,74,.12)}.relay-slots span{display:block;font-size:9px;color:#d8b96f}.relay-slots strong{display:block;margin-top:4px;font-family:var(--font-display);font-size:12px;font-weight:500}.relay-slots small{display:block;margin-top:4px;font-size:8px;color:rgba(238,230,213,.34)}.relay-pool{display:grid;grid-template-columns:repeat(2,1fr);gap:6px}.relay-pool button{display:grid;grid-template-columns:30px 1fr;gap:9px;align-items:center;padding:8px 10px;border:1px solid rgba(255,255,255,.11);background:var(--game-paper);color:#eee6d5;text-align:left}.relay-pool button:hover:not(:disabled){border-color:#d8b96f}.relay-pool button:disabled{opacity:.28}.relay-pool i{width:28px;height:28px;display:grid;place-items:center;border:1px solid rgba(217,187,115,.3);font-family:var(--font-display);font-style:normal;color:#d8b96f}.relay-pool strong,.relay-pool small{display:block}.relay-pool strong{font-family:var(--font-display);font-size:11px;font-weight:500}.relay-pool small{margin-top:2px;font-size:8px;color:rgba(238,230,213,.42)}.game-confirm{justify-self:end;min-width:150px;padding:9px 16px;border:1px solid rgba(217,187,115,.5);background:rgba(217,187,115,.11);color:#f1dfb1}.game-confirm:hover:not(:disabled){background:rgba(217,187,115,.2)}.game-confirm:disabled{opacity:.34}
.layout-game{grid-template-columns:310px 1fr}.layout-game .game-head,.layout-game .game-resolution{grid-column:1/-1}.layout-preview{position:relative;min-height:205px;overflow:hidden;border:1px solid rgba(217,187,115,.2);background:linear-gradient(145deg,rgba(228,211,173,.14),rgba(71,88,76,.08))}.layout-preview::before,.layout-preview::after{content:'';position:absolute;top:23px;bottom:34px;width:1px;background:rgba(217,187,115,.24)}.layout-preview::before{left:50%}.layout-preview::after{left:12%;opacity:.45}.layout-frame{position:absolute;top:34px;width:112px;height:124px;padding:14px;border:1px solid rgba(217,187,115,.42);transition:transform .32s ease,border-color .25s ease}.frame-a{left:24px}.frame-b{right:24px}.outer-shared .frame-a{transform:translateX(21px)}.outer-shared .frame-b{transform:translateX(-21px)}.layout-frame i{display:block;width:70%;height:8px;margin:8px 0;background:#ac8f58;opacity:.62;transition:width .32s ease,margin .32s ease,transform .32s ease}.layout-frame i:nth-child(even){width:42%;margin-left:28%}.frame-b i{transform:rotate(90deg);transform-origin:left center;margin-left:44%;margin-bottom:13px}.spacing-shared .layout-frame i{width:88%;margin-left:0}.flow-shared .frame-b i{transform:none;margin:8px 0}.layout-preview>span{position:absolute;left:0;right:0;bottom:9px;text-align:center;font-size:8px;letter-spacing:.1em;color:rgba(238,230,213,.34)}.layout-controls{display:grid;gap:7px}.layout-controls>div{display:grid;grid-template-columns:95px 1fr 1fr;gap:6px;align-items:center;padding:7px;border-bottom:1px solid rgba(255,255,255,.06)}.layout-controls strong{font-family:var(--font-display);font-size:12px;font-weight:500;color:#efd18a}
.relation-row{display:grid;grid-template-columns:1fr 330px;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06)}.relation-row>p{display:grid;grid-template-columns:1fr 22px 1.35fr;align-items:center;gap:7px;font-size:10px}.relation-row>p span{min-height:38px;display:flex;align-items:center;padding:7px 9px;background:var(--game-paper)}.relation-row>p i{color:#d8b96f;font-style:normal;text-align:center}.relation-row>div{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}.relation-verdict{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:2px}.relation-verdict>span{grid-column:1/-1;font-size:9px;letter-spacing:.08em;color:#d8b96f}
.overlap-board{position:relative;height:190px;overflow:hidden;border:1px solid rgba(217,187,115,.22);background:radial-gradient(circle at 50% 50%,rgba(217,187,115,.12),transparent 50%),rgba(0,0,0,.16)}.overlap-board .paper{position:absolute;top:22px;left:50%;width:245px;height:145px;padding:17px;border:1px solid rgba(231,214,176,.56);background:rgba(205,181,131,.13);transition:transform .18s ease,box-shadow .3s ease}.overlap-board .paper span{font-size:8px;letter-spacing:.12em;color:#e5ca89}.overlap-board .paper i{display:block;width:72%;height:6px;margin-top:13px;background:rgba(225,204,158,.38)}.overlap-board .paper i:nth-child(odd){width:44%;margin-left:18%}.paper-a{transform:translateX(-50%) rotate(-1.5deg)}.paper-b{transform:translateX(calc(-50% + var(--overlap-shift))) rotate(1.5deg);border-color:rgba(95,169,159,.64)!important;background:rgba(63,125,120,.16)!important;mix-blend-mode:screen}.overlap-board.solved .paper{box-shadow:0 0 34px rgba(217,187,115,.18)}.overlap-axis{position:absolute;top:12px;bottom:12px;left:50%;width:1px;background:linear-gradient(transparent,#d8b96f,transparent);box-shadow:0 0 12px #d8b96f}.overlap-control{display:grid;grid-template-columns:40px 1fr 40px;gap:10px;align-items:center;font-size:9px;color:rgba(238,230,213,.46)}.overlap-control input{width:100%;accent-color:#d8b96f}.overlap-control span:last-child{text-align:right}
.rule-board{display:grid;grid-template-columns:1fr 1fr;gap:8px}.rule-card{display:grid;grid-template-columns:120px 1fr;align-items:center;gap:12px;padding:10px;border:1px solid rgba(217,187,115,.14);background:rgba(255,255,255,.025)}.rule-card>strong{font-family:var(--font-display);font-weight:500}.rule-card>div{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}.rule-card button,.archive-row button{padding:7px 5px;border:1px solid rgba(255,255,255,.13);background:transparent;color:rgba(238,230,213,.54);font-size:10px}.rule-card button.selected,.archive-row button.selected{border-color:#c28855;color:#fff}.rule-card button.correct,.archive-row button.correct{border-color:#7eb69a;background:rgba(89,153,119,.18)}.rule-board>p{grid-column:1/-1;margin-top:5px;color:#a8d5bd;text-align:center}
.choice-list{display:grid;gap:9px}.choice-list button{display:grid;grid-template-columns:1fr;gap:5px;padding:15px;border:1px solid rgba(217,187,115,.2);background:rgba(255,255,255,.03);color:#eee6d5;text-align:left}.choice-list button:hover,.choice-list button.selected{border-color:#d9bb73;background:rgba(217,187,115,.1)}.choice-list strong{font-family:var(--font-display);font-size:16px;font-weight:500}.choice-list small{color:rgba(238,230,213,.56);line-height:1.5}.choice-list.final{grid-template-columns:repeat(3,1fr)}.choice-list.final button{grid-template-columns:32px 1fr;align-content:start}.choice-list.final span{grid-row:1/3;width:27px;height:27px;display:grid;place-items:center;border:1px solid #b88951;color:#e2bd72}.choice-list.final small{grid-column:2}
.final-deduction{height:100%;grid-template-rows:auto 44px auto minmax(72px,1fr) 36px}.deduction-tabs{grid-template-columns:repeat(3,1fr)}.deduction-question{display:grid;grid-template-columns:110px 1fr;align-items:center;gap:14px;padding:8px 12px;border-left:3px solid #d8b96f;background:rgba(217,187,115,.07)}.deduction-question span{font-size:9px;letter-spacing:.12em;color:#d8b96f}.deduction-question strong{font-family:var(--font-display);font-size:14px;font-weight:500}.deduction-options{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.deduction-options button{display:grid;align-content:center;gap:7px;min-width:0;padding:10px 12px;border:1px solid rgba(255,255,255,.12);background:rgba(0,0,0,.13);color:rgba(238,230,213,.72);text-align:left}.deduction-options button:hover,.deduction-options button.selected{border-color:#d8b96f;background:rgba(217,187,115,.11);color:#fff}.deduction-options strong{font-family:var(--font-display);font-size:12px;font-weight:500;line-height:1.35}.deduction-options small{overflow:hidden;color:rgba(145,190,176,.68);font-size:8px;line-height:1.45;text-overflow:ellipsis}.decision-consequences{display:grid;grid-template-rows:auto 1fr;gap:8px;min-height:0}.deduction-seal{display:grid;grid-template-columns:repeat(6,auto);justify-content:center;align-items:center;gap:8px;padding:6px;border:1px solid rgba(108,175,151,.25);background:rgba(75,135,112,.09);font-size:9px}.deduction-seal span{color:rgba(238,230,213,.42)}.deduction-seal i{font-family:var(--font-display);font-style:normal;color:#bfe0ce}.decision-consequences .choice-list.final{min-height:0}.decision-consequences .choice-list.final button{min-height:0;padding:10px 12px}.decision-consequences .choice-list.final strong{font-size:13px}.decision-consequences .choice-list.final small{font-size:9px}
.consequence-board{padding:18px 22px;border:1px solid rgba(217,187,115,.26);background:rgba(8,18,16,.72)}.consequence-board header{display:flex;align-items:baseline;justify-content:space-between;padding-bottom:12px;border-bottom:1px solid rgba(217,187,115,.15)}.consequence-board header span{font-size:9px;letter-spacing:.18em;color:#d8b96f}.consequence-board header strong{font-family:var(--font-display);font-size:20px;font-weight:500}.consequence-meters{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:18px 0}.consequence-meters label{display:grid;grid-template-columns:34px 1fr 24px;align-items:center;gap:8px;font-size:9px}.consequence-meters i{height:4px;overflow:hidden;background:rgba(255,255,255,.1)}.consequence-meters b{display:block;height:100%;background:linear-gradient(90deg,#4f8f84,#d8b96f)}.consequence-meters em{font-style:normal;color:#d8b96f;text-align:right}.consequence-board p{font-family:var(--font-display);font-size:13px;line-height:1.6;color:rgba(238,230,213,.7)}.consequence-board.tone-risk{border-color:rgba(190,91,69,.5)}.consequence-board.tone-delay{border-color:rgba(93,151,156,.45)}
.archive-editor{display:grid;gap:8px}.draft-warning{display:flex;justify-content:space-between;padding:10px 13px;border-left:3px solid #d78759;background:rgba(189,89,47,.13)}.draft-warning span{font-size:10px;letter-spacing:.15em}.draft-warning strong{color:#f0bd86;font-size:12px}.archive-row{display:grid;grid-template-columns:1fr 310px;align-items:center;gap:12px;padding:7px 10px;border-bottom:1px solid rgba(255,255,255,.08)}.archive-row p{font-size:12px}.archive-row>div{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}.archive-editor blockquote{padding:12px 14px;border:1px solid rgba(107,172,140,.36);background:rgba(65,126,97,.12);font-family:var(--font-display);font-size:12px;line-height:1.7;color:#cde3d6}.keep-version{display:grid;grid-template-columns:1fr 150px 190px;align-items:center;gap:7px}.keep-version span{font-size:11px;color:#d9bb73}
.evidence-graph{position:relative;height:230px;display:grid;place-items:center}.graph-core{position:relative;z-index:2;width:180px;height:180px;border:1px solid #d9bb73;border-radius:50%;display:grid;place-content:center;text-align:center;font-family:var(--font-display);font-size:20px;background:rgba(15,29,27,.86);box-shadow:0 0 70px rgba(217,187,115,.18)}.graph-core small{font-size:12px;color:#d9bb73}.evidence-graph>span{--angle:calc(var(--i) * 72deg - 90deg);position:absolute;left:calc(50% + cos(var(--angle)) * 270px);top:calc(50% + sin(var(--angle)) * 92px);transform:translate(-50%,-50%);padding:9px 14px;border:1px solid rgba(217,187,115,.28);background:#1b2926;font-size:11px;color:#dec98f}
.story-feedback{position:absolute;left:50%;bottom:236px;transform:translateX(-50%);z-index:12;max-width:min(680px,80vw);padding:9px 28px;background:linear-gradient(90deg,transparent,rgba(26,59,54,.94) 12%,rgba(26,59,54,.94) 88%,transparent);color:#f4d894;text-align:center;font-family:var(--font-display);font-size:13px}
.dialogue-panel{position:absolute;z-index:10;left:clamp(18px,3vw,48px);right:clamp(18px,3vw,48px);bottom:20px;min-height:190px;display:grid;grid-template-columns:1fr 230px;gap:22px;padding:20px 24px;border:1px solid rgba(217,187,115,.42);background:linear-gradient(90deg,rgba(18,28,26,.96),rgba(22,32,29,.93));box-shadow:0 26px 80px rgba(0,0,0,.5);clip-path:polygon(10px 0,calc(100% - 10px) 0,100% 10px,100% calc(100% - 10px),calc(100% - 10px) 100%,10px 100%,0 calc(100% - 10px),0 10px)}.dialogue-history{display:flex;flex-direction:column;justify-content:flex-end;gap:7px;min-width:0}.dialogue-history p{display:grid;grid-template-columns:88px 1fr;gap:12px;opacity:.38;font-size:12px;line-height:1.55}.dialogue-history p.current{opacity:1;font-size:14px}.dialogue-history strong{color:#d9bb73;font-family:var(--font-display);font-weight:500}.dialogue-history span{color:rgba(245,238,222,.85)}.dialogue-history .tone-turn span{color:#f4d68d}.dialogue-history .tone-tense span{color:#efb58f}.dialogue-history .tone-system strong{color:#86bdc7}.dialogue-actions{display:flex;flex-direction:column;justify-content:flex-end;gap:8px}.dialogue-actions button{min-height:48px;padding:0 15px;border:1px solid rgba(217,187,115,.45);background:rgba(217,187,115,.1);color:#f1e6d1;text-align:left}.dialogue-actions button:hover:not(:disabled){border-color:#eacb83;background:rgba(217,187,115,.16)}.dialogue-actions button:disabled{opacity:.42;cursor:not-allowed}.dialogue-actions button span{float:right;font-size:19px}.dialogue-actions small{font-size:9px;line-height:1.45;color:rgba(238,230,213,.38)}
.evidence-drawer{position:absolute;z-index:30;right:0;top:0;bottom:0;width:min(390px,92vw);padding:24px;background:rgba(238,236,218,.98);color:#29454a;box-shadow:-24px 0 70px rgba(0,0,0,.35);overflow:hidden}.evidence-drawer header{display:flex;justify-content:space-between;align-items:start;padding-bottom:18px;border-bottom:1px solid rgba(40,95,97,.18)}.evidence-drawer header span{display:block;font-size:9px;letter-spacing:.18em;color:#b2513d}.evidence-drawer header strong{display:block;margin-top:3px;font-family:var(--font-display);font-size:24px}.evidence-drawer header button{border:0;background:transparent;font-size:28px;color:#29454a}.evidence-drawer ol{list-style:none;margin:18px 0 0;padding:0}.evidence-drawer li{display:grid;grid-template-columns:34px 1fr;gap:9px;padding:12px 0;border-bottom:1px solid rgba(40,95,97,.12)}.evidence-drawer li span{color:#b28a45;font-size:10px}.evidence-drawer li strong{font-family:var(--font-display);font-weight:500}.evidence-drawer>p{margin-top:16px;font-size:10px;line-height:1.6;color:rgba(41,69,74,.58)}.evidence-drawer .reset{width:100%;margin-top:24px;padding:10px;border:1px solid rgba(178,81,61,.3);background:transparent;color:#9e3f32}
.story-footnote{position:fixed;z-index:25;left:0;right:0;bottom:0;height:calc(26px + env(safe-area-inset-bottom));display:flex;justify-content:space-between;align-items:flex-start;padding:7px 28px env(safe-area-inset-bottom);background:#0b1211;color:rgba(238,230,213,.38);font-size:9px;letter-spacing:.08em;box-sizing:border-box}
.workbench-enter-active,.workbench-leave-active,.notice-enter-active,.notice-leave-active,.drawer-enter-active,.drawer-leave-active{transition:opacity .25s ease,transform .35s ease}.workbench-enter-from,.workbench-leave-to{opacity:0;transform:translate(-50%,-46%) scale(.98)}.notice-enter-from,.notice-leave-to{opacity:0;transform:translate(-50%,8px)}.drawer-enter-from,.drawer-leave-to{opacity:0;transform:translateX(100%)}
@keyframes scene-in{from{opacity:.18;filter:blur(5px);transform:scale(1.065)}to{opacity:1;filter:blur(0);transform:scale(1)}}

/* V10 商业叙事舞台：同一拓印美术体系，不同镜头；单人物、单句对白。 */
.story-stage{
  --stage-ink:#09110f;
  --stage-jade:#3f7d78;
  --stage-gold:#d8b96f;
  --stage-paper:#eee2c8;
  --stage-red:#ae5a46;
  background:var(--stage-ink);
}
.story-backdrop{overflow:hidden;background:#121b18}
.story-backdrop::after{content:'';position:absolute;inset:0;pointer-events:none;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.48' numOctaves='3' stitchTiles='stitchTiles'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.22'/%3E%3C/svg%3E");mix-blend-mode:soft-light;opacity:.32}
.story-backdrop__main,.story-backdrop__mid,.story-backdrop__foreground{will-change:transform,opacity;transition:transform 8s ease-out,filter .8s ease,opacity .8s ease}
.story-backdrop__main{filter:saturate(.68) contrast(1.08) brightness(.62);transform:scale(1.045);animation:camera-breathe 14s ease-in-out infinite alternate}
.story-backdrop__mid{object-fit:contain!important;opacity:.34;mix-blend-mode:screen;filter:saturate(.62) sepia(.18)}
.story-backdrop__foreground{object-fit:contain!important;top:auto!important;bottom:-3%!important;height:38%!important;opacity:.78;filter:brightness(.72) saturate(.65)}
.story-backdrop__rain{position:absolute;inset:-20%;opacity:.42;background:repeating-linear-gradient(106deg,transparent 0 16px,rgba(214,230,218,.32) 17px,transparent 19px);transform:translate3d(0,-12%,0);animation:rain-fall .72s linear infinite}
.story-shade{background:linear-gradient(90deg,rgba(6,12,11,.74),rgba(6,12,11,.08) 30%,rgba(6,12,11,.04) 66%,rgba(6,12,11,.64)),linear-gradient(180deg,rgba(4,9,8,.26),transparent 38%,rgba(4,9,8,.2) 62%,rgba(4,9,8,.88) 88%)}

/* 十二幕拥有独立的镜头与景别，但沿用同一矿物色和拓印质感。 */
.framing-archive-desk .story-backdrop__main{object-position:52% 42%;filter:saturate(.32) brightness(.44) contrast(1.16)}
.framing-archive-desk .story-backdrop__mid{width:43%;height:43%;left:auto;right:3%;top:22%;opacity:.26;mix-blend-mode:screen}
.framing-wide-arrival .story-backdrop__main{object-position:50% 43%}
.framing-work-yard .story-backdrop__main{object-position:50% 28%;filter:saturate(.5) brightness(.5) contrast(1.12)}
.framing-work-yard .story-backdrop__mid{height:82%;top:4%;opacity:.7;mix-blend-mode:normal}
.framing-work-yard .story-backdrop__foreground{width:46%;height:48%!important;left:auto;right:3%;bottom:12%!important;opacity:.42}
.framing-wall-close .story-backdrop__main{object-position:18% 20%;transform:scale(1.28);filter:saturate(.5) brightness(.48) contrast(1.14)}
.framing-wall-close .story-backdrop__mid{opacity:.22;mix-blend-mode:screen}
.framing-rain-table .story-backdrop__main{object-position:50% 10%;filter:saturate(.24) brightness(.38) contrast(1.18)}
.framing-rain-table .story-backdrop__mid{height:88%;top:0;opacity:.5;mix-blend-mode:normal}
.framing-paper-close .story-backdrop__main{object-position:42% 38%;transform:scale(1.08);filter:saturate(.52) brightness(.36) contrast(1.16)}
.framing-paper-close .story-backdrop__mid{opacity:.16;mix-blend-mode:screen}
.framing-shared-table .story-backdrop__main{object-position:center 38%;filter:saturate(.45) brightness(.4) contrast(1.13)}
.framing-shared-table .story-backdrop__foreground{height:52%!important;bottom:8%!important;opacity:.46}
.framing-inscription-wall .story-backdrop__main{object-position:82% 20%;transform:scale(1.22);filter:saturate(.56) brightness(.43) contrast(1.18)}
.framing-inscription-wall .story-backdrop__mid{opacity:.3;mix-blend-mode:screen}
.framing-decision-stage .story-backdrop__main{object-position:50% 36%;filter:saturate(.6) brightness(.4) contrast(1.15)}
.framing-decision-stage .story-backdrop__foreground{height:44%!important;opacity:.83}
.framing-road-passage .story-backdrop__main{object-position:center 56%;filter:saturate(.52) brightness(.5) contrast(1.08)}
.framing-road-passage .story-backdrop__mid{height:92%;opacity:.64;mix-blend-mode:normal}
.framing-road-passage .story-backdrop__foreground{height:31%!important;opacity:.68}
.framing-archive-review .story-backdrop__main{object-position:74% 36%;filter:saturate(.24) brightness(.38) contrast(1.22)}
.framing-archive-review .story-backdrop__mid,.framing-archive-graph .story-backdrop__mid{opacity:.34;mix-blend-mode:screen}
.framing-archive-graph .story-backdrop__main{object-position:50% 50%;filter:saturate(.18) brightness(.29) contrast(1.2);transform:scale(1.1)}

.scene-heading{z-index:6;top:24px;animation:heading-develop .72s .2s cubic-bezier(.2,.76,.22,1) both}.scene-heading h1{font-size:clamp(28px,3.4vw,48px)}
.scene-heading p::before{content:'';display:inline-block;width:22px;height:1px;margin:0 9px 3px 0;background:currentColor;transform-origin:left;animation:location-rule .7s .35s ease both}.scene-objective{z-index:6;animation:objective-develop .62s .32s ease both}

/* V13 场景显影：拓纸从两侧覆合，以金色拼缝完成换幕，再揭开下一景。 */
.scene-transition{position:absolute;z-index:40;inset:0;overflow:hidden;pointer-events:none;contain:paint;perspective:1000px}
.transition-sheet{position:absolute;top:-8%;width:56%;height:116%;overflow:hidden;background-color:#172420;background-image:linear-gradient(104deg,rgba(230,215,177,.055),transparent 18% 78%,rgba(0,0,0,.26)),url("data:image/svg+xml,%3Csvg viewBox='0 0 160 160' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='r'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.065 .48' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23r)' opacity='.34'/%3E%3C/svg%3E");box-shadow:0 0 80px rgba(0,0,0,.7);will-change:transform}
.transition-sheet::before{content:'';position:absolute;inset:0;background:radial-gradient(circle at 56% 35%,rgba(93,143,126,.2),transparent 32%),repeating-linear-gradient(172deg,transparent 0 38px,rgba(225,207,164,.035) 39px 40px);mix-blend-mode:screen}
.transition-sheet::after{content:'';position:absolute;top:0;bottom:0;width:42px;background:linear-gradient(90deg,transparent,rgba(225,193,118,.16),rgba(255,228,158,.5),rgba(225,193,118,.08),transparent);filter:blur(.4px)}
.transition-sheet--left{left:-5%;transform-origin:right center;clip-path:polygon(0 0,96% 0,100% 5%,97% 11%,100% 18%,98% 27%,100% 36%,97% 44%,100% 53%,98% 61%,100% 70%,97% 79%,100% 88%,98% 94%,100% 100%,0 100%)}
.transition-sheet--right{right:-5%;transform-origin:left center;clip-path:polygon(4% 0,100% 0,100% 100%,0 100%,2% 94%,0 88%,3% 79%,0 70%,2% 61%,0 53%,3% 44%,0 36%,2% 27%,0 18%,3% 11%,0 5%)}
.transition-sheet--left::after{right:-8px}.transition-sheet--right::after{left:-8px;transform:scaleX(-1)}
.transition-sheet i,.transition-sheet b{position:absolute;display:block;border:1px solid rgba(215,184,111,.17);border-radius:50%;opacity:.5}
.transition-sheet i{width:44vw;height:44vw;left:18%;top:7%}.transition-sheet b{width:22vw;height:22vw;right:7%;bottom:8%;border-style:dashed}
.transition-seam{position:absolute;z-index:2;left:50%;top:0;width:1px;height:100%;background:linear-gradient(180deg,transparent 4%,#f0d18a 24%,#a67938 72%,transparent 96%);box-shadow:0 0 7px #f1ce7d,0 0 28px rgba(230,189,91,.55);transform:scaleY(0);transform-origin:center}
.transition-seam i{position:absolute;left:50%;top:50%;width:11px;height:11px;border:1px solid #edcf8a;background:#1c2b27;transform:translate(-50%,-50%) rotate(45deg);box-shadow:0 0 22px rgba(239,203,121,.8)}
.transition-title{position:absolute;z-index:3;left:50%;top:50%;width:min(520px,76vw);transform:translate(-50%,-50%);text-align:center;color:#f0e5cc;text-shadow:0 4px 24px #000}
.transition-title::before,.transition-title::after{content:'';display:inline-block;width:76px;height:1px;margin:0 16px 3px;background:linear-gradient(90deg,transparent,#d9b867)}
.transition-title::after{transform:scaleX(-1)}
.transition-title span{font-size:9px;letter-spacing:.3em;color:#d5b56e}.transition-title strong{display:block;margin:12px 0 8px;font-family:var(--font-display);font-size:clamp(28px,3.8vw,52px);font-weight:400;letter-spacing:.08em}.transition-title small{font-size:10px;letter-spacing:.16em;color:rgba(238,226,200,.55)}
.phase-cover .transition-sheet--left{animation:sheet-cover-left .34s cubic-bezier(.22,.72,.24,1) both}.phase-cover .transition-sheet--right{animation:sheet-cover-right .34s cubic-bezier(.22,.72,.24,1) both}.phase-cover .transition-seam{animation:seam-in .26s .13s ease-out both}.phase-cover .transition-title{animation:transition-title-in .25s .1s ease-out both}
.phase-reveal .transition-sheet--left{animation:sheet-reveal-left .62s cubic-bezier(.52,.04,.3,1) both}.phase-reveal .transition-sheet--right{animation:sheet-reveal-right .62s cubic-bezier(.52,.04,.3,1) both}.phase-reveal .transition-seam{animation:seam-out .36s ease-in both}.phase-reveal .transition-title{animation:transition-title-out .38s .12s ease-in both}

.speaker-portrait{position:absolute;z-index:3;bottom:116px;width:min(42vw,590px);height:min(72vh,690px);margin:0;pointer-events:none;filter:drop-shadow(0 25px 35px rgba(0,0,0,.52));transition:opacity .35s ease,filter .35s ease,transform .55s cubic-bezier(.18,.78,.18,1)}
.speaker-portrait.is-left{left:3vw}.speaker-portrait.is-right{right:3vw}.speaker-portrait.is-center{left:50%;transform:translateX(-50%)}
.speaker-portrait__image{position:absolute;inset:0;background-image:var(--portrait-image);background-repeat:no-repeat;background-size:contain;background-position:center bottom;filter:saturate(.75) contrast(1.05)}
.speaker-portrait figcaption{position:absolute;left:8%;bottom:8%;padding:5px 10px;border-left:2px solid var(--stage-gold);background:rgba(8,18,16,.74);font-size:9px;letter-spacing:.14em;color:rgba(238,226,200,.62);opacity:0;transition:opacity .2s ease}
.speaker-portrait:hover figcaption{opacity:1}
.speaker-chen .speaker-portrait__image,.speaker-passer-a .speaker-portrait__image{background-size:auto 102%;background-position:left bottom}
.speaker-temur .speaker-portrait__image{background-position:center bottom}
.speaker-sangjie .speaker-portrait__image{background-position:center bottom}
.speaker-foreman .speaker-portrait__image{background-position:center bottom}
.speaker-player .speaker-portrait__image{transform:scaleX(-1);filter:saturate(.35) brightness(.52) sepia(.2);opacity:.75}
.speaker-passer-a,.speaker-passer-b{opacity:.65;transform:scale(.86);transform-origin:bottom}.speaker-passer-b .speaker-portrait__image{filter:saturate(.34) brightness(.62)}
.speaker-portrait.is-working{opacity:.16;filter:blur(1px) drop-shadow(0 18px 30px rgba(0,0,0,.4));transform:translateY(18px) scale(.96)}
.speaker-portrait.is-center.is-working{transform:translateX(-50%) translateY(18px) scale(.96)}
.speaker-portrait__sigil{position:absolute;right:9%;bottom:20%;width:210px;height:210px;border:1px solid rgba(113,185,178,.48);border-radius:50%;display:grid;place-content:center;text-align:center;background:radial-gradient(circle,rgba(83,155,150,.25),rgba(9,23,22,.42) 58%,transparent 70%);box-shadow:0 0 90px rgba(91,177,168,.22)}
.speaker-portrait__sigil::before,.speaker-portrait__sigil::after{content:'';position:absolute;inset:20px;border:1px solid rgba(217,187,115,.25);border-radius:50%;animation:sigil-spin 18s linear infinite}.speaker-portrait__sigil::after{inset:48px;border-style:dashed;animation-direction:reverse}
.speaker-portrait__sigil i{position:absolute;left:50%;top:50%;width:8px;height:8px;border-radius:50%;background:#d9bb73;box-shadow:0 0 28px 9px rgba(217,187,115,.42);transform:translate(-50%,-50%)}
.speaker-portrait__sigil b,.speaker-portrait__sigil span{font-family:var(--font-display);font-size:31px;font-weight:400;color:#cce3dc}.speaker-portrait__sigil span{margin-top:-6px;color:#d9bb73}

.workbench{z-index:8;top:43%;width:min(920px,70vw);max-height:40vh;border-color:rgba(217,187,115,.32);background:linear-gradient(135deg,rgba(13,25,23,.92),rgba(25,34,30,.86));box-shadow:0 28px 90px rgba(0,0,0,.48),0 0 0 1px rgba(255,244,210,.07) inset;clip-path:polygon(8px 0,calc(100% - 8px) 0,100% 8px,100% calc(100% - 8px),calc(100% - 8px) 100%,8px 100%,0 calc(100% - 8px),0 8px)}
.interaction-01,.interaction-04{width:min(1040px,80vw)}.interaction-02,.interaction-03{width:min(960px,76vw)}.interaction-05{width:min(760px,68vw)}.interaction-07,.interaction-08{width:min(980px,78vw)}.interaction-09{background:rgba(12,24,21,.72)}.interaction-10{top:42%;max-height:45vh}

.dialogue-panel{position:absolute;z-index:14;left:clamp(26px,7vw,110px);right:clamp(26px,7vw,110px);bottom:31px;width:auto;min-height:142px;display:block;padding:35px 72px 24px;border:1px solid rgba(221,192,127,.62);background:linear-gradient(90deg,rgba(10,21,19,.97),rgba(18,31,28,.96) 48%,rgba(10,21,19,.97));box-shadow:0 34px 90px rgba(0,0,0,.62),0 0 38px rgba(217,187,115,.07) inset;clip-path:polygon(14px 0,calc(100% - 14px) 0,100% 14px,100% calc(100% - 14px),calc(100% - 14px) 100%,14px 100%,0 calc(100% - 14px),0 14px);color:inherit;text-align:left;cursor:pointer;outline:none;user-select:none;transition:border-color .2s ease,background .2s ease,transform .15s ease}
.dialogue-panel::before{content:'';position:absolute;left:22px;right:22px;top:9px;height:1px;background:linear-gradient(90deg,transparent,var(--stage-gold),transparent);opacity:.55}
.dialogue-panel:hover,.dialogue-panel:focus-visible{border-color:#efd08a;background:linear-gradient(90deg,rgba(11,25,22,.99),rgba(25,39,35,.98),rgba(11,25,22,.99))}.dialogue-panel:active{transform:translateY(1px)}
.dialogue-panel.is-blocked{cursor:default;border-color:rgba(139,164,151,.38)}
.dialogue-name{position:absolute;left:42px;top:-18px;min-width:130px;padding:8px 24px 7px;border:1px solid rgba(221,192,127,.68);background:#14231f;font-family:var(--font-display);font-size:18px;letter-spacing:.12em;color:#f2d386;text-align:center;box-shadow:0 10px 24px rgba(0,0,0,.3)}
.dialogue-role{position:absolute;left:194px;top:10px;font-size:9px;letter-spacing:.16em;color:rgba(226,211,180,.46)}
.dialogue-text{display:block;max-width:980px;margin:0;font-family:var(--font-display);font-size:clamp(17px,1.55vw,22px);line-height:1.82;letter-spacing:.025em;color:#f3ecdc;text-shadow:0 2px 14px rgba(0,0,0,.3)}
.dialogue-panel.tone-turn>.dialogue-text{color:#f4d890}.dialogue-panel.tone-tense>.dialogue-text{color:#efc1a2}.dialogue-panel.tone-system .dialogue-name{color:#bce0d9;border-color:rgba(104,177,169,.62)}.dialogue-panel.tone-system>.dialogue-text{color:#d7e7e1}
.dialogue-cue{position:absolute;right:34px;bottom:22px;display:flex;align-items:center;gap:12px;font-size:9px;letter-spacing:.14em;color:rgba(238,226,200,.45)}.dialogue-cue i{font-style:normal;font-size:10px;color:#e0bf72;animation:cue-pulse 1.15s ease-in-out infinite}.dialogue-cue i.paused{color:#829b8f;animation:none}
.line-change-enter-active,.line-change-leave-active{transition:opacity .16s ease,transform .2s ease}.line-change-enter-from{opacity:0;transform:translateY(6px)}.line-change-leave-to{opacity:0;transform:translateY(-4px)}
.portrait-enter-active,.portrait-leave-active{transition:opacity .28s ease,transform .45s cubic-bezier(.2,.78,.18,1)}.portrait-enter-from,.portrait-leave-to{opacity:0}.portrait-enter-from.is-left,.portrait-leave-to.is-left{transform:translateX(-38px)}.portrait-enter-from.is-right,.portrait-leave-to.is-right{transform:translateX(38px)}
.story-feedback{z-index:16;bottom:190px}
.yuan-story button:focus-visible,.yuan-story a:focus-visible{outline:2px solid #efd08a;outline-offset:3px}
.ending-risk .graph-core{border-color:#b45d4a;box-shadow:0 0 70px rgba(180,93,74,.24)}.ending-delay .graph-core{border-color:#6b9ca1;box-shadow:0 0 70px rgba(82,142,151,.22)}

/* V14 单屏证据台：一次只解决一个判断，所有玩法均在固定舞台内完成。 */
.yuan-story{overscroll-behavior:none;touch-action:manipulation}
.workbench{height:min(350px,42vh);max-height:none;overflow:hidden;box-sizing:border-box}
.case-table{height:100%;min-height:0;gap:8px}
.game-head{min-height:38px;padding-bottom:8px}.game-head strong{font-size:15px}.game-head em{align-self:center}
.case-tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;min-height:44px}
.case-tabs button{display:grid;grid-template-columns:28px 1fr 16px;align-items:center;gap:7px;min-width:0;min-height:44px;padding:5px 8px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.025);color:rgba(238,230,213,.46);text-align:left;transition:border-color .18s ease,background .18s ease,color .18s ease}
.case-tabs button:hover,.case-tabs button.active{border-color:rgba(217,187,115,.65);background:rgba(217,187,115,.1);color:#f4e7cc}.case-tabs button.done{color:#b9d8c8}.case-tabs button.error{border-color:#b45d4a;color:#efbaa9}.case-tabs i{font-size:8px;font-style:normal;color:#d8b96f}.case-tabs span{overflow:hidden;font-family:var(--font-display);font-size:11px;white-space:nowrap;text-overflow:ellipsis}.case-tabs b{font-size:8px;font-weight:400;text-align:right}
.compare-game{grid-template-rows:auto 44px minmax(80px,1fr) 44px auto}
.compare-stage{display:grid;grid-template-columns:minmax(0,1fr) 104px minmax(0,1fr);gap:10px;min-height:0;align-items:stretch}
.sample-card{position:relative;overflow:hidden;display:grid;align-content:center;gap:7px;padding:14px 17px;border:1px solid rgba(223,198,138,.24);background:linear-gradient(145deg,rgba(221,198,151,.13),rgba(255,255,255,.025))}
.sample-card::before{content:'';position:absolute;inset:0;background:repeating-linear-gradient(173deg,transparent 0 17px,rgba(224,204,158,.035) 18px);pointer-events:none}.sample-card span{font-size:8px;letter-spacing:.18em;color:#d8b96f}.sample-card strong{position:relative;font-family:var(--font-display);font-size:14px;font-weight:500;line-height:1.45}.sample-b{border-color:rgba(92,157,149,.36);background:linear-gradient(145deg,rgba(63,125,120,.17),rgba(255,255,255,.025))}.scan-line{position:absolute;left:0;right:0;top:12%;height:1px;background:linear-gradient(90deg,transparent,#efd58e,transparent);box-shadow:0 0 10px rgba(239,213,142,.45);animation:evidence-scan 2.1s ease-in-out infinite}
.comparison-lens{display:grid;place-content:center;text-align:center;border-left:1px solid rgba(217,187,115,.18);border-right:1px solid rgba(217,187,115,.18)}.comparison-lens span{font-size:9px;letter-spacing:.13em;color:#d8b96f}.comparison-lens b{font-family:var(--font-display);font-size:25px;font-weight:400;color:#8ebcb0}.comparison-lens small{font-size:8px;color:rgba(238,230,213,.38)}
.verdict-deck,.relation-options{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.verdict-deck button,.relation-options button{display:flex;align-items:center;justify-content:center;gap:8px;min-height:44px;border:1px solid rgba(255,255,255,.13);background:rgba(0,0,0,.12);color:rgba(238,230,213,.6)}.verdict-deck button:hover,.verdict-deck button.selected,.relation-options button:hover,.relation-options button.selected{border-color:#d8b96f;background:rgba(217,187,115,.12);color:#fff}.verdict-deck i,.relation-options i{font-family:var(--font-display);font-size:18px;font-style:normal;color:#d8b96f}.verdict-deck span,.relation-options span{font-size:10px}.compare-game>.game-confirm,.layout-game>.game-confirm,.relation-game>.game-confirm{justify-self:stretch;min-height:44px;padding:6px}
.relay-game{grid-template-rows:auto 20px 65px minmax(68px,1fr) 44px auto}.relay-signal{position:relative;height:18px;overflow:hidden;background:rgba(0,0,0,.18)}.relay-signal::before{content:'';position:absolute;left:0;top:50%;width:var(--relay-progress);height:2px;background:linear-gradient(90deg,#4d8d87,#e4c16e);box-shadow:0 0 11px rgba(217,187,115,.45);transition:width .35s ease}.relay-signal i{position:absolute;left:calc(var(--relay-progress) - 5px);top:4px;width:10px;height:10px;border:1px solid #e1c274;background:#172622;transform:rotate(45deg);transition:left .35s ease}.relay-signal span,.relay-signal b{position:absolute;top:3px;font-size:8px;letter-spacing:.12em}.relay-signal span{left:10px;color:rgba(238,230,213,.42)}.relay-signal b{right:10px;font-weight:400;color:#d8b96f}.relay-slots button{min-height:61px;padding:7px}.relay-pool button{min-height:44px;padding:5px 8px}.relay-pool i{width:24px;height:24px}.relay-pool small{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.relay-game>.game-confirm{min-height:44px;padding:5px 12px}
.layout-game{grid-template-columns:minmax(270px,.9fr) minmax(310px,1.1fr);grid-template-rows:auto 36px minmax(130px,1fr) auto}.layout-game .game-head,.layout-game .layout-tabs,.layout-game .game-resolution,.layout-game>.game-confirm{grid-column:1/-1}.layout-preview{min-height:0}.layout-console{display:grid;align-content:center;gap:7px;padding:12px 16px;border:1px solid rgba(217,187,115,.14);background:rgba(0,0,0,.12)}.layout-console>span{font-size:8px;letter-spacing:.16em;color:rgba(238,230,213,.4)}.layout-console>strong{font-family:var(--font-display);font-size:17px;font-weight:500;color:#efd18a}.layout-console>div{display:grid;grid-template-columns:1fr 1fr;gap:7px}.layout-console button{min-height:38px;border:1px solid rgba(255,255,255,.13);background:transparent;color:rgba(238,230,213,.58)}.layout-console button:hover,.layout-console button.selected{border-color:#d8b96f;background:rgba(217,187,115,.12);color:#fff}.layout-console small{font-size:8px;line-height:1.5;color:rgba(238,230,213,.36)}.calibration-reticle{position:absolute;left:50%;top:50%;width:34px;height:34px;border:1px solid rgba(115,183,171,.62);border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 22px rgba(92,157,149,.25)}.calibration-reticle i{position:absolute;background:#79aa9f}.calibration-reticle i:first-child{left:50%;top:-10px;width:1px;height:54px}.calibration-reticle i:last-child{left:-10px;top:50%;width:54px;height:1px}.layout-frame{top:18px;height:104px}.frame-a{left:15px}.frame-b{right:15px}
.relation-game{grid-template-rows:auto 44px minmax(78px,1fr) 44px auto}.relation-stage{display:grid;grid-template-columns:minmax(0,1fr) 120px minmax(0,1.2fr);align-items:center;gap:8px;min-height:0}.relation-node{height:100%;display:grid;align-content:center;gap:5px;padding:12px 16px;border:1px solid rgba(217,187,115,.2);background:var(--game-paper)}.relation-node span{font-size:8px;letter-spacing:.16em;color:#d8b96f}.relation-node strong{font-family:var(--font-display);font-size:15px;font-weight:500}.relation-node.is-conclusion{border-color:rgba(96,157,149,.3)}.relation-wire{position:relative;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:5px}.relation-wire i{height:1px;background:linear-gradient(90deg,transparent,#d8b96f)}.relation-wire i:last-child{transform:scaleX(-1)}.relation-wire b{font-size:8px;font-weight:400;color:rgba(238,230,213,.38)}.relation-verdict{height:100%;align-content:center;margin:0}.relation-verdict button{min-height:44px}.relation-tabs{grid-template-columns:repeat(3,1fr)}
.overlap-game{grid-template-rows:auto minmax(118px,1fr) 28px 44px auto}.overlap-board{height:auto;min-height:0}.overlap-board output{position:absolute;right:10px;bottom:8px;font-size:8px;letter-spacing:.1em;color:#d8b96f}.registration-mark{position:absolute;left:50%;top:50%;width:44px;height:44px;border:1px solid rgba(121,184,170,.55);border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 calc(var(--alignment-glow,12px)) rgba(105,177,163,.28)}.registration-mark i,.registration-mark b{position:absolute;background:#d8b96f}.registration-mark i{left:50%;top:-8px;width:1px;height:60px}.registration-mark b{left:-8px;top:50%;width:60px;height:1px}.overlap-board.solved .registration-mark{border-color:#e4c878;box-shadow:0 0 28px rgba(228,200,120,.52)}
.rule-game{height:100%;grid-template-rows:auto 44px minmax(112px,1fr) 44px}.rule-tabs{grid-template-columns:repeat(6,1fr)}.rule-stage{display:grid;grid-template-columns:minmax(180px,.72fr) minmax(0,1.28fr);gap:9px;min-height:0}.rule-stage>div:first-child{display:grid;align-content:center;gap:5px;padding:12px 16px;border-left:3px solid #d8b96f;background:var(--game-paper)}.rule-stage>div:first-child span{font-size:8px;letter-spacing:.16em;color:#d8b96f}.rule-stage>div:first-child strong{font-family:var(--font-display);font-size:21px;font-weight:500}.rule-stage>div:first-child small{font-size:9px;line-height:1.45;color:rgba(238,230,213,.42)}.rule-options{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.rule-options button{display:grid;align-content:center;gap:6px;min-width:0;min-height:76px;padding:9px;border:1px solid rgba(255,255,255,.12);background:rgba(0,0,0,.12);color:rgba(238,230,213,.62)}.rule-options button:hover,.rule-options button.selected{border-color:#d8b96f;background:rgba(217,187,115,.11);color:#fff}.rule-options strong{font-family:var(--font-display);font-weight:500}.rule-options small{font-size:8px;line-height:1.4;color:rgba(238,230,213,.4)}.rule-game>.game-confirm{justify-self:stretch;min-height:44px}
.people-game{height:100%;grid-template-rows:auto 44px minmax(76px,1fr) 44px 44px}.people-tabs{grid-template-columns:repeat(3,1fr)}.people-stage{display:grid;grid-template-columns:1fr 76px 1.25fr;align-items:stretch;gap:7px;min-height:0}.people-stage>div{display:grid;align-content:center;gap:5px;padding:10px 13px;border:1px solid rgba(217,187,115,.18);background:var(--game-paper)}.people-stage span{font-size:8px;letter-spacing:.16em;color:#d8b96f}.people-stage strong{font-family:var(--font-display);font-size:13px;font-weight:500;line-height:1.4}.people-stage>i{display:grid;place-items:center;color:rgba(238,230,213,.36);font-size:8px;font-style:normal}.people-options{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.people-options button{display:flex;align-items:center;justify-content:center;gap:8px;min-height:44px;border:1px solid rgba(255,255,255,.12);background:rgba(0,0,0,.12);color:rgba(238,230,213,.6)}.people-options button:hover,.people-options button.selected{border-color:#d8b96f;background:rgba(217,187,115,.11);color:#fff}.people-options i{width:23px;height:23px;display:grid;place-items:center;border:1px solid rgba(217,187,115,.35);font-family:var(--font-display);font-style:normal;color:#d8b96f}.people-game>.game-confirm{justify-self:stretch;min-height:44px}.knowledge-response{display:grid;grid-template-rows:auto 1fr;gap:8px;min-height:0}.boundary-seal{display:flex;justify-content:center;align-items:center;gap:8px;padding:8px;border:1px solid rgba(99,165,145,.25);background:rgba(67,126,106,.1);font-size:9px}.boundary-seal span{color:rgba(238,230,213,.4)}.boundary-seal strong{font-family:var(--font-display);font-weight:500;color:#c4dfd2}.boundary-seal i{width:20px;height:1px;background:rgba(217,187,115,.38)}.knowledge-response .choice-list{grid-template-columns:repeat(3,1fr);gap:6px}.knowledge-response .choice-list button{min-height:86px;padding:10px}.knowledge-response .choice-list strong{font-size:13px}.knowledge-response .choice-list small{font-size:9px}
.archive-editor{height:100%;grid-template-rows:auto 36px minmax(0,1fr);align-content:start}.archive-tabs{grid-template-columns:repeat(4,1fr)}.archive-card{height:100%;grid-template-columns:1fr 270px;border:1px solid rgba(217,187,115,.14);background:rgba(0,0,0,.12)}.archive-card p{align-self:center;font-family:var(--font-display);font-size:16px;line-height:1.6}.archive-editor blockquote{margin:0;align-self:center}.keep-version{align-self:end}
.evidence-drawer{display:flex;flex-direction:column;overflow:hidden}.evidence-drawer ol{min-height:0;flex:1;display:grid;align-content:start;grid-auto-rows:minmax(42px,1fr);overflow:hidden}.evidence-drawer li{min-height:0;padding:8px 0}.drawer-pages{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;margin-top:12px}.drawer-pages button{padding:7px;border:1px solid rgba(41,69,74,.24);background:transparent;color:#29454a}.drawer-pages button:disabled{opacity:.3}.drawer-pages span{font-size:9px}.evidence-drawer .reset{margin-top:12px}
.puzzle-card-enter-active,.puzzle-card-leave-active{transition:opacity .16s ease,transform .2s ease}.puzzle-card-enter-from{opacity:0;transform:translateX(12px)}.puzzle-card-leave-to{opacity:0;transform:translateX(-12px)}

@keyframes camera-breathe{from{transform:scale(1.045) translate3d(-.4%,0,0)}to{transform:scale(1.075) translate3d(.4%,-.6%,0)}}
@keyframes rain-fall{to{transform:translate3d(-6%,12%,0)}}
@keyframes cue-pulse{0%,100%{opacity:.35;transform:translateY(-2px) rotate(45deg)}50%{opacity:1;transform:translateY(2px) rotate(45deg)}}
@keyframes sigil-spin{to{transform:rotate(360deg)}}
@keyframes heading-develop{from{opacity:0;transform:translate3d(-22px,5px,0);filter:blur(3px)}to{opacity:1;transform:translate3d(0,0,0);filter:blur(0)}}
@keyframes location-rule{from{transform:scaleX(0);opacity:0}to{transform:scaleX(1);opacity:1}}
@keyframes objective-develop{from{opacity:0;transform:translateX(18px)}to{opacity:1;transform:translateX(0)}}
@keyframes sheet-cover-left{from{transform:translate3d(-106%,0,0) rotateY(-7deg)}to{transform:translate3d(0,0,0) rotateY(0)}}
@keyframes sheet-cover-right{from{transform:translate3d(106%,0,0) rotateY(7deg)}to{transform:translate3d(0,0,0) rotateY(0)}}
@keyframes sheet-reveal-left{0%{transform:translate3d(0,0,0)}15%{transform:translate3d(-1.5%,0,0)}100%{transform:translate3d(-108%,0,0) rotateY(-5deg)}}
@keyframes sheet-reveal-right{0%{transform:translate3d(0,0,0)}15%{transform:translate3d(1.5%,0,0)}100%{transform:translate3d(108%,0,0) rotateY(5deg)}}
@keyframes seam-in{from{opacity:0;transform:scaleY(0)}to{opacity:1;transform:scaleY(1)}}
@keyframes seam-out{from{opacity:1;transform:scaleY(1)}to{opacity:0;transform:scaleY(.25)}}
@keyframes transition-title-in{from{opacity:0;transform:translate(-50%,-46%) scale(.98);letter-spacing:.04em}to{opacity:1;transform:translate(-50%,-50%) scale(1);letter-spacing:normal}}
@keyframes transition-title-out{from{opacity:1;transform:translate(-50%,-50%) scale(1)}to{opacity:0;transform:translate(-50%,-54%) scale(1.02)}}
@keyframes evidence-scan{0%,100%{top:13%;opacity:.15}50%{top:84%;opacity:.8}}
@media(max-width:900px){
  .story-nav{grid-template-columns:52px 1fr 118px;gap:6px;padding:0 12px}.story-brand span,.story-progress{display:none}.story-nav>a{font-size:0}.story-nav>a::after{content:'返回';font-size:12px}.story-brand strong{font-size:16px}.story-nav-actions{gap:3px}.story-nav-actions button{min-height:44px;font-size:11px}.story-nav-actions button:first-child{width:44px;min-height:44px}.story-nav-actions button:last-child{flex:1;white-space:nowrap}
  .story-stage{overflow:hidden}.scene-heading{top:14px;left:18px}.scene-heading h1{font-size:29px}.scene-objective{display:none}
  .speaker-portrait{bottom:142px;width:72vw;height:60vh}.speaker-portrait.is-left{left:-8vw}.speaker-portrait.is-right{right:-8vw}.speaker-portrait__sigil{width:150px;height:150px}
  .workbench,.interaction-01,.interaction-02,.interaction-03,.interaction-04,.interaction-05,.interaction-07,.interaction-08{top:42%;width:calc(100% - 24px);max-height:40vh;padding:10px}.clue-grid,.choice-list.final,.rule-board{grid-template-columns:1fr}.samples{grid-template-columns:1fr 1fr}.rule-card{grid-template-columns:86px 1fr}.archive-row{grid-template-columns:1fr}.keep-version{grid-template-columns:1fr 1fr}.keep-version span{grid-column:1/-1}
  .game-head strong{font-size:14px}.compare-row{grid-template-columns:64px 1fr 1fr}.compare-row>div{grid-column:1/-1}.relay-slots{grid-template-columns:1fr 1fr}.relay-slots button:nth-child(2)::after{display:none}.relay-pool{grid-template-columns:1fr}.layout-game{grid-template-columns:1fr}.layout-game .game-head,.layout-game .game-resolution{grid-column:auto}.layout-preview{min-height:180px}.relation-row{grid-template-columns:1fr}.relation-verdict{grid-template-columns:1fr}.relation-verdict>span{grid-column:auto}.overlap-board{height:165px}.overlap-board .paper{width:210px;height:125px}
  .dialogue-panel{left:12px;right:12px;bottom:calc(34px + env(safe-area-inset-bottom));min-height:132px;padding:34px 24px 25px}.dialogue-name{left:18px;top:-16px;min-width:110px;padding:7px 14px;font-size:16px}.dialogue-role{left:145px;top:9px}.dialogue-text{font-size:15px;line-height:1.72}.dialogue-cue{right:20px;bottom:13px}.story-feedback{bottom:176px;max-width:92vw}
  .evidence-graph>span{position:static;transform:none;margin:3px}.evidence-graph{display:flex;flex-wrap:wrap;justify-content:center;align-content:center}.graph-core{width:112px;height:112px}.story-footnote span:last-child{display:none}
  .workbench{height:40vh;overflow:hidden}.game-head strong{max-width:250px;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.game-head em{min-width:46px;padding:5px}
  .case-tabs{gap:3px;min-height:44px}.case-tabs button{grid-template-columns:18px 1fr 10px;gap:3px;min-height:44px;padding:4px}.case-tabs span{font-size:10px}
  .compare-stage{grid-template-columns:minmax(0,1fr) 54px minmax(0,1fr);gap:5px}.sample-card{padding:8px}.sample-card strong{font-size:11px}.comparison-lens small{display:none}.comparison-lens b{font-size:18px}.verdict-deck button,.relation-options button{gap:3px}.verdict-deck i,.relation-options i{font-size:14px}
  .relay-slots{grid-template-columns:repeat(4,1fr);gap:3px}.relay-slots button{min-width:0;padding:4px}.relay-slots strong{font-size:9px}.relay-slots small{display:none}.relay-slots button:nth-child(2)::after{display:block}.relay-pool{grid-template-columns:repeat(2,1fr);gap:3px}.relay-pool button{grid-template-columns:20px 1fr;gap:4px;padding:3px}.relay-pool i{width:19px;height:19px}.relay-pool strong{font-size:9px}.relay-pool small{display:none}
  .layout-game{grid-template-columns:1fr 1fr;grid-template-rows:auto 44px minmax(120px,1fr) auto}.layout-game .game-head,.layout-game .layout-tabs,.layout-game .game-resolution,.layout-game>.game-confirm{grid-column:1/-1}.layout-preview{min-height:0}.layout-frame{top:18px;width:58px;height:94px;padding:7px}.frame-a{left:7px}.frame-b{right:7px}.layout-frame i{height:5px;margin:7px 0}.layout-console{padding:7px}.layout-console>strong{font-size:13px}.layout-console>div{grid-template-columns:1fr;gap:4px}.layout-console button{min-height:44px;font-size:9px}.layout-console small{display:none}
  .relation-stage{grid-template-columns:minmax(0,1fr) 48px minmax(0,1.15fr);gap:4px}.relation-node{padding:7px}.relation-node strong{font-size:11px}.relation-wire{grid-template-columns:1fr}.relation-wire i{display:none}.relation-wire b{text-align:center}.relation-options button{font-size:9px}.relation-verdict button{min-height:44px;padding:6px;font-size:9px}
  .overlap-board{height:auto}.overlap-board .paper{top:12px;width:180px;height:108px;padding:10px}.overlap-board .paper i{height:4px;margin-top:9px}.overlap-game{grid-template-rows:auto minmax(98px,1fr) 28px 44px auto}
  .rule-game{grid-template-rows:auto 88px minmax(92px,1fr) 44px}.rule-tabs{grid-template-columns:repeat(3,1fr)}.rule-tabs button{min-height:42px}.rule-stage{grid-template-columns:100px 1fr;gap:4px}.rule-stage>div:first-child{padding:7px}.rule-stage>div:first-child strong{font-size:14px}.rule-stage>div:first-child small{display:none}.rule-options{gap:3px}.rule-options button{min-height:70px;padding:5px}.rule-options strong{font-size:10px}.rule-options small{display:none}
  .people-game{grid-template-rows:auto 44px minmax(72px,1fr) 44px 44px}.people-stage{grid-template-columns:1fr 42px 1.2fr;gap:3px}.people-stage>div{padding:6px}.people-stage strong{font-size:10px}.people-options{gap:3px}.people-options button{gap:3px;font-size:9px}.people-options i{width:20px;height:20px}.boundary-seal{display:grid;grid-template-columns:repeat(3,auto);gap:3px 6px;padding:5px;font-size:8px}.boundary-seal i{display:none}.knowledge-response .choice-list{grid-template-columns:1fr;gap:4px}.knowledge-response .choice-list button{min-height:48px;padding:6px 8px}.knowledge-response .choice-list strong{font-size:11px}.knowledge-response .choice-list small{font-size:8px}
  .archive-editor{grid-template-rows:auto 44px minmax(0,1fr)}.archive-tabs{grid-template-columns:repeat(4,1fr)}.archive-tabs span{display:none}.archive-card{grid-template-columns:1fr;padding:10px}.archive-card p{font-size:12px;line-height:1.4}.archive-row>div{grid-template-columns:repeat(3,1fr)}.archive-row button,.keep-version button{min-height:44px;font-size:10px}.archive-editor blockquote{font-size:10px;line-height:1.45}.keep-version{grid-template-columns:1fr 1fr}.keep-version button{padding:7px}.rule-board{grid-template-columns:1fr 1fr;gap:4px}.rule-card{grid-template-columns:1fr;gap:4px;padding:5px}.rule-card>strong{font-size:11px}.rule-card>div{gap:3px}.rule-card button{min-height:44px;padding:4px 2px;font-size:9px}.rule-board>p{font-size:10px;grid-column:1/-1}
  .final-deduction{grid-template-rows:auto 44px auto minmax(76px,1fr) 44px}.deduction-question{grid-template-columns:72px 1fr;gap:6px;padding:6px 8px}.deduction-question strong{font-size:11px;line-height:1.35}.deduction-options{gap:4px}.deduction-options button{min-height:76px;padding:6px}.deduction-options strong{font-size:10px}.deduction-options small{font-size:8px;line-height:1.25}.final-deduction>.game-confirm{min-height:44px}.deduction-seal{grid-template-columns:repeat(3,auto);gap:3px 6px;font-size:8px}.choice-list.final{grid-template-columns:1fr;gap:4px}.choice-list.final button{min-height:54px;padding:6px 8px;grid-template-columns:26px 1fr;gap:2px 6px}.choice-list.final span{width:22px;height:22px}.choice-list.final strong{font-size:11px}.choice-list.final small{display:block;font-size:8px;line-height:1.3}.decision-consequences{gap:4px}.decision-consequences .choice-list.final{grid-template-columns:1fr}.decision-consequences .choice-list.final button{min-height:48px;padding:5px 8px}.consequence-board{padding:12px}.consequence-board header strong{font-size:15px}.consequence-meters{gap:6px;margin:12px 0}.consequence-meters label{grid-template-columns:28px 1fr 18px;gap:4px}.consequence-board p{font-size:11px}
  .transition-title::before,.transition-title::after{width:32px;margin-inline:8px}.transition-sheet i{width:76vw;height:76vw}.transition-sheet b{width:44vw;height:44vw}
}
@media(prefers-reduced-motion:reduce){
  .story-backdrop,.story-backdrop__main,.story-backdrop__rain,.scene-heading,.scene-heading p::before,.scene-objective,.dialogue-cue i,.speaker-portrait__sigil::before,.speaker-portrait__sigil::after{animation:none!important}
  .phase-cover .transition-sheet--left,.phase-cover .transition-sheet--right,.phase-reveal .transition-sheet--left,.phase-reveal .transition-sheet--right{animation:none;transform:translate3d(0,0,0)}
  .phase-cover .transition-title,.phase-reveal .transition-title{animation:none}.phase-reveal.scene-transition{opacity:0;transition:opacity .12s linear}
}

/* V7.1 统一商业化外壳：十二幕脊线、全局阅读模式、拓印式阶段小结。 */
.story-nav{grid-template-columns:126px minmax(190px,.8fr) minmax(390px,1.7fr) 286px;gap:16px;padding:0 22px;background:linear-gradient(90deg,#0a1917,#112622);box-shadow:0 10px 30px rgba(0,0,0,.22)}
.story-brand{flex-direction:column;align-items:flex-start;gap:1px}.story-brand strong{font-size:17px}.story-brand span{font-size:8px}
.story-progress{display:grid;grid-template-columns:108px minmax(180px,1fr) 32px;align-items:center;gap:11px}.story-progress>div{display:flex;flex-direction:column;min-width:0}.story-progress>div span{font-size:8px;color:#d9bb73}.story-progress>div em{overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-family:var(--font-display);font-size:11px;font-style:normal;letter-spacing:.04em;color:rgba(255,248,230,.72)}.story-progress ol{display:grid;grid-template-columns:repeat(12,1fr);gap:3px;list-style:none;margin:0;padding:0}.story-progress li{height:5px;background:rgba(255,255,255,.09);transform:skewX(-14deg);transition:background-color .25s ease,transform .25s ease}.story-progress li.is-done{background:linear-gradient(90deg,#4d98a9,#9ab7a6)}.story-progress li.is-current{background:#efd083;transform:skewX(-14deg) scaleY(1.65);box-shadow:0 0 12px rgba(217,187,115,.42)}.story-progress>b{display:block;height:auto;background:none;font-size:9px;font-weight:500;color:rgba(255,244,215,.54)}
.story-nav-actions{display:grid;grid-template-columns:58px 68px 1fr;gap:6px}.story-nav-actions button,.story-nav-actions button:first-child{width:auto;min-height:39px;padding:0 8px;border:1px solid rgba(221,191,123,.2);border-radius:0;background:rgba(255,255,255,.02);font-size:9px;letter-spacing:.06em;color:rgba(238,226,200,.58)}.story-nav-actions button:hover,.story-nav-actions button[aria-pressed='true']{border-color:rgba(221,191,123,.62);color:#f4d68d}.story-nav-actions button:last-child{color:#e5c77f}.story-nav-actions button:last-child b{display:inline-grid;place-items:center;min-width:20px;height:20px;margin-left:5px;border-radius:50%;background:#4d98a9;color:#fff;font-size:8px}
.workbench::before{content:'RUBBING DESK / 云台校勘台';position:absolute;z-index:2;right:17px;top:8px;font-size:7px;letter-spacing:.15em;color:rgba(217,187,115,.34);pointer-events:none}.speaker-portrait.is-working{opacity:.17;filter:blur(1px) grayscale(.45)}
.dialogue-cue{display:flex;align-items:center;gap:7px}.dialogue-cue kbd{padding:2px 5px;border:1px solid rgba(255,255,255,.16);border-radius:2px;background:rgba(255,255,255,.04);font:7px/1 var(--font-ui);color:rgba(255,255,255,.5)}.is-large-text .dialogue-text{font-size:clamp(20px,1.75vw,24px);line-height:1.82}.is-large-text .dialogue-panel{min-height:155px}.is-large-text .workbench{font-size:1.05em}
.yuan-interlude{position:fixed;z-index:80;inset:0;display:grid;place-items:center;padding:24px;background:rgba(3,13,12,.89);backdrop-filter:blur(15px);animation:yuan-interlude-in .35s ease both}.yuan-interlude::before{content:'';position:absolute;inset:12%;border-block:1px solid rgba(217,187,115,.28);pointer-events:none}.yuan-interlude section{position:relative;width:min(700px,92vw);padding:49px 58px 42px;border:1px solid rgba(217,187,115,.68);background:linear-gradient(145deg,#172925,#0d1b19);box-shadow:0 35px 120px rgba(0,0,0,.7),inset 0 0 0 7px rgba(255,255,255,.025);text-align:center}.yuan-interlude section::before{content:'拓';position:absolute;right:24px;top:21px;width:40px;height:40px;display:grid;place-items:center;border:1px solid rgba(77,152,169,.44);font-family:var(--font-display);font-size:21px;color:rgba(123,189,198,.62);transform:rotate(3deg)}.yuan-interlude section>span{font-size:9px;font-weight:650;letter-spacing:.18em;color:#82bdc6}.yuan-interlude h2{margin-top:13px;font-family:var(--font-display);font-size:35px;font-weight:500;color:#f2e6ca}.yuan-interlude p{max-width:555px;margin:17px auto 0;font-family:var(--font-display);font-size:15px;line-height:1.82;color:rgba(238,230,213,.72)}.yuan-interlude__ledger{display:flex;justify-content:center;align-items:center;gap:10px;margin-top:21px}.yuan-interlude__ledger b{font-family:var(--font-display);font-size:30px;font-weight:500;color:#d9bb73}.yuan-interlude__ledger small{max-width:150px;text-align:left;font-size:9px;line-height:1.45;color:rgba(238,230,213,.45)}.yuan-interlude button{min-width:300px;min-height:48px;margin-top:23px;padding:0 18px;border:1px solid rgba(217,187,115,.62);background:linear-gradient(90deg,#305e5c,#397067);color:#fff4dc;font-family:var(--font-display);font-size:13px}.yuan-interlude button:hover{border-color:#efd083;background:linear-gradient(90deg,#39706c,#477d70)}.yuan-interlude button i{margin-left:13px;font-style:normal;color:#efd083}@keyframes yuan-interlude-in{from{opacity:0}to{opacity:1}}
.yuan-interlude section>aside{max-width:565px;margin:15px auto 0;padding:10px 13px;border:1px solid rgba(123,189,198,.16);background:rgba(123,189,198,.055);text-align:left}.yuan-interlude section>aside span{font-size:8px;letter-spacing:.16em;color:#82bdc6}.yuan-interlude section>aside p{margin-top:5px;font-family:var(--font-ui);font-size:10px;line-height:1.65;color:rgba(238,230,213,.64)}
@media(max-width:1100px){.story-nav{grid-template-columns:108px 160px minmax(300px,1fr) 242px;gap:9px;padding:0 14px}.story-progress{grid-template-columns:88px 1fr 28px}.story-nav-actions{grid-template-columns:52px 62px 1fr}}
@media(max-width:900px){.story-nav{grid-template-columns:64px 1fr auto}.story-brand{display:none}.story-progress{display:grid;grid-template-columns:70px minmax(120px,1fr)}.story-progress>b{display:none}.story-nav-actions{grid-template-columns:40px 40px 48px;gap:3px}.story-nav-actions button,.story-nav-actions button:first-child{min-height:40px;padding:0 3px;font-size:8px}.story-nav-actions button:nth-child(2){font-size:0}.story-nav-actions button:nth-child(2)::before{content:'音';font-size:9px}.story-nav-actions button:last-child{font-size:0}.story-nav-actions button:last-child::before{content:'证据';font-size:8px}.story-nav-actions button:last-child b{display:none}.dialogue-cue kbd{display:none}}
@media(max-width:520px){.story-progress{grid-template-columns:55px minmax(90px,1fr);gap:5px}.story-progress>div em{display:none}.story-progress ol{gap:2px}.yuan-interlude{padding:14px}.yuan-interlude section{padding:40px 23px 31px}.yuan-interlude section::before{right:14px;top:13px;width:32px;height:32px;font-size:17px}.yuan-interlude h2{font-size:27px}.yuan-interlude p{font-size:14px}.yuan-interlude button{width:100%;min-width:0;font-size:12px}}
</style>
