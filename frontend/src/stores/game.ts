import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { GAME_CATALOG, type GameAction, type MethodKey } from '@/game/catalog'
import type { ChapterSlug } from '@/types'

const STORAGE_KEY = 'tongxin.game.v2'

export interface ChapterGameState {
  started: boolean
  completed: boolean
  actions: Partial<Record<GameAction, boolean>>
  evidenceIds: string[]
  decisionId: string | null
  methods: Record<MethodKey, number>
  updatedAt: string | null
}

function emptyState(): ChapterGameState {
  return {
    started: false,
    completed: false,
    actions: {},
    evidenceIds: [],
    decisionId: null,
    methods: { truth: 0, empathy: 0, connection: 0 },
    updatedAt: null,
  }
}

export const useGameStore = defineStore('game', () => {
  const chapters = ref<Partial<Record<ChapterSlug, ChapterGameState>>>({})
  const hydrated = ref(false)

  function bootstrap() {
    if (hydrated.value) return
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) chapters.value = JSON.parse(raw)
    } catch {
      chapters.value = {}
    }
    hydrated.value = true
  }

  function stateFor(slug: ChapterSlug): ChapterGameState {
    if (!chapters.value[slug]) chapters.value[slug] = emptyState()
    return chapters.value[slug]!
  }

  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chapters.value))
    } catch {
      // 存档失败不阻断游玩。
    }
  }

  function mark(slug: ChapterSlug, action: GameAction, evidenceId?: string) {
    const state = stateFor(slug)
    state.started = true
    state.actions[action] = true
    if (action === 'INSPECT' && evidenceId && !state.evidenceIds.includes(evidenceId)) {
      state.evidenceIds.push(evidenceId)
    }
    if (action === 'COMPLETE') state.completed = true
    state.updatedAt = new Date().toISOString()
    save()
  }

  function choose(slug: ChapterSlug, decisionId: string) {
    const state = stateFor(slug)
    if (state.decisionId) return
    const choice = GAME_CATALOG[slug].decision.choices.find((item) => item.id === decisionId)
    if (!choice) return
    state.decisionId = choice.id
    state.actions.DECISION = true
    for (const key of Object.keys(choice.impact) as MethodKey[]) {
      state.methods[key] += choice.impact[key] ?? 0
    }
    state.updatedAt = new Date().toISOString()
    save()
  }

  function progressFor(slug: ChapterSlug) {
    const state = stateFor(slug)
    const meta = GAME_CATALOG[slug]
    const earned = meta.objectives.filter((objective) => {
      if (objective.action === 'INSPECT') {
        return state.evidenceIds.length >= (objective.target ?? 1)
      }
      return !!state.actions[objective.action]
    }).length
    return Math.round((earned / meta.objectives.length) * 100)
  }

  function objectiveDone(slug: ChapterSlug, action: GameAction, target = 1) {
    const state = stateFor(slug)
    if (action === 'INSPECT') return state.evidenceIds.length >= target
    return !!state.actions[action]
  }

  function resetChapter(slug: ChapterSlug) {
    chapters.value[slug] = emptyState()
    save()
  }

  const completedCount = computed(
    () => Object.values(chapters.value).filter((state) => state?.completed).length,
  )

  return {
    chapters,
    hydrated,
    completedCount,
    bootstrap,
    stateFor,
    mark,
    choose,
    progressFor,
    objectiveDone,
    resetChapter,
  }
})
