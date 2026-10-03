export type YuanEvidenceLayer = '史料确证' | '合理重建' | '剧情虚构'

export interface YuanDialogueLine {
  speaker: string
  text: string
  tone?: 'quiet' | 'tense' | 'turn' | 'system'
}

export interface YuanStoryScene {
  id: string
  title: string
  period: string
  location: string
  objective: string
  layer: YuanEvidenceLayer
  layerNote: string
  dialogue: YuanDialogueLine[]
}

export interface RuleCard {
  id: string
  label: string
  answer: RuleGroup
}

export type RuleGroup = 'shared' | 'coordinate' | 'preserve'

export const YUAN_STORY_SCENES: YuanStoryScene[] = [
  {
    id: '00',
    title: '第七块',
    period: '当代',
    location: '数字档案室',
    objective: '确认冲突，进入证据剧场',
    layer: '合理重建',
    layerNote: '数字校勘界面为游戏化重构；云台及六体题刻为史实锚点。',
    dialogue: [
      { speaker: '同心', text: '第七块存在位置冲突：尺寸和边缘关系与当前位置匹配，文本结构却在这里断裂。', tone: 'system' },
      { speaker: '你', text: '旧档案为什么把它放在这里？' },
      { speaker: '同心', text: '记录只写着“位置据旧校样复核”。旧校样没有完整保存，判断者也无法确认。', tone: 'system' },
      { speaker: '同心', text: '是否进入证据剧场，查看这一判断可能形成的历史情境？', tone: 'turn' },
    ],
  },
  {
    id: '01',
    title: '两份都对不上',
    period: '元至正五年 · 1345',
    location: '居庸关过街塔施工现场',
    objective: '分别检查两份都曾被使用的校样',
    layer: '剧情虚构',
    layerNote: '人物、双校样冲突与限时情境为剧情创作，不视作真实档案。',
    dialogue: [
      { speaker: '现场负责人', text: '这一面今天必须定。天黑以前，给我一个能让人继续做事的说法。', tone: 'tense' },
      { speaker: '陈砺', text: '右边这一份位置、尺寸都核过。可今天早上，木架后面又翻出左边这张。' },
      { speaker: '帖木儿', text: '都有折痕，都在现场用过，也都有核过的记号。没人能证明哪张才是最后一张。' },
      { speaker: '你', text: '他们争的不是同一件事：一个在问能不能施工，一个在问文本是否还接得上。', tone: 'turn' },
    ],
  },
  {
    id: '02',
    title: '最方便的一版',
    period: '1345',
    location: '石壁与施工木案',
    objective: '从施工链条理解“统一”的价值',
    layer: '合理重建',
    layerNote: '工种协作与校样流程属于基于营造逻辑的合理重建。',
    dialogue: [
      { speaker: '陈砺', text: '写样、凿石、搬运是不同的人。一个人画得再明白，下一道工序看不懂，就等于没画。' },
      { speaker: '你', text: '所以才统一编号和位置？' },
      { speaker: '陈砺', text: '大家一起做事，总得有大家都认得的规矩。' },
      { speaker: '帖木儿', text: '规矩没错。问题是，这套规矩管到了文字本身的排列。', tone: 'turn' },
    ],
  },
  {
    id: '03',
    title: '一份更整齐的石壁',
    period: '1345',
    location: '第二份校样前',
    objective: '辨认哪些变化会切断文本结构',
    layer: '合理重建',
    layerNote: '版面、方向和文本内部结构的校核方式为玩法重构。',
    dialogue: [
      { speaker: '帖木儿', text: '施工版确实更规整。如果只是画一张好看的图，没有问题。' },
      { speaker: '你', text: '改开一点，也会改变内容？' },
      { speaker: '帖木儿', text: '有些不会，有些会。所以我们才需要核。' },
      { speaker: '帖木儿', text: '我认得纸上的东西，却不认得它经历过什么。', tone: 'quiet' },
    ],
  },
  {
    id: '04',
    title: '雨水',
    period: '1345',
    location: '木案背面',
    objective: '检查水痕、折线和墨迹，不急着归责',
    layer: '剧情虚构',
    layerNote: '雨天移动纸样及其造成的嫌疑是剧情装置。',
    dialogue: [
      { speaker: '陈砺', text: '前些天雨来得快。我收过一批纸。' },
      { speaker: '帖木儿', text: '后来怎么放回去？你根本不知道上面写的是什么。', tone: 'tense' },
      { speaker: '陈砺', text: '对，我不知道。但哪块石料换过、哪处重新量过，我知道。' },
      { speaker: '陈砺', text: '你不能因为我看不懂这些字，就先把答案写在我头上。', tone: 'turn' },
    ],
  },
  {
    id: '05',
    title: '不是谁把它放错了',
    period: '1345',
    location: '两份校样之间',
    objective: '验证两份校样是否真的在争同一个位置',
    layer: '剧情虚构',
    layerNote: '人物自改校样和版本反转服务于证据推理，不是史实陈述。',
    dialogue: [
      { speaker: '桑结', text: '你们一直在找谁动过、谁放错了。可如果它们本来就是两个阶段留下来的呢？', tone: 'turn' },
      { speaker: '桑结', text: '前一份确定大体位置，后一份再根据文本调整——或者反过来。' },
      { speaker: '帖木儿', text: '这里是我改的。比那场雨早。没人让我改。', tone: 'quiet' },
      { speaker: '你', text: '问题不再是谁把旧版放回来，而是为什么两个版本一直被不同的人修改。', tone: 'turn' },
    ],
  },
  {
    id: '06',
    title: '共同的规矩',
    period: '1345',
    location: '共同校勘木案',
    objective: '把规则分成“统一、协调、保留”三类',
    layer: '合理重建',
    layerNote: '规则分层是对共同施工问题的游戏化抽象。',
    dialogue: [
      { speaker: '你', text: '第二版没有推翻第一版，它沿用了位置编号和尺度基准，只在部分区域恢复文本原有结构。' },
      { speaker: '陈砺', text: '所以前一版也没全错。' },
      { speaker: '桑结', text: '本来就不是谁全错、谁全对。' },
      { speaker: '你', text: '问题不是有规矩，而是有些规矩管到了不该管的地方。', tone: 'turn' },
    ],
  },
  {
    id: '07',
    title: '六种文字，多少种人',
    period: '1345',
    location: '券洞石壁前',
    objective: '回答文字、语言与人群是否可以直接对应',
    layer: '史料确证',
    layerNote: '六体并存可确认；由文字数量直接推断固定数量的人群则不成立。',
    dialogue: [
      { speaker: '陈砺', text: '这么多种写法放在一处，是不是说明来这里的人也有这么多种？' },
      { speaker: '帖木儿', text: '可以数文字，但不能顺手把人也数出来。' },
      { speaker: '桑结', text: '文字留下来了；人留下的痕迹，不一定都这么清楚。', tone: 'quiet' },
    ],
  },
  {
    id: '08',
    title: '今天到底按什么做',
    period: '1345',
    location: '施工决定现场',
    objective: '把复杂证据压缩成一个可以执行的判断',
    layer: '剧情虚构',
    layerNote: '三种决定及其人物反馈为互动结局，不改变真实历史。',
    dialogue: [
      { speaker: '现场负责人', text: '定了？你说。', tone: 'tense' },
      { speaker: '你', text: '证据并不整齐，但施工需要一个能够承担后果的判断。' },
    ],
  },
  {
    id: '09',
    title: '门洞',
    period: '1345',
    location: '过街塔券洞',
    objective: '观察决定之后，协作如何继续',
    layer: '剧情虚构',
    layerNote: '人物收束与路人对白为剧情创作。',
    dialogue: [
      { speaker: '帖木儿', text: '外边加定位，不动里面——你刚才那个编号法挺好。' },
      { speaker: '陈砺', text: '本来就该这么做。' },
      { speaker: '路人甲', text: '看得懂？' },
      { speaker: '路人乙', text: '看不懂。看看不行？', tone: 'quiet' },
      { speaker: '桑结', text: '有人看懂这一部分，有人看懂另一部分，也有人一处都看不懂。', tone: 'turn' },
    ],
  },
  {
    id: '10',
    title: '回到当代',
    period: '当代',
    location: '数字档案室',
    objective: '校验 AI 草稿，留下有限而可靠的档案表述',
    layer: '史料确证',
    layerNote: '推荐表述遵守“文字、语言、文本、人群不互相替代”的证据边界。',
    dialogue: [
      { speaker: '同心', text: '空间匹配：高。文本结构匹配：高。版本来源：部分可确认。使用人群对应：无法直接确认。', tone: 'system' },
      { speaker: '同心', text: '是否自动生成新的档案描述？', tone: 'system' },
      { speaker: 'AI 草稿', text: '“云台六种文字反映了六个不同民族在此共同融合……”', tone: 'system' },
      { speaker: '系统警告', text: '该表述包含未经证据支持的一一对应关系。', tone: 'tense' },
      { speaker: '同心', text: '生成语言和证据校验是两个不同过程。最后仍需要你判断。', tone: 'turn' },
    ],
  },
  {
    id: '11',
    title: '证据关系图',
    period: '当代',
    location: '数字云台档案',
    objective: '封存本章记录',
    layer: '史料确证',
    layerNote: '结论只连接得到证据支持的部分，并显式保留未知。',
    dialogue: [
      { speaker: '同心', text: '版本关系已记录为“前期施工校样／后续调整版本”；具体转换过程仍有部分无法确认。', tone: 'system' },
      { speaker: '你', text: '还是有不知道的。这次不用补了。' },
      { speaker: '同心', text: '已保留。', tone: 'system' },
      { speaker: '章节结语', text: '共同留下，并不意味着变得相同。', tone: 'turn' },
    ],
  },
]

export const CONSTRUCTION_CLUES = [
  { id: 'position_marks', label: '位置标记', detail: '不同区域使用相近定位方式，便于跨工序传递。' },
  { id: 'scale_baseline', label: '尺度基准', detail: '石面预留范围明确，后续工序能够快速复核。' },
  { id: 'handoff_marks', label: '交接记号', detail: '不识读文本的人，也能依照编号继续工作。' },
]

export const TEXT_CLUES = [
  { id: 'spacing_shift', label: '间距变化', detail: '施工版把原本较密的排列拉开，使整体更规整。' },
  { id: 'direction_change', label: '方向差异', detail: '部分区域的书写方向不能套用相同定位方式。' },
  { id: 'structure_break', label: '结构断裂', detail: '一个段落关系被重新切分，内容关系可能随之改变。' },
]

export const RAIN_CLUES = [
  { id: 'water_mark', label: '纸边水痕', detail: '水痕沿纸张折叠方向延伸。' },
  { id: 'fold_line', label: '折线错位', detail: '两张纸都被移动和重新折叠过。' },
  { id: 'ink_spread', label: '墨迹扩散', detail: '墨迹与水痕一致，但不能单独证明版本先后。' },
]

export const RULE_GROUPS: { id: RuleGroup; label: string; note: string }[] = [
  { id: 'shared', label: '必须一致', note: '让不同工序能够共同执行' },
  { id: 'coordinate', label: '需要协调', note: '依据相邻区域共同调整' },
  { id: 'preserve', label: '必须保留', note: '不能为了整齐强行改变' },
]

export const RULE_CARDS: RuleCard[] = [
  { id: 'numbering', label: '施工编号', answer: 'shared' },
  { id: 'scale', label: '尺度基准', answer: 'shared' },
  { id: 'spacing', label: '区域间距', answer: 'coordinate' },
  { id: 'adjacency', label: '相邻关系', answer: 'coordinate' },
  { id: 'direction', label: '书写方向', answer: 'preserve' },
  { id: 'text_structure', label: '文本内部结构', answer: 'preserve' },
]

export const ARCHIVE_CHECKS = [
  { id: 'spatial', label: '多种文字共同出现于同一建筑空间', answer: 'supported', result: '空间关系可确认' },
  { id: 'structure', label: '不同文字的版面结构完全相同', answer: 'unsupported', result: '差异需要保留' },
  { id: 'version', label: '两份校样的具体先后与转换过程', answer: 'partial', result: '只能部分确认' },
  { id: 'people', label: '六种文字分别对应六个固定人群', answer: 'unsupported', result: '不能由文字数量直接推出' },
] as const

export const RECOMMENDED_ARCHIVE_TEXT =
  '居庸关云台题刻中，多种文字传统共同出现于同一建筑空间。不同文字在文本内容、书写方式和版面结构上既存在联系，也保留差异。现有证据可以说明不同书写传统和相关人员曾在同一工程中发生实际协作，但不能仅凭文字数量，将其简单对应为固定数量的语言或人群。'

