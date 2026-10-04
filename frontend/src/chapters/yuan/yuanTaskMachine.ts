/** 元代章任务状态机（2号队员维护）。只消费标准事件，不读对话/AI内部实现。 */
export type YuanPhase =
  | 'NOT_STARTED' | 'ROLE_ACCEPTED' | 'SCENE_ENTERED'
  | 'THREE_SCRIPTS_INSPECTED' | 'SCRIPT_LENS_USED'
  | 'FIXED_DIALOGUE_COMPLETED' | 'EVIDENCE_REVIEWED'
  | 'AI_OR_KNOWLEDGE_COMPLETED' | 'GRAPH_OPENED'
  | 'DECISION_READY' | 'CHAPTER_COMPLETED';

export interface YuanTaskState {
  phase: YuanPhase;
  roleAccepted: boolean;
  sceneEntered: boolean;
  seenScripts: string[];
  lensUsed: boolean;
  lensAllSeen: boolean;
  dialogueDone: boolean;
  evidenceReviewed: boolean;
  aiOrKnowledgeDone: boolean;
  graphOpened: boolean;
  decisionId: string | null;
  completed: boolean;
}

export const SCRIPT_ORDER = [
  'script_sanskrit_lantsa','script_tibetan','script_phagspa',
  'script_old_uyghur','script_chinese','script_tangut',
] as const;

export function emptyYuanTask(): YuanTaskState {
  return {
    phase: 'NOT_STARTED', roleAccepted: false, sceneEntered: false,
    seenScripts: [], lensUsed: false, lensAllSeen: false,
    dialogueDone: false, evidenceReviewed: false,
    aiOrKnowledgeDone: false, graphOpened: false,
    decisionId: null, completed: false,
  };
}

const KEY = 'tongxin.yuan.task.v1';
export function loadYuanTask(): YuanTaskState {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...emptyYuanTask(), ...JSON.parse(raw) };
  } catch { /* 本地记录失败不阻断 */ }
  return emptyYuanTask();
}
export function saveYuanTask(s: YuanTaskState) {
  try { localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* ignore */ }
}

/** 标准事件 → 状态推进。返回是否发生变化 */
export function applyYuanEvent(s: YuanTaskState, type: string, entityId?: string): boolean {
  let changed = false;
  const touch = (p: YuanPhase) => { if (s.phase !== 'CHAPTER_COMPLETED') { s.phase = p; changed = true; } };
  switch (type) {
    case 'YUAN_ROLE_ACCEPTED': s.roleAccepted = true; touch('ROLE_ACCEPTED'); break;
    case 'YUAN_SCENE_ENTERED': s.sceneEntered = true; touch('SCENE_ENTERED'); break;
    case 'YUAN_HOTSPOT_OPENED':
    case 'YUAN_THREE_SCRIPTS_OPENED': {
      if (entityId && (SCRIPT_ORDER as readonly string[]).includes(entityId)
        && !s.seenScripts.includes(entityId)) { s.seenScripts.push(entityId); changed = true; }
      if (s.seenScripts.length >= 3 && s.phase !== 'CHAPTER_COMPLETED') { touch('THREE_SCRIPTS_INSPECTED'); }
      break;
    }
    case 'YUAN_ALL_SCRIPTS_OPENED': s.lensAllSeen = true; changed = true; break;
    case 'YUAN_SCRIPT_LENS_USED': s.lensUsed = true; touch('SCRIPT_LENS_USED'); break;
    case 'YUAN_DIALOGUE_COMPLETED': s.dialogueDone = true; touch('FIXED_DIALOGUE_COMPLETED'); break;
    case 'YUAN_AI_QUESTION_COMPLETED':
    case 'YUAN_SOURCE_VIEWED': s.aiOrKnowledgeDone = true; s.evidenceReviewed = true; touch('AI_OR_KNOWLEDGE_COMPLETED'); break;
    case 'YUAN_GRAPH_OPENED':
    case 'YUAN_RELATION_EVIDENCE_VIEWED': s.graphOpened = true; touch('GRAPH_OPENED'); break;
    case 'YUAN_DECISION_SUBMITTED': touch('DECISION_READY'); break;
    case 'YUAN_CHAPTER_COMPLETED': s.completed = true; s.phase = 'CHAPTER_COMPLETED'; changed = true; break;
  }
  // 派生 DECISION_READY：对话+证据+图谱/AI 任一完成即可解锁选择
  if (!s.completed && s.dialogueDone && (s.aiOrKnowledgeDone || s.graphOpened) && s.phase !== 'DECISION_READY') {
    // 保持向后兼容：不强制覆盖更晚阶段
  }
  if (changed) saveYuanTask(s);
  return changed;
}

export function yuanDecisionReady(s: YuanTaskState): boolean {
  return s.dialogueDone && (s.aiOrKnowledgeDone || s.graphOpened);
}
export function yuanMinComplete(s: YuanTaskState): boolean {
  return s.sceneEntered && s.seenScripts.length >= 3 && s.aiOrKnowledgeDone && s.graphOpened;
}
