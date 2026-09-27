import type { ChapterSlug } from '@/types'

export type GameAction =
  | 'ENTER'
  | 'INSPECT'
  | 'LENS'
  | 'DECISION'
  | 'CHAT'
  | 'GRAPH'
  | 'COMPLETE'

export type MethodKey = 'truth' | 'empathy' | 'connection'

export interface DecisionChoice {
  id: string
  label: string
  description: string
  response: string
  impact: Partial<Record<MethodKey, number>>
}

export interface ChapterGameMeta {
  slug: ChapterSlug
  gameTitle: string
  chapterMark: string
  role: string
  roleNote: string
  mission: string
  mechanic: string
  duration: string
  artifact: string
  storyAnchor: {
    /** 进入剧情时反复回到的真实文物、遗存或具体作品。 */
    name: string
    /** 给玩家看的对象类别，不用数据库内部枚举。 */
    kind: string
    /** verified=已核验；review=内容待核；rights=必须先取得作品授权。 */
    status: 'verified' | 'review' | 'rights'
    statusLabel: string
    /** 防止为了戏剧性越过年代、代表性或权利边界。 */
    boundary: string
  }
  openingLine: string
  objectives: Array<{
    action: GameAction
    label: string
    target?: number
  }>
  decision: {
    eyebrow: string
    title: string
    context: string
    choices: DecisionChoice[]
  }
}

export const GAME_CATALOG: Record<ChapterSlug, ChapterGameMeta> = {
  han: {
    slug: 'han',
    gameTitle: '未定之路',
    chapterMark: '相遇之结',
    role: '丝路专题展年轻记录员',
    roleNote: '游戏原创当代角色 · 通过文物展签校勘进入汉代交通史，不扮演可考历史人物',
    mission: '核对一张把“五星出东方利中国”锦护膊直接归因于张骞的展签，沿路线、年代与出土信息区分直接证据和长期联系。',
    mechanic: '路线追索 · 展签校勘',
    duration: '约 25 分钟',
    artifact: '有证据边界的锦护膊展签',
    storyAnchor: {
      name: '“五星出东方利中国”锦护膊',
      kind: '汉晋织锦文物',
      status: 'verified',
      statusLabel: '文物已核验',
      boundary: '它是交通网络延续到后世的物证，现有资料不支持它与张骞存在直接关系。',
    },
    openingLine: '一件后世出土的织锦，能被写成张骞带回的遗物吗？',
    objectives: [
      { action: 'ENTER', label: '领取错误展签的校勘任务' },
      { action: 'INSPECT', label: '核对三处路线或文物证据', target: 3 },
      { action: 'LENS', label: '比较年代、地点与关系强度' },
      { action: 'DECISION', label: '决定如何改写锦护膊展签' },
      { action: 'CHAT', label: '向数字历史角色追问' },
      { action: 'GRAPH', label: '把道路连接成关系网络' },
    ],
    decision: {
      eyebrow: '展签校勘',
      title: '展签把锦护膊写成“张骞带回的遗物”',
      context: '锦护膊出土于尼雅遗址，能够帮助理解长期交通网络中的物质文化；但它的年代与现有证据都不能证明它由张骞直接带回。你准备怎样修改？',
      choices: [
        { id: 'mark_uncertain', label: '删除直接归因', description: '明确写出目前没有证据证明它与张骞存在直接关系。', response: '展签删掉了一个醒目的传奇，却保住了文物与历史之间真正可证的距离。', impact: { truth: 2 } },
        { id: 'ask_travellers', label: '改写为长期网络物证', description: '说明它呈现的是此后长期发展出的交通与文化联系。', response: '织锦不再被绑在一个人的旅程上，而被放回跨越多个世纪的联系网络。', impact: { truth: 1, connection: 2 } },
        { id: 'follow_fast', label: '并列年代与出土信息', description: '让观众自己看见张骞出使与锦护膊之间的时间距离。', response: '年代、出土地点和证据边界被并排写下，展签留下了继续追问的入口。', impact: { empathy: 1, truth: 1 } },
      ],
    },
  },
  'northern-wei': {
    slug: 'northern-wei',
    gameTitle: '两座城之间',
    chapterMark: '交融之结',
    role: '北魏专题展陈助理',
    roleNote: '游戏原创角色 · 只依据墓志、石窟与器物证据组织展陈，不替文物补写细节',
    mission: '以元羽墓志为主证物，比较平城与洛阳的石窟和器物证据，判断一方墓志能够说明什么、不能代表什么。',
    mechanic: '双城比较 · 物证展陈',
    duration: '约 30 分钟',
    artifact: '元羽墓志证据展签',
    storyAnchor: {
      name: '元羽墓志',
      kind: '北魏墓志文物',
      status: 'verified',
      statusLabel: '主证物已核验',
      boundary: '墓志可以说明墓主个案及相关制度变化，不能单独代表整个北魏社会。',
    },
    openingLine: '一方墓志能说明一个人的变化，能代表整个时代吗？',
    objectives: [
      { action: 'ENTER', label: '接下墓志展签委托' },
      { action: 'INSPECT', label: '比较三组墓志、石窟或器物证据', target: 3 },
      { action: 'LENS', label: '区分个案、变化与未知' },
      { action: 'DECISION', label: '决定展签如何使用一方墓志' },
      { action: 'CHAT', label: '追问改革与迁都的边界' },
      { action: 'GRAPH', label: '找出延续、变化与并存' },
    ],
    decision: {
      eyebrow: '展签定稿',
      title: '策展人想用一方墓志概括整个北魏',
      context: '元羽墓志提供了清楚的个案线索，但石窟、陶俑和其他材料呈现的变化并不完全相同。你要怎样处理这件主证物？',
      choices: [
        { id: 'compare_first', label: '明确标为个案证据', description: '说明墓志支持到哪里，并把未知留在展签上。', response: '墓志不再替一个时代发言，却更准确地讲清了它所记录的那个人。', impact: { truth: 2 } },
        { id: 'workshop_together', label: '与石窟、陶俑并列', description: '让不同材料共同呈现延续、变化与并存。', response: '一件主证物与多组旁证形成对话，变化不再被压缩成单一路线。', impact: { connection: 2, truth: 1 } },
        { id: 'keep_family_mark', label: '保留墓主个人尺度', description: '从姓名、籍贯等可证信息讲述个体经历，不扩写整个社会。', response: '展签把宏大的迁都重新落到一个具体生命留下的文字上。', impact: { empathy: 2 } },
      ],
    },
  },
  tang: {
    slug: 'tang',
    gameTitle: '画外来使',
    chapterMark: '交流之结',
    role: '鸿胪寺基层译语人',
    roleNote: '游戏原创角色 · 不代表任何可考真实人物',
    mission: '从《步辇图》的画内人物出发，校对一次会见背后的身份、事件与画外关系。',
    mechanic: '画卷搜证 · 信息质询',
    duration: '约 25 分钟',
    artifact: '画内—画外人物谱',
    storyAnchor: {
      name: '《步辇图》',
      kind: '唐代历史画',
      status: 'verified',
      statusLabel: '画作已核验',
      boundary: '历史画不是现场照片；画内人物与画外事件必须通过其他来源建立关系。',
    },
    openingLine: '请在画中找到文成公主。',
    objectives: [
      { action: 'ENTER', label: '领取待核名册' },
      { action: 'INSPECT', label: '观察三处画面线索', target: 3 },
      { action: 'LENS', label: '切换画内与画外关系' },
      { action: 'DECISION', label: '决定如何描述画面之外的人' },
      { action: 'CHAT', label: '向《步辇图》追问证据边界' },
      { action: 'GRAPH', label: '连接人物、事件与地点' },
    ],
    decision: {
      eyebrow: '展签校对',
      title: '文成公主不在画面里',
      context: '她与事件密切相关，却没有出现在画中。你要为画卷写下一句说明。',
      choices: [
        { id: 'state_absence', label: '明确写出“不在画中”', description: '再说明她如何经由事件与画面建立联系。', response: '空白没有被虚构图像填满，而被一条有依据的画外关系照亮。', impact: { truth: 2, connection: 1 } },
        { id: 'follow_envoy', label: '从禄东赞继续追索', description: '让使臣成为走出画面的线索。', response: '名册、会见与后续事件依次展开，画卷第一次有了边界之外的道路。', impact: { connection: 2 } },
        { id: 'keep_multiple_views', label: '并列图像与文献', description: '不让任何一种材料独自代表全部历史。', response: '两种证据并排放置。它们彼此补充，也彼此提醒对方的限度。', impact: { truth: 1, empathy: 1 } },
      ],
    },
  },
  yuan: {
    slug: 'yuan',
    gameTitle: '石壁上的六种声音',
    chapterMark: '共存之结',
    role: '云台营造场校勘助手',
    roleNote: '游戏原创角色 · 任务依据题刻空间、书写系统与校勘工作合理重构',
    mission: '找回一张位置标记脱落的拓片，用字形、版面和相邻区域完成一次有依据的校勘。',
    mechanic: '拓印辨识 · 空间校勘',
    duration: '约 18 分钟',
    artifact: '六体索引拓册',
    storyAnchor: {
      name: '居庸关云台六体文字题刻',
      kind: '元代建筑题刻',
      status: 'verified',
      statusLabel: '遗存已核验',
      boundary: '文字、语言、文本与人群身份分层记录，不能互相替代。',
    },
    openingLine: '看起来陌生，不等于毫无秩序。',
    objectives: [
      { action: 'ENTER', label: '接下错位拓片的校勘任务' },
      { action: 'INSPECT', label: '查验三处题刻区域', target: 3 },
      { action: 'LENS', label: '开启六体文字透镜' },
      { action: 'DECISION', label: '为错位拓片选择处理方式' },
      { action: 'CHAT', label: '向云台追问多种文字为何并置' },
      { action: 'GRAPH', label: '把文字、建筑与人群往来相连' },
    ],
    decision: {
      eyebrow: '校勘节点',
      title: '拓片的位置标记已经脱落',
      context: '字形看起来与一处题刻相似，但版面间距又指向另一区域。工期将近，你必须决定怎样处理。',
      choices: [
        { id: 'leave_pending', label: '暂列“位置待核”', description: '不强行归位，保留字形和版面两组证据。', response: '你在索引上留下一格空白。空白没有完成任务，却守住了证据的边界。', impact: { truth: 2 } },
        { id: 'compare_neighbours', label: '比对相邻题刻', description: '用空间关系继续查验，而不是只凭字形。', response: '灯光移向石壁边缘。相邻装饰和行距给出了新的连接。', impact: { truth: 1, connection: 2 } },
        { id: 'ask_other_scribes', label: '请不同校勘者会看', description: '承认单一视角有限，用协作换取判断。', response: '几种读法没有变成同一种声音，却共同排除了一个草率答案。', impact: { empathy: 1, connection: 1 } },
      ],
    },
  },
  qing: {
    slug: 'qing',
    gameTitle: '向东的长路',
    chapterMark: '归属之结',
    role: '东归专题展陈记录员',
    roleNote: '游戏原创角色 · 不把宫廷纪念物当作全部迁徙者的共同声音',
    mission: '以《万法归一图屏》为展柜主物，结合路线、人数与官方文本，判断它记录了东归的哪些面向，又遗漏了哪些声音。',
    mechanic: '迁徙追索 · 文物展陈',
    duration: '约 35 分钟',
    artifact: '多声部东归展柜档案',
    storyAnchor: {
      name: '《万法归一图屏》',
      kind: '清代绘画文物',
      status: 'verified',
      statusLabel: '主展品已核验',
      boundary: '它能呈现特定宫廷叙事及相关活动，不能替代迁徙者经历与多来源记录。',
    },
    openingLine: '一件宫廷纪念物，能替所有迁徙者讲述东归吗？',
    objectives: [
      { action: 'ENTER', label: '接下东归展柜策划任务' },
      { action: 'INSPECT', label: '查看三处路线、时间或文物证据', target: 3 },
      { action: 'LENS', label: '比较物证与记录的叙述位置' },
      { action: 'DECISION', label: '决定图屏如何进入东归展柜' },
      { action: 'CHAT', label: '追问东归动机与来源差异' },
      { action: 'GRAPH', label: '连接迁徙、接应与安置' },
    ],
    decision: {
      eyebrow: '展柜抉择',
      title: '主展品只能讲述东归的一部分',
      context: '《万法归一图屏》与宫廷活动相关，路线和人数记录却来自不同材料。若只展示图屏，观众可能把一种叙述误当成全部历史。',
      choices: [
        { id: 'record_range', label: '标明宫廷叙事视角', description: '保留图屏，同时写清它能证明的范围与叙述位置。', response: '图屏仍是主展品，但不再被要求替所有迁徙者说话。', impact: { truth: 2 } },
        { id: 'record_names', label: '补入个体与人数分歧', description: '让无法被图像覆盖的生命经验和统计差异进入展柜。', response: '宏大的纪念图像旁出现了名字、范围和问号，观众开始看见数字背后的人。', impact: { empathy: 2, truth: 1 } },
        { id: 'follow_route', label: '与路线、文本并列', description: '用多种材料说明迁徙、接应和纪念不是同一层面的证据。', response: '图屏、地图和文本彼此校正，东归不再被压缩成一幅静止画面。', impact: { connection: 2 } },
      ],
    },
  },
  contemporary: {
    slug: 'contemporary',
    gameTitle: '一针之后',
    chapterMark: '传承之结',
    role: '羌绣数字工坊实习生',
    roleNote: '当代身份 · 你需要为自己的素材选择和生成结果负责',
    mission: '为一件具体羌绣作品建立数字档案；只有创作者、来源、用途与授权边界完整时，才允许它进入 AI 辅助共创。',
    mechanic: '作品建档 · 授权共创',
    duration: '约 30 分钟',
    artifact: '羌绣作品溯源与授权记录',
    storyAnchor: {
      name: '待授权的具体羌绣作品',
      kind: '当代传承作品',
      status: 'rights',
      statusLabel: '授权前置',
      boundary: '真实作品与作者信息到位前，只能使用明确标注的演示素材，不能把通用纹样冒充传统原作。',
    },
    openingLine: '这件作品是谁做的？谁允许它进入数字共创？',
    objectives: [
      { action: 'ENTER', label: '领取具体作品建档任务' },
      { action: 'INSPECT', label: '核对三项技艺、用途或来源信息', target: 3 },
      { action: 'LENS', label: '查看作品与元素的权利状态' },
      { action: 'DECISION', label: '决定授权不足时是否继续生成' },
      { action: 'CHAT', label: '向工坊讲述者追问' },
      { action: 'GRAPH', label: '连接技艺、生活与传承实践' },
    ],
    decision: {
      eyebrow: '作品授权确认',
      title: '具体作品只取得了展示授权',
      context: '作品的作者与来源已经记录，但现有授权只允许网页展示，没有允许裁切、生成参考或模型训练。',
      choices: [
        { id: 'remove_asset', label: '仅保留作品档案', description: '允许展示与学习，但不把作品图像送入生成模型。', response: '作品仍被看见，它的权利边界也被同样清楚地看见。', impact: { truth: 2 } },
        { id: 'request_review', label: '暂停并请求创作者确认', description: '把生成用途、裁切范围和署名方式交给权利人决定。', response: '生成按钮暂时熄灭。等待不是流程中断，而是对创作者决定权的保留。', impact: { empathy: 2, connection: 1 } },
        { id: 'use_authorized', label: '改用已授权演示元素', description: '不替代真实作品，只完成明确标注的流程演示。', response: '共创继续进行，但结果清楚标明它使用的是演示素材，不是传统羌绣原作。', impact: { connection: 2, truth: 1 } },
      ],
    },
  },
}

export function getGameMeta(slug: string | undefined) {
  return slug && slug in GAME_CATALOG ? GAME_CATALOG[slug as ChapterSlug] : null
}
