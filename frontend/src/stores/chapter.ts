import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getChapters, getChapter, getChapterScene, getScene } from '@/api/endpoints'
import type { Chapter, ChapterSlug, Hotspot, Scene } from '@/types'

const FALLBACK_CHAPTERS: Chapter[] = [
  { id: 'han_encounter', slug: 'han', era: '汉代', keyword: '相遇', title: '张骞与丝路交通', date_label: '公元前202—公元220', guiding_question: '一件后世出土的织锦，如何证明长期联系，又不被误写成张骞的直接遗物？', accent: '#B1783A', primary_interaction: 'route_flow', ai_character_id: 'person_zhang_qian', core_entity_ids: ['person_zhang_qian', 'concept_silk_road_network', 'site_niya', 'artifact_five_star_brocade'], sort_order: 1 },
  { id: 'northern_wei_integration', slug: 'northern-wei', era: '北魏', keyword: '交融', title: '从平城到洛阳', date_label: '386—534', guiding_question: '一方墓志能说明一个人的变化，能不能代表整个时代？', accent: '#657887', primary_interaction: 'evidence_compare', ai_character_id: 'person_emperor_xiaowen', core_entity_ids: ['person_emperor_xiaowen', 'heritage_yungang', 'heritage_longmen', 'artifact_yuanyu_epitaph'], sort_order: 2 },
  { id: 'tang_exchange', slug: 'tang', era: '唐代', keyword: '交流', title: '从《步辇图》走进画外历史', date_label: '618—907', guiding_question: '一位使臣背后连接着怎样的人物与事件？', accent: '#9B3D35', primary_interaction: 'scroll_relation', ai_character_id: 'artifact_bunian_tu', core_entity_ids: ['artifact_bunian_tu', 'person_emperor_taizong', 'person_ludongzan', 'person_princess_wencheng'], sort_order: 3 },
  { id: 'yuan_yuntai', slug: 'yuan', era: '元代', keyword: '共存', title: '居庸关云台', date_label: '1271—1368', guiding_question: '为什么多种文字会同时出现在一座建筑上？', accent: '#2C6F89', primary_interaction: 'script_lens', ai_character_id: 'artifact_yuntai', core_entity_ids: ['artifact_yuntai', 'inscription_six_scripts'], sort_order: 4 },
  { id: 'qing_return', slug: 'qing', era: '清代', keyword: '归属', title: '土尔扈特东归', date_label: '1636—1912', guiding_question: '一件宫廷纪念物能记录东归的哪些面向，又遗漏了哪些声音？', accent: '#7A513B', primary_interaction: 'migration_timeline', ai_character_id: 'person_ubashi', core_entity_ids: ['person_ubashi', 'group_torghut', 'event_torghut_return_1771', 'region_ili', 'artifact_wanfa_guiyi_screen'], sort_order: 5 },
  { id: 'contemporary_qiang_embroidery', slug: 'contemporary', era: '当代', keyword: '传承', title: '羌绣数字工坊', date_label: '1949年至今', guiding_question: '一件羌绣作品进入数字共创前，谁有权决定它如何被使用？', accent: '#B64D43', primary_interaction: 'knowledge_cocreation', ai_character_id: 'qiang_workshop_narrator', core_entity_ids: ['ich_qiang_embroidery', 'technique_tiaohua', 'institution_wenchuan_cultural_center'], sort_order: 6 },
]

const FALLBACK_YUAN_SCENE: Scene = {
  id: 'yuntai_inner',
  chapter_id: 'yuan_yuntai',
  name: '云台券洞内壁',
  scene_kind: 'image',
  background_asset_id: '/assets/yuan/yuntai-east-wall-original.jpg',
  width: 3072,
  height: 2304,
  disclaimer: '历史遗址实拍图，画面为云台东壁。六种文字热点已按东壁真实版式与本图的 16:9 展示裁切校准；框选边界用于交互导览，不代表文物测绘边界。',
  hotspots: [
    { id: 'hs_artifact_yuntai', entity_id: 'artifact_yuntai', shape: 'polygon', normalized_points: [[0.30,0.06],[0.70,0.06],[0.70,0.17],[0.30,0.17]], label: '券顶', sort_order: 0 },
    { id: 'hs_script_sanskrit_lantsa', entity_id: 'script_sanskrit_lantsa', shape: 'polygon', normalized_points: [[0.03,0.245],[0.97,0.245],[0.97,0.36],[0.03,0.36]], label: '梵文书写系统', sort_order: 1 },
    { id: 'hs_script_tibetan', entity_id: 'script_tibetan', shape: 'polygon', normalized_points: [[0.03,0.365],[0.97,0.365],[0.97,0.50],[0.03,0.50]], label: '藏文', sort_order: 2 },
    { id: 'hs_script_phagspa', entity_id: 'script_phagspa', shape: 'polygon', normalized_points: [[0.025,0.505],[0.245,0.505],[0.245,0.925],[0.025,0.925]], label: '八思巴文', sort_order: 3 },
    { id: 'hs_script_old_uyghur', entity_id: 'script_old_uyghur', shape: 'polygon', normalized_points: [[0.255,0.505],[0.48,0.505],[0.48,0.925],[0.255,0.925]], label: '回鹘文', sort_order: 4 },
    { id: 'hs_script_tangut', entity_id: 'script_tangut', shape: 'polygon', normalized_points: [[0.49,0.505],[0.735,0.505],[0.735,0.925],[0.49,0.925]], label: '西夏文', sort_order: 5 },
    { id: 'hs_script_chinese', entity_id: 'script_chinese', shape: 'polygon', normalized_points: [[0.745,0.505],[0.975,0.505],[0.975,0.925],[0.745,0.925]], label: '汉文', sort_order: 6 },
    { id: 'hs_concept_buddhist_stone_carving', entity_id: 'concept_buddhist_stone_carving', shape: 'polygon', normalized_points: [[0.06,0.44],[0.17,0.42],[0.18,0.56],[0.07,0.58]], label: '石雕', sort_order: 7 },
  ],
}

const FALLBACK_TANG_SCENE: Scene = {
  id: 'tang_bunian_scroll',
  chapter_id: 'tang_exchange',
  name: '《步辇图》横向画卷',
  scene_kind: 'image',
  background_asset_id: '/assets/tang/bunian-original.jpg',
  width: 3053,
  height: 853,
  disclaimer: '历史画是理解历史的重要图像材料，但不等同于历史现场；人物热点为人工预标注。',
  hotspots: [
    { id: 'hs_bunian_taizong', entity_id: 'person_emperor_taizong', shape: 'polygon', normalized_points: [[0.78,0.31],[0.86,0.30],[0.87,0.80],[0.77,0.82]], label: '唐太宗', sort_order: 1 },
    { id: 'hs_bunian_ludongzan', entity_id: 'person_ludongzan', shape: 'polygon', normalized_points: [[0.54,0.36],[0.61,0.35],[0.62,0.87],[0.53,0.87]], label: '禄东赞', sort_order: 2 },
    { id: 'hs_bunian_introductory_official', entity_id: 'figure_introductory_official', shape: 'polygon', normalized_points: [[0.61,0.31],[0.69,0.30],[0.70,0.88],[0.60,0.88]], label: '引见官员', sort_order: 3 },
    { id: 'hs_bunian_inner_attendant', entity_id: 'figure_inner_attendant', shape: 'polygon', normalized_points: [[0.46,0.36],[0.53,0.35],[0.54,0.88],[0.45,0.87]], label: '内官', sort_order: 4 },
    { id: 'hs_bunian_palace_women', entity_id: 'group_palace_women', shape: 'polygon', normalized_points: [[0.72,0.25],[0.97,0.23],[0.97,0.94],[0.71,0.94]], label: '宫女群体', sort_order: 5 },
    { id: 'hs_bunian_artwork_self', entity_id: 'artifact_bunian_tu', shape: 'polygon', normalized_points: [[0,0],[1,0],[1,1],[0,1]], label: '《步辇图》', sort_order: 99 },
  ],
}

const FALLBACK_WEI_SCENE: Scene = {
  id: 'wei_evidence_compare',
  chapter_id: 'northern_wei_integration',
  name: '云冈与龙门石窟证据对照',
  scene_kind: 'image',
  background_asset_id: '/assets/wei/yungang-cave20-original.jpg',
  width: 1920,
  height: 1440,
  disclaimer: '两侧均为历史遗址实拍；热点只表示待复核的证据区域，不是自动识别结果。',
  hotspots: [
    { id: 'hs_yungang_tanyao', entity_id: 'evidence_yungang_tanyao', shape: 'polygon', normalized_points: [[0.21,0.23],[0.39,0.20],[0.41,0.60],[0.20,0.62]], label: '昙曜五窟', group_key: 'sculpture', sort_order: 1 },
    { id: 'hs_yungang_art_exchange', entity_id: 'evidence_yungang_art_exchange', shape: 'polygon', normalized_points: [[0.55,0.24],[0.82,0.22],[0.84,0.58],[0.54,0.60]], label: '多来源艺术因素', group_key: 'religious_art', sort_order: 2 },
    { id: 'hs_longmen_guyang', entity_id: 'evidence_longmen_guyang', shape: 'polygon', normalized_points: [[0.22,0.24],[0.41,0.22],[0.42,0.58],[0.21,0.60]], label: '古阳洞造像与龛饰', group_key: 'sculpture', sort_order: 3 },
    { id: 'hs_longmen_inscriptions', entity_id: 'evidence_longmen_inscriptions', shape: 'polygon', normalized_points: [[0.60,0.27],[0.84,0.25],[0.85,0.54],[0.59,0.56]], label: '造像题记', group_key: 'inscription', sort_order: 4 },
  ],
}

const FALLBACK_HAN_SCENE: Scene = {
  id: 'han_silk_road_network',
  chapter_id: 'han_encounter',
  name: '丝路历史网络主场景',
  scene_kind: 'map',
  background_asset_id: '/assets/han/han-caravan-v1.png',
  width: 2400,
  height: 1350,
  disclaimer: '历史交通网络示意，并非现代导航路线。节点只表达相对空间关系，古代路线会随时期、政治环境与自然条件变化。',
  hotspots: [
    { id: 'hs_han_changan', entity_id: 'place_changan', shape: 'polygon', normalized_points: [[0.15,0.47],[0.21,0.47],[0.21,0.57],[0.15,0.57]], label: '长安', sort_order: 1 },
    { id: 'hs_han_hexi', entity_id: 'region_hexi_corridor', shape: 'polygon', normalized_points: [[0.29,0.41],[0.35,0.41],[0.35,0.51],[0.29,0.51]], label: '河西走廊', sort_order: 2 },
    { id: 'hs_han_dunhuang', entity_id: 'place_dunhuang', shape: 'polygon', normalized_points: [[0.43,0.37],[0.49,0.37],[0.49,0.47],[0.43,0.47]], label: '敦煌', sort_order: 3 },
    { id: 'hs_han_yumen', entity_id: 'place_yumen_pass', shape: 'polygon', normalized_points: [[0.50,0.45],[0.56,0.45],[0.56,0.55],[0.50,0.55]], label: '玉门关', sort_order: 4 },
    { id: 'hs_han_western', entity_id: 'region_western_regions', shape: 'polygon', normalized_points: [[0.63,0.33],[0.69,0.33],[0.69,0.43],[0.63,0.43]], label: '西域', sort_order: 5 },
    { id: 'hs_han_niya', entity_id: 'site_niya', shape: 'polygon', normalized_points: [[0.65,0.59],[0.71,0.59],[0.71,0.69],[0.65,0.69]], label: '尼雅遗址', sort_order: 6 },
  ],
}

const FALLBACK_QING_SCENE = {
  id: 'qing_torghut_return_map',
  chapter_id: 'qing_return',
  name: '东归迁徙示意地图',
  scene_kind: 'map',
  background_asset_id: '/assets/qing/qing-migration-v1.png',
  width: 2400,
  height: 1350,
  disclaimer: '历史迁徙路线示意，并非现代 GPS 轨迹。连线只表示依据史料与研究重建的大体方向和廊道。',
  map: {
    id: 'qing_torghut_return_map',
    name: '东归迁徙示意地图',
    default_route_scope: 'MASS_MIGRATION',
    nodes: [
      { id: 'map_node_volga_region', entity_id: 'region_volga_lower', label: '伏尔加河下游', node_type: 'historical_region', x: 0.16, y: 0.43, certainty: 'confirmed_region', route_scope: 'MASS_MIGRATION', sort_order: 1 },
      { id: 'map_node_departure_region', entity_id: 'event_torghut_return_departure_1771', label: '东归出发节点（区域级）', node_type: 'event_marker', x: 0.24, y: 0.40, certainty: 'approximate_corridor', route_scope: 'MASS_MIGRATION', sort_order: 2 },
      { id: 'map_node_steppe_corridor', entity_id: 'region_eurasian_steppe', label: '欧亚草原中段聚合区段', node_type: 'corridor_area', x: 0.50, y: 0.42, certainty: 'approximate_corridor', route_scope: 'MASS_MIGRATION', sort_order: 3 },
      { id: 'map_node_ili_region', entity_id: 'region_ili', label: '伊犁河流域', node_type: 'historical_region', x: 0.78, y: 0.50, certainty: 'confirmed_region', route_scope: 'MASS_MIGRATION', sort_order: 4 },
      { id: 'map_node_settlement_region', entity_id: 'region_xinjiang_settlement', label: '抵达后安置地区（聚合节点）', node_type: 'settlement_area', x: 0.86, y: 0.62, certainty: 'approximate_corridor', route_scope: 'SETTLEMENT_DISTRIBUTION', sort_order: 5 },
      { id: 'map_node_chengde', entity_id: 'place_chengde', label: '承德 / 热河', node_type: 'historical_place', x: 0.92, y: 0.20, certainty: 'confirmed_region', route_scope: 'LEADER_AUDIENCE_JOURNEY', sort_order: 6 },
    ],
    segments: [
      { id: 'seg_qing_migration_01', from_node_id: 'map_node_departure_region', to_node_id: 'map_node_steppe_corridor', label: '草原中段（具体行进路线存在不确定性）', geometry: [], certainty: 'uncertain_segment', route_scope: 'MASS_MIGRATION', evidence_note: '公开资料支持整体向东行进，但不足以逐段复原具体路径。', sort_order: 1 },
      { id: 'seg_qing_migration_02', from_node_id: 'map_node_volga_region', to_node_id: 'map_node_ili_region', label: '大体迁徙区段（欧亚草原廊道）', geometry: [[0.16,0.43],[0.34,0.38],[0.55,0.44],[0.78,0.50]], certainty: 'approximate_corridor', route_scope: 'MASS_MIGRATION', evidence_note: '折线只表达大体方向，不代表逐日行程或唯一固定路径。', sort_order: 2 },
      { id: 'seg_qing_settlement_01', from_node_id: 'map_node_ili_region', to_node_id: 'map_node_settlement_region', label: '抵达后安置分布（聚合示意）', geometry: [[0.78,0.50],[0.82,0.56],[0.86,0.62]], certainty: 'approximate_corridor', route_scope: 'SETTLEMENT_DISTRIBUTION', evidence_note: '表达安置方向，不是一次行进路线。', sort_order: 3 },
      { id: 'seg_qing_audience_01', from_node_id: 'map_node_ili_region', to_node_id: 'map_node_chengde', label: '渥巴锡等首领赴承德觐见行程', geometry: [[0.78,0.50],[0.85,0.35],[0.92,0.20]], certainty: 'curatorial_connector', route_scope: 'LEADER_AUDIENCE_JOURNEY', evidence_note: '首领行程与大部众迁徙必须分层显示。', sort_order: 4 },
    ],
  },
  hotspots: [
    { id: 'hs_qing_volga', entity_id: 'region_volga_lower', shape: 'polygon', normalized_points: [[0.13,0.38],[0.19,0.38],[0.19,0.48],[0.13,0.48]], label: '伏尔加河下游', sort_order: 1 },
    { id: 'hs_qing_departure', entity_id: 'event_torghut_return_departure_1771', shape: 'polygon', normalized_points: [[0.21,0.35],[0.27,0.35],[0.27,0.45],[0.21,0.45]], label: '东归出发节点', sort_order: 2 },
    { id: 'hs_qing_steppe', entity_id: 'region_eurasian_steppe', shape: 'polygon', normalized_points: [[0.47,0.37],[0.53,0.37],[0.53,0.47],[0.47,0.47]], label: '欧亚草原中段', sort_order: 3 },
    { id: 'hs_qing_ili', entity_id: 'region_ili', shape: 'polygon', normalized_points: [[0.75,0.45],[0.81,0.45],[0.81,0.55],[0.75,0.55]], label: '伊犁河流域', sort_order: 4 },
    { id: 'hs_qing_settlement', entity_id: 'region_xinjiang_settlement', shape: 'polygon', normalized_points: [[0.83,0.57],[0.89,0.57],[0.89,0.67],[0.83,0.67]], label: '抵达后安置地区', sort_order: 5 },
    { id: 'hs_qing_chengde', entity_id: 'place_chengde', shape: 'polygon', normalized_points: [[0.89,0.15],[0.95,0.15],[0.95,0.25],[0.89,0.25]], label: '承德 / 热河', sort_order: 6 },
  ],
} as Scene & { map: Record<string, unknown> }

const FALLBACK_CONTEMPORARY_SCENE: Scene = {
  id: 'qiang_workbench',
  chapter_id: 'contemporary_qiang_embroidery',
  name: '羌绣数字工坊',
  scene_kind: 'workbench',
  background_asset_id: '/assets/contemporary/qiang-workshop-v1.png',
  disclaimer: '本章以知识卡与关系图呈现，不使用视觉识别或 OCR 推断针法、纹样名称或文化寓意。只有明确完成权利审核的项目自绘元素可进入共创。',
  hotspots: [],
}

function fallbackSceneFor(chapterId: string): Scene | null {
  if (chapterId === 'han_encounter') return FALLBACK_HAN_SCENE
  if (chapterId === 'yuan_yuntai') return FALLBACK_YUAN_SCENE
  if (chapterId === 'tang_exchange') return FALLBACK_TANG_SCENE
  if (chapterId === 'northern_wei_integration') return FALLBACK_WEI_SCENE
  if (chapterId === 'qing_return') return FALLBACK_QING_SCENE
  if (chapterId === 'contemporary_qiang_embroidery') return FALLBACK_CONTEMPORARY_SCENE
  return null
}

/** slug ↔ chapter_id 映射。slug 同时是设计系统的章节色 key。 */
export const SLUG_TO_ID: Record<ChapterSlug, string> = {
  han: 'han_encounter',
  'northern-wei': 'northern_wei_integration',
  tang: 'tang_exchange',
  yuan: 'yuan_yuntai',
  qing: 'qing_return',
  contemporary: 'contemporary_qiang_embroidery',
}

export const ID_TO_SLUG: Record<string, ChapterSlug> = Object.fromEntries(
  Object.entries(SLUG_TO_ID).map(([slug, id]) => [id, slug as ChapterSlug]),
) as Record<string, ChapterSlug>

export const CHAPTER_ACCENT: Record<ChapterSlug, string> = {
  han: '#B1783A',
  'northern-wei': '#657887',
  tang: '#9B3D35',
  yuan: '#2C6F89',
  qing: '#7A513B',
  contemporary: '#B64D43',
}

export const useChapterStore = defineStore('chapter', () => {
  const chapters = ref<Chapter[]>([])
  const current = ref<Chapter | null>(null)
  const scene = ref<Scene | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  /** 热点状态：UNSEEN / SEEN / SELECTED（设计系统 §24） */
  const hotspotStatus = ref<Record<string, 'UNSEEN' | 'SEEN' | 'SELECTED'>>({})
  const selectedEntityId = ref<string | null>(null)
  const lensOpen = ref(false)

  const slug = computed<ChapterSlug | null>(() =>
    current.value ? ID_TO_SLUG[current.value.id] ?? null : null,
  )

  const accent = computed(() => (slug.value ? CHAPTER_ACCENT[slug.value] : '#96352B'))

  const hotspots = computed<Hotspot[]>(() => scene.value?.hotspots ?? [])

  const seenHotspotIds = computed(() =>
    Object.entries(hotspotStatus.value)
      .filter(([, s]) => s === 'SEEN' || s === 'SELECTED')
      .map(([id]) => id),
  )

  async function loadChapters() {
    if (chapters.value.length) return chapters.value
    loading.value = true
    error.value = null
    try {
      chapters.value = await getChapters()
    } catch (e) {
      chapters.value = FALLBACK_CHAPTERS
      error.value = '实时内容服务未连接，正在使用内置章节导览。'
    } finally {
      loading.value = false
    }
    return chapters.value
  }

  async function loadChapter(chapterId: string) {
    loading.value = true
    error.value = null
    try {
      current.value = await getChapter(chapterId)
      // 场景可选：当代章节没有空间场景
      try {
        scene.value = await getChapterScene(chapterId)
      } catch {
        scene.value = fallbackSceneFor(chapterId)
      }
      resetHotspots()
    } catch (e) {
      current.value = FALLBACK_CHAPTERS.find((item) => item.id === chapterId) ?? null
      scene.value = fallbackSceneFor(chapterId)
      error.value = current.value ? '实时内容服务未连接，场景数据暂不可用。' : '这段内容暂时没有完成数字化整理。'
    } finally {
      loading.value = false
    }
  }

  async function loadScene(sceneId: string) {
    scene.value = await getScene(sceneId)
    resetHotspots()
  }

  function resetHotspots() {
    const next: Record<string, 'UNSEEN' | 'SEEN' | 'SELECTED'> = {}
    for (const h of hotspots.value) next[h.id] = 'UNSEEN'
    hotspotStatus.value = next
    selectedEntityId.value = null
  }

  function markSeen(hotspotId: string) {
    if (hotspotStatus.value[hotspotId]) hotspotStatus.value[hotspotId] = 'SEEN'
  }

  function selectHotspot(hotspotId: string) {
    for (const k of Object.keys(hotspotStatus.value)) {
      if (hotspotStatus.value[k] === 'SELECTED') hotspotStatus.value[k] = 'SEEN'
    }
    hotspotStatus.value[hotspotId] = 'SELECTED'
  }

  function selectEntity(entityId: string | null) {
    selectedEntityId.value = entityId
    if (!entityId) return
    const hs = hotspots.value.find((h) => h.entity_id === entityId)
    if (hs) selectHotspot(hs.id)
  }

  function setLens(open: boolean) {
    lensOpen.value = open
  }

  return {
    chapters,
    current,
    scene,
    loading,
    error,
    hotspotStatus,
    selectedEntityId,
    lensOpen,
    slug,
    accent,
    hotspots,
    seenHotspotIds,
    loadChapters,
    loadChapter,
    loadScene,
    resetHotspots,
    markSeen,
    selectHotspot,
    selectEntity,
    setLens,
  }
})
