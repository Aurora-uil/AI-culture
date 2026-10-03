export type ComparisonAnswer = 'same' | 'different' | 'unknown'
export type LayoutChoice = 'shared' | 'preserve'
export type RelationAnswer = 'supported' | 'partial' | 'unsupported'
export type FinalDeductionSlot = 'fact' | 'action' | 'boundary'

export interface FinalDeductionOption {
  id: string
  label: string
  note: string
  evidenceIds: string[]
}

export interface FinalDeductionStage {
  id: FinalDeductionSlot
  index: string
  label: string
  prompt: string
  answer: string
  options: FinalDeductionOption[]
}

export const SAMPLE_COMPARE_ROWS: {
  id: string
  label: string
  clueA: string
  clueB: string
  answer: ComparisonAnswer
  result: string
}[] = [
  {
    id: 'usage',
    label: '使用痕迹',
    clueA: '折痕清楚，有现场核记',
    clueB: '边缘磨损，同样有核记',
    answer: 'same',
    result: '两份都进入过施工现场，不能先把其中一份排除。',
  },
  {
    id: 'layout',
    label: '版面处理',
    clueA: '编号与边界更统一',
    clueB: '局部保留原有组块',
    answer: 'different',
    result: '两份校样采用了不同的整理逻辑。',
  },
  {
    id: 'sequence',
    label: '版本先后',
    clueA: '没有日期与签押',
    clueB: '也没有最终版标记',
    answer: 'unknown',
    result: '使用痕迹只能证明“用过”，不能证明谁先谁后。',
  },
]

export const COMPARISON_OPTIONS: { id: ComparisonAnswer; label: string }[] = [
  { id: 'same', label: '相同' },
  { id: 'different', label: '不同' },
  { id: 'unknown', label: '无法确认' },
]

export const RELAY_STEPS = [
  { id: 'mark', short: '定', label: '校样标出位置与尺度', note: '先让所有工种看到共同基准。' },
  { id: 'number', short: '编', label: '按编号分配石料', note: '石料与施工区域建立对应。' },
  { id: 'handoff', short: '交', label: '用交接记号转入下一工序', note: '不要求每个人识读文本内容。' },
  { id: 'verify', short: '核', label: '上石前复核边缘范围', note: '在不可逆加工前再次检查。' },
] as const

export const LAYOUT_CONTROLS: {
  id: string
  label: string
  sharedLabel: string
  preserveLabel: string
  answer: LayoutChoice
  consequence: string
}[] = [
  {
    id: 'outer_anchor',
    label: '外框定位',
    sharedLabel: '统一定位',
    preserveLabel: '各自定位',
    answer: 'shared',
    consequence: '外框统一后，不同工种能够找到同一施工区域。',
  },
  {
    id: 'inner_spacing',
    label: '内部间距',
    sharedLabel: '全部拉齐',
    preserveLabel: '保留组块',
    answer: 'preserve',
    consequence: '内部间距可能属于文本结构，不能只为整齐而拉开。',
  },
  {
    id: 'writing_flow',
    label: '书写方向',
    sharedLabel: '改成同向',
    preserveLabel: '保持原向',
    answer: 'preserve',
    consequence: '方向不是装饰参数，错误调整会切断原有关系。',
  },
]

export const RAIN_RELATIONS: {
  id: string
  from: string
  to: string
  answer: RelationAnswer
  result: string
}[] = [
  {
    id: 'rain_trace',
    from: '突发雨水',
    to: '纸边水痕与墨迹扩散',
    answer: 'supported',
    result: '痕迹可以支持纸张受潮。',
  },
  {
    id: 'paper_move',
    from: '陈砺收过一批纸',
    to: '两张校样后来都被移动',
    answer: 'partial',
    result: '可以确认移动发生过，无法确认由谁完成全部归位。',
  },
  {
    id: 'old_version',
    from: '其中一份带水痕',
    to: '它一定是被放回的旧稿',
    answer: 'unsupported',
    result: '水痕不等于版本先后，更不能单独完成归责。',
  },
]

export const RELATION_OPTIONS: { id: RelationAnswer; label: string }[] = [
  { id: 'supported', label: '可连接' },
  { id: 'partial', label: '只能部分连接' },
  { id: 'unsupported', label: '不能连接' },
]

export const PEOPLE_INFERENCES: {
  id: string
  claim: string
  basis: string
  answer: RelationAnswer
  result: string
}[] = [
  {
    id: 'shared_space',
    claim: '多种文字共同出现于同一建筑空间',
    basis: '石壁现状与题刻位置关系',
    answer: 'supported',
    result: '共同空间可以确认。',
  },
  {
    id: 'fixed_groups',
    claim: '六种文字分别对应六个固定人群',
    basis: '文字种类的数量',
    answer: 'unsupported',
    result: '文字数量不能直接替代历史人群证据。',
  },
  {
    id: 'working_together',
    claim: '不同书写传统相关人员曾发生实际协作',
    basis: '共同位置基准、版面衔接与施工关系',
    answer: 'partial',
    result: '协作关系可以合理说明，但参与者身份和过程不能完整复原。',
  },
]

export const PEOPLE_INFERENCE_OPTIONS: { id: RelationAnswer; label: string; mark: string }[] = [
  { id: 'supported', label: '证据支持', mark: '实' },
  { id: 'partial', label: '部分确认', mark: '限' },
  { id: 'unsupported', label: '不能推出', mark: '断' },
]

/**
 * 第八幕不是知识点复述，而是把前七幕产出的证据重新编成一条可执行结论。
 * 每组都保留一个“听起来很完整”的错误答案，用于检查玩家是否会跨越证据边界。
 */
export const FINAL_DEDUCTION_STAGES: FinalDeductionStage[] = [
  {
    id: 'fact',
    index: '壹',
    label: '确认事实',
    prompt: '两份都被使用、共同定位角可以叠合，这最多支持什么？',
    answer: 'layered_versions',
    options: [
      {
        id: 'wrong_first_draft',
        label: '第一份就是被误放回来的废稿',
        note: '水痕和移动痕迹不能证明版本先后。',
        evidenceIds: ['water_mark', 'fold_line'],
      },
      {
        id: 'layered_versions',
        label: '两份校样可能承担不同阶段功能',
        note: '共同定位与局部差异同时存在，阶段关系成立，具体先后仍未知。',
        evidenceIds: ['sample_a', 'sample_b', 'version_layers'],
      },
      {
        id: 'second_is_final',
        label: '第二份一定是最终定稿',
        note: '结构更完整不等于时间上更晚，也不等于已经签押定稿。',
        evidenceIds: ['structure_break', 'version_layers'],
      },
    ],
  },
  {
    id: 'action',
    index: '贰',
    label: '形成行动',
    prompt: '今天必须继续施工，怎样让共同标准不越过文字边界？',
    answer: 'shared_shell',
    options: [
      {
        id: 'copy_second',
        label: '全部照第二份统一排齐',
        note: '这会把施工外框的统一扩大为内部结构的统一。',
        evidenceIds: ['position_marks', 'spacing_shift'],
      },
      {
        id: 'shared_shell',
        label: '统一外框定位，保留内部结构',
        note: '编号与尺度连接工序；间距、方向和文本结构继续分别校核。',
        evidenceIds: ['scale_baseline', 'direction_change', 'shared_rules'],
      },
      {
        id: 'stop_everything',
        label: '所有区域一律停工等待新稿',
        note: '承认未知不等于放弃已经获得充分支持的行动。',
        evidenceIds: ['handoff_marks', 'shared_rules'],
      },
    ],
  },
  {
    id: 'boundary',
    index: '叁',
    label: '保留未知',
    prompt: '哪一部分必须明确写成“现在还不能推出”？',
    answer: 'sequence_and_people',
    options: [
      {
        id: 'craft_method',
        label: '共同编号是否能帮助施工',
        note: '工序接力已经直接验证了它的作用。',
        evidenceIds: ['handoff_marks', 'scale_baseline'],
      },
      {
        id: 'sequence_and_people',
        label: '版本确切先后，以及文字对应哪些人群',
        note: '现有证据只能确认协作与版本层次，不能补齐时间链和人群映射。',
        evidenceIds: ['version_layers', 'script_people_boundary'],
      },
      {
        id: 'shared_space',
        label: '多种文字是否共同存在于这处空间',
        note: '共同空间是可以确认的史实锚点，不属于未知。',
        evidenceIds: ['script_people_boundary'],
      },
    ],
  },
]
