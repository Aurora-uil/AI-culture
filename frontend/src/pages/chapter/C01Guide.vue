<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GAME_CATALOG } from '@/game/catalog'
import { useChapterStore, SLUG_TO_ID } from '@/stores/chapter'
import { useExplorationStore } from '@/stores/exploration'
import { useGameStore } from '@/stores/game'
import { getNarration } from '@/api/endpoints'
import type { ChapterSlug } from '@/types'

const route = useRoute()
const router = useRouter()
const chapterStore = useChapterStore()
const exploration = useExplorationStore()
const game = useGameStore()

const slug = computed(() => route.params.slug as ChapterSlug)
const chapter = computed(() => chapterStore.current)
const meta = computed(() => GAME_CATALOG[slug.value])
const CHAPTER_ART: Record<ChapterSlug, { src: string; label: string; fit?: 'cover' | 'contain'; position?: string }> = {
  han: { src: '/assets/han/han-route-scene-v2.png', label: 'AI历史环境重构 · 非史实照片', position: '58% center' },
  'northern-wei': { src: '/assets/wei/yungang-cave20-original.jpg', label: '云冈石窟历史原图' },
  tang: { src: '/assets/tang/bunian-original.jpg', label: '《步辇图》历史原图', position: '64% center' },
  yuan: { src: '/assets/yuan/yuntai-east-wall-original.jpg', label: '居庸关云台历史原图', position: '52% center' },
  qing: { src: '/assets/qing/qing-migration-photoreal-v2.png', label: 'AI历史环境重构 · 非史实照片', position: '47% center' },
  contemporary: { src: '/assets/contemporary/qiang-workshop-photoreal-v2.png', label: 'AI当代工坊情境重构 · 非纪实照片', position: '48% center' },
}
const art = computed(() => CHAPTER_ART[slug.value])
const CHAPTER_STAKES: Record<ChapterSlug, string> = {
  han: '展签把一件汉晋织锦直接写成张骞带回的遗物，但年代与现有证据并不支持这层关系。',
  'northern-wei': '策展人想用元羽墓志概括整个北魏，但一方墓志只能支持一个有限的个案。',
  tang: '画中人物已经入席，真正影响事件的人却没有出现在画卷里。',
  yuan: '一张位置标记脱落的拓片等待归位，字形与版面给出了不同答案。',
  qing: '《万法归一图屏》进入主展柜，但它无法独自承载迁徙者、路线与人数记录的全部声音。',
  contemporary: '一件具体羌绣作品只取得展示授权，你必须决定它能否进入生成流程。',
}
const stake = computed(() => CHAPTER_STAKES[slug.value])
const narration = ref('')
const narrationOpen = ref(false)
const yuanStoryScene = ref<number | null>(null)
const yuanStoryHasSave = ref(false)
const STORY_VISIT_STORAGE_KEY = 'tongxin.chapter.story.visits.v1'
const storyVisits = ref<Partial<Record<ChapterSlug, boolean>>>({})

type ChapterModuleKind = 'explore' | 'ai' | 'story'

interface ChapterModuleCopy {
  id: ChapterModuleKind
  title: string
  description: string
  experience: string
}

const CHAPTER_MODULE_COPY: Record<ChapterSlug, ChapterModuleCopy[]> = {
  han: [
    { id: 'explore', title: '路线与文物探查', description: '查看道路节点、文物线索与路线证据，开启路线证据透镜。', experience: '路线节点 · 文物查验' },
    { id: 'ai', title: 'AI 助手问答', description: '围绕张骞、交通路线与锦护膊的证据关系自由提问。', experience: '自由提问 · 回答来源' },
    { id: 'story', title: '展签校勘剧情', description: '进入现有完整任务，核对年代、路线与出土信息并完成展签抉择。', experience: '证据搜集 · 展签校勘' },
  ],
  'northern-wei': [
    { id: 'explore', title: '双城证据探查', description: '对照云冈、龙门与墓志材料，查看不同证据可以支持到哪里。', experience: '双城对照 · 证据查验' },
    { id: 'ai', title: 'AI 助手问答', description: '围绕迁都、改革、墓志与石窟证据自由提问并查看来源。', experience: '自由提问 · 回答来源' },
    { id: 'story', title: '墓志展陈剧情', description: '进入现有完整任务，以元羽墓志为主证物完成展签与展陈抉择。', experience: '物证比较 · 展陈抉择' },
  ],
  tang: [
    { id: 'explore', title: '画卷人物探查', description: '展开《步辇图》，查看画内人物、画外事件与图像证据边界。', experience: '画卷热点 · 画外关系' },
    { id: 'ai', title: 'AI 助手问答', description: '围绕《步辇图》、禄东赞与文成公主相关史实自由提问。', experience: '自由提问 · 回答来源' },
    { id: 'story', title: '画外来使剧情', description: '进入现有完整任务，校对会见名册并完成画内—画外展签抉择。', experience: '人物搜证 · 展签校对' },
  ],
  yuan: [
    { id: 'explore', title: '六体文字探查', description: '查看文字热点、开启六体文字透镜，并核对实体与来源信息。', experience: '6 类文字热点 · 透镜查验' },
    { id: 'ai', title: 'AI 助手问答', description: '围绕云台、题刻、文字与人群关系自由提问，查看回答依据。', experience: '自由提问 · 回答来源' },
    { id: 'story', title: '12 幕证据剧情', description: '进入双校样证据剧场，完成版本校勘、规则分层与档案校验。', experience: '12 幕剧情 · 证据校勘' },
  ],
  qing: [
    { id: 'explore', title: '东归路线探查', description: '沿时间与迁徙路线查验节点，比较不同来源的精度和叙述范围。', experience: '路线节点 · 时间追索' },
    { id: 'ai', title: 'AI 助手问答', description: '围绕土尔扈特东归、路线、人数与安置记录自由提问。', experience: '自由提问 · 回答来源' },
    { id: 'story', title: '多声部东归剧情', description: '进入现有完整任务，把图屏、路线和文本放入同一展柜完成抉择。', experience: '迁徙追索 · 展柜策划' },
  ],
  contemporary: [
    { id: 'explore', title: '羌绣知识探查', description: '查看针法、纹样、用途和权利记录，开启来源与权利透镜。', experience: '工坊卡片 · 权利查验' },
    { id: 'ai', title: 'AI 助手问答', description: '围绕羌绣技艺、生活用途、传承实践与授权边界自由提问。', experience: '自由提问 · 回答来源' },
    { id: 'story', title: '授权共创剧情', description: '进入现有完整任务，为具体作品建档并完成授权与生成抉择。', experience: '作品建档 · 授权共创' },
  ],
}

const chapterModules = computed(() => {
  const currentSlug = slug.value
  const state = game.stateFor(currentSlug)
  const explorationStatus = state.evidenceIds.length >= 3
    ? '已查验'
    : state.evidenceIds.length > 0 || state.actions.LENS
      ? '进行中'
      : '未开始'
  const storyStatus = currentSlug === 'yuan'
    ? state.completed
      ? '已完成'
      : yuanStoryHasSave.value && yuanStoryScene.value !== null
        ? `第 ${yuanStoryScene.value + 1} 幕`
        : '未开始'
    : state.completed
      ? '已完成'
      : state.decisionId
        ? '待总结'
        : storyVisits.value[currentSlug]
          ? '进行中'
          : '未开始'

  return CHAPTER_MODULE_COPY[currentSlug].map((module, index) => ({
    ...module,
    index: String(index + 1).padStart(2, '0'),
    status: module.id === 'explore'
      ? explorationStatus
      : module.id === 'ai'
        ? state.actions.CHAT ? '已访问' : '未开始'
        : storyStatus,
    path: module.id === 'ai'
      ? `/chapter/${currentSlug}/chat`
      : module.id === 'story' && currentSlug === 'yuan'
        ? '/chapter/yuan/story'
        : {
            path: `/chapter/${currentSlug}/scene`,
            query: { module: module.id },
          },
  }))
})

onMounted(async () => {
  game.bootstrap()
  try {
    storyVisits.value = JSON.parse(localStorage.getItem(STORY_VISIT_STORAGE_KEY) ?? '{}')
  } catch {
    storyVisits.value = {}
  }
  if (slug.value === 'yuan') {
    try {
      const raw = localStorage.getItem('tongxin.yuan.story.v6')
      if (raw) {
        const saved = JSON.parse(raw) as { sceneIndex?: number }
        yuanStoryHasSave.value = true
        yuanStoryScene.value = Math.min(Math.max(saved.sceneIndex ?? 0, 0), 11)
      }
    } catch {
      yuanStoryHasSave.value = false
      yuanStoryScene.value = null
    }
  }
  const id = SLUG_TO_ID[slug.value]
  if (!id) return
  if (chapterStore.current?.id !== id) await chapterStore.loadChapter(id)
  await exploration.ensureSession(id)

  try { narration.value = (await getNarration(id)).narration }
  catch { narration.value = chapterStore.current?.narration ?? '' }
})

function openModule(path: string | { path: string; query: { module: ChapterModuleKind } }) {
  void router.push(path)
}

function goChat() {
  game.mark(slug.value, 'CHAT')
  void router.push(`/chapter/${slug.value}/chat`)
}

function goGraph() {
  game.mark(slug.value, 'GRAPH')
  void router.push(`/chapter/${slug.value}/graph`)
}
</script>

<template>
  <div v-if="chapter" class="briefing" :style="{ '--era-accent': chapter.accent }">
    <div class="briefing__grain" aria-hidden="true" />
    <header class="briefing__nav">
      <RouterLink to="/timeline">← 返回千年行卷</RouterLink>
      <span>{{ chapter.era }} · {{ chapter.date_label }}</span>
      <RouterLink to="/about">史料边界</RouterLink>
    </header>

    <main class="briefing__main">
      <section class="briefing__stage" aria-label="章节身份">
        <figure class="briefing__art" aria-hidden="true">
          <img
            :src="art.src"
            alt=""
            :style="{ objectFit: art.fit || 'cover', objectPosition: art.position || 'center' }"
          />
          <figcaption>{{ art.label }}</figcaption>
        </figure>
        <div class="briefing__halo" aria-hidden="true" />
        <span class="briefing__index">第 {{ String(chapter.sort_order).padStart(2, '0') }} 章</span>
        <p class="briefing__keyword">{{ chapter.keyword }}</p>
        <div class="briefing__identity">
          <span>这一次，你将成为</span>
          <strong>{{ meta.role }}</strong>
          <small>{{ meta.roleNote }}</small>
        </div>
        <blockquote>“{{ meta.openingLine }}”</blockquote>
        <div class="briefing__artifact">
          <span>完成本章后带回</span>
          <strong>{{ meta.artifact }}</strong>
        </div>
      </section>

      <section class="briefing__content">
        <div class="briefing__role-sigil" aria-hidden="true">
          <span>{{ chapter.keyword }}</span>
          <small>{{ meta.role }}</small>
        </div>
        <p class="briefing__eyebrow">{{ chapter.era }} · {{ chapter.keyword }} · {{ meta.mechanic }}</p>
        <h1>{{ meta.gameTitle }}</h1>
        <p class="briefing__source-title">历史核心：{{ chapter.title }}</p>

        <div class="briefing__anchor" :class="`is-${meta.storyAnchor.status}`">
          <div>
            <span>剧情锚点 · {{ meta.storyAnchor.kind }}</span>
            <strong>{{ meta.storyAnchor.name }}</strong>
          </div>
          <em>{{ meta.storyAnchor.statusLabel }}</em>
          <p>{{ meta.storyAnchor.boundary }}</p>
        </div>

        <div class="briefing__situation">
          <span>当前困境</span>
          <strong>{{ stake }}</strong>
        </div>

        <div class="briefing__mission">
          <span>你的任务</span>
          <p>{{ meta.mission }}</p>
        </div>

        <div class="briefing__question">
          <span>本章之问</span>
          <p>{{ chapter.guiding_question }}</p>
        </div>

        <div class="briefing__objectives">
          <span>进入场景后</span>
          <ol>
            <li v-for="(objective, index) in meta.objectives.slice(0, 3)" :key="objective.action">
              <b>{{ index + 1 }}</b><em>{{ objective.label }}</em>
            </li>
          </ol>
        </div>

        <div class="briefing__facts">
          <div>
            <span>核心玩法</span>
            <strong>{{ meta.mechanic }}</strong>
          </div>
          <div>
            <span>预计时间</span>
            <strong>{{ meta.duration }}</strong>
          </div>
          <div>
            <span>锚点状态</span>
            <strong>{{ meta.storyAnchor.statusLabel }}</strong>
          </div>
        </div>

        <div class="briefing__modules" :aria-label="`${chapter.era}章节板块`">
          <button
            v-for="module in chapterModules"
            :key="module.id"
            class="briefing__module"
            type="button"
            @click="openModule(module.path)"
          >
            <span class="briefing__module-head">
              <i>{{ module.index }}</i>
              <em class="briefing__module-progress">当前进度 · {{ module.status }}</em>
            </span>
            <strong>{{ module.title }}</strong>
            <p>{{ module.description }}</p>
            <span class="briefing__module-experience">预计体验 · {{ module.experience }}</span>
            <span class="briefing__module-enter">进入板块 <b aria-hidden="true">→</b></span>
          </button>
        </div>

        <button
          class="briefing__narration-toggle"
          type="button"
          @click="narrationOpen = !narrationOpen"
        >
          {{ narrationOpen ? '收起固定讲述' : '先听一段固定讲述' }}
        </button>

        <Transition name="reveal">
          <div v-if="narrationOpen" class="briefing__narration">
            <p>{{ narration || '这段固定讲述需要连接内容服务后显示。' }}</p>
            <small>固定审核文本，不由大模型临场编写。</small>
          </div>
        </Transition>

        <footer class="briefing__footer">
          <div class="briefing__layers" aria-label="内容证据层级">
            <span><i class="attested" />史料确证</span>
            <span><i class="interpreted" />研究解释</span>
            <span><i class="reconstructed" />情境重构</span>
            <span><i class="dramatized" />游戏创作</span>
          </div>
          <div>
            <button type="button" @click="goChat">向角色追问</button>
            <button type="button" @click="goGraph">查看关系底图</button>
          </div>
        </footer>
      </section>
    </main>
  </div>
</template>

<style scoped>
.briefing { position: relative; min-height: 100vh; overflow: hidden; color: #eee5d2; background: #0c1413; }
.briefing__grain { position: absolute; inset: 0; pointer-events: none; opacity: .2; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 160 160' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.76' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.17'/%3E%3C/svg%3E"); mix-blend-mode: soft-light; }
.briefing__nav { position: relative; z-index: 2; height: 64px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 0 clamp(20px,4vw,64px); border-bottom: 1px solid rgba(225,207,170,.12); font-size: 11px; letter-spacing: .12em; color: rgba(238,229,210,.45); }
.briefing__nav a:last-child { justify-self: end; }
.briefing__nav a:hover { color: #dfc981; }
.briefing__main { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(420px, 48%) 1fr; min-height: calc(100vh - 64px); }
.briefing__stage { position: relative; min-height: 650px; overflow: hidden; display: flex; flex-direction: column; padding: clamp(38px,6vw,82px); border-right: 1px solid rgba(225,207,170,.12); background: radial-gradient(circle at 50% 36%, color-mix(in srgb, var(--era-accent) 20%, transparent), transparent 42%), linear-gradient(145deg, rgba(255,255,255,.025), transparent); }
.briefing__art{position:absolute;inset:0;margin:0;overflow:hidden;opacity:.36;mask-image:linear-gradient(180deg,#000 0,#000 48%,transparent 88%)}
.briefing__art::after{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(230,240,230,.03),rgba(28,70,68,.28))}
.briefing__art img{width:100%;height:68%;display:block;filter:saturate(.72) contrast(.95)}
.briefing__art figcaption{position:absolute;z-index:1;right:18px;top:18px;padding:5px 9px;border:1px solid rgba(255,255,255,.34);border-radius:999px;background:rgba(246,249,242,.76);backdrop-filter:blur(8px);font-size:9px;letter-spacing:.1em;color:rgba(41,69,74,.72)}
.briefing__stage::before, .briefing__stage::after { content: ''; position: absolute; width: 320px; height: 320px; border: 1px solid color-mix(in srgb, var(--era-accent) 32%, transparent); transform: rotate(45deg); }
.briefing__stage::before { top: -190px; left: -170px; }
.briefing__stage::after { right: -210px; bottom: -220px; }
.briefing__halo { position: absolute; width: 42vw; height: 42vw; max-width: 620px; max-height: 620px; left: 50%; top: 43%; transform: translate(-50%,-50%); border-radius: 50%; border: 1px solid color-mix(in srgb, var(--era-accent) 23%, transparent); box-shadow: 0 0 90px color-mix(in srgb, var(--era-accent) 10%, transparent); }
.briefing__halo::before, .briefing__halo::after { content: ''; position: absolute; border-radius: 50%; inset: 12%; border: 1px solid color-mix(in srgb, var(--era-accent) 15%, transparent); }
.briefing__halo::after { inset: 28%; }
.briefing__index { position: relative; font-size: 10px; letter-spacing: .28em; color: color-mix(in srgb, var(--era-accent) 74%, #dfc981); }
.briefing__keyword { position: relative; margin: auto 0 8px; font-family: var(--font-display); font-size: clamp(92px,14vw,210px); line-height: .85; color: color-mix(in srgb, var(--era-accent) 58%, #e9d8b1); opacity: .2; letter-spacing: -.08em; }
.briefing__identity { position: relative; display: flex; flex-direction: column; align-items: flex-start; gap: 5px; max-width: 520px; }
.briefing__identity span, .briefing__artifact span { font-size: 10px; letter-spacing: .2em; color: rgba(238,229,210,.4); }
.briefing__identity strong { font-family: var(--font-display); font-size: clamp(25px,3vw,40px); font-weight: 500; color: #f0e6d2; }
.briefing__identity small { max-width: 460px; color: rgba(238,229,210,.36); line-height: 1.6; }
.briefing blockquote { position: relative; margin: 28px 0 0; padding-left: 16px; border-left: 1px solid color-mix(in srgb, var(--era-accent) 62%, #dfc981); font-family: var(--font-display); color: rgba(238,229,210,.62); }
.briefing__artifact { position: relative; display: flex; align-items: baseline; gap: 12px; margin-top: auto; padding-top: 30px; }
.briefing__artifact strong { font-family: var(--font-display); font-weight: 500; color: #dfc981; }
.briefing__content { padding: clamp(42px,6vw,88px) clamp(28px,6vw,90px) 34px; display: flex; flex-direction: column; min-width: 0; }
.briefing__eyebrow { font-size: 10px; letter-spacing: .23em; color: color-mix(in srgb, var(--era-accent) 74%, #dfc981); }
.briefing h1 { margin-top: 10px; font-family: var(--font-display); font-size: clamp(42px,5.3vw,76px); line-height: 1.1; font-weight: 500; color: #f0e7d6; }
.briefing__source-title { margin-top: 6px; color: rgba(238,229,210,.38); font-size: 12px; }
.briefing__anchor{display:grid;grid-template-columns:1fr auto;gap:4px 14px;margin-top:14px;padding:11px 13px 10px;border:1px solid rgba(40,95,97,.16);border-left:3px solid var(--era-accent);background:rgba(255,255,255,.28)}
.briefing__anchor>div{min-width:0;display:flex;align-items:baseline;gap:9px}
.briefing__anchor span{flex:none;font-size:8px;letter-spacing:.14em;color:rgba(41,69,74,.48)}
.briefing__anchor strong{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:var(--font-display);font-size:14px;font-weight:500;color:var(--color-mineral-800)}
.briefing__anchor em{align-self:center;padding:3px 7px;border:1px solid rgba(78,132,100,.28);border-radius:999px;background:rgba(78,132,100,.07);font-size:8px;font-style:normal;letter-spacing:.08em;color:#50765b}
.briefing__anchor p{grid-column:1/-1;font-size:10px;line-height:1.55;color:rgba(41,69,74,.58)}
.briefing__anchor.is-rights{border-left-color:var(--color-scroll-red)}
.briefing__anchor.is-rights em{border-color:rgba(178,81,61,.28);background:rgba(178,81,61,.06);color:var(--color-scroll-red)}
.briefing__mission, .briefing__question { display: grid; grid-template-columns: 82px 1fr; gap: 20px; margin-top: 38px; padding: 16px 0; border-top: 1px solid rgba(225,207,170,.12); border-bottom: 1px solid rgba(225,207,170,.12); }
.briefing__question { margin-top: 0; border-top: 0; }
.briefing__mission span, .briefing__question span { font-size: 10px; letter-spacing: .16em; color: rgba(238,229,210,.4); }
.briefing__mission p, .briefing__question p { font-family: var(--font-display); font-size: 16px; line-height: 1.75; color: rgba(238,229,210,.75); }
.briefing__facts { display: grid; grid-template-columns: repeat(3,1fr); gap: 1px; margin-top: 22px; background: rgba(225,207,170,.1); border: 1px solid rgba(225,207,170,.1); }
.briefing__facts div { min-width: 0; padding: 12px; background: #0c1413; display: flex; flex-direction: column; gap: 5px; }
.briefing__facts span { font-size: 9px; letter-spacing: .13em; color: rgba(238,229,210,.36); }
.briefing__facts strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: var(--font-display); font-size: 13px; font-weight: 500; color: rgba(238,229,210,.7); }
.briefing__actions { display: flex; gap: 10px; margin-top: 28px; }
.briefing__actions button { height: 50px; padding: 0 18px; border: 1px solid rgba(225,207,170,.18); border-radius: 0; background: transparent; color: rgba(238,229,210,.58); font-size: 12px; }
.briefing__actions button:hover { border-color: #dfc981; color: #f0e7d6; }
.briefing__start { flex: 1; display: flex; justify-content: space-between; align-items: center; background: color-mix(in srgb, var(--era-accent) 19%, transparent) !important; border-color: color-mix(in srgb, var(--era-accent) 70%, #dfc981) !important; font-family: var(--font-display); font-size: 15px !important; color: #f0e7d6 !important; }
.briefing__start i { font-style: normal; color: #dfc981; }
.briefing__modules{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:16px}
.briefing__module{min-width:0;min-height:158px;padding:13px;display:flex;flex-direction:column;gap:8px;text-align:left;border:1px solid rgba(40,95,97,.2);background:linear-gradient(145deg,rgba(255,255,255,.62),rgba(226,238,228,.42));color:var(--color-slate-text);box-shadow:0 8px 22px rgba(42,77,73,.055);transition:transform var(--dur-fast) var(--ease-standard),border-color var(--dur-fast) var(--ease-standard),box-shadow var(--dur-fast) var(--ease-standard)}
.briefing__module:hover,.briefing__module:focus-visible{transform:translateY(-4px);border-color:color-mix(in srgb,var(--era-accent) 65%,var(--color-scroll-gold));box-shadow:0 16px 32px rgba(42,77,73,.14);outline:none}
.briefing__module-head{display:flex;align-items:center;justify-content:space-between;gap:8px}
.briefing__module-head i{font-style:normal;font-size:10px;letter-spacing:.16em;color:var(--color-scroll-red)}
.briefing__module-head em{padding:3px 7px;border-radius:999px;background:rgba(40,95,97,.08);font-size:8px;font-style:normal;color:var(--color-mineral-700)}
.briefing__module>strong{font-family:var(--font-display);font-size:15px;font-weight:500;color:var(--color-mineral-800)}
.briefing__module>p{font-size:10px;line-height:1.55;color:rgba(41,69,74,.62)}
.briefing__module-experience{font-size:9px;line-height:1.45;color:rgba(41,69,74,.5)}
.briefing__module-enter{display:flex;align-items:center;justify-content:space-between;margin-top:auto;padding-top:8px;border-top:1px solid rgba(40,95,97,.12);font-size:9px;letter-spacing:.08em;color:var(--color-mineral-700)}
.briefing__module-enter b{font-size:15px;font-weight:400;color:var(--color-scroll-red)}
.briefing__narration-toggle{align-self:flex-end;margin-top:10px;padding:4px 0;border:0;background:transparent;color:rgba(41,69,74,.52);font-size:10px}
.briefing__narration-toggle:hover,.briefing__narration-toggle:focus-visible{color:var(--color-scroll-red)}
.briefing__narration { margin-top: 14px; padding: 16px; border-left: 2px solid var(--era-accent); background: rgba(255,255,255,.025); }
.briefing__narration p { font-family: var(--font-display); line-height: 1.8; color: rgba(238,229,210,.68); }
.briefing__narration small { display: block; margin-top: 9px; color: rgba(238,229,210,.3); }
.briefing__footer { margin-top: auto; padding-top: 26px; display: flex; justify-content: space-between; gap: 20px; align-items: end; }
.briefing__layers { display: flex; flex-wrap: wrap; gap: 9px 14px; max-width: 390px; }
.briefing__layers span { display: flex; align-items: center; gap: 5px; font-size: 9px; color: rgba(238,229,210,.34); }
.briefing__layers i { width: 6px; height: 6px; border-radius: 50%; }
.attested { background: #78a586; }.interpreted { background: #c5a25e; }.reconstructed { background: #718995; }.dramatized { background: #9a7fa6; }
.briefing__footer > div:last-child { display: flex; gap: 10px; }
.briefing__footer button { border: 0; background: transparent; color: rgba(238,229,210,.4); font-size: 10px; }
.briefing__footer button:hover { color: #dfc981; }
.reveal-enter-active,.reveal-leave-active { transition: opacity 180ms ease, transform 180ms ease; }.reveal-enter-from,.reveal-leave-to { opacity: 0; transform: translateY(-5px); }

@media (max-width: 980px) {
  .briefing__main { grid-template-columns: 1fr; }
  .briefing__stage { min-height: 520px; border-right: 0; border-bottom: 1px solid rgba(225,207,170,.12); }
}
@media (max-width: 620px) {
  .briefing__nav { grid-template-columns: 1fr 1fr; }.briefing__nav span { display:none; }.briefing__nav a:last-child { justify-self:end; }
  .briefing__stage { padding: 30px 24px; }
  .briefing__content { padding: 38px 24px 28px; }
  .briefing__anchor>div{align-items:flex-start;flex-direction:column;gap:3px}
  .briefing__anchor strong{white-space:normal}
  .briefing__facts { grid-template-columns: 1fr; }
  .briefing__actions, .briefing__footer { flex-direction: column; align-items: stretch; }
  .briefing__modules { grid-template-columns: 1fr; }
  .briefing__module { min-height: 0; }
  .briefing__narration-toggle { align-self: stretch; min-height: 44px; text-align: left; }
}

/* V3 青绿任务简报：左右双页摊开，桌面端不滚动整页。 */
.briefing{height:100dvh;min-height:700px;color:var(--color-slate-text);background:linear-gradient(145deg,#edf3ea,#d5e5dc)}
.briefing__grain{opacity:.08;mix-blend-mode:multiply}
.briefing__nav{border-bottom-color:rgba(40,95,97,.16);color:rgba(41,69,74,.58);background:rgba(248,250,244,.38)}
.briefing__nav a:hover{color:var(--color-scroll-red)}
.briefing__main{height:calc(100dvh - 64px);min-height:636px}
.briefing__stage{min-height:0;border-right-color:rgba(40,95,97,.16);background:radial-gradient(circle at 50% 36%,color-mix(in srgb,var(--era-accent) 14%,white),transparent 44%),rgba(234,242,234,.45)}
.briefing__identity span,.briefing__artifact span{color:rgba(41,69,74,.48)}
.briefing__identity strong{color:var(--color-mineral-800)}
.briefing__identity small{color:rgba(41,69,74,.52)}
.briefing blockquote{color:rgba(41,69,74,.72)}
.briefing__artifact strong{color:var(--color-scroll-gold)}
.briefing__content{overflow-y:auto;overscroll-behavior:contain;background:rgba(248,250,244,.28)}
.briefing h1{color:var(--color-mineral-800)}
.briefing__source-title{color:rgba(41,69,74,.48)}
.briefing__mission,.briefing__question{border-color:rgba(40,95,97,.14)}
.briefing__mission span,.briefing__question span{color:rgba(41,69,74,.48)}
.briefing__mission p,.briefing__question p{color:rgba(41,69,74,.78)}
.briefing__facts{background:rgba(40,95,97,.12);border-color:rgba(40,95,97,.12)}
.briefing__facts div{background:rgba(248,250,244,.86)}
.briefing__facts span{color:rgba(41,69,74,.45)}
.briefing__facts strong{color:rgba(41,69,74,.75)}
.briefing__actions button{border-color:rgba(40,95,97,.22);background:rgba(255,255,255,.34);color:rgba(41,69,74,.68)}
.briefing__actions button:hover{border-color:var(--color-scroll-red);color:var(--color-scroll-red)}
.briefing__start{background:color-mix(in srgb,var(--era-accent) 10%,rgba(255,255,255,.62))!important;border-color:color-mix(in srgb,var(--era-accent) 62%,var(--color-mineral-700))!important;color:var(--color-mineral-800)!important}
.briefing__start i{color:var(--color-scroll-red)}
.briefing__narration{background:rgba(255,255,255,.4)}
.briefing__narration p{color:rgba(41,69,74,.74)}
.briefing__narration small,.briefing__layers span{color:rgba(41,69,74,.46)}
.briefing__footer button{color:rgba(41,69,74,.54)}
.briefing__footer button:hover{color:var(--color-scroll-red)}

@media (min-width:981px) and (max-height:820px){
  .briefing__stage{padding:34px 50px}
  .briefing__content{padding:34px 54px 24px}
  .briefing__mission{margin-top:22px}
  .briefing__facts{margin-top:14px}
  .briefing__actions{margin-top:18px}
  .briefing__footer{padding-top:14px}
}

/* V6 真实场景任务大厅：场景承担吸引力，任务卷承担操作，不再整页泛白。 */
@media (min-width:981px){
  .briefing__main{grid-template-columns:minmax(0,62%) minmax(430px,38%)}
  .briefing__stage{padding:44px 54px 38px;border-right:0;color:#fff9e8;box-shadow:18px 0 52px rgba(29,61,57,.18)}
  .briefing__content{position:relative;padding:34px 44px 24px;background:linear-gradient(145deg,rgba(248,250,242,.98),rgba(226,238,228,.96));box-shadow:-16px 0 48px rgba(22,56,53,.14);overflow-y:auto}
}
@media (min-width:981px) and (max-width:1240px){
  .briefing__modules{grid-template-columns:repeat(2,minmax(0,1fr))}
  .briefing__module{min-height:0}
}
.briefing__art{opacity:1;mask-image:none}
.briefing__art::after{
  background:
    linear-gradient(90deg,rgba(14,38,38,.08) 42%,rgba(13,38,37,.5) 100%),
    linear-gradient(0deg,rgba(11,34,34,.9) 0,rgba(14,38,37,.55) 28%,transparent 67%),
    linear-gradient(180deg,rgba(9,31,32,.14),transparent 28%);
}
.briefing__art img{width:100%;height:100%;filter:saturate(.92) contrast(1.07) brightness(.9);transform:scale(1.015);animation:briefing-camera 8s ease-out both}
.briefing__art figcaption{right:20px;top:20px;border-color:rgba(255,247,222,.44);background:rgba(20,50,48,.7);color:#fff7e3;text-shadow:0 1px 8px rgba(0,0,0,.32)}
.briefing__stage::before,.briefing__stage::after,.briefing__halo{display:none}
.briefing__index{z-index:1;align-self:flex-start;padding:6px 10px;border:1px solid rgba(244,210,132,.42);background:rgba(17,46,44,.46);backdrop-filter:blur(8px);color:#f2cf80}
.briefing__keyword{z-index:1;margin:auto 0 10px;font-size:clamp(58px,7vw,104px);line-height:.9;letter-spacing:.02em;color:rgba(255,242,207,.22);opacity:1;text-shadow:0 3px 24px rgba(0,0,0,.34)}
.briefing__identity{z-index:1;max-width:600px}
.briefing__identity span,.briefing__artifact span{color:rgba(255,246,220,.7)}
.briefing__identity strong{color:#fff9e8;text-shadow:0 3px 22px rgba(0,0,0,.5)}
.briefing__identity small{color:rgba(255,247,226,.7);text-shadow:0 2px 10px rgba(0,0,0,.4)}
.briefing blockquote{z-index:1;margin-top:20px;color:rgba(255,247,226,.9);text-shadow:0 2px 12px rgba(0,0,0,.5)}
.briefing__artifact{z-index:1;margin-top:18px;padding-top:14px;border-top:1px solid rgba(255,240,201,.24)}
.briefing__artifact strong{color:#f1cc75;text-shadow:0 2px 10px rgba(0,0,0,.35)}
.briefing__role-sigil{position:absolute;z-index:2;left:-62px;top:72px;width:112px;height:112px;padding:14px 10px;display:grid;align-content:center;justify-items:center;text-align:center;border:1px solid rgba(178,138,69,.52);border-radius:50%;background:rgba(245,240,217,.94);box-shadow:0 16px 40px rgba(30,69,64,.2),0 0 0 7px rgba(235,242,231,.52);backdrop-filter:blur(12px)}
.briefing__role-sigil span{font-family:var(--font-display);font-size:25px;color:var(--color-scroll-red)}
.briefing__role-sigil small{max-width:86px;margin-top:3px;font-size:8px;line-height:1.35;color:rgba(41,69,74,.68)}
.briefing__eyebrow{padding-left:64px;color:color-mix(in srgb,var(--era-accent) 70%,var(--color-scroll-gold))}
.briefing h1{margin-top:7px;font-size:clamp(43px,4.4vw,68px);color:var(--color-mineral-800)}
.briefing__source-title{color:rgba(41,69,74,.52)}
.briefing__situation{margin-top:18px;padding:13px 15px;border-left:3px solid var(--color-scroll-red);background:linear-gradient(90deg,rgba(178,81,61,.08),transparent)}
.briefing__situation span{display:block;font-size:9px;letter-spacing:.18em;color:var(--color-scroll-red)}
.briefing__situation strong{display:block;margin-top:5px;font-family:var(--font-display);font-size:15px;font-weight:500;line-height:1.65;color:var(--color-mineral-800)}
.briefing__mission,.briefing__question{grid-template-columns:68px 1fr;gap:13px;margin-top:14px;padding:11px 0;border-color:rgba(40,95,97,.16)}
.briefing__question{margin-top:0}
.briefing__mission p,.briefing__question p{font-size:14px;line-height:1.62;color:rgba(41,69,74,.82)}
.briefing__objectives{display:grid;grid-template-columns:68px 1fr;gap:13px;padding:12px 0;border-bottom:1px solid rgba(40,95,97,.16)}
.briefing__objectives>span{font-size:9px;letter-spacing:.14em;color:rgba(41,69,74,.5)}
.briefing__objectives ol{list-style:none;margin:0;padding:0;display:flex;gap:7px}
.briefing__objectives li{min-width:0;flex:1;display:grid;grid-template-columns:18px 1fr;gap:6px;align-items:start}
.briefing__objectives b{width:18px;height:18px;display:grid;place-items:center;border-radius:50%;background:rgba(40,95,97,.1);color:var(--color-mineral-700);font-size:9px}
.briefing__objectives em{font-style:normal;font-size:10px;line-height:1.45;color:rgba(41,69,74,.65)}
.briefing__facts{margin-top:14px;border-color:rgba(40,95,97,.15);background:rgba(40,95,97,.15)}
.briefing__facts div{padding:10px;background:rgba(250,252,245,.78)}
.briefing__actions{margin-top:16px}
.briefing__actions button{height:46px}
.briefing__start{position:relative;overflow:hidden;background:linear-gradient(90deg,color-mix(in srgb,var(--era-accent) 12%,#fff9e5),rgba(255,250,232,.86))!important;box-shadow:0 12px 28px rgba(40,83,76,.11)}
.briefing__start::before{content:'';position:absolute;inset:-80% -30%;background:linear-gradient(105deg,transparent 42%,rgba(255,255,255,.82) 50%,transparent 58%);transform:translateX(-72%);transition:transform 560ms var(--ease-standard)}
.briefing__start:hover::before{transform:translateX(72%)}
.briefing__start span,.briefing__start i{position:relative;z-index:1}
.briefing__footer{padding-top:14px}
@keyframes briefing-camera{from{transform:scale(1.07)}to{transform:scale(1.015)}}
@media(max-width:980px){
  .briefing{height:auto;min-height:100dvh;overflow:auto}
  .briefing__main{height:auto;min-height:0;display:block}
  .briefing__stage{min-height:62dvh;padding:32px 28px}
  .briefing__content{overflow:visible;padding:34px 28px}
  .briefing__role-sigil{display:none}
  .briefing__eyebrow{padding-left:0}
}
@media(prefers-reduced-motion:reduce){.briefing__art img{animation:none}}
</style>
