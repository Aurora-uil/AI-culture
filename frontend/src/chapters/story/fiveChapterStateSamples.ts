import type { StoryChapterSlug } from './fiveChapterStories'

/** 交给自动化测试与联调使用的剧情状态样例。 */
export interface StoryStateSample {
  id: string
  chapter: StoryChapterSlug
  sceneId: string
  description: string
  input: {
    kind: 'inspect' | 'choice' | 'classify' | 'assemble' | 'decision' | 'advance'
    value: string[] | Record<string, string> | string
  }
  expected: {
    sceneCompleted: boolean
    nextSceneId?: string
    decisionId?: string
    evidenceId?: string
    revisionDelta?: number
    thematicOutcome: string
  }
}

export const FIVE_CHAPTER_STATE_SAMPLES: Record<StoryChapterSlug, StoryStateSample[]> = {
  han: [
    { id: 'han-opening-evidence', chapter: 'han', sceneId: '00', description: '查完三张卡后识别错误来自强行建立直接关系。', input: { kind: 'inspect', value: ['mission_138', 'niya_1995', 'direct_relation'] }, expected: { sceneCompleted: true, nextSceneId: '01', evidenceId: 'han_caption_split', thematicOutcome: '保留张骞与锦护膊的历史联系，但删除未经证实的携带关系。' } },
    { id: 'han-retry-boundary', chapter: 'han', sceneId: '01', description: '把年代相容误选为直接关系时保留当前场并记录修订。', input: { kind: 'choice', value: ['direct'] }, expected: { sceneCompleted: false, revisionDelta: 1, thematicOutcome: '反馈强调年代相容不能自动生成直接人物关系。' } },
    { id: 'han-final-network', chapter: 'han', sceneId: '07', description: '选择长期网络路线后进入人物后果场。', input: { kind: 'decision', value: 'ask_travellers' }, expected: { sceneCompleted: true, nextSceneId: '08', decisionId: 'ask_travellers', thematicOutcome: '张骞仍是重要节点，匿名参与者与后续往来共同进入展签。' } },
  ],
  'northern-wei': [
    { id: 'wei-individual-scope', chapter: 'northern-wei', sceneId: '01', description: '把墓志限定在可确认的个人尺度。', input: { kind: 'choice', value: ['identity', 'institution'] }, expected: { sceneCompleted: true, nextSceneId: '02', evidenceId: 'wei_epitaph_scope', thematicOutcome: '墓志不再替整个时代发言。' } },
    { id: 'wei-change-model', chapter: 'northern-wei', sceneId: '06', description: '完成个案、比较与未知三层变化叙述。', input: { kind: 'assemble', value: { case: 'case_good', comparison: 'compare_good', unknown: 'unknown_good' } }, expected: { sceneCompleted: true, nextSceneId: '07', evidenceId: 'wei_change_model', thematicOutcome: '采用、改造、并存与延续不再被写成单向替代。' } },
    { id: 'wei-final-two-cities', chapter: 'northern-wei', sceneId: '07', description: '选择让平城来处与洛阳生活并列。', input: { kind: 'decision', value: 'workshop_together' }, expected: { sceneCompleted: true, nextSceneId: '08', decisionId: 'workshop_together', thematicOutcome: '墓石不要求墓主在两座城之间选边。' } },
  ],
  tang: [
    { id: 'tang-name-chain', chapter: 'tang', sceneId: '01', description: '从画中禄东赞连接到画外事件而不把缺席者画入。', input: { kind: 'assemble', value: { inside: 'ludongzan', event: 'reception', outside: 'wencheng_outside' } }, expected: { sceneCompleted: true, nextSceneId: '02', evidenceId: 'tang_outside_chain', thematicOutcome: '名字成为连接相见、翻译与画外关系的入口。' } },
    { id: 'tang-private-voice-retry', chapter: 'tang', sceneId: '05', description: '替历史人物补写内心时停留当前场并触发修订。', input: { kind: 'choice', value: ['envoy_event', 'guess_dialogue'] }, expected: { sceneCompleted: false, revisionDelta: 1, thematicOutcome: '翻译可以连接语言，不能制造没有来源的私人心声。' } },
    { id: 'tang-final-multiple', chapter: 'tang', sceneId: '07', description: '选择让画卷、事件与后世档案彼此限定。', input: { kind: 'decision', value: 'keep_multiple_views' }, expected: { sceneCompleted: true, nextSceneId: '08', decisionId: 'keep_multiple_views', thematicOutcome: '任何一种材料都不独占历史，相见走向长期关系。' } },
  ],
  qing: [
    { id: 'qing-relief-with-boundary', chapter: 'qing', sceneId: '01', description: '名册受损时先按眼前丁口救急，同时把原册信息标为待核。', input: { kind: 'choice', value: ['aid_and_mark'] }, expected: { sceneCompleted: true, nextSceneId: '02', evidenceId: 'qing_relief_first', thematicOutcome: '档案空白既没有被虚构填满，也没有替眼前的人拒绝救急。' } },
    { id: 'qing-average-retry', chapter: 'qing', sceneId: '03', description: '把不同来源数字平均成唯一值时记录修订。', input: { kind: 'choice', value: ['average'] }, expected: { sceneCompleted: false, revisionDelta: 1, thematicOutcome: '数字差异被保留为来源问题，而非计算误差。' } },
    { id: 'qing-final-shared-ledger', chapter: 'qing', sceneId: '07', description: '选择建立今夜—明春双页责任链。', input: { kind: 'decision', value: 'follow_route' }, expected: { sceneCompleted: true, nextSceneId: '08', decisionId: 'follow_route', thematicOutcome: '归来者、书手与赶运人共同签下未完事项，救急与长久生活被接在一起。' } },
  ],
  contemporary: [
    { id: 'now-recovery-network', chapter: 'contemporary', sceneId: '01', description: '把灾后羌绣恢复中的支援、本地主体行动与协作连接分别放回关系图。', input: { kind: 'classify', value: { display: 'support', crop: 'local', generation: 'connection', training: 'connection' } }, expected: { sceneCompleted: true, nextSceneId: '02', evidenceId: 'contemporary_many_hands', thematicOutcome: '公共支援和本地生产自救同时可见，重建不再被叙述成单向施予。' } },
    { id: 'now-unified-pattern-retry', chapter: 'contemporary', sceneId: '03', description: '选择统一AI纹样让二十四校分区填色时记录修订。', input: { kind: 'choice', value: ['symbol'] }, expected: { sceneCompleted: false, revisionDelta: 1, thematicOutcome: '参与人数不等于共同决定，统一外观不能代替真实往返。' } },
    { id: 'now-final-question-first', chapter: 'contemporary', sceneId: '07', description: '选择先寄问题卡，让学生发问、创作者自主选择回应。', input: { kind: 'decision', value: 'request_review' }, expected: { sceneCompleted: true, nextSceneId: '08', decisionId: 'request_review', thematicOutcome: '双方共同定义交流起点，用延期换取更平等的进入方式。' } },
  ],
}

