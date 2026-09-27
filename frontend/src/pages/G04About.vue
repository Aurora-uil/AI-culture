<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import GlobalHeader from '@/components/global/GlobalHeader.vue'
import EvidenceBadge from '@/components/global/EvidenceBadge.vue'
import DsIcon from '@/components/ds/DsIcon.vue'
import { useSessionStore } from '@/stores/session'
import type { VerificationLabel } from '@/types'

/**
 * G04 项目说明（设计系统 §46 / §87）
 *
 * Tab：[项目理念] [AI如何工作] [史料与内容审核] [数字复原说明] [数据与版权]
 *
 * 「AI如何工作」用简单可视化，不做技术堆砌。
 */
const session = useSessionStore()
const tab = ref<'idea' | 'ai' | 'sources' | 'recon' | 'rights'>('idea')

onMounted(() => {
  void session.checkHealth()
})

const TABS = [
  { key: 'idea', label: '项目理念' },
  { key: 'ai', label: 'AI如何工作' },
  { key: 'sources', label: '史料与内容审核' },
  { key: 'recon', label: '数字复原说明' },
  { key: 'rights', label: '数据与版权' },
] as const

const BADGES: { type: VerificationLabel; desc: string }[] = [
  { type: 'historical_fact', desc: '有可靠来源直接支持的史实。' },
  { type: 'scholarly_view', desc: '属于研究解释，不是唯一确定结论。' },
  { type: 'digital_reconstruction', desc: '为帮助理解制作的数字化示意，不等同考古精确复原。' },
  { type: 'ai_narrative', desc: 'AI 基于审核资料生成的第一人称叙事，非历史人物真实原话。' },
  { type: 'curatorial', desc: '为帮助理解建立的主题联系，不是历史因果。' },
  { type: 'disputed', desc: '关于这一点，学界存在不同观点。' },
]

const health = computed(() => session.health)
</script>

<template>
  <div class="page">
    <GlobalHeader :show-breadcrumb="false" />

    <main class="ab page-body">
      <header class="ab__head">
        <h1 class="ab__title tt-h1">项目说明</h1>
        <p class="ab__sub">
          关于我们如何组织内容、AI 如何参与，以及我们如何避免让技术越过史料本身。
        </p>
      </header>

      <nav class="ab__tabs" role="tablist">
        <button
          v-for="t in TABS"
          :key="t.key"
          class="ab__tab"
          :class="{ 'is-on': tab === t.key }"
          role="tab"
          :aria-selected="tab === t.key"
          type="button"
          @click="tab = t.key"
        >
          {{ t.label }}
        </button>
      </nav>

      <!-- 项目理念 -->
      <section v-if="tab === 'idea'" class="ab__panel">
        <h2 class="ab__h2">从「看文物」到「理解关系」</h2>
        <p class="ab__p">
          传统数字文化展示通常让用户看到一个个孤立的文物。本项目希望把
          <strong>人物、文物、事件、地点、语言、技艺与文化遗产</strong>
          连接成一张可以被主动探索的关系网络。
        </p>
        <p class="ab__p">
          六个时代是产品为了帮助用户理解<strong>不同类型的历史联系</strong>而设置的叙事组织方式，
          不是对复杂历史进程的单线概括：
        </p>
        <ul class="ab__list">
          <li><b>汉代 · 相遇</b> — 道路与人员往来如何开始形成长期联系</li>
          <li><b>北魏 · 交融</b> — 文化进入彼此生活后如何被吸收、改变与重构</li>
          <li><b>唐代 · 交流</b> — 政治交往与人员流动如何延展出更长的关系</li>
          <li><b>元代 · 共存</b> — 多种文字与文化如何共享同一历史空间</li>
          <li><b>清代 · 归属</b> — 迁徙、家园记忆与共同历史经历如何构成群体身份的一部分</li>
          <li><b>当代 · 传承</b> — 数字技术如何帮助我们先理解、再参与传统文化</li>
        </ul>
        <p class="ab__note">
          需要特别说明：长期交往、交流与交融为后来共同历史记忆与文化联系的形成提供了重要历史基础，
          但这不等于说古代某个事件就是为了某个现代结果而发生的。
        </p>
      </section>

      <!-- AI 如何工作 -->
      <section v-else-if="tab === 'ai'" class="ab__panel">
        <h2 class="ab__h2">AI 在我们的系统里做什么</h2>
        <p class="ab__p">
          AI 不是用来「随便聊天」的。它承担四件事：<b>检索史料</b>、<b>组织讲述</b>、
          <b>回答追问</b>、<b>核验引用</b>。
        </p>

        <ol class="ab__flow">
          <li class="ab__flow-step">
            <span class="ab__flow-num">1</span>
            <div>
              <b>用户提问</b>
              <p>补足「这里」「它」等指代，形成完整检索问题。</p>
            </div>
          </li>
          <li class="ab__flow-step">
            <span class="ab__flow-num">2</span>
            <div>
              <b>从已审核资料中检索</b>
              <p>只检索 <code>已审核</code> 且来源等级为官方或学术的资料。</p>
            </div>
          </li>
          <li class="ab__flow-step">
            <span class="ab__flow-num">3</span>
            <div>
              <b>判断证据是否真的支持这个问题</b>
              <p>不因为片段提到「元代」就当作高度相关。</p>
            </div>
          </li>
          <li class="ab__flow-step">
            <span class="ab__flow-num">4</span>
            <div>
              <b>生成回答并核验</b>
              <p>检查年代、名称、因果是否都有证据，引用编号是否真实存在。</p>
            </div>
          </li>
          <li class="ab__flow-step">
            <span class="ab__flow-num">5</span>
            <div>
              <b>回答 + 来源</b>
              <p>每条重要事实都可以点开看它的依据。</p>
            </div>
          </li>
        </ol>

        <div class="ab__callout">
          <DsIcon name="alert" :size="17" />
          <div>
            <p class="ab__callout-title">我们不做的事</p>
            <ul class="ab__list ab__list--tight">
              <li>没有可靠资料时，明确回答「资料不足」，不猜测</li>
              <li>不让 AI 编造历史人物对白、私人心理或「亲眼所见」的情节</li>
              <li>不让 AI 处理存在学术争议的问题时给出唯一结论</li>
              <li>不把现代概念直接当作古人的自觉目标</li>
            </ul>
          </div>
        </div>

        <div v-if="health" class="ab__status">
          <h3 class="ab__h3">当前运行状态</h3>
          <div class="ab__status-grid">
            <div class="ab__status-item">
              <span class="ab__status-label">内容数据库</span>
              <span class="ab__status-val" :class="{ ok: health.postgres }">
                {{ health.postgres ? '已连接' : '未连接' }}
              </span>
            </div>
            <div class="ab__status-item">
              <span class="ab__status-label">关系图谱</span>
              <span class="ab__status-val" :class="{ ok: health.neo4j }">
                {{ health.neo4j ? '已连接' : '未连接' }}
              </span>
            </div>
            <div class="ab__status-item">
              <span class="ab__status-label">AI 模型</span>
              <span class="ab__status-val" :class="{ ok: health.llm.configured }">
                {{ health.llm.configured ? health.llm.model || '已配置' : '未配置 · 演示保障模式' }}
              </span>
            </div>
            <div class="ab__status-item">
              <span class="ab__status-label">向量检索</span>
              <span class="ab__status-val" :class="{ ok: health.embedding.configured }">
                {{ health.embedding.configured ? health.embedding.provider : '本地中文检索' }}
              </span>
            </div>
          </div>
          <p v-if="!health.llm.configured" class="ab__status-note">
            当前未配置大模型 API Key，AI 回答来自<strong>已审核的预设问答库</strong>，
            界面会明确标注「演示保障模式」，不会伪装成实时生成。
          </p>
        </div>
      </section>

      <!-- 史料与内容审核 -->
      <section v-else-if="tab === 'sources'" class="ab__panel">
        <h2 class="ab__h2">每一条内容都能追溯</h2>
        <p class="ab__p">
          我们不采用「一个实体挂几个参考书名」的做法，而是把
          <strong>具体的事实主张（Claim）</strong>单独记录，并为它绑定支持来源与出处位置。
          这样 RAG 问答和知识图谱的每一条边，共用同一套溯源机制。
        </p>

        <div class="ab__levels">
          <div class="ab__level">
            <span class="ab__level-tag ab__level-tag--s">官方资料</span>
            <p>文物主管部门、博物馆、权威公共文化机构</p>
          </div>
          <div class="ab__level">
            <span class="ab__level-tag ab__level-tag--a">学术研究</span>
            <p>学术论文、专业著作、学术机构</p>
          </div>
          <div class="ab__level">
            <span class="ab__level-tag ab__level-tag--b">专业资料</span>
            <p>高校与专业科普材料</p>
          </div>
        </div>

        <h3 class="ab__h3">可信度标签</h3>
        <p class="ab__p">我们把内容的性质直接标在界面上，让用户能区分：</p>
        <ul class="ab__badges">
          <li v-for="b in BADGES" :key="b.type" class="ab__badge-row">
            <EvidenceBadge :type="b.type" size="m" />
            <span class="ab__badge-desc">{{ b.desc }}</span>
          </li>
        </ul>

        <div class="ab__callout ab__callout--warn">
          <DsIcon name="info" :size="17" />
          <div>
            <p class="ab__callout-title">关于来源视角</p>
            <p class="ab__p ab__p--tight">
              清代御制文献等官方记述，既是重要史料，也带有其作者与政治语境。
              我们在展示时会标明来源视角，不把它当作所有历史参与者共同的声音。
            </p>
          </div>
        </div>
      </section>

      <!-- 数字复原说明 -->
      <section v-else-if="tab === 'recon'" class="ab__panel">
        <h2 class="ab__h2">什么不是「真实复原」</h2>
        <p class="ab__p">
          本项目中的历史场景画面，用于帮助理解空间与氛围，
          <strong>不等同于考古意义上的精确复原</strong>。
          所有 AI 辅助生成的画面都固定带有标识。
        </p>

        <h3 class="ab__h3">我们如何控制「精度不超过证据」</h3>
        <ul class="ab__list">
          <li>
            <b>路线不画成 GPS 轨迹。</b>
            迁徙路线按可信度分级显示：确认地点、较高置信历史廊道、大体迁徙区段、
            路线存在不确定性、策展关联，并配有固定图例。
          </li>
          <li>
            <b>历史数字不合并。</b>
            当不同资料统计口径不同时，我们并列展示各来源的原始表述，
            不计算平均值，也不给出一个虚假的「唯一精确值」。
          </li>
          <li>
            <b>事件时间保留原始精度。</b>
            资料只记到季节的，就显示「夏季」，不虚构具体日期。
          </li>
          <li>
            <b>历史画不等于现场照片。</b>
            画面中的站位、神态、服饰是艺术表现，
            具体历史事实需要与文献和其它材料互相核验。
          </li>
        </ul>
      </section>

      <!-- 数据与版权 -->
      <section v-else class="ab__panel">
        <h2 class="ab__h2">数据、版权与使用边界</h2>

        <h3 class="ab__h3">我们不采集什么</h3>
        <p class="ab__p">
          访问无需注册。平台不采集身份证号、手机号或任何敏感个人信息，
          探索记录匿名保存，仅用于生成你自己看到的文化足迹。
        </p>

        <h3 class="ab__h3">素材与权利状态</h3>
        <p class="ab__p">
          每一项视觉素材都有独立的权利记录，分别说明是否可以网页展示、
          裁切、作为生成参考、用于模型训练、公开下载或商业使用。
          <strong>知识可以公开展示，不等于素材可以用于 AI 生成</strong> —— 这是两套权限。
        </p>
        <ul class="ab__list ab__list--tight">
          <li>
            唐代《步辇图》：
            <a href="https://commons.wikimedia.org/wiki/File:Buliantu.jpg" target="_blank" rel="noreferrer">公版数字图像</a>，
            藏品信息以<a href="https://www.dpm.org.cn/collection/paint/234620.html" target="_blank" rel="noreferrer">故宫博物院藏品页</a>为准。
          </li>
          <li>
            云冈石窟第20窟与龙门古阳洞实拍：Wikimedia Commons，CC0。
          </li>
          <li>
            居庸关云台东壁实拍：BabelStone / Wikimedia Commons，CC BY-SA 3.0。
          </li>
          <li>
            首页“千年行卷”与部分章节索引为项目原创生成视觉，不作为历史原图使用。
          </li>
        </ul>

        <h3 class="ab__h3">关于 AI 共创</h3>
        <ul class="ab__list">
          <li>生成结果始终标注「AI辅助文化创意作品 · 非传统羌绣原作」</li>
          <li>AI 新增的内容与传统参考元素会被分别说明</li>
          <li>没有明确授权的元素不会进入生成流程</li>
          <li>不模拟在世传承人的人格、口吻或声音</li>
          <li>传统针法是手工技艺，不是图像风格或滤镜</li>
        </ul>

        <h3 class="ab__h3">待核验内容</h3>
        <p class="ab__p">
          项目交付时附有一份<strong>待内容组核验清单</strong>，列出所有由工程实现方补写、
          尚未经史料核验的数据（如部分来源链接、热点标注坐标、来源等级）。
          这些内容在数据库中标记为 <code>draft</code> / <code>review</code>，
          <strong>不会进入 AI 检索</strong>。
        </p>
      </section>
    </main>
  </div>
</template>

<style scoped>
.ab {
  padding-top: var(--sp-10);
  padding-bottom: var(--sp-16);
  max-width: 920px;
}

.ab__title {
  color: var(--color-ink-900);
}
.ab__sub {
  margin-top: var(--sp-2);
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
}

.ab__tabs {
  display: flex;
  gap: var(--sp-1);
  margin: var(--sp-8) 0 var(--sp-8);
  padding: 3px;
  border-radius: var(--radius-btn);
  background: var(--color-paper-200);
  width: fit-content;
}
.ab__tab {
  border: 0;
  background: transparent;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: var(--fs-body-s);
  color: var(--color-ink-700);
  transition:
    background-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard);
}
.ab__tab.is-on {
  background: #fff;
  color: var(--color-cinnabar-600);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(39, 34, 27, 0.08);
}

.ab__panel {
  font-size: var(--fs-body);
  line-height: var(--lh-body-l);
  color: var(--color-ink-700);
}

.ab__h2 {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  line-height: var(--lh-h1);
  color: var(--color-ink-900);
  margin-bottom: var(--sp-4);
}
.ab__h3 {
  font-size: var(--fs-h3);
  color: var(--color-ink-900);
  margin: var(--sp-8) 0 var(--sp-3);
}

.ab__p {
  margin-bottom: var(--sp-4);
}
.ab__p--tight {
  margin-bottom: 0;
}
.ab__p strong {
  color: var(--color-ink-900);
}

.ab__list {
  margin: 0 0 var(--sp-4);
  padding-left: 1.15em;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.ab__list--tight {
  margin-bottom: 0;
  gap: 4px;
}
.ab__list li {
  padding-left: 0.15em;
}
.ab__list b {
  color: var(--color-ink-900);
}

.ab__note {
  margin-top: var(--sp-4);
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  border-left: 3px solid var(--color-gold-500);
  font-size: var(--fs-body-s);
  line-height: var(--lh-body-l);
  color: var(--color-ink-700);
}

/* ---------- AI 流程 ---------- */
.ab__flow {
  list-style: none;
  margin: 0 0 var(--sp-8);
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.ab__flow-step {
  display: flex;
  gap: var(--sp-4);
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  background: #fff;
  border: 1px solid var(--color-border);
}
.ab__flow-num {
  flex: none;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-cinnabar-600);
  color: #fff;
  font-size: var(--fs-caption);
  font-weight: 600;
}
.ab__flow-step b {
  color: var(--color-ink-900);
}
.ab__flow-step p {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  margin-top: 2px;
}

.ab__callout {
  display: flex;
  gap: var(--sp-3);
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  border: 1px solid var(--color-border);
  margin-bottom: var(--sp-6);
  color: var(--color-ink-700);
}
.ab__callout--warn {
  background: color-mix(in srgb, var(--color-warning) 9%, transparent);
  border-color: color-mix(in srgb, var(--color-warning) 30%, transparent);
}
.ab__callout-title {
  font-weight: 600;
  color: var(--color-ink-900);
  margin-bottom: var(--sp-2);
}
.ab__callout svg {
  flex: none;
  margin-top: 2px;
}

/* ---------- 运行状态 ---------- */
.ab__status {
  padding: var(--sp-4);
  border-radius: var(--radius-card);
  background: var(--color-paper-100);
  border: 1px solid var(--color-border);
}
.ab__status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-3);
}
.ab__status-item {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-3);
  font-size: var(--fs-body-s);
  padding: var(--sp-2) 0;
  border-bottom: 1px dashed var(--color-border);
}
.ab__status-label {
  color: var(--color-ink-500);
}
.ab__status-val {
  color: var(--color-warning);
}
.ab__status-val.ok {
  color: var(--color-success);
}
.ab__status-note {
  margin-top: var(--sp-4);
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  line-height: var(--lh-body-s);
}

/* ---------- 来源等级 ---------- */
.ab__levels {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  margin-bottom: var(--sp-6);
}
.ab__level {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}
.ab__level p {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
  margin: 0;
}
.ab__level-tag {
  flex: none;
  width: 76px;
  text-align: center;
  padding: 3px 0;
  border-radius: var(--radius-pill);
  font-size: var(--fs-caption);
}
.ab__level-tag--s {
  background: color-mix(in srgb, var(--evidence-fact) 14%, transparent);
  color: var(--evidence-fact);
}
.ab__level-tag--a {
  background: color-mix(in srgb, var(--evidence-interpretation) 16%, transparent);
  color: var(--color-gold-700);
}
.ab__level-tag--b {
  background: rgba(65, 55, 42, 0.07);
  color: var(--color-ink-500);
}

.ab__badges {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}
.ab__badge-row {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
}
.ab__badge-desc {
  font-size: var(--fs-body-s);
  color: var(--color-ink-500);
}

code {
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
  font-size: 0.9em;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(65, 55, 42, 0.07);
  color: var(--color-ink-900);
}
</style>
