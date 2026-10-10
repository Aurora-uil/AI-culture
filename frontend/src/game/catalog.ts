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
  protects: string
  cost: string
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
    gameTitle: '路从来不是一个人的',
    chapterMark: '相遇之结',
    role: '丝路关系追索者',
    roleNote: '游戏原创当代角色 · 从一次出使追索不同人群长期往来形成的历史网络',
    mission: '拆开“一个英雄开通一条路”的传奇，沿年代、地点、人物与物证寻找使者、向导、商旅、工匠、军民和定居者共同延续联系的证据。',
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
        { id: 'mark_uncertain', label: '删除直接归因', description: '明确写出目前没有证据证明它与张骞存在直接关系。', response: '展签删掉了一个醒目的传奇，却保住了文物与历史之间真正可证的距离。', protects: '人物与文物之间的证据边界', cost: '失去一句最容易传播的开场，需要重新建立吸引力', impact: { truth: 2 } },
        { id: 'ask_travellers', label: '改写为长期网络物证', description: '说明它呈现的是此后长期发展出的交通与文化联系。', response: '织锦不再被绑在一个人的旅程上，而被放回跨越多个世纪的联系网络。', protects: '长期网络中众多参与者的位置', cost: '叙事不再围绕单一英雄，解释成本更高', impact: { truth: 1, connection: 2 } },
        { id: 'follow_fast', label: '并列年代与出土信息', description: '让观众自己看见张骞出使与锦护膊之间的时间距离。', response: '年代、出土地点和证据边界被并排写下，展签留下了继续追问的入口。', protects: '观众依据材料自行判断的空间', cost: '阅读负担增加，也可能有人看见数字却没有理解关系', impact: { empathy: 1, truth: 1 } },
      ],
    },
  },
  'northern-wei': {
    slug: 'northern-wei',
    gameTitle: '一方石上，两座故乡',
    chapterMark: '交融之结',
    role: '迁洛墓志协作人',
    roleNote: '游戏原创角色 · 进入明确虚构的迁洛家庭证据剧场，不扮演可考历史人物',
    mission: '协助阿洛、陆萤与慧生完成一方迁洛墓志。沿姓名、籍贯、衣冠、迁都与石窟证据，决定一个人的平城记忆与洛阳新生活怎样同时被留下。',
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
    openingLine: '父亲生在平城，死在洛阳。墓石上的籍贯，该留下哪一座城？',
    objectives: [
      { action: 'ENTER', label: '接下墓志展签委托' },
      { action: 'INSPECT', label: '比较三组墓志、石窟或器物证据', target: 3 },
      { action: 'LENS', label: '区分个案、变化与未知' },
      { action: 'DECISION', label: '决定展签如何使用一方墓志' },
      { action: 'CHAT', label: '追问改革与迁都的边界' },
      { action: 'GRAPH', label: '找出延续、变化与并存' },
    ],
    decision: {
      eyebrow: '墓志落款',
      title: '空白石面只剩最后一行',
      context: '墓主生于平城、迁居洛阳，经历了姓名、籍贯与生活方式的变化。真实墓志、石窟、陶俑和制度材料能够提供背景，却不能替这个虚构家庭完成选择。你准备让后人先看见怎样的他？',
      choices: [
        { id: 'compare_first', label: '只刻能够确认的经历', description: '写下迁徙与新籍贯，把不能确认的家庭记忆留在石外。', response: '墓志没有替时代发言，墓主的迁徙与新生活被准确留下。', protects: '一方墓志能够证明的个人尺度', cost: '家人熟悉的旧称与生活细节没有进入石面', impact: { truth: 2 } },
        { id: 'workshop_together', label: '让两座城并列出现', description: '将平城来处、洛阳居处和变化中的生活并置记录。', response: '墓石没有要求墓主在两座城之间选边，两段生活共同构成一个完整的人。', protects: '迁徙前后关系与多种传统的并存', cost: '落款更复杂，无法给后人一个整齐的单一身份', impact: { connection: 2, truth: 1 } },
        { id: 'keep_family_mark', label: '留下家中的旧称', description: '标明这是亲属记忆，并与正式姓名同时保存。', response: '制度承认的名字与家人记得的名字同时留在石上。', protects: '具体家庭的记忆与情感来处', cost: '旧称只能作为个案记忆，不能推广为所有人的共同经验', impact: { empathy: 2 } },
      ],
    },
  },
  tang: {
    slug: 'tang',
    gameTitle: '画卷只画下相见',
    chapterMark: '交流之结',
    role: '长安客馆关系记录人',
    roleNote: '游戏原创角色 · 进入明确虚构的接见前夜证据剧场，不扮演唐太宗、禄东赞或文成公主',
    mission: '协助许照、桑波与青禾重写来使名册。分清画中人物、历史事件和画外关系，让一次相见通向翻译、往返与长期而复杂的唐蕃交往。',
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
    openingLine: '名册上只写“吐蕃使臣一人”。若连名字都没有，究竟是谁在与谁相见？',
    objectives: [
      { action: 'ENTER', label: '领取待核名册' },
      { action: 'INSPECT', label: '观察三处画面线索', target: 3 },
      { action: 'LENS', label: '切换画内与画外关系' },
      { action: 'DECISION', label: '决定如何描述画面之外的人' },
      { action: 'CHAT', label: '向《步辇图》追问证据边界' },
      { action: 'GRAPH', label: '连接人物、事件与地点' },
    ],
    decision: {
      eyebrow: '相见记录',
      title: '一幅画只能留下相见的一面',
      context: '禄东赞在画中，文成公主与松赞干布通过事件进入画外关系；一次接见又不能概括此后全部唐蕃历史。你准备怎样保存这次相见？',
      choices: [
        { id: 'state_absence', label: '写清谁没有被画下', description: '明确文成公主不在画中，再说明她如何经由事件进入关系。', response: '画面的空白没有被想象填满，真正的使臣往返与事件联系反而更清楚。', protects: '图像边界和画外人物的真实位置', cost: '开头不再直接呈现最熟悉的人物，需要观众继续追索', impact: { truth: 2, connection: 1 } },
        { id: 'follow_envoy', label: '沿来使继续走向画外', description: '从禄东赞、接见和相关事件展开长期关系。', response: '来使不再只是宫廷画面中的一个名字，而成为双方翻译、协商和往返的关系入口。', protects: '从画中人物通向长期交往的连续性', cost: '仍需提醒观众，精英使节不能代表所有参与交往的人', impact: { connection: 2 } },
        { id: 'keep_multiple_views', label: '并列画卷、事件与后世档案', description: '让三种材料彼此补充，也彼此限制。', response: '相见的画面、发生的事件和后世的作品认识共同存在，没有一种材料独占历史。', protects: '复杂关系与多来源解释空间', cost: '叙事不再只有一个简单结论，需要投入更多比较', impact: { truth: 1, empathy: 1 } },
      ],
    },
  },
  yuan: {
    slug: 'yuan',
    gameTitle: '石壁上的六种声音',
    chapterMark: '共存之结',
    role: '云台营造场校勘助手',
    roleNote: '游戏原创角色 · 任务依据题刻空间、书写系统与校勘工作合理重构',
    mission: '调查两份都曾被使用的校样，分清共同施工规则与文字自身结构，并为当代档案留下一个有限、可执行、有依据的判断。',
    mechanic: '版本校勘 · 规则分层 · 证据归档',
    duration: '约 30 分钟',
    artifact: '云台版本证据卷',
    storyAnchor: {
      name: '居庸关云台六体文字题刻',
      kind: '元代建筑题刻',
      status: 'verified',
      statusLabel: '遗存已核验',
      boundary: '文字、语言、文本与人群身份分层记录，不能互相替代。',
    },
    openingLine: '看起来陌生，不等于毫无秩序。',
    objectives: [
      { action: 'ENTER', label: '进入“双校样”证据剧场' },
      { action: 'INSPECT', label: '查验三项施工或文本证据', target: 3 },
      { action: 'LENS', label: '完成共同规则分层' },
      { action: 'DECISION', label: '给出可执行的施工判断' },
      { action: 'CHAT', label: '回应文字与人群的关系' },
      { action: 'GRAPH', label: '完成当代档案证据校验' },
    ],
    decision: {
      eyebrow: '施工判断',
      title: '今天到底按什么做',
      context: '两份校样可能属于不同阶段。第二版更尊重文本结构，第一版也建立了仍被沿用的共同施工标准。天黑以前，你必须给出一个能够承担后果的判断。',
      choices: [
        { id: 'over_simplify', label: '采用第二版，判定第一版错误', description: '施工可以继续，但把尚未证实的版本关系写成确定结论。', response: '施工判断基本可执行，历史叙述却过度确定。你后来发现，第一版仍保留着后续沿用的共同规范。', protects: '当日施工进度与现场执行效率', cost: '版本链被简化，旧版证据价值受损', impact: { connection: 1 } },
        { id: 'limited_confirm', label: '有限确认，并保留两份版本', description: '沿用共同标准，保留文本差异，也把前一版作为版本证据保存。', response: '旧版本没有因为不再使用而失去价值；共同标准与应被保留的差异同时进入档案。', protects: '可执行规则、文字差异与版本证据', cost: '现场需要承担额外保管和解释工作', impact: { truth: 2, connection: 2, empathy: 1 } },
        { id: 'evidence_insufficient', label: '证据不足，暂缓施工', description: '避免草率判断，但承担施工延误的现实成本。', response: '档案证据得到完整保存，工程却因此延后。承认未知并不意味着没有代价。', protects: '未经证实的版本关系不被写死', cost: '工期延误，已经可执行的环节也必须等待', impact: { truth: 2, empathy: 1 } },
      ],
    },
  },
  qing: {
    slug: 'qing',
    gameTitle: '向东的长路，有人接住',
    chapterMark: '归属之结',
    role: '伊犁接济簿协作人',
    roleNote: '游戏原创角色 · 在河岸第一夜协助归来者、书手与赶运人共同记录救急、核名和安置',
    mission: '在天黑前完成一份双页接济簿：让受损名册不再阻断眼前救急，分开迁徙、觐见与安置三条路线，并把四方调运与归来者自身行动接成新的生活。',
    mechanic: '河岸核名 · 接济调度 · 双页安置簿',
    duration: '约 35 分钟',
    artifact: '伊犁河岸双页接济簿',
    storyAnchor: {
      name: '《优恤土尔扈特部众记》与相关接济记录',
      kind: '清代文献与东归安置史料',
      status: 'verified',
      statusLabel: '接济史实已核验',
      boundary: '史料支持食衣、牲畜、物资调运与分地安居；不能据此虚构某户家庭的具体领取现场或私人感受。',
    },
    openingLine: '名册被雨水泡掉一个名字，眼前的人就该少领一碗粮吗？',
    objectives: [
      { action: 'ENTER', label: '接下河岸第一夜的核名与发放任务' },
      { action: 'INSPECT', label: '核对抵达、接济、路线与人数证据', target: 3 },
      { action: 'LENS', label: '完成双页接济簿的三层记录' },
      { action: 'DECISION', label: '决定今夜优先保护什么' },
      { action: 'CHAT', label: '追问东归、接济与共同生活' },
      { action: 'GRAPH', label: '连接四方调运与归来者重建行动' },
    ],
    decision: {
      eyebrow: '灯下定簿',
      title: '一盏灯的时间，救急、核名与安置无法同时做完',
      context: '第一批食衣必须尽快发下，受潮名册与失散者又需要逐户复核，牲畜和牧地关系到来日生活。你必须先保护一项，并把未完成的责任明确交给后来者。',
      choices: [
        { id: 'record_range', label: '先把食衣发到眼前每个人', description: '按在场丁口先完成救急，所有受损信息清楚标为待核。', response: '河岸这一夜少挨了许多饿；簿册也诚实留下“救急完成，安置未完”。', protects: '抵达者眼前的生命与基本需要', cost: '失散者复核、牲畜分配与牧地安排必须延到明日', impact: { empathy: 2 } },
        { id: 'record_names', label: '先把失散与受损名字核清', description: '邀请归来者逐户辨认，保留每一个待寻者与材料空白。', response: '许多名字没有从簿上消失，但发放速度变慢，必须为等候者安排补发。', protects: '个体不被总数与受损档案抹去', cost: '今夜发放更慢，寒饿中的人需要承受等待', impact: { truth: 1, empathy: 2 } },
        { id: 'follow_route', label: '建立今夜—明春双页责任链', description: '同步记录食衣、待核家口、牲畜状态、牧地需求和下一位责任人。', response: '归来者、书手和赶运人共同签下未完成事项，第一夜与来日生活被接在一起。', protects: '救急、核名、恢复生计和长久安置的连续关系', cost: '流程最复杂，需要更多人长期参与并持续复核', impact: { connection: 2, truth: 1, empathy: 1 } },
      ],
    },
  },
  contemporary: {
    slug: 'contemporary',
    gameTitle: '一针之后，二十四封回信',
    chapterMark: '传承之结',
    role: '跨地共创档案协调员',
    roleNote: '当代身份 · 复原灾后羌绣帮扶中的多方行动，并让今天的跨地学习形成真正的双向往返',
    mission: '从一只二〇〇八年灾后羌绣帮扶资料箱出发，辨清支援、本地生产、培训与市场之间的关系；再为二十四所学校设计“接针共创包”，让远方学生以自己的材料回应，而不是复制一种统一的民族风格。',
    mechanic: '关系复原 · 接针往返 · 回信地图',
    duration: '约 35—40 分钟',
    artifact: '灾后—当代关系图与二十四份接针档案',
    storyAnchor: {
      name: '灾后羌绣帮扶资料箱（剧情重建）',
      kind: '培训、生产、验收与销售关系的组合证据',
      status: 'verified',
      statusLabel: '史实关系 · 情节重建',
      boundary: '灾后保护、培训就业和市场连接有公开资料依据；资料箱、角色、学校与回信均为剧情虚构，不把任何个人写成整个民族的代表。',
    },
    openingLine: '如果只写“外界援助挽救了羌绣”，本地妇女的针、订单、授艺和十几年后的新连接去了哪里？',
    objectives: [
      { action: 'ENTER', label: '打开灾后羌绣帮扶资料箱' },
      { action: 'INSPECT', label: '辨认支援、本地主体行动与协作连接', target: 3 },
      { action: 'LENS', label: '比较十几年后不同来路的学习者与角色' },
      { action: 'DECISION', label: '决定二十四只接针包如何寄出并被接回' },
      { action: 'CHAT', label: '追问同心为何不是同样' },
      { action: 'GRAPH', label: '连接灾后重建、当代学习与跨地回信' },
    ],
    decision: {
      eyebrow: '接针项目寄出决定',
      title: '二十四所学校已准备收件，工坊却只有八位创作者完成材料',
      context: '统一印刷可以准时铺满二十四校，却会抹掉创作者差异，也没人能接住大量回件。你必须在准确叙述、平等发问与小规模深度往返之间选择，并把延期、规模和回应责任如实告诉所有参与者。',
      choices: [
        { id: 'remove_asset', label: '先做关系档案展，不寄材料', description: '完整讲清灾后到今天的支援、本地行动与协作链，让学生先观看和提问。', response: '二十四校在线参观并留下问题，但没有作品回到工坊；本轮只能记录为“看见与发问”，不能称为共同创作。', protects: '历史叙述的准确与创作者当前回应能力', cost: '远方参与停在观看端，双向往返尚未开始', impact: { truth: 2, empathy: 1 } },
        { id: 'request_review', label: '先寄问题卡，一个月后结对', description: '让学生先提出真正关心的问题，再由创作者选择愿意回应的对象与方式。', response: '项目延期一个月，创作者不再被平台分配任务；二十四条关系从学生发问和创作者自主选择开始。', protects: '双方定义交流起点与自主进入关系的权利', cost: '失去整齐的首发效果，也必须承担延期沟通', impact: { empathy: 2, connection: 1 } },
        { id: 'use_authorized', label: '先做八组一对一，十六校延期', description: '只寄出八份完整起针包，保证每位创作者有能力接住一份回信并再次回应。', response: '八组完成至少一次往返，其余学校看到真实进度与等待原因；关系图较小，却没有用复制品冒充连接。', protects: '具体的人、具体的回应与可持续的关系深度', cost: '参与规模缩小，十六所学校必须等待下一轮', impact: { connection: 2, truth: 1, empathy: 1 } },
      ],
    },
  },
}

export function getGameMeta(slug: string | undefined) {
  return slug && slug in GAME_CATALOG ? GAME_CATALOG[slug as ChapterSlug] : null
}
