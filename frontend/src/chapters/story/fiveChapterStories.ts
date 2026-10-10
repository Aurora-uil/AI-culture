import type { ChapterSlug } from '@/types'

export type StoryChapterSlug = Exclude<ChapterSlug, 'yuan'>

export type StoryTone = 'normal' | 'question' | 'warning' | 'resolve' | 'quiet'

export interface StoryDialogueLine {
  speaker: string
  role: string
  text: string
  side?: 'left' | 'right'
  tone?: StoryTone
}

export interface StoryEvidenceCard {
  id: string
  label: string
  detail: string
  stamp?: string
  correctBin?: string
}

export interface StoryOption {
  id: string
  label: string
  detail: string
}

export interface StoryBin {
  id: string
  label: string
  note: string
}

export interface StorySlot {
  id: string
  label: string
  prompt: string
  options: StoryOption[]
  correctId: string
}

export type StoryChallenge =
  | {
      kind: 'inspect'
      title: string
      instruction: string
      cards: StoryEvidenceCard[]
      success: string
    }
  | {
      kind: 'single' | 'multi'
      title: string
      instruction: string
      options: StoryOption[]
      correctIds: string[]
      success: string
      retry: string
    }
  | {
      kind: 'classify'
      title: string
      instruction: string
      cards: StoryEvidenceCard[]
      bins: StoryBin[]
      success: string
      retry: string
    }
  | {
      kind: 'assemble'
      title: string
      instruction: string
      slots: StorySlot[]
      success: string
      retry: string
    }
  | {
      kind: 'final'
      title: string
      instruction: string
    }

export interface StoryScene {
  id: string
  title: string
  place: string
  objective: string
  layer: '史料确证' | '研究解释' | '合理重建' | '剧情虚构' | '当代情境'
  layerNote: string
  background: string
  position?: string
  framing: string
  motif: string
  dialogue: StoryDialogueLine[]
  branchDialogue?: Partial<Record<string, StoryDialogueLine[]>>
  challenge?: StoryChallenge
  evidenceId?: string
  marksLens?: boolean
}

export interface StoryCharacter {
  name: string
  role: string
  mark: string
  color: string
}

export interface StoryAct {
  id: 'act-1' | 'act-2' | 'act-3' | 'act-4' | 'act-5'
  label: string
  title: string
  sceneIds: [string, string]
  dramaticQuestion: string
  stateGoal: string
}

export interface StoryChapter {
  slug: StoryChapterSlug
  archiveTitle: string
  subtitle: string
  themeQuestion: string
  playerRole: string
  premise: string
  boundary: string
  acts: StoryAct[]
  recap: {
    confirmed: string
    interpretation: string
    unknown: string
    fiction: string
  }
  accent: string
  accentSoft: string
  ink: string
  characters: StoryCharacter[]
  scenes: StoryScene[]
}

const han: StoryChapter = {
  slug: 'han',
  archiveTitle: '路从来不是一个人的',
  subtitle: '从一次出使，看见几百年间不断发生的相遇',
  themeQuestion: '一条路如何由不同人群在长期往来中共同形成？',
  playerRole: '丝路关系追索者：校勘一张错误展签，把单一英雄传奇改写成有证据、有众人也有时间纵深的关系网络。',
  premise: '张骞出使与尼雅出土的锦护膊相隔数百年，却常被压缩成“一个英雄开通一条路、带回一件文物”的传奇。本章要追问的不是谁独自创造了丝绸之路，而是不同地区、不同人群如何在一代代出使、引路、贸易、迁徙与定居中，把一次相遇延续成长期联系。',
  boundary: '张骞出使是重要历史节点；锦护膊是后世长期交通网络的物证。两者可以进入同一章，但现有资料不支持直接人物—文物关系。',
  acts: [
    { id: 'act-1', label: '第一幕', title: '拆开传奇', sceneIds: ['00', '01'], dramaticQuestion: '张骞出使与后世锦护膊能否被写成同一件事？', stateGoal: '确认年代距离，拒绝未经证实的直接归因。' },
    { id: 'act-2', label: '第二幕', title: '让道路显影', sceneIds: ['02', '03'], dramaticQuestion: '一次出使怎样进入跨越数百年的交通史？', stateGoal: '区分人物行程、长期网络与文物出土语境。' },
    { id: 'act-3', label: '第三幕', title: '把众人放回路上', sceneIds: ['04', '05'], dramaticQuestion: '除了英雄，还有谁让联系持续发生？', stateGoal: '识别多类参与者，并为关系强度分级。' },
    { id: 'act-4', label: '第四幕', title: '承担展签选择', sceneIds: ['06', '07'], dramaticQuestion: '短展签如何同时保留事实、联系与未知？', stateGoal: '组装结论并作出有代价的核心选择。' },
    { id: 'act-5', label: '第五幕', title: '路重新有了人', sceneIds: ['08', '09'], dramaticQuestion: '民族交往为何不是一个人的功绩？', stateGoal: '查看选择后果，把道路理解为共同生活的历史。' },
  ],
  recap: {
    confirmed: '张骞出使是重要节点；锦护膊出土于尼雅，其断代与出土信息必须独立说明。',
    interpretation: '二者可共同进入长期交通网络史，说明跨区域联系由不同年代、地区与人群持续形成。',
    unknown: '现有材料不能证明张骞与这件锦护膊存在直接接触或携带关系。',
    fiction: '林岫、邵远、何骁及展签校勘任务为当代剧情设计。',
  },
  accent: '#bb6f42',
  accentSoft: '#e6c59d',
  ink: '#172f31',
  characters: [
    { name: '林岫', role: '专题展主笔 · 虚构角色', mark: '岫', color: '#b96543' },
    { name: '邵远', role: '路线研究员 · 虚构角色', mark: '远', color: '#4b7b78' },
    { name: '何骁', role: '展陈制作负责人 · 虚构角色', mark: '骁', color: '#876843' },
    { name: '档案助手', role: '证据提示系统', mark: '证', color: '#b69a55' },
  ],
  scenes: [
    {
      id: '00', title: '一个人能走出一条路吗', place: '丝路历史网络 · 起点', objective: '从英雄传奇进入多民族长期交往的历史',
      layer: '当代情境', layerNote: '人物对话为叙事设计；所讨论的出使、文物与长期交通网络均受证据边界约束。',
      background: '/assets/han/han-route-scene-v2.png', position: '60% center', framing: 'label-desk', motif: 'broken-caption',
      dialogue: [
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '我小时候听到的故事很简单：张骞向西走了一趟，丝绸之路便从他脚下出现了。可一条延续几百年的路，真能只属于一个人吗？', side: 'right', tone: 'question' },
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '我们总想给历史找一个开门的人，好像门一开，后来的人只需沿路前行。于是连几百年后出现在尼雅的锦护膊，也被塞进了张骞的行囊。', side: 'left' },
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '张骞的出使当然重要。但真正让道路延续的，还有辨认水源的向导、翻译语言的译者、交换货物的商旅、守护交通的军民，以及在沿线生活的一代代人。', side: 'right' },
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '那我们就从这句过于顺畅的传奇出发，把被一个名字遮住的人重新放回路上。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'inspect', title: '拆开展签', instruction: '依次查验句子里被强行缝合的三段事实。',
        cards: [
          { id: 'mission_138', label: '公元前138年', detail: '汉武帝派张骞第一次出使西域。', stamp: '人物事件' },
          { id: 'niya_1995', label: '1995年 · 尼雅M8', detail: '锦护膊在尼雅遗址1号墓地M8出土。', stamp: '考古出土' },
          { id: 'direct_relation', label: '“张骞带回”', detail: '现有资料不支持张骞与这件锦护膊存在直接关系。', stamp: '关系不成立' },
        ],
        success: '错误不在任一事实本身，而在它们被写成了直接因果。',
      }, evidenceId: 'han_caption_split',
    },
    {
      id: '01', title: '两只时间盒', place: '年代比对室', objective: '让年代先于故事发言',
      layer: '史料确证', layerNote: '出使年代、出土信息与“汉晋”断代表述来自本章已审核内容。',
      background: '/assets/han/han-caravan-v1.png', position: '46% center', framing: 'time-boxes', motif: 'double-date',
      dialogue: [
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '这张卡是公元前138年，写张骞第一次出使；那张卡写“汉晋”，跨度一直到公元420年。你把它们扣在一起，中间的时间就被藏掉了。', side: 'right' },
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '可“汉晋”里确实有汉。我要是只写“可能有关”，是不是还站得住？', side: 'left', tone: 'question' },
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '年代能让两件事进入同一段交通史，不能替你认出谁拿过它。', side: 'right' },
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '我听懂了：不是完全无关，是不能写成同一只手。那新展签就得把这层距离说清。', side: 'left', tone: 'quiet' },
      ],
      challenge: {
        kind: 'single', title: '年代能支持到哪里？', instruction: '选择这组年代证据能够支持的最稳妥结论。',
        options: [
          { id: 'direct', label: '张骞携带过锦护膊', detail: '把宽泛年代重叠误写成直接关系。' },
          { id: 'network', label: '两者可进入同一段长期交通史', detail: '人物事件与后世物证可在网络层面关联，但不能直连。' },
          { id: 'same_year', label: '两者发生在同一年', detail: '现有断代与出土资料不支持。' },
        ], correctIds: ['network'], success: '你保留了联系，也保留了时间距离。', retry: '年代相容只能建立讨论背景，不能自动生成直接人物关系。',
      }, evidenceId: 'han_chronology_gap',
    },
    {
      id: '02', title: '一条路，两张图', place: '历史网络投影台', objective: '区分出使节点与长期交通网络',
      layer: '史料确证', layerNote: '地图只表达节点与廊道层级，不是张骞逐日路线或现代导航轨迹。',
      background: '/assets/han/han-route-scene-v2.png', position: '52% center', framing: 'dual-route', motif: 'route-layers',
      dialogue: [
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '路线动画也得改。现在一根红线从长安直扎尼雅，像导航记录。重做要四个小时。', side: 'left' },
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '那就拆成两层：一层只标出使相关节点，一层标后来长期形成的交通网络。', side: 'right' },
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '尼雅只在第二层。它仍在这段历史里，却不再冒充张骞的脚印。', side: 'left', tone: 'quiet' },
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '能做。但你们得告诉我，哪些点属于人物行程，哪些属于后来的路网。别让我替史料猜。', side: 'right' },
      ],
      challenge: {
        kind: 'classify', title: '双层路网', instruction: '为每个节点选择证据支持的路线层。',
        bins: [
          { id: 'direct', label: '出使相关节点', note: '与张骞出使直接相关，但仍非逐日路线。' },
          { id: 'longterm', label: '长期网络节点', note: '进入后世不断发展的交通网络。' },
          { id: 'both', label: '两层都可见', note: '同时出现在人物事件与网络视图。' },
        ],
        cards: [
          { id: 'changan', label: '长安', detail: '两次出使均从长安出发。', correctBin: 'both' },
          { id: 'western_regions', label: '西域', detail: '人物事件与长期网络都涉及的地域概念。', correctBin: 'both' },
          { id: 'niya', label: '尼雅遗址', detail: '丝路沿线重要考古遗址。', correctBin: 'longterm' },
          { id: 'zhangqian_line', label: '长安—西域示意连接', detail: '仅标示出使相关节点，不表示真实行进轨迹。', correctBin: 'direct' },
        ], success: '同一画布出现了两种尺度：一次出使，与跨越多个世纪的网络。', retry: '注意“人物到过”与“网络后来连接”不是同一种关系。',
      }, evidenceId: 'han_dual_route', marksLens: true,
    },
    {
      id: '03', title: '尼雅不是道具', place: '文物恒湿展柜', objective: '从出土语境认识锦护膊',
      layer: '史料确证', layerNote: '文物出土地点、时间与断代均来自本章审核资料。',
      background: '/assets/han/han-caravan-v1.png', position: '72% center', framing: 'artifact-case', motif: 'woven-grid',
      dialogue: [
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '拿掉张骞，这件锦在观众眼里会不会只剩一串编号？', side: 'left', tone: 'question' },
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '1995年、尼雅遗址一号墓地M8、汉晋织锦——它有自己的来处。为什么一定要借一个名人才算有故事？', side: 'right' },
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '因为编号不会自己说话。可要是让出土地、时间跨度和织锦本身说话，我能把展柜做成三层，不必硬塞一个主人。', side: 'left', tone: 'quiet' },
      ],
      challenge: {
        kind: 'inspect', title: '文物自身的档案', instruction: '查验文物无需依附名人也能成立的证据。',
        cards: [
          { id: 'findspot', label: '出土地', detail: '新疆民丰地区尼雅遗址1号墓地M8。', stamp: '地点' },
          { id: 'dating', label: '断代标签', detail: '公开展览资料标为“汉晋（公元前202—公元420年）”。', stamp: '年代范围' },
          { id: 'material', label: '物质遗存', detail: '它让抽象的长距离交通与真实丝织品遗存发生联系。', stamp: '物证' },
        ], success: '文物不再是人物传奇的配图，而成为长期网络的独立证人。',
      }, evidenceId: 'han_niya_context',
    },
    {
      id: '04', title: '一个人的行囊装不下网络', place: '物品流动墙', objective: '停止把所有传播归给一个人',
      layer: '史料确证', layerNote: '物品流动以类别呈现，不绑定唯一原产地、运输者或单一路线。',
      background: '/assets/han/han-route-scene-v2.png', position: '34% center', framing: 'flow-wall', motif: 'many-hands',
      dialogue: [
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '我承认那只“张骞行囊”装得太满。可拿掉它，丝织品、马匹、植物、器物全散了，观众抓什么？', side: 'left' },
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '抓住“很多人走了很久”。使者、商旅、随行者、工匠和定居者，不该都缩成一个人的功劳。', side: 'right' },
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '那我不画行囊，改画接力。每件东西只标我们知道的范围，不给它指定唯一搬运人。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'multi', title: '哪些表述可以保留？', instruction: '选择所有没有把长期网络压缩成个人功劳的表述。',
        options: [
          { id: 'many_people', label: '人员流动包含多类参与者', detail: '不把全部交流等同于官方使节。' },
          { id: 'one_creator', label: '张骞一人创造了丝绸之路', detail: '把长期变化的网络压缩成单一创始人。' },
          { id: 'changing_network', label: '路线与联系在长期中变化', detail: '承认网络不是一条固定道路。' },
          { id: 'all_species', label: '所有西域物种都由张骞带入', detail: '现有资料不支持。' },
        ], correctIds: ['many_people', 'changing_network'], success: '人物的重要性被保留，但不再吞没无数匿名参与者。', retry: '请排除“一人创造全部网络”和“所有物种都归于一人”的过度归因。',
      }, evidenceId: 'han_network_actors',
    },
    {
      id: '05', title: '关系不是只有“有”或“没有”', place: '证据刻度台', objective: '为关系标注强度',
      layer: '当代情境', layerNote: '关系刻度是本项目的证据教学设计，不是历史时期原有分类。',
      background: '/assets/han/han-caravan-v1.png', position: '54% center', framing: 'relation-scale', motif: 'relation-ruler',
      dialogue: [
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '我最怕那句“没有直接证据”。写上去像是我们折腾一晚，最后只告诉观众什么都不知道。', side: 'left' },
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '我们知道的并不少：出使是真的，尼雅的物证是真的，长期网络也是真的。错的是把三种关系都写成“他带回”。', side: 'right' },
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '那就别只写“有”或“没有”。给关系加刻度，让观众看见哪条线硬，哪条线远，哪条线不能画。', side: 'left' },
      ],
      challenge: {
        kind: 'classify', title: '关系强度刻度', instruction: '判断每条关系是直接支持、长期联系，还是现有证据不支持。',
        bins: [
          { id: 'direct', label: '直接支持', note: '来源明确支持主体与事件。' },
          { id: 'network', label: '长期联系', note: '可在网络层面建立关联。' },
          { id: 'unsupported', label: '不支持直连', note: '不能写成直接人物关系。' },
        ],
        cards: [
          { id: 'mission', label: '张骞—第一次出使', detail: '史料支持人物参与。', correctBin: 'direct' },
          { id: 'niya_network', label: '尼雅—丝路交通网络', detail: '遗址可进入长期网络讨论。', correctBin: 'network' },
          { id: 'brocade_person', label: '张骞—锦护膊', detail: '没有直接关系证据。', correctBin: 'unsupported' },
        ], success: '“不直连”没有切断历史，反而让真正的连接显得更清楚。', retry: '先问来源支持的是人物事件、网络关系，还是仅仅同章出现。',
      }, evidenceId: 'han_relation_scale',
    },
    {
      id: '06', title: '三句话的展签', place: '展签重写桌', objective: '组合事实、联系与未知',
      layer: '当代情境', layerNote: '展签为玩家生成的策展文本，不是历史原文。',
      background: '/assets/han/han-route-scene-v2.png', position: '64% center', framing: 'caption-compose', motif: 'three-lines',
      dialogue: [
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '如果只能留下三句话，我不想再让观众只记住一个人。我想让他们看见：一件织锦抵达尼雅以前，路上已经有无数次问路、翻译、交换与停留。', side: 'left' },
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '第一行写文物自己能证明的；第二行写它和长期路网怎样相连；第三行把不能直连张骞说清。', side: 'right' },
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '事实、联系、未知。三行可以。但它得像一句邀请，不是三条免责声明。', side: 'left', tone: 'question' },
      ],
      challenge: {
        kind: 'assemble', title: '重写展签', instruction: '每一层选择一条有证据边界的句子。',
        slots: [
          { id: 'fact', label: '确认事实', prompt: '这件文物可以确定什么？', correctId: 'f_good', options: [
            { id: 'f_good', label: '1995年出土于尼雅遗址M8', detail: '明确的考古出土信息。' },
            { id: 'f_bad', label: '由张骞从西域带回', detail: '没有直接证据支持。' },
          ] },
          { id: 'link', label: '形成联系', prompt: '它如何进入本章？', correctId: 'l_good', options: [
            { id: 'l_good', label: '作为后世长期交通网络中的物质遗存', detail: '保留跨世纪联系。' },
            { id: 'l_bad', label: '证明张骞走过尼雅并携带此物', detail: '把网络关系写成个人行程。' },
          ] },
          { id: 'unknown', label: '保留未知', prompt: '必须说明什么？', correctId: 'u_good', options: [
            { id: 'u_good', label: '现有资料不支持它与张骞存在直接关系', detail: '明确关系边界。' },
            { id: 'u_bad', label: '细节虽缺失，但一定与张骞有关', detail: '用推测填补证据空白。' },
          ] },
        ], success: '事实、联系与未知并列出现，展签终于不再靠误认推动。', retry: '三层都必须守住：事实可核、联系有限、未知明确。',
      }, evidenceId: 'han_caption_draft', marksLens: true,
    },
    {
      id: '07', title: '应该记住谁', place: '历史网络中央', objective: '决定用一个英雄还是共同往来解释道路',
      layer: '当代情境', layerNote: '人物选择为互动叙事；历史解释必须区分人物事件、长期网络与文物关系。',
      background: '/assets/han/han-caravan-v1.png', position: '42% center', framing: 'decision-door', motif: 'red-pencil',
      dialogue: [
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '如果把张骞写成唯一的开路者，故事会很完整；可那些真正让道路活了几百年的人，就又一次从地图上消失了。', side: 'right' },
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '我想保留张骞的勇气，也保留后来者的位置。一次出使打开了新的政治联系，无数次往来才让陌生地区逐渐进入彼此的生活。', side: 'left', tone: 'question' },
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '现在请选择观众最终看见的是“一人的功绩”，还是“许多人共同延续的关系”。', side: 'right' },
      ],
      challenge: { kind: 'final', title: '展签定稿', instruction: '选择你愿意署名、也愿意接受追问的记录方式。' },
    },
    {
      id: '08', title: '路上重新有了人', place: '跨世纪交通网络', objective: '看见一次出使如何被后来者延续成共同历史',
      layer: '剧情虚构', layerNote: '不同观众反应为剧情化反馈，不代表真实调查数据。',
      background: '/assets/han/han-route-scene-v2.png', position: '57% center', framing: 'opening-light', motif: 'network-glow',
      dialogue: [
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '地图上的红线慢慢散开。长安、西域与尼雅之间，不再只有一个人的脚印，而出现了使者、向导、商旅、工匠、军民与定居者留下的层层联系。', side: 'right', tone: 'quiet' },
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '观众终于问出了这章真正的问题：不同语言、不同生活方式的人，最初怎样交换一件货物，后来又怎样开始理解彼此？', side: 'left' },
      ],
      branchDialogue: {
        mark_uncertain: [
          { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '最醒目的那句话被删掉了。有人停下来问：那这件锦为什么仍在这里？', side: 'right' },
          { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '因为它见证的不是一人的占有，而是不同人群之间已经能够发生交换、传递与理解。', side: 'left', tone: 'resolve' },
        ],
        ask_travellers: [
          { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '观众的目光从一个人的名字，移动到几百年间不断扩展的路网。', side: 'right' },
          { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '人物没有变小，历史变大了；道路也不再只是地理通道，而成为不同人群持续建立关系的空间。', side: 'left', tone: 'resolve' },
        ],
        follow_fast: [
          { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '两张年代卡并排留在展柜旁。有人先看数字，再读展签。', side: 'right' },
          { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '你保留了时间的距离，也让观众看见：民族之间的联系从来不是瞬间完成，而是在漫长往来中一层层累积。', side: 'left', tone: 'resolve' },
        ],
      },
    },
    {
      id: '09', title: '路从来不是一个人的', place: '同心回望 · 丝路关系图', objective: '理解道路如何连接不同人群的生活',
      layer: '研究解释', layerNote: '本幕为基于全章证据的历史解释，不把现代概念写成汉代人物的自觉表达。',
      background: '/assets/han/han-route-scene-v2.png', position: '50% center', framing: 'network-coda', motif: 'many-hands',
      dialogue: [
        { speaker: '邵远', role: '路线研究员 · 虚构角色', text: '历史上没有谁在某一天修成了一条完整的“丝绸之路”。它是在反复出发、相遇、翻译、交换和共同生活中逐渐形成的。', side: 'right' },
        { speaker: '何骁', role: '展陈制作负责人 · 虚构角色', text: '沿线的人并没有因此变得相同。他们带着各自的语言、技艺和习俗，却开始出现在彼此的物品、知识与日常生活里。', side: 'left' },
        { speaker: '林岫', role: '专题展主笔 · 虚构角色', text: '所以张骞的意义，不是独自完成一切；锦护膊的意义，也不是替某个英雄作证。它们共同说明：联系一旦建立，就会被后来无数人继续拓宽。', side: 'right', tone: 'quiet' },
        { speaker: '档案助手', role: '证据提示系统', text: '本章记录：各民族之间的共同历史，不只由重大事件写成，也由一代代普通人在道路上的往来与相互需要写成。', side: 'left', tone: 'resolve' },
      ],
    },
  ],
}

const northernWei: StoryChapter = {
  slug: 'northern-wei',
  archiveTitle: '一方石上，两座故乡',
  subtitle: '一个迁洛家庭，怎样把平城记忆带进新的共同生活',
  themeQuestion: '迁徙与交融，是抹去旧来处，还是在新关系中重新组合生活？',
  playerRole: '迁洛墓志协作人：与一个虚构家庭共同落刀，在真实证据边界内保存平城来处、洛阳生活与变化中的关系。',
  premise: '迁都后的洛阳，一户从平城迁来的家庭要为逝去的长者刻写墓志。石上该写旧日来处，还是新的籍贯？该留下家中仍沿用的称呼，还是制度规定的新姓？来自平城旧作坊的学徒、洛阳石工之女与墓主之子必须共同完成这方石头。本章以明确虚构的家庭故事承接真实证据，追问交融是否意味着只能保留一种来处。',
  boundary: '阿洛、陆萤、慧生及其家庭、作坊经历均为剧情虚构；元羽墓志、迁都时间差异、云冈—龙门对照、制度与服饰变化为史实锚点。虚构个案不代表全部北魏社会。',
  acts: [
    { id: 'act-1', label: '第一幕', title: '石面为何空着', sceneIds: ['00', '01'], dramaticQuestion: '一方墓石能够替谁说话？', stateGoal: '建立家庭冲突，并限定墓志只能先说明具体个人。' },
    { id: 'act-2', label: '第二幕', title: '两座城一起抵达', sceneIds: ['02', '03'], dramaticQuestion: '迁都与营造变化是瞬间替代，还是长期过程？', stateGoal: '比较迁徙过程与云冈—龙门之间的延续和改变。' },
    { id: 'act-3', label: '第三幕', title: '制度走进家门', sceneIds: ['04', '05'], dramaticQuestion: '衣冠、姓名和诏令能否概括一个人的全部身份？', stateGoal: '分开制度要求、公共表达与家庭生活。' },
    { id: 'act-4', label: '第四幕', title: '最后一刀', sceneIds: ['06', '07'], dramaticQuestion: '怎样写下变化而不把来处抹掉？', stateGoal: '用采用、改造、并存、延续组织证据并承担落款选择。' },
    { id: 'act-5', label: '第五幕', title: '石上两座故乡', sceneIds: ['08', '09'], dramaticQuestion: '交融为何不是变成同一种人？', stateGoal: '查看家庭后果，理解新共同生活如何容纳多重来处。' },
  ],
  recap: {
    confirmed: '北魏迁都、相关制度变化、元羽墓志以及云冈—龙门材料构成本章史实锚点。',
    interpretation: '迁徙后的变化并不同步，采用、改造、并存与延续可以同时发生。',
    unknown: '单件墓志或单类图像不能说明所有迁洛者的生活、身份与情感选择。',
    fiction: '阿洛、陆萤、慧生、迁洛家庭及墓志作坊冲突均为剧情虚构。',
  },
  accent: '#7e7660', accentSoft: '#cdbd99', ink: '#222d2d',
  characters: [
    { name: '阿洛', role: '迁洛家庭青年 · 虚构角色', mark: '洛', color: '#796a57' },
    { name: '陆萤', role: '洛阳石工之女 · 虚构角色', mark: '萤', color: '#557778' },
    { name: '慧生', role: '平城旧作坊学徒 · 虚构角色', mark: '慧', color: '#8b7350' },
    { name: '证据尺', role: '范围校验系统', mark: '尺', color: '#b29351' },
  ],
  scenes: [
    {
      id: '00', title: '空白墓石', place: '迁都后的洛阳 · 城南石作坊', objective: '决定一个人的两处来路能否同时被写下',
      layer: '剧情虚构', layerNote: '石作坊、迁洛家庭及人物对白均为虚构，用于承接北魏迁都与社会变化的史实证据。',
      background: '/assets/wei/yungang-cave20-original.jpg', position: 'center', framing: 'headline-wall', motif: 'stone-type',
      dialogue: [
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '石面只够刻一行籍贯。你父亲生在平城，死在洛阳。阿洛，你要我把哪座城留下？', side: 'right', tone: 'question' },
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '在平城，他教我认北面的山；到洛阳，他又亲手垒起新家的灶。只写一处，另一半日子就像没有活过。', side: 'left' },
        { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '官府要的是能登记的名字，家人要的是认得出的那个人。墓石若想替整个时代下结论，会太重；若连一个人的两处来路都容不下，又太轻。', side: 'right', tone: 'warning' },
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '那我们先不急着落刀。把姓名、籍贯、衣冠和他在两座城里的生活一层层问清，再决定这方石头怎样容下一个没有把过去丢掉的新洛阳人。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'inspect', title: '石面能写到哪里', instruction: '查验一方墓石从个人走向时代时必须区分的三重尺度。',
        cards: [
          { id: 'individual', label: '墓主个案', detail: '墓志记录元羽的身份、生平及相关制度背景。', stamp: '可直接讨论' },
          { id: 'institution', label: '制度变化', detail: '姓氏、服饰、朝堂语言等有各自范围与推行过程。', stamp: '需多来源' },
          { id: 'society', label: '整个社会', detail: '不同群体、场景与时期中的采用、改造、并存并不同步。', stamp: '不可一概而论' },
        ], success: '墓石可以连接“个案—制度—社会”，却不能跳过证据让一个人代表所有人。',
      }, evidenceId: 'wei_scope_split',
    },
    {
      id: '01', title: '墓志先认识一个人', place: '证据叠影 · 元羽墓志', objective: '借真实墓志确认个案能够说明什么',
      layer: '史料确证', layerNote: '元羽墓志为真实史料锚点；剧情家庭不与元羽建立虚构关系。',
      background: '/assets/wei/longmen-guyang-original.jpg', position: '44% center', framing: 'epitaph-case', motif: 'single-name',
      dialogue: [
        { speaker: '证据尺', role: '范围校验系统', text: '证据叠影开启：元羽墓志留下姓名、身份、生平、籍贯及相关制度背景。它能证明一个具体生命，却不能替所有迁洛者说话。', side: 'right' },
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '原来把父亲写得具体，不是把故事写小。先让人看见他是谁，才不会把他的迁徙拿去代表所有人的命运。', side: 'left', tone: 'quiet' },
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '我们可以借真实墓志学习怎样尊重一个人的尺度，却不能照抄别人的人生。你的父亲要从自己的名字和经历开始。', side: 'right' },
      ],
      challenge: {
        kind: 'multi', title: '墓志能说什么？', instruction: '选择所有没有超出墓主个案尺度的表述。',
        options: [
          { id: 'identity', label: '墓主身份与生平线索', detail: '墓志的直接记录对象。' },
          { id: 'institution', label: '相关姓氏与籍贯书写背景', detail: '可与制度材料交叉核对。' },
          { id: 'everyone', label: '所有人的生活方式都同步改变', detail: '单件墓志无法支持。' },
          { id: 'complete', label: '北魏文化被一种传统完全取代', detail: '既超出墓志范围，也过度简化。' },
        ], correctIds: ['identity', 'institution'], success: '墓志回到一个具体生命的尺度，因此更可信，也更有分量。', retry: '请排除“所有人同步改变”和“完全取代”的总体结论。',
      }, evidenceId: 'wei_epitaph_scope',
    },
    {
      id: '02', title: '没有人在同一天迁完一座城', place: '平城至洛阳 · 迁徙叠影', objective: '把迁都年份还原成许多家庭经历的过程',
      layer: '史料确证', layerNote: '不同来源采用493或494的表述，本章保留差异并将迁都写作过程。',
      background: '/assets/wei/yungang-cave20-original.jpg', position: '62% center', framing: 'date-split', motif: 'two-dates',
      dialogue: [
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '有人说迁都是太和十七年，有人记作太和十八年。可我家先送走工具，后来才接老人，最后一车旧物又隔了几个月。哪一天才算离开？', side: 'left', tone: 'question' },
        { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '朝廷的决定有日期，整座城的迁移却由许多不同的脚步完成。493和494，也许记录的是决策、迁移与建置的不同阶段。', side: 'right' },
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '对洛阳人来说，迁都也不是城门一开就结束。新来的人要找住处、谋生、学会城里的规矩；原来的人也要学着同他们一起生活。', side: 'left' },
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '那就写“493至494年前后”。不是含糊，而是承认一项国事怎样落到千家万户，变成漫长的共同适应。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'single', title: '时间轴定稿', instruction: '选择合适的时间表述。',
        options: [
          { id: '493', label: '493年一天之内完成迁都', detail: '过度精确，也把过程压成单点。' },
          { id: '494', label: '只有494年一种正确答案', detail: '抹去来源差异。' },
          { id: 'process', label: '493—494年前后完成的过程', detail: '并列来源差异，强调迁都不是瞬时事件。' },
        ], correctIds: ['process'], success: '时间轴不再争抢唯一数字，而开始解释变化如何发生。', retry: '现有资料更适合呈现为跨年份的迁都过程。',
      }, evidenceId: 'wei_move_process',
    },
    {
      id: '03', title: '旧手艺到了新山崖', place: '证据叠影 · 云冈与龙门', objective: '比较两处石窟，不把变化写成简单替代',
      layer: '史料确证', layerNote: '历史遗址照片与策展并置用于比较，不代表“云冈直接变成龙门”。',
      background: '/assets/wei/longmen-guyang-original.jpg', position: 'center', framing: 'split-grotto', motif: 'stone-seam',
      dialogue: [
        { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '在平城时，我仰头看云冈，以为石佛就该有那样的面容。到了洛阳，山石、观看它的人、城里的审美都不同，手里的线也跟着变。', side: 'right' },
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '可别说云冈直接变成龙门。云冈自己就在不断变化，龙门往后也经历许多时期。两座石窟不是一幅旧图和一幅新图。', side: 'left' },
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '那它们像我父亲的两段生活：彼此有关，却不能把后一段说成前一段被彻底抹掉。', side: 'right', tone: 'quiet' },
        { speaker: '证据尺', role: '范围校验系统', text: '可比较造像、题记、服饰与艺术因素；不可仅凭并置证明某一形象直接演变为另一形象。', side: 'left' },
      ],
      challenge: {
        kind: 'classify', title: '双场景证据槽', instruction: '判断材料属于云冈、龙门北魏阶段，还是两边都需谨慎说明。',
        bins: [
          { id: 'yungang', label: '云冈', note: '平城时期附近的石窟证据。' },
          { id: 'longmen', label: '龙门北魏阶段', note: '洛阳时期相关证据。' },
          { id: 'both', label: '两边都需限定', note: '可以比较，但不能制造单线因果。' },
        ],
        cards: [
          { id: 'tanyao', label: '昙曜五窟', detail: '云冈早期大型洞窟与造像材料。', correctBin: 'yungang' },
          { id: 'guyang', label: '古阳洞', detail: '龙门北魏阶段的重要造像、龛饰与题记。', correctBin: 'longmen' },
          { id: 'music', label: '伎乐与乐器图像', detail: '两处都可观察，具体比较需研究支持。', correctBin: 'both' },
          { id: 'causality', label: '“前者直接变成后者”', detail: '策展并置不能证明直接因果。', correctBin: 'both' },
        ], success: '两座石窟之间出现的是可比较的证据，不是一支替代一切的进化箭头。', retry: '请留意地点、营造阶段，以及“策展对照不等于历史因果”。',
      }, evidenceId: 'wei_grotto_compare', marksLens: true,
    },
    {
      id: '04', title: '父亲最后穿哪件衣', place: '石作坊 · 衣冠草图台', objective: '理解衣着选择不能替一个人宣布身份',
      layer: '史料确证', layerNote: '服饰可反映场合、身份与时尚选择，但不能单独推断民族身份。',
      background: '/assets/wei/yungang-cave20-original.jpg', position: '38% center', framing: 'costume-close', motif: 'fold-lines',
      dialogue: [
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '供养像的衣纹要先定。你父亲入署时穿礼服，回家做木活又换旧袴褶。石上只能刻一身，我该选哪一身？', side: 'right', tone: 'question' },
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '他第一次穿新式礼服，连衣带都系错；后来教邻家孩子骑马时，还是嫌宽袖碍事。两件都是真的，哪件也不能独自说明他是谁。', side: 'left' },
        { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '衣冠会随制度、场合和习惯改变。它能留下生活变化，却不是给人群判定身份的印记。让衣纹讲他当时在做什么，不替他宣布属于哪一边。', side: 'right' },
      ],
      challenge: {
        kind: 'multi', title: '服饰证据边界', instruction: '选择服饰材料可以支持的观察。',
        options: [
          { id: 'shape', label: '观察服饰形制', detail: '属于图像与实物可讨论范围。' },
          { id: 'policy_practice', label: '比较制度规定与实际穿着', detail: '需要不同证据并读。' },
          { id: 'ethnicity', label: '直接判断个人民族身份', detail: '单件服饰不能支持。' },
          { id: 'all_changed', label: '证明所有人同时改变生活方式', detail: '超出个案与材料范围。' },
        ], correctIds: ['shape', 'policy_practice'], success: '服饰仍能讲变化，但不再被当作给人群贴标签的识别器。', retry: '服饰能说明形制和实践，不能直接识别民族身份或代表所有人。',
      }, evidenceId: 'wei_costume_boundary',
    },
    {
      id: '05', title: '诏令到了家门以后', place: '石作坊 · 三层生活账', objective: '区分制度要求、公共形象与实际生活',
      layer: '合理重建', layerNote: '人物家庭反应为虚构；制度文本、图像和出土实物作为不同证据类型的边界来自审核内容。',
      background: '/assets/wei/longmen-guyang-original.jpg', position: '58% center', framing: 'evidence-triad', motif: 'three-surfaces',
      dialogue: [
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '公文里，姓氏和籍贯已经改了；在家里，祖母仍喊父亲旧日的小名。究竟哪一个才算真的？', side: 'left', tone: 'question' },
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '都真，却回答不同问题。制度文本写人应当怎样登记，图像呈现人怎样被看见，器物和墓志只留下某些人曾经怎样生活。', side: 'right' },
        { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '朝廷可以在纸上同时落笔，千家万户却不会在同一天改变说话、穿衣和记忆。共同生活不是齐步走，是快慢不同的人仍要学会彼此相处。', side: 'left', tone: 'quiet' },
      ],
      challenge: {
        kind: 'classify', title: '三类证据', instruction: '按材料首先能够回答的问题分类。',
        bins: [
          { id: 'text', label: '制度文本', note: '规定与官方表达。' },
          { id: 'image', label: '图像材料', note: '艺术与视觉表现。' },
          { id: 'object', label: '出土实物', note: '具体使用与个案线索。' },
        ],
        cards: [
          { id: 'surname', label: '姓氏改革记录', detail: '制度范围与推行时间。', correctBin: 'text' },
          { id: 'donor', label: '供养人服饰形象', detail: '视觉呈现，不能当作社会统计。', correctBin: 'image' },
          { id: 'figurine', label: '侍从陶俑', detail: '具体形制与出土语境。', correctBin: 'object' },
        ], success: '材料没有被混成同一种证据，变化也不再显得整齐划一。', retry: '先问材料是什么，再问它最直接能够回答什么。',
      }, evidenceId: 'wei_evidence_types',
    },
    {
      id: '06', title: '四个动词刻进一生', place: '石作坊 · 墓志定稿', objective: '用采用、改造、并存与延续记录真实变化',
      layer: '史料确证', layerNote: '“采用、改造、并存与延续”概括本章审核后的表达边界。',
      background: '/assets/wei/yungang-cave20-original.jpg', position: '70% center', framing: 'relation-wall', motif: 'branching-lines',
      dialogue: [
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '墓志最怕写成一支箭：生于平城，迁到洛阳，于是旧日一切结束。阿洛，你父亲的一生真是这样吗？', side: 'right', tone: 'question' },
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '他采用了新姓，改造了旧宅的生活方式；平城口音和洛阳邻里在饭桌上并存，教我做木活的手艺一直延续。', side: 'left' },
        { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '采用、改造、并存、延续——不是四个漂亮词，而是一个人怎样在变化中仍保持完整。把它们刻成交叉的纹，不必都指向同一个终点。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'assemble', title: '变化叙述结构', instruction: '为三层各选一句。',
        slots: [
          { id: 'case', label: '个案', prompt: '墓志说明什么？', correctId: 'case_good', options: [
            { id: 'case_good', label: '记录元羽个案及制度背景', detail: '不扩张到所有人。' },
            { id: 'case_bad', label: '代表整个社会已完成改变', detail: '越过个案尺度。' },
          ] },
          { id: 'comparison', label: '比较', prompt: '两座石窟如何并置？', correctId: 'compare_good', options: [
            { id: 'compare_good', label: '观察不同空间与阶段的多种因素', detail: '允许差异与延续同时存在。' },
            { id: 'compare_bad', label: '证明一种文化彻底取代另一种', detail: '制造单线替代。' },
          ] },
          { id: 'unknown', label: '未知', prompt: '墓志要保留什么？', correctId: 'unknown_good', options: [
            { id: 'unknown_good', label: '不同群体与生活实践并不同步', detail: '承认材料覆盖有限。' },
            { id: 'unknown_bad', label: '未见材料的人也必然相同', detail: '替缺席者下结论。' },
          ] },
        ], success: '变化获得了分支与层次，不再被迫指向唯一终点。', retry: '个案不扩张、比较不造因果、未知不被填满。',
      }, evidenceId: 'wei_change_model', marksLens: true,
    },
    {
      id: '07', title: '最后一刀落在哪里', place: '洛阳城南石作坊 · 黄昏', objective: '决定墓石怎样同时保存来处、变化与新关系',
      layer: '剧情虚构', layerNote: '墓志定稿与人物选择为虚构情节；选项对应个案、多证据与家庭记忆三种叙述尺度。',
      background: '/assets/wei/longmen-guyang-original.jpg', position: '48% center', framing: 'decision-slab', motif: 'subject-line',
      dialogue: [
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '空白只剩最后一行。可以只写制度承认的新身份，可以把平城与洛阳并列，也可以留下家人最想保存的称呼。每一种写法都会让后人先看见不同的他。', side: 'right' },
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '我原以为必须替父亲选一边。走到这里才明白，他并不是两个互相冲突的人；正是两座城里的生活，一起组成了他。', side: 'left', tone: 'quiet' },
        { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '最后一刀由你决定。别替整个时代下结论，只回答这方石头怎样让一个人的改变、来处和新关系同时留下。', side: 'right' },
      ],
      challenge: { kind: 'final', title: '墓志落款', instruction: '决定最后一行怎样保存墓主的来处、变化与新关系。' },
    },
    {
      id: '08', title: '石上有两座城', place: '洛阳城南 · 新墓前', objective: '看见一个家庭怎样把迁徙变成新的共同生活',
      layer: '剧情虚构', layerNote: '安葬与人物收束均为虚构，不对应真实墓葬；历史意义由前述证据范围限定。',
      background: '/assets/wei/yungang-cave20-original.jpg', position: 'center', framing: 'open-gallery', motif: 'balanced-stones',
      dialogue: [
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '石屑扫净后，墓志没有写“旧日结束”。平城的来处、新姓、洛阳的居处和家人的称呼，各自占了一小块地方。', side: 'right', tone: 'quiet' },
        { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '送葬的人里，有跟我们一同南来的旧邻，也有父亲到洛阳后认识的新友。两边的人站在一起，我才第一次明白：新故乡不是替代旧故乡，是有人愿意与你共同生活。', side: 'left' },
      ],
      branchDialogue: {
        compare_first: [
          { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '最后一行只写这位墓主能够确认的经历，没有借他替所有迁洛者说话。', side: 'left' },
          { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '从一个人的变化出发，我们反而更能理解不同家庭怎样以不同速度进入共同生活。', side: 'right', tone: 'resolve' },
        ],
        workshop_together: [
          { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '墓志文字、衣冠草图和两处石窟的证据被并置，没有哪一样单独定义墓主。', side: 'left' },
          { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '没有一种传统独占他的一生。彼此影响、各自延续与重新创造因此同时可见。', side: 'right', tone: 'resolve' },
        ],
        keep_family_mark: [
          { speaker: '阿洛', role: '迁洛家庭青年 · 虚构角色', text: '我留下了家中仍使用的旧称，也写明它只是亲属记忆，不是所有人的共同叫法。', side: 'left' },
          { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '共同历史不必抹去个人来处；正是无数具体生命的选择与适应，构成了时代的交融。', side: 'right', tone: 'resolve' },
        ],
      },
    },
    {
      id: '09', title: '一方石上，两座故乡', place: '同心回望 · 平城—洛阳生活关系图', objective: '理解交融怎样发生在一个个具体生命中',
      layer: '研究解释', layerNote: '本幕由虚构个案回到真实历史证据，不把现代共同体概念写成北魏人物原话。',
      background: '/assets/wei/longmen-guyang-original.jpg', position: 'center', framing: 'shared-city-coda', motif: 'branching-lines',
      dialogue: [
        { speaker: '证据尺', role: '范围校验系统', text: '证据剧场结束。阿洛一家并非真实历史人物，但他们面对的姓名、籍贯、衣冠、迁徙与新生活，都能在北魏不同类型的材料中找到历史背景。', side: 'left' },
        { speaker: '慧生', role: '平城旧作坊学徒 · 虚构角色', text: '迁都让不同地域、不同传统的人更密切地相遇。他们没有在同一天变成同一种人，却开始在同一座城里学习彼此的规矩、手艺与生活。', side: 'right' },
        { speaker: '陆萤', role: '洛阳石工之女 · 虚构角色', text: '石头上保留两座故乡，不是把人分成两半；它承认一个新的共同生活，常常由没有被丢弃的旧记忆和不断建立的新关系一起组成。', side: 'left', tone: 'quiet' },
        { speaker: '证据尺', role: '范围校验系统', text: '本章记录：各民族之间的共同性，不以差异消失为前提；它在迁徙、相处、制度调整与文化互鉴中逐渐生长。', side: 'right', tone: 'resolve' },
      ],
    },
  ],
}

const tang: StoryChapter = {
  slug: 'tang', archiveTitle: '画卷只画下相见', subtitle: '真正连接山河的，是相见前后的翻译、往返与共同记忆',
  themeQuestion: '一幅画怎样记录相见，又遗漏了哪些让交流真正发生的人与关系？',
  playerRole: '长安客馆关系记录人：在接见前夜校对来使名册，让名字、翻译与画外人物回到一次真实而有限的相见中。',
  premise: '长安客馆里，一份接见名册把远道而来的禄东赞只写成“吐蕃使臣”，一张画稿又试图把所有关系塞进一次会见。虚构的鸿胪寺书吏、使团译者与画工学徒必须共同整理这次相见：谁被画下，谁留在画外，一位来使怎样连接到更长时期的唐蕃往来。故事不把一次婚姻写成永久和平，而是让观众看见不同人群如何通过翻译、礼仪、协商和持续往返进入彼此历史。',
  boundary: '许照、桑波、青禾及客馆名册情节均为剧情虚构；《步辇图》画中人物、634年遣使、641年前后相关事件及唐蕃关系的长期复杂性为史实锚点。真实历史人物不使用虚构私人对白。',
  acts: [
    { id: 'act-1', label: '第一幕', title: '让名字走出画框', sceneIds: ['00', '01'], dramaticQuestion: '“使臣一人”为什么不足以记录一次相见？', stateGoal: '确认禄东赞，并建立画中人物到画外事件的关系链。' },
    { id: 'act-2', label: '第二幕', title: '画面并不等于现场', sceneIds: ['02', '03'], dramaticQuestion: '图像、事件与后世档案分别能证明什么？', stateGoal: '区分画面表现、历史事件、作品认识与未知内心。' },
    { id: 'act-3', label: '第三幕', title: '翻译守住两岸', sceneIds: ['04', '05'], dramaticQuestion: '没被画下的人和没被说出的话应如何进入记录？', stateGoal: '连接画外参与者，同时不替历史人物虚构私人心声。' },
    { id: 'act-4', label: '第四幕', title: '相见之后', sceneIds: ['06', '07'], dramaticQuestion: '一次接见应怎样放回长期而复杂的唐蕃关系？', stateGoal: '拒绝以单次友好覆盖全部历史，并承担名册写法的后果。' },
    { id: 'act-5', label: '第五幕', title: '关系走向画外', sceneIds: ['08', '09'], dramaticQuestion: '为什么相见只是共同历史的一个节点？', stateGoal: '查看选择后果，理解翻译、协商和往返怎样让彼此进入对方历史。' },
  ],
  recap: {
    confirmed: '画中禄东赞、634年遣使、641年前后相关事件及唐蕃长期往来是本章史实锚点。',
    interpretation: '图像保存一次相见，文献连接事件；翻译、礼仪、协商与往返让关系延续到画外。',
    unknown: '画面不能提供现场全部站位、对白与人物内心，一次会见也不能概括此后全部唐蕃历史。',
    fiction: '许照、桑波、青禾、客馆名册及接见前夜的协作均为剧情虚构。',
  },
  accent: '#9a4c3b', accentSoft: '#dec29c', ink: '#2e2924',
  characters: [
    { name: '许照', role: '鸿胪寺书吏 · 虚构角色', mark: '照', color: '#a4513f' },
    { name: '桑波', role: '吐蕃使团译者 · 虚构角色', mark: '桑', color: '#5c7771' },
    { name: '青禾', role: '长安画工学徒 · 虚构角色', mark: '禾', color: '#8c7049' },
    { name: '画外索引', role: '关系提示系统', mark: '索', color: '#b08c4e' },
  ],
  scenes: [
    {
      id: '00', title: '名册上只有“吐蕃使臣”', place: '长安客馆 · 接见前夜', objective: '让远道而来的人不只剩一个模糊称呼',
      layer: '剧情虚构', layerNote: '客馆、名册与三位角色为虚构；禄东赞作为吐蕃使臣受到接见属于史实锚点。',
      background: '/assets/tang/bunian-original.jpg', position: '67% center', framing: 'search-scroll', motif: 'empty-hotspot',
      dialogue: [
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '明日接见，名册先写“吐蕃使臣一人”便够了。礼仪按身份安排，名字太长，抄错反而失礼。', side: 'left' },
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '他不是“一人”。他叫禄东赞，带着松赞干布的托付，也带着一路翻山越岭才送到长安的来意。若名字都不写，谁在与谁相见？', side: 'right', tone: 'warning' },
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '我在画稿上也只给他留了一小块位置。可若没有这位来使，画外的文成公主、松赞干布和后来的事，又从哪里接进来？', side: 'left', tone: 'question' },
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '那就先把名册重新打开。我们不替大人物编话，只把这次相见真正连接了谁、又没有说完什么，一项项写清。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'inspect', title: '画内搜寻', instruction: '查验画面中可由藏品资料识别的三组人物。',
        cards: [
          { id: 'taizong', label: '唐太宗', detail: '坐于步辇之上的核心人物。', stamp: '画中' },
          { id: 'ludongzan', label: '禄东赞', detail: '唐太宗面前拱手而立的吐蕃使臣。', stamp: '画中' },
          { id: 'palace_group', label: '宫女群体', detail: '抬辇、掌扇与持华盖；不可将其中任何人指认为文成公主。', stamp: '画中群体' },
        ], success: '画中名册已经核对完毕：文成公主不在画里。',
      }, evidenceId: 'tang_absent_search',
    },
    {
      id: '01', title: '一个名字怎样走出画框', place: '客馆灯下 · 关系名册', objective: '从禄东赞进入画外事件与人物关系',
      layer: '史料确证', layerNote: '画中人物识别与画外事件关系来自本章审核资料。',
      background: '/assets/tang/bunian-original.jpg', position: '55% center', framing: 'inside-outside', motif: 'aperture-thread',
      dialogue: [
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '画里没有文成公主，为什么后人仍会从这幅画想到她？', side: 'left', tone: 'question' },
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '因为关系不只存在于同一张画里。禄东赞奉命出使，由接见与相关事件，才能连接到画外的松赞干布和文成公主。', side: 'right' },
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '名册记录出场的人，关系簿记录事情怎样继续。把两页混在一起，会认错人；把第二页撕掉，又会让一次相见失去来路和后续。', side: 'left' },
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '那我不把公主偷偷画进宫女里。我从禄东赞身后留一条线，让画外的人有证据地出现。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'assemble', title: '画外关系链', instruction: '选择每一环真正承担的关系。',
        slots: [
          { id: 'inside', label: '画内起点', prompt: '从谁开始？', correctId: 'ludongzan', options: [
            { id: 'ludongzan', label: '禄东赞', detail: '画中可确认的吐蕃使臣。' },
            { id: 'wencheng', label: '文成公主', detail: '她不在画中。' },
          ] },
          { id: 'event', label: '关系中介', prompt: '通过什么走出画面？', correctId: 'reception', options: [
            { id: 'reception', label: '使臣会见与相关历史事件', detail: '由人物关系进入画外史事。' },
            { id: 'expression', label: '人物表情', detail: '不能据此推断完整历史。' },
          ] },
          { id: 'outside', label: '画外人物', prompt: '关系最终连接到谁？', correctId: 'wencheng_outside', options: [
            { id: 'wencheng_outside', label: '文成公主 · 画外', detail: '与事件相关，但非画中人物。' },
            { id: 'wencheng_inside', label: '文成公主 · 画中宫女', detail: '错误指认。' },
          ] },
        ], success: '一条有来源的关系线越过画框，却没有把画外人物偷偷塞进画里。', retry: '从画中禄东赞，经由会见与事件，再连接画外的文成公主。',
      }, evidenceId: 'tang_outside_chain', marksLens: true,
    },
    {
      id: '02', title: '画只能留下相见的一面', place: '长安画坊 · 初稿前', objective: '区分画面表现、真实事件与无法知道的内心',
      layer: '史料确证', layerNote: '本章固定边界：历史画不能被当作现场照片。',
      background: '/assets/tang/bunian-original.jpg', position: '76% center', framing: 'camera-fallacy', motif: 'shutter-cross',
      dialogue: [
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '若我把禄东赞画得更低一些，观者一眼就懂谁远道而来、谁在宫廷中央。可他们会不会以为这就是当日站位？', side: 'left', tone: 'question' },
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '画面可以组织观看，不能代替现场记录。你能画一次相见怎样被记忆，不能替唐太宗和禄东赞确定当时每一步、每句话和每一种心情。', side: 'right' },
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '译者也一样。我能转达说出口的话，却不能因为熟悉两边语言，就替任何人补出没有说过的心意。', side: 'left', tone: 'quiet' },
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '那我画“相见如何被呈现”，名册写“谁确实参与”，未知就留给未知。三者不再互相冒充。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'multi', title: '图像证据边界', instruction: '选择所有可以直接从画面描述、但没有冒充历史现场的内容。',
        options: [
          { id: 'composition', label: '人物在画面中的位置与构图', detail: '属于可观察的艺术表现。' },
          { id: 'catalogue', label: '藏品资料识别的画中人物', detail: '可结合来源说明。' },
          { id: 'dialogue', label: '双方当时说过的具体对白', detail: '画面不能提供。' },
          { id: 'emotion', label: '人物真实且唯一的内心感受', detail: '不能由表情直接推出。' },
        ], correctIds: ['composition', 'catalogue'], success: '画面仍然重要，但它不再被误当成一台穿越到现场的相机。', retry: '可描述构图与资料识别，不能补写对白或唯一心理。',
      }, evidenceId: 'tang_image_boundary',
    },
    {
      id: '03', title: '同一次相见，三种记法', place: '证据叠影 · 画卷、事件与后世档案', objective: '让不同材料各自回答重要问题',
      layer: '史料确证', layerNote: '画面主题、634年遣使、641年前后相关事件及故宫现行编目来自审核资料。作者归属说明降为档案背景。',
      background: '/assets/tang/bunian-original.jpg', position: '24% center', framing: 'attribution-desk', motif: 'three-seals',
      dialogue: [
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '公文会记使团何时到来、承担什么使命；画卷会选择一个相见的场面；后世档案又会记录作品怎样被收藏与认识。它们写的是同一段关系，却不是同一本账。', side: 'left' },
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '使团从634年的遣使走到641年前后的相关事件，也不是一次会见就能说完。若只留下画面，路上的往返会消失；若只留年月，人怎样来到彼此面前也会变冷。', side: 'right' },
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '那就让图像保存相见，让文献连接事件，让后世档案说明我们今天看到的究竟是什么。三种记法不争谁独占历史。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'classify', title: '相见的三层记录', instruction: '把信息放入它首先能够回答的证据层。',
        bins: [
          { id: 'catalogue', label: '画面呈现', note: '作品选择并组织的相见场景。' },
          { id: 'inscription', label: '历史事件', note: '由文献关系连接的遣使与相关事件。' },
          { id: 'discussion', label: '后世档案', note: '作品今天的编目与归属说明。' },
        ],
        cards: [
          { id: 'dpm', label: '唐太宗接见禄东赞', detail: '《步辇图》所表现的核心场景。', correctBin: 'catalogue' },
          { id: 'song', label: '634年遣使与641年前后相关事件', detail: '由审核资料连接的唐蕃交往节点。', correctBin: 'inscription' },
          { id: 'scholarship', label: '“唐，阎立本作”及归属说明', detail: '故宫现行编目，相关研究史另有讨论。', correctBin: 'discussion' },
        ], success: '画面、事件与后世档案共同留下相见，却没有任何一层冒充全部历史。', retry: '先判断材料在记录画面、历史事件，还是作品的后世档案。',
      }, evidenceId: 'tang_attribution_layers',
    },
    {
      id: '04', title: '没被画下的人仍在关系里', place: '长安客馆 · 双页名册', objective: '区分画中出场与历史参与',
      layer: '史料确证', layerNote: '人物是否画中出现与是否参与历史事件分开建模。',
      background: '/assets/tang/bunian-original.jpg', position: '62% center', framing: 'cast-list', motif: 'inside-outside-list',
      dialogue: [
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '我的画面容不下所有人。若只按画中名册记事，文成公主和松赞干布是不是就被留在历史外面？', side: 'left', tone: 'question' },
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '不是删掉，是分清关系。唐太宗与禄东赞属于画中人物；文成公主与松赞干布经由使节活动和相关事件进入画外关系页。', side: 'right' },
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '使者之所以远行，正因为不在场的人也能通过他建立联系。不在一幅画里，从来不等于不在共同历史里。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'classify', title: '画内／画外名册', instruction: '按“是否在画中被描绘”分类。',
        bins: [
          { id: 'inside', label: '画内人物', note: '可由藏品资料识别。' },
          { id: 'outside', label: '画外关系人物', note: '与事件相关，但不在画中。' },
        ],
        cards: [
          { id: 'taizong_card', label: '唐太宗', detail: '画中核心人物。', correctBin: 'inside' },
          { id: 'ludongzan_card', label: '禄东赞', detail: '画中吐蕃使臣。', correctBin: 'inside' },
          { id: 'wencheng_card', label: '文成公主', detail: '经由事件连接的画外人物。', correctBin: 'outside' },
          { id: 'songtsen_card', label: '松赞干布', detail: '经由使臣与事件连接的画外人物。', correctBin: 'outside' },
        ], success: '画外人物没有消失，也没有被错误地塞进画中。', retry: '本题只判断“是否被画出”，不是判断“是否与事件有关”。',
      }, evidenceId: 'tang_cast_boundary',
    },
    {
      id: '05', title: '翻译不能替人多说一句', place: '长安客馆 · 译写席', objective: '理解翻译怎样建立联系，也怎样守住边界',
      layer: '剧情虚构', layerNote: '译写情境与人物对白为虚构；真实历史人物的私人话语不被补写。',
      background: '/assets/tang/bunian-original.jpg', position: '47% center', framing: 'relation-index', motif: 'thread-map',
      dialogue: [
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '译者最怕两件事：只换词，不管对方是否听懂；或为了让话更动人，替人多说一句。前者让相见停在礼仪表面，后者让自己的声音冒充别人的心意。', side: 'right' },
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '所以关系簿只能沿有来源的线继续：禄东赞参与使臣会见，相关事件再连接文成公主。不能从一个表情直接写出告别与承诺。', side: 'left' },
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '原来真正的桥不是把空白填满，而是知道哪一句可以送到对岸，哪一句必须停在岸边。', side: 'right', tone: 'quiet' },
      ],
      challenge: {
        kind: 'multi', title: '关系线续接', instruction: '选择所有有证据支持的展开方式。',
        options: [
          { id: 'envoy_event', label: '禄东赞 → 使臣会见', detail: '人物与画面主题直接相关。' },
          { id: 'event_wencheng', label: '会见／相关事件 → 文成公主', detail: '由来源建立画外关系。' },
          { id: 'guess_dialogue', label: '表情 → 私人对白', detail: '没有证据支持。' },
          { id: 'guess_mood', label: '站位 → 全部人物真实心理', detail: '把艺术表现当现场记录。' },
        ], correctIds: ['envoy_event', 'event_wencheng'], success: '关系线走出了画框，却停在证据能够到达的地方。', retry: '画外关系仍需来源；表情与站位不能生成私人对白或心理。',
      }, evidenceId: 'tang_relation_thread', marksLens: true,
    },
    {
      id: '06', title: '相见之后还有下一程', place: '长安客馆 · 送行前', objective: '把一次会见放回长期而复杂的唐蕃关系',
      layer: '合理重建', layerNote: '送行情境为虚构；634年遣使、641年前后相关事件及此后关系的长期复杂性为史实边界。',
      background: '/assets/tang/bunian-original.jpg', position: '70% center', framing: 'rehearsal', motif: 'blank-caption',
      dialogue: [
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '画稿完成时，我差点以为故事也完成了：两边相见，婚姻将成，从此只剩圆满。', side: 'left', tone: 'quiet' },
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '使团还要走回去，承诺还要被传达，往后的关系也会继续变化。一次相见很重要，却不能保证此后没有分歧与冲突。', side: 'right' },
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '共同历史不是一张“从此永远和平”的凭据。它意味着双方已经一次次进入彼此的决定、记忆与生活，再不能被讲成毫无往来的两端。', side: 'left' },
      ],
      challenge: {
        kind: 'single', title: '关系续写', instruction: '选择能够从一次相见走向长期关系、又不过度美化的表述。',
        options: [
          { id: 'inside_wrong', label: '一次婚姻使双方从此完全相同', detail: '把交流误写成差异消失。' },
          { id: 'outside_good', label: '一次会见打开联系，长期关系仍会继续变化', detail: '承认交往、协商与关系变化并存。' },
          { id: 'photo_wrong', label: '一幅画已经说明全部唐蕃历史', detail: '把单一场景扩张为全部关系。' },
        ], correctIds: ['outside_good'], success: '相见成为长期关系的节点，而不是一个虚假的完美终点。', retry: '既不能把一次会见写成全部历史，也不能把交流等同于差异和矛盾从此消失。',
      }, evidenceId: 'tang_guide_line',
    },
    {
      id: '07', title: '名册最后一行', place: '长安客馆 · 天将明', objective: '决定这次相见怎样被后人理解',
      layer: '剧情虚构', layerNote: '名册定稿为虚构情节；最终选择对应画内边界、使臣路径与多来源并置。',
      background: '/assets/tang/bunian-original.jpg', position: '60% center', framing: 'frame-decision', motif: 'open-frame',
      dialogue: [
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '名册最后一行可以只说明谁在画中，也可以沿禄东赞写出画外关系，还可以把图像、事件和后世档案并列。写法不同，后人看到的“相见”也不同。', side: 'left' },
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '我不想再让一幅画独自承担全部历史。它可以让人记住这一面，但还要有人告诉观者：有人从远方来，也有人要继续走向远方。', side: 'right' },
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '请选择留下怎样的关系：只让双方在画中相见一次，还是让这次相见成为彼此不断理解、协商，也不断面对变化的开始。', side: 'left', tone: 'question' },
      ],
      challenge: { kind: 'final', title: '相见记录', instruction: '决定画中一面与画外长期关系怎样被共同保存。' },
    },
    {
      id: '08', title: '客馆门开，来路仍在', place: '长安清晨 · 使团启程', objective: '看见一次相见怎样成为继续往返的关系节点',
      layer: '剧情虚构', layerNote: '送行与人物收束为虚构，不对应具体可考现场；长期往来意义由审核资料限定。',
      background: '/assets/tang/bunian-original.jpg', position: '64% center', framing: 'scroll-open', motif: 'thread-beyond',
      dialogue: [
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '天亮时，使团的身影走出客馆。我的画把他们留在长安，真正的人却还要把见闻、礼仪与承诺带回另一端。', side: 'left', tone: 'quiet' },
        { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '新名册不再只有“吐蕃使臣一人”。禄东赞的名字后面连着使命、接见和画外关系，也留着一句：此后的往来与变化，不由这一次相见说完。', side: 'right' },
      ],
      branchDialogue: {
        state_absence: [
          { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '画卷明确写下文成公主不在画中，却没有把她从事件关系中删去。', side: 'left' },
          { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '诚实的空白没有削弱交流，反而让使臣、往返与真正的关系路径重新出现。', side: 'right', tone: 'resolve' },
        ],
        follow_envoy: [
          { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '关系线从禄东赞出发，穿过接见、相关事件与往返道路，抵达画框之外。', side: 'left' },
          { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '使臣不再只是宫廷画面里的一个名字，而成为不同人群尝试理解、协商并建立联系的入口。', side: 'right', tone: 'resolve' },
        ],
        keep_multiple_views: [
          { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '画卷、事件记录与后世档案并列时，它们互相补充，也互相限制。', side: 'left' },
          { speaker: '许照', role: '鸿胪寺书吏 · 虚构角色', text: '没有一种材料独占历史，唐蕃关系中的联系、变化与复杂性才能同时留下。', side: 'right', tone: 'resolve' },
        ],
      },
    },
    {
      id: '09', title: '画卷只画下相见', place: '同心回望 · 长安—吐蕃关系网', objective: '理解相见如何使不同人群进入彼此历史',
      layer: '研究解释', layerNote: '本幕由虚构客馆故事返回史实关系，不把现代概念写成唐代人物的主观目标。',
      background: '/assets/tang/bunian-original.jpg', position: '58% center', framing: 'relation-coda', motif: 'thread-beyond',
      dialogue: [
        { speaker: '画外索引', role: '关系提示系统', text: '证据剧场结束。许照、桑波和青禾并非真实历史人物；他们使我们看见，一次接见背后还需要记录、翻译、往返与彼此理解。', side: 'left' },
        { speaker: '桑波', role: '吐蕃使团译者 · 虚构角色', text: '一次会见和一次婚姻不能概括全部唐蕃关系。此后仍有往来与协商，也有矛盾和冲突；关系复杂，不等于彼此从未进入对方历史。', side: 'right' },
        { speaker: '青禾', role: '长安画工学徒 · 虚构角色', text: '画卷只能留住相见的一面。真正连接山河的，是一代代人仍愿意出发、接待、翻译，并把对方带回自己的记忆。', side: 'left', tone: 'quiet' },
        { speaker: '画外索引', role: '关系提示系统', text: '本章记录：各民族之间的关系并非只有相同与对立。长期交往使彼此的历史相连，也让理解共同历史成为今天仍要继续完成的事情。', side: 'right', tone: 'resolve' },
      ],
    },
  ],
}

const qing: StoryChapter = {
  slug: 'qing', archiveTitle: '向东的长路，有人接住', subtitle: '伊犁河岸的第一夜，一本接济簿怎样把远行者与四方来援连在一起',
  themeQuestion: '一场万里东归，怎样从“回到故土”变成不同人群共同重建生活？',
  playerRole: '伊犁接济簿协作人：在明确虚构的河岸证据剧场中，协助归来者、粮台书手与牧群赶运人完成第一夜的发放和来日安置记录。',
  premise: '1771年夏，土尔扈特部众历经长途跋涉抵达伊犁。河岸接济点要在天黑前发下第一批食物和衣物，一份受潮的名册却漏掉了乌娜一家；另一边，牲畜、茶米、棉布与皮衣正从不同地方接续运来。玩家必须与归来者乌娜、粮台书手宁成和牧群赶运人巴图共同完成两页簿册：一页解决今夜，一页安排来日。本章追问的不是谁单方面“拯救”谁，而是故土认同、国家接纳、四方调运与归来者自身行动怎样共同把抵达变成新的生活。',
  boundary: '乌娜、宁成、巴图及“受潮名册”均为剧情虚构；1771年抵达伊犁、口给以食、人授之衣、调运牲畜茶米棉布、分地安居与首领后续赴承德为史实锚点。具体个人对白、家庭遭遇、发放次序与河岸现场不得冒充真实档案。',
  acts: [
    { id: 'act-1', label: '第一幕', title: '河岸少了一个名字', sceneIds: ['00', '01'], dramaticQuestion: '名册不全时，是先救急，还是等一切核准？', stateGoal: '建立乌娜一家与接济簿的现实冲突，在不虚构事实的前提下先让人被看见。' },
    { id: 'act-2', label: '第二幕', title: '三条路，许多个人', sceneIds: ['02', '03'], dramaticQuestion: '大部众抵达、首领赴承德与后续安置为何不能合成一条胜利路线？', stateGoal: '分开三条空间线，并让不同口径的数字回到具体生命尺度。' },
    { id: 'act-3', label: '第三幕', title: '四方来援', sceneIds: ['04', '05'], dramaticQuestion: '故土认同与现实困境怎样推动东归，抵达后又由谁接续长路？', stateGoal: '保留多重动因，把食衣、牲畜和牧地连接为跨地域接济网络。' },
    { id: 'act-4', label: '第四幕', title: '今夜与来日', sceneIds: ['06', '07'], dramaticQuestion: '一本簿册怎样既解决眼前饥寒，又不把归来者只写成等待救助的数字？', stateGoal: '由归来者参与核名和分配，完成带有现实代价的双页安置选择。' },
    { id: 'act-5', label: '第五幕', title: '长路被许多双手接住', sceneIds: ['08', '09'], dramaticQuestion: '归属怎样在接纳、协作与共同重建中真正发生？', stateGoal: '查看第一夜的选择后果，理解“同心”是不同人群共同承担生活。' },
  ],
  recap: {
    confirmed: '1771年土尔扈特部众抵达伊犁；清廷组织食衣、茶米、牲畜等接济并安排牧地，首领后续赴承德。',
    interpretation: '东归的凝聚力不仅体现于万里返乡，也体现于抵达后跨地域调运、制度接纳和归来者参与重建共同生活。',
    unknown: '路线细节、人数口径以及普通迁徙者的个人感受存在材料缺口，不能由宏大叙事或虚构独白填满。',
    fiction: '乌娜、宁成、巴图、受潮名册、河岸第一夜与三种簿册方案均为剧情虚构。',
  },
  accent: '#697d78', accentSoft: '#c5b78f', ink: '#192c31',
  characters: [
    { name: '乌娜', role: '东归部众青年 · 虚构角色', mark: '乌', color: '#9a6549' },
    { name: '宁成', role: '伊犁粮台书手 · 虚构角色', mark: '宁', color: '#5f7977' },
    { name: '巴图', role: '牧群赶运人 · 虚构角色', mark: '巴', color: '#826f4f' },
    { name: '安置簿', role: '史实边界与接济记录系统', mark: '簿', color: '#b49a5b' },
  ],
  scenes: [
    {
      id: '00', title: '河岸名册少了一户', place: '1771年夏 · 伊犁河岸证据剧场', objective: '在受潮名册与眼前的人之间作出第一项判断',
      layer: '合理重建', layerNote: '1771年抵达伊犁与组织接济为史实锚点；乌娜一家、受潮名册和河岸对白均为明确虚构。',
      background: '/assets/qing/qing-ili-relief-v1.png', position: '50% center', framing: 'empty-case', motif: 'silent-screen',
      dialogue: [
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '天黑前要按名册发下第一批粮和衣。可雨水把这一页泡成了团，最后一户只剩半个墨点。没有姓名，我不敢落笔。', side: 'right', tone: 'warning' },
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '你纸上少的是一户，我身后站着的却是祖母、弟弟和走不动的妹妹。我们走到河边，不会因为墨褪了就少掉一个人。', side: 'left' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '我的羊群也只到了一半，后队还在路上。若非等齐不可，今夜人要挨饿，牲畜也会倒在河岸。', side: 'right' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '那就请你与我同写这本簿：不凭想象补名字，也不让空白挡住眼前的人。先弄清哪些是史实，哪些只是我们为理解那一夜搭起的场景。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'inspect', title: '河岸第一夜的三层证据', instruction: '依次确认史实锚点、可作解释的关系与明确虚构的个人。',
        cards: [
          { id: 'arrival', label: '1771年抵达伊犁', detail: '土尔扈特部众历经长途跋涉抵达伊犁，是本章的史实起点。', stamp: '史料确证' },
          { id: 'relief', label: '食衣与后续安置', detail: '史料记录了口给以食、人授之衣、调运牲畜物资与分地安居。', stamp: '史料确证' },
          { id: 'fiction_household', label: '乌娜一家与受潮名册', detail: '为让玩家承担选择而设置的虚构个案，不对应真实历史家庭。', stamp: '剧情虚构' },
        ], success: '河岸场景可以承载历史关系，但不能冒充某个真实家庭留下的证词。',
      }, evidenceId: 'qing_arrival_ledger',
    },
    {
      id: '01', title: '先发一碗粮，还是先补一个名字', place: '伊犁河岸 · 临时粮台', objective: '在记录不全时同时守住救急与证据边界',
      layer: '合理重建', layerNote: '接济原则有史料依据；具体家庭、对话与临时处置为剧情重建，不对应真实行政个案。',
      background: '/assets/qing/qing-ili-relief-v1.png', position: '54% center', framing: 'route-map', motif: 'corridor-band',
      dialogue: [
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '照旧例，账目要能对上。若我凭一句话添四个人，后面每一袋粮都会跟着这笔未经核实的记录走。', side: 'right' },
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '那就别把我的话写成已经核准。写“眼前四人，原册受损，待与同队复核”。你可以承认不知道，却不能假装没看见。', side: 'left', tone: 'question' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '粮先按眼前的人发，名字让同队的人一道来认。救急和核名不是只能选一个先活、一个先死。', side: 'right' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '好。事实写到事实的位置，待核写到待核的位置，今夜该发的粮也写进责任栏。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'single', title: '缺页时怎样落笔', instruction: '选择既不制造档案事实、也不让空白阻断救急的处理。',
        options: [
          { id: 'deny', label: '名册无名，一律暂不发放', detail: '账面整齐，却让行政空白伤害眼前的人。' },
          { id: 'invent', label: '替一家人补齐来历与姓名', detail: '用好意制造未经核实的档案事实。' },
          { id: 'aid_and_mark', label: '先按眼前丁口救急，并把名册受损标为待核', detail: '行动与证据边界同时进入记录。' },
        ], correctIds: ['aid_and_mark'], success: '一袋粮先解决今夜，一行“待核”保住了明天继续追问的可能。', retry: '不能因记录不全拒绝眼前需要，也不能用虚构信息填满受损名册。',
      }, evidenceId: 'qing_relief_first', marksLens: true,
    },
    {
      id: '02', title: '为什么我的终点画在承德', place: '河岸摊开的三层路线图', objective: '从乌娜的疑问中分开迁徙、觐见与安置',
      layer: '史料确证', layerNote: '大部众抵达伊犁与首领之后赴承德是不同范围的路线。',
      background: '/assets/qing/qing-migration-photoreal-v2.png', position: '57% center', framing: 'dual-route', motif: 'split-destination',
      dialogue: [
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '这张图说我们的路还要去承德。可祖母已经走不动了，弟弟问今晚把毡毯铺在哪里。难道我们还没有抵达？', side: 'left', tone: 'question' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '大部众抵达的是伊犁一带；后来赴承德的是渥巴锡等首领。把首领的路续在所有人脚下，宫廷接见就会遮住河岸上的安置。', side: 'right' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '还有第三条路：粮送到哪里，牲畜分到哪里，牧地又安排在哪里。那条路不壮丽，却决定你们明年能不能重新过日子。', side: 'left' },
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '那就把三条路分开。首领替部众去见皇帝，我们在伊犁接住今晚，往后的生活再从这里出发。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'classify', title: '双路线分流', instruction: '区分大部众迁徙与抵达后的首领活动。',
        bins: [
          { id: 'mass', label: '大部众迁徙', note: '伏尔加河下游向东，抵达伊犁河流域。' },
          { id: 'leader', label: '首领赴承德', note: '抵达之后的首领活动。' },
          { id: 'settlement', label: '抵达后安置', note: '安置分布，不是原迁徙终点线。' },
        ],
        cards: [
          { id: 'volga', label: '伏尔加河下游', detail: '东归出发区域。', correctBin: 'mass' },
          { id: 'ili', label: '伊犁河流域', detail: '1771年夏季抵达区域。', correctBin: 'mass' },
          { id: 'chengde', label: '承德／热河', detail: '渥巴锡等首领抵达后赴此觐见。', correctBin: 'leader' },
          { id: 'placement', label: '新疆相关安置地区', detail: '抵达后的安置聚合节点。', correctBin: 'settlement' },
        ], success: '三条线终于分开：迁徙、首领活动与安置不再共享一个终点。', retry: '伊犁是大部众抵达区域；承德属于之后的首领活动。',
      }, evidenceId: 'qing_route_scopes',
    },
    {
      id: '03', title: '三个数字，眼前是四个人', place: '伊犁河岸 · 丁口与户数复核处', objective: '让统计口径回到具体的食衣发放',
      layer: '史料确证', layerNote: '“约17万人”“16.8万余人”“三万多户”等应保留来源原始表述。',
      background: '/assets/qing/qing-migration-v1.png', position: '42% center', framing: 'number-ledger', motif: 'three-counts',
      dialogue: [
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '总册写约十七万人，另一份记十六万八千余，还有材料按三万多户来算。若只求一个整齐数字，今天按丁口发粮、按户补帐篷时就会错位。', side: 'right' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '一户可能有四口，也可能只剩一个人。牲畜按“户”分，今晚的食物却要看站在这里的每一张脸。', side: 'left' },
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '路上失去的人不能被一个平均数抹平，活着抵达的人也不能只剩总数。把每个数字是谁记的、记人在何时，都写在旁边。', side: 'right', tone: 'quiet' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '总数帮助筹措，丁口决定眼前发放，户数关系后续安置。它们不是三个互相争胜的答案。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'single', title: '数字如何并列', instruction: '选择不制造虚假精确度的方案。',
        options: [
          { id: 'average', label: '计算平均值作为唯一答案', detail: '把不同单位与口径强行合并。' },
          { id: 'source', label: '保留原表述并标明来源与口径', detail: '让差异本身可见。' },
          { id: 'largest', label: '只保留最大的数字', detail: '用视觉冲击替代证据说明。' },
        ], correctIds: ['source'], success: '数字没有被统一，却更接近各自来源真正说过的话。', retry: '不同单位和统计口径不能求平均或挑一个当唯一答案。',
      }, evidenceId: 'qing_number_sources',
    },
    {
      id: '04', title: '为什么一定要向东', place: '河岸夜风 · 未走完的路线旁', objective: '让故土认同与现实压力共同进入东归动因',
      layer: '史料确证', layerNote: '不同资料从政治环境、军事压力、草场生存、内部政治、长期联系与历史记忆等角度讨论。',
      background: '/assets/qing/qing-migration-photoreal-v2.png', position: '44% center', framing: 'motive-wall', motif: 'many-arrows',
      dialogue: [
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '总册旁要写东归缘由。若只写“思念故土”，人人看得懂，可你们一路面对的政治军事压力、草场生计与长期联系都会被藏起来。', side: 'right' },
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '我可以告诉你这个虚构家庭为何向东，却不能替真实的万千人说同一句心里话。有人记得故土，有人先想着活下去，也有人只是跟紧亲人不掉队。', side: 'left', tone: 'quiet' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '一支队伍可以朝同一个方向走，不等于每个人只有同一个理由。真正把他们连在一起的，是愿意共同承担这条路和同一个归处。', side: 'right' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '那就把故土认同写在中心，把政治、军事、生计与长期联系写成彼此交织的背景，不替所有人规定唯一内心。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'multi', title: '多重背景', instruction: '选择所有可以进入多来源讨论、但不能被宣布为唯一动因的因素。',
        options: [
          { id: 'pressure', label: '政治与军事压力', detail: '公开资料讨论的重要背景之一。' },
          { id: 'livelihood', label: '草场与生存环境', detail: '现代研究涉及的背景之一。' },
          { id: 'contact', label: '与清朝的长期联系', detail: '公开资料记录的背景之一。' },
          { id: 'single_heart', label: '所有人都怀着完全相同的愿望', detail: '现有资料不能支持统一心理。' },
        ], correctIds: ['pressure', 'livelihood', 'contact'], success: '多种背景并列出现，但没有任何一张卡替所有参与者宣布唯一内心。', retry: '可并列多个有来源的背景，不能把群体心理写成完全一致。',
      }, evidenceId: 'qing_motive_plural',
    },
    {
      id: '05', title: '四方送来的，不只是一批牛羊', place: '伊犁河岸 · 接济物资交接处', objective: '把救急、恢复生计与长久安置连成协作网络',
      layer: '史料确证', layerNote: '食衣、茶米、棉布、牲畜与分地安居来自接济记录；人物交接对白为合理重建。',
      background: '/assets/qing/qing-ili-relief-v1.png', position: '58% center', framing: 'term-table', motif: 'voice-labels',
      dialogue: [
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '这批羊不是从一处赶来的，茶米、皮衣、棉布也走了不同的路。有人采办，有人调拨，有人赶运，最后才在河岸成为你们手里的东西。', side: 'right' },
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '一碗粮让妹妹熬过今晚，一件衣能挡住秋寒。可若明年还要生活，我们需要的不只是被喂饱，还要有牲畜、有牧地，也要让我们自己重新把日子撑起来。', side: 'left' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '史料把原则写得很短：口给以食，人授之衣，分地安居。短短三层，背后却是从多地筹措、一路转运，再到伊犁分发和安置的许多双手。', side: 'right', tone: 'quiet' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '我把牲畜赶到这里，乌娜却比我更清楚哪家有人会照料、哪家眼下缺劳力。接济若没有归来者参与，只会把人排成领东西的队伍。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'classify', title: '把接济接成生活', instruction: '判断每项行动首先解决今夜、明日生计，还是长久安置。',
        bins: [
          { id: 'tonight', label: '今夜救急', note: '先处理饥饿、寒冷与眼前生存。' },
          { id: 'livelihood', label: '恢复生计', note: '让归来者重新具备生产与生活能力。' },
          { id: 'settlement', label: '长久安置', note: '让新的共同生活有可以持续的空间。' },
        ],
        cards: [
          { id: 'food_clothing', label: '按口给食、按人授衣', detail: '首先解决抵达后的饥寒。', correctBin: 'tonight' },
          { id: 'animals', label: '调运与采办马牛羊', detail: '既可救急，也关系游牧生计；本题按主要长期作用归类。', correctBin: 'livelihood' },
          { id: 'tea_rice_cloth', label: '茶米与棉布持续运抵', detail: '补给并支持生活恢复。', correctBin: 'livelihood' },
          { id: 'pasture', label: '划定水草适宜的安置地', detail: '关系到部众能否长久安居。', correctBin: 'settlement' },
        ], success: '物资不再只是赏赐清单：有人筹措、有人运送、有人接收并重新组织生活。', retry: '食衣首先救急；牲畜与持续物资帮助恢复生计；牧地关系长久安置。',
      }, evidenceId: 'qing_relief_chain',
    },
    {
      id: '06', title: '不能让空白替人挨饿', place: '伊犁河岸 · 双页接济簿', objective: '由归来者参与核名，把已知、待核与行动分别写下',
      layer: '合理重建', layerNote: '双页簿册与乌娜参与核名为剧情重建；“口给以食、人授之衣、分地安居”为史实依据。',
      background: '/assets/qing/qing-ili-relief-v1.png', position: '62% center', framing: 'polyphonic-case', motif: 'empty-lines',
      dialogue: [
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '我把簿册分成两页：左页记今夜谁领食衣，右页记牲畜、牧地与待核家口。可我不认识你们同队的人，名字写得再工整也可能认错。', side: 'right' },
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '让我坐到桌子这一边。我能认出同队的称呼，能请其他人彼此作证，也能告诉你哪一户只剩老人，哪一户还有人失散。', side: 'left' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '我来记牲畜状态。能挤奶的、能驮物的、需要休养的不能只写成同一个“羊”或“马”。把东西发下去只是一步，还要让它们真正接上生活。', side: 'right' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '这才是共同写簿。不是我替你们安排一切，也不是你们独自再走一段；每个人把自己知道的写进同一份可继续核对的记录。', side: 'left', tone: 'resolve' },
      ],
      challenge: {
        kind: 'assemble', title: '完成双页接济簿', instruction: '分别写清史实依据、名册空白与当下行动。',
        slots: [
          { id: 'fact', label: '史实依据', prompt: '接济原则怎样写？', correctId: 'fact_good', options: [
            { id: 'fact_good', label: '食衣、牲畜与安置均有史料记录', detail: '只写材料能够支持的范围。' },
            { id: 'fact_bad', label: '每户都在同一晚得到完全相同物资', detail: '现有材料不能支持具体统一现场。' },
          ] },
          { id: 'blank', label: '受损空白', prompt: '乌娜一家怎样记？', correctId: 'blank_good', options: [
            { id: 'blank_good', label: '眼前丁口先登记救急，原册信息标为待核', detail: '既不拒绝人，也不伪造档案。' },
            { id: 'blank_bad', label: '代写完整家史并标成真实记录', detail: '把虚构剧情冒充历史证词。' },
          ] },
          { id: 'action', label: '共同动作', prompt: '谁参与后续核名与分配？', correctId: 'action_good', options: [
            { id: 'action_good', label: '归来者、书手与赶运人分别提供所知', detail: '让接纳与自助进入同一过程。' },
            { id: 'action_bad', label: '只由一名书手替所有人决定', detail: '把归来者写成被动领取者。' },
          ] },
        ], success: '空白没有被偷偷填满，也没有继续挡住救急；归来者第一次坐到了记录桌的同一边。', retry: '把史实、待核信息和当下行动分开，并让归来者参与决定。',
      }, evidenceId: 'qing_settlement_ledger', marksLens: true,
    },
    {
      id: '07', title: '今夜的粮，明春的路', place: '伊犁河岸 · 灯下定簿', objective: '决定接济簿怎样同时承担救急、核名与来日生活',
      layer: '剧情虚构', layerNote: '三种簿册方案及其人物后果为互动剧情，不对应真实清代行政决策。',
      background: '/assets/qing/qing-ili-relief-v1.png', position: '50% center', framing: 'case-decision', motif: 'three-voices',
      dialogue: [
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '灯只够再烧一阵。可以先按眼前丁口把食衣发完；可以放慢速度，把失散和受损名字逐户补上；也可以做成双页，一页管今夜，一页把牲畜、牧地和复核责任接到明春。', side: 'right' },
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '先救急，我的妹妹今晚不会饿；先补名，走失的人不会被轻易抹掉；写双页，我们能一起安排以后，却要更多人继续守着这本簿。', side: 'left', tone: 'question' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '没有哪一条路不付代价。请选择先保护什么，也把来不及做的事写在欠账栏里。共同承担，不是说一句大家一条心，是有人愿意接住这份没做完的工作。', side: 'right' },
      ],
      challenge: { kind: 'final', title: '灯下定簿', instruction: '决定这本簿先保护什么，并承担它留下的现实代价。' },
    },
    {
      id: '08', title: '第一锅茶烧起来', place: '伊犁河岸 · 接济点入夜', objective: '看见选择怎样改变第一夜，也怎样留下尚待承担的工作',
      layer: '剧情虚构', layerNote: '河岸入夜、人物行动与分支结果均为虚构；茶米、食衣、牲畜与安置关系受史实边界约束。',
      background: '/assets/qing/qing-ili-relief-v1.png', position: '50% center', framing: 'case-lit', motif: 'braided-route',
      dialogue: [
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '第一锅茶烧起来时，妹妹终于肯松开空碗。祖母把新领的衣裹在她身上，又催我回记录桌——同队还有几户没有核清。', side: 'left', tone: 'quiet' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '我原以为接济就是把仓里的东西发出去。现在才知道，每一袋粮都要有人认领，每一笔待核都要有人继续追，每一处安置还要与真实生活对得上。', side: 'right' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '河岸上没有谁只是给予，也没有谁只是接受。我们带来牲畜和物资，你们带来照料牧群的知识、彼此的名字和重建生活的意志。明早，这些才会一起上路。', side: 'left' },
      ],
      branchDialogue: {
        record_range: [
          { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '食衣最先发完，河岸这一夜少挨了许多饿。可牲畜和牧地页仍有大片空白，我在封面写下：救急完成，安置未完。', side: 'right' },
          { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '今晚被接住了，明天还要回来。谢谢你没有把第一碗粮写成故事的结局。', side: 'left', tone: 'resolve' },
        ],
        record_names: [
          { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '我们逐户核到深夜，受潮页旁添了许多“待寻”。发放慢了，但失散的人没有因为不在眼前就从簿上消失。', side: 'left' },
          { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '我留下几处空格，也留下明早优先补发的记号。承认未完，比用一个整齐数字遮住人更可靠。', side: 'right', tone: 'resolve' },
        ],
        follow_route: [
          { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '双页把今晚食衣、明日核名、牲畜照料和牧地复核接成了一条责任链。谁也不能写完就走。', side: 'left' },
          { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '我在右页按下手印，不是只证明领过什么，也答应与宁成、巴图一起把后面的生活接下去。', side: 'right', tone: 'resolve' },
        ],
      },
    },
    {
      id: '09', title: '长路被许多双手接住', place: '同心回望 · 东归—接济—安置关系图', objective: '理解同心如何从故土认同走向共同承担与共同生活',
      layer: '研究解释', layerNote: '本幕总结迁徙、接纳与安置的历史意义，不替所有历史参与者虚构同一种心理。',
      background: '/assets/qing/qing-ili-relief-v1.png', position: '50% center', framing: 'belonging-coda', motif: 'braided-route',
      dialogue: [
        { speaker: '乌娜', role: '东归部众青年 · 虚构角色', text: '向东时，我们带着自己的语言、信仰、亲人记忆和过日子的本领。抵达以后，这些没有被要求丢在河对岸，而要带进新的牧地和新的邻里。', side: 'left' },
        { speaker: '巴图', role: '牧群赶运人 · 虚构角色', text: '从不同地方调来的粮、衣、茶米和牲畜，也不只是物资。它们让原本互不相识的人为同一批抵达者接力，把一件国家大事变成许多人手里的具体责任。', side: 'right' },
        { speaker: '宁成', role: '伊犁粮台书手 · 虚构角色', text: '而归来者不是被写进簿册就算完成归属。你们参与核名、照料牲畜、重建家庭与生产，也把自己的经验带进共同生活。接纳因此不是一方施予，是双方开始彼此需要。', side: 'left', tone: 'quiet' },
        { speaker: '安置簿', role: '史实边界与接济记录系统', text: '本章记录：同心不是让不同人群失去差异，而是让万里归来的选择、四方接续的支援与共同重建的行动汇入同一个家园。长路在抵达处没有结束，它被许多双手接成了此后的共同历史。', side: 'right', tone: 'resolve' },
      ],
    },
  ],
}

const contemporary: StoryChapter = {
  slug: 'contemporary', archiveTitle: '一针之后，二十四封回信', subtitle: '从灾后羌绣帮扶到跨地共创，让一门技艺连接不相识的人，也保留每个人自己的声音',
  themeQuestion: '一门具体民族技艺，怎样不被做成统一的“民族风格”，却能进入各民族共同参与的当代生活？',
  playerRole: '跨地共创档案协调员：校正一段把灾后重建写成单向救助的展览叙事，并为二十四所学校完成可以往返的“接针包”。',
  premise: '映秀的一间羌绣工坊准备把二十四个“接针共创包”寄往不同地区的学校。每个包里原本应有一位羌绣创作者为本次交流新作的起针片、一段本人说明和一块留给远方学生回应的空白材料；学生完成回应后，再把作品与问题寄回工坊。顾槿却用AI把多位创作者的作品平均成一张“同心纹样”，认为统一图案更便于复制和传播。与此同时，工坊旧柜里发现的一只2008年资料箱，又把灾后羌绣帮扶简单写成“外部力量拯救羌绣”。玩家必须沿着培训、生产、销售、教学与回信重新辨认关系：外部支援重要，当地妇女的生产自救和持续传承同样重要；不同民族、地区的参与者可以共同学习和创造，但不能靠抹掉差异来证明团结。AI最终只负责转写说明、核对许可和绘制关系图，不替任何人生成统一传统。',
  boundary: '羌绣灾后就业帮扶、技能培训、合作社与市场连接具有公开史实依据；2008资料箱、二十四所学校、所有角色、作品与回信均为剧情重建。阿若、顾槿、拉姆只能说明自己的经历与工作，不能代表整个民族或所有从业者。AI生成内容不得冒充传统羌绣原作。',
  acts: [
    { id: 'act-1', label: '第一幕', title: '旧箱子里的共同重建', sceneIds: ['00', '01'], dramaticQuestion: '灾后羌绣重新进入生产和生活，究竟是谁帮助了谁？', stateGoal: '把外部支援、当地生产自救、培训教学与市场连接放回同一条关系链。' },
    { id: 'act-2', label: '第二幕', title: '今天谁在继续这门技艺', sceneIds: ['02', '03'], dramaticQuestion: '当羌绣进入跨县培训、学校和市场，传承者、学习者与合作方各自做了什么？', stateGoal: '让教师、学员、设计者、销售者和消费者分别留下姓名与行动。' },
    { id: 'act-3', label: '第三幕', title: '同心不是做成同样', sceneIds: ['04', '05'], dramaticQuestion: 'AI把二十多件作品合成统一纹样时，抹掉了哪些真实关系？', stateGoal: '删除统一生成图，组装保留作者和回应空间的“接针包”。' },
    { id: 'act-4', label: '第四幕', title: '把一针交给远方', sceneIds: ['06', '07'], dramaticQuestion: '远方学生怎样参与，才不是模仿、占用或把所有作品混成一种风格？', stateGoal: '完成试寄规则，并在规模、速度与真实往返之间作出选择。' },
    { id: 'act-5', label: '第五幕', title: '作品从远方寄回来', sceneIds: ['08', '09'], dramaticQuestion: '二十四件不同的回应，为什么比一张统一图更能说明同心？', stateGoal: '查看选择后果，把共同体理解为有来有往、彼此需要又保留差异的关系。' },
  ],
  recap: {
    confirmed: '2008年汶川地震后，羌绣进入非遗保护、就业帮扶、技能培训和市场连接；当地妇女通过生产、学习、授艺与合作社参与恢复生计。此后羌绣继续进入跨县培训、学校教育和文创合作。',
    interpretation: '同心既包括国家、社会与不同地区的支援，也包括当地文化主体用自己的技艺参与重建并反过来丰富共同文化；共同参与不等于把不同作品平均成一种风格。',
    unknown: '没有具体档案与当事人确认，不能推定某件绣品的创作者、纹样寓意、授权范围、收益分配或个人灾后经历。',
    fiction: '阿若、顾槿、拉姆、2008资料箱、二十四个接针包、学校试寄与所有回信均为剧情虚构，不对应任何真实个人的私密记忆。',
  },
  accent: '#8b4e68', accentSoft: '#d8b392', ink: '#223338',
  characters: [
    { name: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', mark: '若', color: '#9b6a48' },
    { name: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', mark: '槿', color: '#8c506b' },
    { name: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', mark: '姆', color: '#4f7b75' },
    { name: '同心档案台', role: '来源、许可与往返记录系统', mark: '同', color: '#b18d4e' },
  ],
  scenes: [
    {
      id: '00', title: '旧箱子上写着“受助作品”', place: '2026年秋 · 映秀羌绣工坊资料室', objective: '从一只虚构资料箱进入灾后羌绣保护、就业与生产重建的真实关系',
      layer: '合理重建', layerNote: '资料箱与人物为虚构；灾后羌绣计划、技能培训、居家生产与市场销售具有公开资料依据。',
      background: '/assets/contemporary/qiang-workshop-photoreal-v2.png', position: '48% center', framing: 'scan-table', motif: 'red-button',
      dialogue: [
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '阿若老师，最里面还有一只旧纸箱。标签是“2008年受助作品”，下面压着培训表、领料单和几张已经褪色的订单复印件。', side: 'left' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '正好可以做新展的开场。我先写一句：“地震后，来自全国的援助让濒危羌绣重新活了下来。”观众一下就能理解“同心”。', side: 'right' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '全国支援当然要写，可这句话里，本地人只剩下等别人来救。培训表后面还有领料、交活和结算；有人学会，有人把绣片带回家做，也有人后来开始教别人。', side: 'left', tone: 'warning' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '箱子里没有完整姓名，只有编号和数量。我们不能拿它给某个人编灾后经历，但可以把已经确认的项目结构重新排出来。', side: 'right' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '也就是说，不能写成“谁拯救了谁”，要问资金、培训、针线、订单和本地劳动怎样接在一起。那我先把刚才那句撤下。', side: 'left' },
        { speaker: '同心档案台', role: '来源、许可与往返记录系统', text: '建档任务开启：确认国家级非遗、灾后帮扶、技能培训和生产销售四项公开事实；人物姓名与私人经历保持未知。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'inspect', title: '旧箱子里的四条关系', instruction: '依次确认哪些内容有公开资料支持，不能用虚构个人故事替代。',
        cards: [
          { id: 'creator', label: '国家级非遗', detail: '羌族刺绣于2008年列入第二批国家级非物质文化遗产名录。', stamp: '史实可核' },
          { id: 'source', label: '灾后就业帮扶', detail: '灾后有关部门和地方共同推进羌绣保护与妇女就业帮扶。', stamp: '史实可核' },
          { id: 'purpose', label: '培训与居家生产', detail: '参与者接受技能培训，合格后可领取材料，在家完成绣片。', stamp: '史实可核' },
          { id: 'permission', label: '销售与生活重建', detail: '成品通过帮扶中心、企业等渠道进入市场，帮助家庭增加收入。', stamp: '史实可核' },
        ], success: '箱子里不是一条“援助者—被救助者”直线，而是一条由公共支援、本地劳动、组织协作和市场连接共同组成的生产链。',
      }, evidenceId: 'contemporary_recovery_chain',
    },
    {
      id: '01', title: '援助名单背面，还有交活和结算', place: '资料室长桌 · 灾后生产关系复原图', objective: '把支援者、当地参与者和连接双方的组织分别放回行动位置',
      layer: '研究解释', layerNote: '角色讨论依据公开项目结构；具体名单、分工与个人感受不能由这只虚构纸箱证明。',
      background: '/assets/contemporary/qiang-workshop-v1.png', position: '52% center', framing: 'rights-matrix', motif: 'permission-grid',
      dialogue: [
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '我把资料按动作排好了：有人组织培训和提供资源，有人在家完成绣片，有人验收结算，有人把产品带到市场。少掉任何一段，链条都走不通。', side: 'left' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '但展览只有九十秒。写得太多人，观众会不会记不住？保留“全国援助”不是更有力量吗？', side: 'right', tone: 'question' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '九十秒也能把动词写全。外面送来资源，本地人拿起针线；老师教，学员做；组织收，市场买。帮助不是把另一方写成没有行动的人。', side: 'left' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '而且这条链后来没有停。有人从学员变成老师，从居家接单变成合作社成员。她们不是只收到一次帮助，也把技艺、产品和就业机会继续交给别人。', side: 'right' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '那我不再画一只伸向灾区的手，改成四组相接的手：提供资源、生产授艺、组织连接、购买使用。每组都写清它做了什么。', side: 'left' },
        { speaker: '同心档案台', role: '来源、许可与往返记录系统', text: '关系校准：支援具有公共价值；当地参与者同时是生产者、传承者和后来合作的发起者。共同重建不是单向施予。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'classify', title: '把每一种行动放回关系图', instruction: '判断这些行动主要属于公共支援、本地主体行动，还是连接双方的协作环节。',
        bins: [
          { id: 'support', label: '公共与社会支援', note: '提供政策、培训资源与恢复条件。' },
          { id: 'local', label: '本地主体行动', note: '生产、学习、授艺并组织长期生活。' },
          { id: 'connection', label: '协作连接', note: '让材料、产品、订单和市场形成往返。' },
        ],
        cards: [
          { id: 'display', label: '组织培训并提供就业帮扶资源', detail: '为恢复生产和学习创造条件。', correctBin: 'support' },
          { id: 'crop', label: '当地妇女学习、绣制并逐步参与授艺', detail: '不是被动等待，而是持续实践。', correctBin: 'local' },
          { id: 'generation', label: '帮扶中心、合作社与企业组织验收销售', detail: '把家庭生产接入稳定协作。', correctBin: 'connection' },
          { id: 'training', label: '各地消费者购买和使用羌绣产品', detail: '让技艺进入更广阔的共同生活。', correctBin: 'connection' },
        ], success: '关系图同时保留支援与自救：有人搭桥，有人走路，也有人后来把桥继续修向别人。', retry: '不要把所有行动都归给援助方；生产、学习和授艺属于当地参与者的主体行动。',
      }, evidenceId: 'contemporary_many_hands', marksLens: true,
    },
    {
      id: '02', title: '十几年后，培训表上出现更多来路', place: '当代培训教室 · 汶理茂与跨地学员墙', objective: '看见羌绣如何由灾后恢复进入跨县培训、学校教育和不同地区的共同学习',
      layer: '史料确证', layerNote: '跨县培训、不同省份及汉藏羌等多民族学员共同研修见于公开资料；本幕具体班级和对白为虚构。',
      background: '/assets/contemporary/qiang-workshop-photoreal-v2.png', position: '62% center', framing: 'technique-table', motif: 'stitch-path',
      dialogue: [
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '旧箱子的编号只有一列，现在这张学员墙却来自汶川、理县、茂县，也有外省来研修的教师和设计学生。大家为什么来，答案并不一样。', side: 'left' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '有人要继续做老师，有人想改进产品，有人研究非遗保护，也有人第一次拿针。共同上课不等于学完以后都做同一种作品。', side: 'right' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '我来之前准备了很多“赋能传统”的方案。上了两天课才发现，我连布面为什么起皱都看不懂，先要学会把自己的技术放到合适的位置。', side: 'left' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '我不准备把自己包装成羌绣传承人。我学的是电商，要解决的是作者名字、订单规格和结算别在平台页面上消失。', side: 'right' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '这就是现在的传承网络：会绣的人继续教，不会绣的人也能在记录、设计、销售和教育里承担责任，但谁都不能越过自己的位置替别人发言。', side: 'left' },
        { speaker: '同心档案台', role: '来源、许可与往返记录系统', text: '当前关系新增：跨县师资、不同民族与地区的学员、职业教育、设计合作、线上市场。请保留参与差异，不把共同学习写成身份同化。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'multi', title: '今天的传承网络', instruction: '选择所有能够由资料支持、又不抹去参与差异的判断。',
        options: [
          { id: 'knowledge', label: '汶川、理县、茂县通过跨县协同开展羌绣培训', detail: '培训资源开始跨越县域组织。' },
          { id: 'visual_ref', label: '不同省份、不同民族的学员可以共同研修', detail: '共同学习不要求身份和目标相同。' },
          { id: 'finished_craft', label: '教师、学员、设计者和销售者承担不同责任', detail: '传承网络不只包含手工制作一个环节。' },
          { id: 'replace_learning', label: '只要共同上课，所有人就获得同样的文化解释权', detail: '参与学习不等于可以替文化主体统一发言。' },
        ], correctIds: ['knowledge', 'visual_ref', 'finished_craft'], success: '同一间教室里的人可以拥有不同来路、能力与目标；共同的是学习和负责，不是变成同一种身份。', retry: '跨地协同、多民族共同研修和角色分工有资料支持；共同上课不等于获得同样解释权。',
      }, evidenceId: 'contemporary_learning_network',
    },
    {
      id: '03', title: '二十四个共创包，不能只装一种声音', place: '工坊打包台 · 跨地学校交流项目', objective: '把羌绣创作者、远方学生和往返记录设计成平等参与的交流结构',
      layer: '剧情虚构', layerNote: '二十四所学校与接针包为虚构项目，用于承接真实存在的学校传习、研修与跨地交流。',
      background: '/assets/contemporary/qiang-workshop-v1.png', position: '44% center', framing: 'motif-shelf', motif: 'unlabelled-pattern',
      dialogue: [
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '合作学校要二十四套材料。我原计划打印同一张“同心纹样”，每校完成一部分，最后在网上拼成完整大图，制作速度最快。', side: 'left' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '那远方学生只是在替你的大图填颜色，本地创作者也只是提供“民族风格”。看起来很多人参与，决定权还是只在设计图的人手里。', side: 'right' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '能不能做成往返？每个包先放一位创作者为这次交流新做的起针片和语音卡，再留一块空白，让学生用自己的生活经验回应。', side: 'left' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '回应可以是刺绣吗？如果学生只上过一节线上课，就把成品称作羌绣，会不会又把体验当成掌握？', side: 'right', tone: 'question' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '可以练习看得懂的步骤，但回件要写“学习回应”，不能冒充传统羌绣。也可以用绘画、文字、编织或影像说自己的家乡，不必复制我们的花样。', side: 'left' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '最后再放一张回邮卡：谁做了起针，谁作了回应，各自允许展示到哪里，又从对方那里学到了什么。二十四个包不必长得一样。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'single', title: '选择共创包结构', instruction: '哪一种结构能够产生真正的往返，而不是让多人替一张统一设计图劳动？',
        options: [
          { id: 'category', label: '署名起针片 + 创作者说明 + 空白回应材料 + 双方回邮卡', detail: '双方都有内容、选择与被记录的位置。' },
          { id: 'symbol', label: '统一AI纹样 + 二十四校分区填色', detail: '参与人数增加了，决定仍集中在一张标准图上。' },
          { id: 'identity', label: '匿名传统纹样 + 模仿教程', detail: '既看不见来源，也容易把短期体验冒充技艺掌握。' },
        ], correctIds: ['category'], success: '“接针包”建立了往返结构：一方发出具体作品和说明，另一方带着自己的生活回应，再把问题与成果送回。', retry: '真正的共创必须让双方都有独立贡献、署名、选择和回到对方身边的路径。',
      }, evidenceId: 'contemporary_exchange_kit',
    },
    {
      id: '04', title: '模型把二十多件作品平均成一张', place: '数字工作台 · “同心纹样”预览页', objective: '识别统一生成图抹掉的作者、差异和往返关系，并重新限定AI用途',
      layer: '剧情虚构', layerNote: '统一纹样生成事故为虚构；AI仅可在本项目中承担经确认的转写、检索和关系可视化。',
      background: '/assets/contemporary/qiang-workshop-photoreal-v2.png', position: '38% center', framing: 'source-rights', motif: 'two-ledgers',
      dialogue: [
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '我得承认已经做过一个版本。我把二十多张学员作品送进生成工具，提示它“提炼共同特征，生成中华民族同心纹样”。', side: 'left' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '预览图确实整齐，可作者栏只剩“AI与联合学员”。阿若老师的停针、另一位学员的配色、初学者保留下来的不熟练，全被平均掉了。', side: 'right' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '二十多件作品放在一起，本来能看见不同年龄、不同学习阶段和不同选择。合成一张以后，只剩下机器认为大家共同的外观。', side: 'left' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '我原以为相似越多越能表达团结。现在看，它证明的只是算法会取平均值，不能证明这些人真正认识过彼此。', side: 'right', tone: 'quiet' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: 'AI不是完全不能用。二十四段语音可以在本人确认后转成文字，学校回件可以按问题分类，关系图也可以帮助大家找到谁回应了谁。', side: 'left' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '可以。让它整理来往，不替我们制造一件从来没有共同做过的“共同传统”。生成图删除，原作品和作者卡恢复。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'classify', title: '重新安排AI和作品的位置', instruction: '把内容分别放入保留原作、AI辅助或退出项目三类。',
        bins: [
          { id: 'knowledge', label: '保留独立作品', note: '作者、差异与具体说明不可被平均。' },
          { id: 'generation', label: 'AI辅助往返', note: '只承担经确认的转写、检索与关系整理。' },
          { id: 'review', label: '退出项目', note: '无法说明真实共同创作关系的统一生成物。' },
        ],
        cards: [
          { id: 'official_text', label: '二十四位创作者分别署名的起针片', detail: '差异本身就是学习材料。', correctBin: 'knowledge' },
          { id: 'demo_asset', label: '经本人复核的语音转写与问题索引', detail: '帮助远方学生理解和提问。', correctBin: 'generation' },
          { id: 'public_photo', label: 'AI生成的统一“同心纹样”', detail: '没有真实共同创作过程，却抹掉具体作者。', correctBin: 'review' },
          { id: 'display_only', label: '学校、作者与回件之间的关系地图', detail: '只呈现谁与谁发生了往返，不评价哪件更正宗。', correctBin: 'generation' },
        ], success: 'AI从“替大家画成一样”改为“帮助大家找到彼此”；作品和解释仍留在具体参与者手中。', retry: '保留独立作品；转写、检索和关系图可以辅助；统一生成纹样退出。',
      }, evidenceId: 'contemporary_ai_boundary',
    },
    {
      id: '05', title: '一只接针包，要走一个来回', place: '工坊打包台 · 起针、回应与回邮三栏', objective: '组装能够让本地创作者和远方学生都作出贡献的往返结构',
      layer: '剧情虚构', layerNote: '接针包玩法为项目虚构；分别署名、明确用途和持续确认是共创方法边界。',
      background: '/assets/contemporary/qiang-workshop-v1.png', position: '58% center', framing: 'consent-screen', motif: 'pause-thread',
      dialogue: [
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '我先做第一只。起针片只完成一半，旁边的语音卡说明我为什么从这里开始，也明确这不是让学生照抄的标准答案。', side: 'left' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '我在平板里放三种入口：看正反面细节、听创作者说明、提交问题。AI只生成转写初稿，阿若确认后才能随包寄出。', side: 'right' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '空白回应材料不能只配一种。有人会针线，有人不会；可以选布、纸或录音卡，只要说清自己回应的是哪句话、哪一个动作。', side: 'left' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '回件不要写“学生完成羌绣”。写“学习回应”，并保留学生自己的家乡、生活和材料选择。我们收到以后也要认真回一段，不是收完展出就算结束。', side: 'right' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '那关系图不按“谁最像原作”排序，只显示谁发出、谁回应、双方问了什么、是否继续联系。', side: 'left' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '我负责每包的作者卡、学校卡和回邮编号。二十四次往返都能查到具体人，不能最后只剩一句“全国青少年共同创作”。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'assemble', title: '组装第一只接针包', instruction: '依次选择出发、回应和归来三个环节，保证双方都有自己的内容与名字。',
        slots: [
          { id: 'purpose', label: '从工坊出发', prompt: '包里先放什么？', correctId: 'purpose_good', options: [
            { id: 'purpose_good', label: '署名起针片、本人说明、允许用途与一个真实问题', detail: '创作者不是素材来源，而是交流发起者。' },
            { id: 'purpose_bad', label: '匿名传统纹样和统一模仿步骤', detail: '没有具体作者，也没有提问关系。' },
          ] },
          { id: 'credit', label: '在远方回应', prompt: '学生怎样参与？', correctId: 'credit_good', options: [
            { id: 'credit_good', label: '用自己的材料回应具体内容，标注学习而非冒充传承', detail: '回应者保留自己的生活经验。' },
            { id: 'credit_bad', label: '尽量复制得和原作一样，再统一署名', detail: '把相似度误当理解。' },
          ] },
          { id: 'choice', label: '回到工坊', prompt: '作品寄回后怎么办？', correctId: 'choice_good', options: [
            { id: 'choice_good', label: '双方分别落款、互相回信，再决定是否共同展示', detail: '往返完成以后仍保留选择。' },
            { id: 'choice_bad', label: '平台自动合并成统一民族纹样', detail: '往返重新被压回一张平均图。' },
          ] },
        ], success: '第一只接针包可以出发：它带着一位创作者的具体问题去，也为远方学生的生活留下位置，最后还必须带着两个人的名字回来。', retry: '出发要有创作者和问题，回应要有自己的内容，归来要有双方落款与继续决定。',
      }, evidenceId: 'contemporary_exchange_protocol',
    },
    {
      id: '06', title: '试寄回信没有照着原作绣', place: '跨地视频课 · 第一只接针包试寄', objective: '判断远方学生的参与是模仿、学习，还是带着自身经验作出回应',
      layer: '剧情虚构', layerNote: '试寄学校、学生与回件均为虚构；学生体验不能被表述为完成传统羌绣传承。',
      background: '/assets/contemporary/cocreation-sample-v1.png', position: 'center', framing: 'provenance-card', motif: 'woven-provenance',
      dialogue: [
        { speaker: '小满', role: '远方学校学生 · 虚构角色', text: '阿若老师，我试着照起针片做，线总是拉歪。我后来没有继续模仿，改用蓝纸剪了家门口每天经过的潮水线。这样算没有完成任务吗？', side: 'left', tone: 'question' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '这反而回答了我放进包里的问题：“一条线怎样记住你生活的地方？”你没有把剪纸叫羌绣，也没有假装已经学会针法；你的潮水线是你自己的回应。', side: 'right' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '系统刚才自动把你的作品标题写成“海洋版羌绣纹样”，我已经撤下。AI只看见它回应了起针片，却分不清学习关系和作品类别。', side: 'left', tone: 'warning' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '回件卡改成两栏：阿若的起针片属于羌绣当代创作；小满用剪纸回应家乡潮水。两件作品有关系，但不会因此变成同一种技艺。', side: 'right' },
        { speaker: '小满', role: '远方学校学生 · 虚构角色', text: '那我还想问：阿若老师为什么把一半留给陌生人？我原以为任务是把空白填满，现在觉得也可以留下没回答完的地方。', side: 'left' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '这个问题我要带回班里，请其他创作者分别回答。你没有替我们完成作品，却让我们重新想自己的做法。这就是回信对工坊的作用。', side: 'right', tone: 'resolve' },
      ],
      challenge: {
        kind: 'single', title: '给试寄成果写联合展签', instruction: '选择能够说明二者关系、又不把剪纸冒充羌绣的写法。',
        options: [
          { id: 'proper', label: '阿若羌绣起针片《山路》× 小满剪纸回应《潮水线》', detail: '共同问题：一条线怎样记录生活的地方；两位作者、两种材料分别署名。' },
          { id: 'authentic', label: '沿海学生创新完成“海洋羌绣”', detail: '把短期学习回应误写成新的羌绣类别。' },
          { id: 'style', label: 'AI融合山地与海洋民族风格', detail: '再次用统一生成结果取代真实往返。' },
        ], correctIds: ['proper'], success: '两件不同的作品因一个真实问题建立联系；它们不必改成同一种技艺，也能共同进入展览。', retry: '保留两位作者、两种材料和同一个往返问题，不能把回应冒充羌绣。',
      }, evidenceId: 'contemporary_pilot_reply', marksLens: true,
    },
    {
      id: '07', title: '二十四只箱子，三种寄法', place: '工坊出货区 · 学校交流项目决策会', objective: '在传播规模、准备时间和真实往返之间决定项目如何继续',
      layer: '剧情虚构', layerNote: '三条路线均保留作者与作品边界，但在参与规模、速度、成本和关系深度上承担不同代价。',
      background: '/assets/contemporary/qiang-workshop-photoreal-v2.png', position: '50% center', framing: 'generation-decision', motif: 'four-threads',
      dialogue: [
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '二十四所学校都确认收件，但工坊只有八位创作者完成了起针片和语音复核。若强行按期寄出，其余十六包只能换成统一印刷品。', side: 'left', tone: 'warning' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '可以把八份内容复制三次，二十四所学校都能参与，关系图也会很热闹。只是同一位创作者要面对三组回件，未必有时间逐一回答。', side: 'right' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '也可以先只做八组一对一。规模小，但每封回信都有人接。剩下十六校要说明延期，不能让统一材料假装已经准备好。', side: 'left' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '第三条路是先寄问题卡，不寄作品。让二十四校说想了解什么，再由创作者选择愿意回应的问题；往返更平等，但项目至少延后一个月。', side: 'right' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '还有最稳妥的一条：不寄材料，只做灾后到今天的档案展。事实最完整，也不会产生模仿误解，可远方学生只剩观看。', side: 'left' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '选择哪条都要写清代价。不要为了画面上出现更多连接线，就把没人有时间回应的寄件也算作“同心”。', side: 'right', tone: 'resolve' },
      ],
      challenge: { kind: 'final', title: '接针项目寄出决定', instruction: '选择你愿意承担的交流方式；真正的连接不仅要寄出去，也要有人接住并回到对方身边。' },
    },
    {
      id: '08', title: '寄出的材料，必须有人接回来', place: '接针项目第一次复盘会', objective: '按照已经作出的寄送决定，检查这次交流是否真的形成了往返关系',
      layer: '剧情虚构', layerNote: '学校数量、回件数据和项目反馈均为剧情虚构；不同路线展示规模、速度与关系深度之间的真实张力。',
      background: '/assets/contemporary/cocreation-sample-v1.png', position: 'center', framing: 'source-wall', motif: 'thread-complete',
      dialogue: [
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '复盘表不按“寄出多少只箱子”排名。我们记四件事：谁寄出、谁接到、对方做了什么、这件事有没有再回到原作者手里。', side: 'left' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '关系图也删掉了参与热度和相似度评分。AI只帮我们索引问题、回件、复核状态和下一次联系，不判断谁的作品更像谁。', side: 'right' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '寄得多，能让更多人看见；寄得少，才有可能一封一封回。我们要诚实记录自己接得住多少关系，不能把单向投递画成同心。', side: 'left', tone: 'resolve' },
      ],
      branchDialogue: {
        remove_asset: [
          { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '你选择了先做档案展，不寄材料。旧箱里的培训、交活、验收、销售和后来的授艺关系被完整展开，二十四所学校都在线参观。', side: 'left' },
          { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '学生留下了一百三十七个问题：有人问一件作品怎样定价，有人问灾后为什么还愿意继续学，也有人问年轻人会不会离开家乡。', side: 'right' },
          { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '但没有一件学生作品回来，也没有创作者承诺逐一回答。现在的关系只到“看见和发问”，不能把它写成已经共同创作。', side: 'left' },
          { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '这条路线守住了准确叙述，是第一步。下一轮必须为谁回答、怎样回信、何时结束留出位置，联系才能继续长下去。', side: 'right', tone: 'resolve' },
        ],
        request_review: [
          { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '你选择先寄问题卡。一个月后，二十四校寄回的问题很不整齐：有人关心针脚，有人问收入，有人把家乡的布、纸和声音也放进信封。', side: 'left' },
          { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '创作者没有被分配题目，而是各自挑选愿意回答的问题，再决定做怎样的起针片。学生第一次参与的不是模仿图案，而是决定交流从哪里开始。', side: 'right' },
          { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '项目晚了一个月，没有整齐的开箱照片，也少了一轮宣传。但关系的第一笔变成“学生发问—创作者选择回应”，不是平台替双方配对。', side: 'left' },
          { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '进度慢了，位置却更平等：远方学生不是只负责接受，本地创作者也不是被要求展示。二十四条线从问题出发，之后才进入作品往返。', side: 'right', tone: 'resolve' },
        ],
        use_authorized: [
          { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '你选择八组一对一先行，十六校延期。八件回件没有一件照抄起针片：有剪纸、声音地图、旧校服拼贴，也有一块坦白标着“初学练习”的针脚。', side: 'left' },
          { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '系统只确认每一组至少完成一次“寄出—回应—原作者再答复”。八位创作者没有被迫同时应付三所学校，关系图虽然稀疏，却每条都闭合。', side: 'right' },
          { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '延期的十六校能看到准确进度、等待原因和下一轮名单。我们没有拿复制材料填满空位，也没有把收到快递冒充成已经建立关系。', side: 'left' },
          { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '规模小，等待长，但八封回信都改变了两边下一步要问的问题。同心不是把线画得最多，而是线的两端都有人。', side: 'right', tone: 'resolve' },
        ],
      },
    },
    {
      id: '09', title: '关系图没有生成一朵“共同的花”', place: '同心回望 · 灾后重建—当代学习—跨地回信关系图', objective: '理解共同体如何在支援、自主行动、互相学习和持续往返中形成',
      layer: '研究解释', layerNote: '本幕依据灾后非遗保护、生产帮扶和当代培训实践作综合解释；角色均为个体化虚构人物，不代表任何民族的统一立场。',
      background: '/assets/contemporary/qiang-workshop-photoreal-v2.png', position: '50% center', framing: 'living-culture-coda', motif: 'thread-complete',
      dialogue: [
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '我把二〇〇八年的资料箱和今天的回信放在同一张图上。前一段有政策、培训、生产和销售；后一段有教师、设计者、学生、学校，也有寄出去又回来的问题。', side: 'left' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '图上没有中心纹样，也没有相似度排名。它只记录谁提供条件、谁学习和生产、谁购买与传播、谁提出问题、谁作出回应。', side: 'right' },
        { speaker: '阿若', role: '羌绣合作社青年教师 · 羌族虚构角色', text: '灾后支援让生产和培训有了条件，本地人又用一针一线恢复生活、继续授艺。今天我们把作品寄出去，不是在偿还一份人情，而是在以创作者的身份参与共同生活。', side: 'left' },
        { speaker: '拉姆', role: '州内职校电商学生 · 藏族虚构角色', text: '远方学生没有因此成为羌绣传承人，我也不会因为负责销售就替阿若解释所有纹样。每个人的位置说得更清楚，合作反而更可信。', side: 'right' },
        { speaker: '顾槿', role: '东部高校交互设计师 · 汉族虚构角色', text: '我最初想生成一朵人人看得懂的“同心花”。现在才明白，图上这些不整齐、会停顿、还要继续回信的线，比一张统一图案更能说明共同意味着什么。', side: 'left' },
        { speaker: '同心档案台', role: '来源、边界与往返记录系统', text: '本章归档：各民族文化在交往交流交融中共同构成中华文化，但共同从不要求差异消失。支援与自强、传承与创新、本地与远方，只有在彼此有位置、能回应、愿意继续往返时，才真正连成同心。', side: 'right', tone: 'resolve' },
      ],
    },
  ],
}

export const FIVE_CHAPTER_STORIES: Record<StoryChapterSlug, StoryChapter> = {
  han,
  'northern-wei': northernWei,
  tang,
  qing,
  contemporary,
}

export function isStoryChapterSlug(slug: string): slug is StoryChapterSlug {
  return slug in FIVE_CHAPTER_STORIES
}
