import type { StoryChapterSlug } from './fiveChapterStories'

/**
 * 角色问答只负责解释玩家已经接触到的材料，不生成关键剧情、关卡答案或新史实。
 * fallback 是断网与模型不可用时直接展示的完整回答，不依赖在线生成。
 */
export interface StoryAiIntent {
  id: string
  exampleQuestion: string
  answerPoints: string[]
  sourceRequirement: string[]
  refusalBoundary: string
  fallback: string
}

const commonRefusal = '不得虚构史料、私人心理或未获授权的口述；超出本章材料时应明确说“现有证据不能确认”。'

export const FIVE_CHAPTER_AI_INTENTS: Record<StoryChapterSlug, StoryAiIntent[]> = {
  han: [
    { id: 'han_route_creator', exampleQuestion: '丝绸之路是张骞一个人开通的吗？', answerPoints: ['张骞出使是重要节点', '长期网络由多代、多地、多类参与者共同延续'], sourceRequirement: ['han_dual_route', 'han_network_actors'], refusalBoundary: commonRefusal, fallback: '不能把延续数百年的交通网络归给一个人。张骞出使是重要节点，后续的向导、译者、商旅、工匠、军民与沿线居民共同让联系持续发生。' },
    { id: 'han_brocade_relation', exampleQuestion: '锦护膊是张骞带回来的吗？', answerPoints: ['现有资料不支持直接关系', '可作为后世长期网络物证'], sourceRequirement: ['han_caption_split', 'han_chronology_gap'], refusalBoundary: commonRefusal, fallback: '现有证据不能证明张骞携带过这件锦护膊。它可以帮助理解后世长期交通网络，但不能被写成张骞个人遗物。' },
    { id: 'han_route_precision', exampleQuestion: '地图上的线就是张骞每天走的路线吗？', answerPoints: ['节点与廊道是概括表达', '不是逐日导航轨迹'], sourceRequirement: ['han_dual_route'], refusalBoundary: commonRefusal, fallback: '不是。本章地图表达的是有证据支持的节点和交通廊道层级，不应被当作张骞逐日行程或现代导航轨迹。' },
    { id: 'han_niya_context', exampleQuestion: '为什么一定要讲尼雅的出土环境？', answerPoints: ['文物意义来自出土语境', '不能只把它当传奇道具'], sourceRequirement: ['han_niya_context'], refusalBoundary: commonRefusal, fallback: '出土地点、墓葬语境和断代决定了文物能证明什么。离开尼雅语境，锦护膊很容易被误写成替某位英雄作证的道具。' },
    { id: 'han_ordinary_people', exampleQuestion: '普通人在这条路上重要吗？', answerPoints: ['长期联系依赖许多无名行动者', '共同历史不只由重大事件构成'], sourceRequirement: ['han_network_actors'], refusalBoundary: commonRefusal, fallback: '重要。道路之所以持续，依靠一代代翻译、引路、交换、生产、守护和定居。许多人没有留下姓名，却参与了共同历史。' },
    { id: 'han_goods_culture', exampleQuestion: '物品流动就等于民族交融吗？', answerPoints: ['物品是联系证据之一', '交融还包括知识、技艺与共同生活'], sourceRequirement: ['han_relation_scale'], refusalBoundary: commonRefusal, fallback: '不能画等号。物品流动能证明联系的一部分；民族交融还需要结合人员往来、知识与技艺传播、制度互动和共同生活来理解。' },
    { id: 'han_modern_term', exampleQuestion: '汉代人会说“中华民族共同体”吗？', answerPoints: ['现代概念不可倒置给古人', '可用今天的问题解释长期共同历史'], sourceRequirement: ['han_caption_draft'], refusalBoundary: commonRefusal, fallback: '不能把现代概念写成汉代人物的原话或自觉表达。今天可以借可靠史料讨论长期交往怎样成为共同历史，但必须标清这是当代解释。' },
    { id: 'han_unknown', exampleQuestion: '能不能补一个张骞拿到锦护膊的故事？', answerPoints: ['缺少直接证据', '关键关系不得用戏剧补写'], sourceRequirement: ['han_caption_split'], refusalBoundary: commonRefusal, fallback: '不能。这个补写会制造不存在的直接关系。本章可以虚构当代校勘人物，却不能虚构张骞与具体文物的接触。' },
  ],
  'northern-wei': [
    { id: 'wei_total_replacement', exampleQuestion: '迁都以后旧传统是不是都消失了？', answerPoints: ['变化速度不同', '采用、改造、并存、延续同时存在'], sourceRequirement: ['wei_change_model'], refusalBoundary: commonRefusal, fallback: '不能写成整齐的替代。不同制度、手艺和生活习惯变化速度不同，采用、改造、并存与延续可能同时发生。' },
    { id: 'wei_epitaph_scope', exampleQuestion: '一方墓志能代表整个北魏吗？', answerPoints: ['墓志首先说明个案', '社会结论需要多类材料'], sourceRequirement: ['wei_epitaph_scope', 'wei_scope_split'], refusalBoundary: commonRefusal, fallback: '不能。一方墓志能帮助认识具体墓主及其制度背景，要讨论更广社会变化还需与更多墓志、制度文本、图像和实物互证。' },
    { id: 'wei_move_year', exampleQuestion: '北魏迁都到底是493年还是494年？', answerPoints: ['决策与迁移过程不必压成一天', '家庭经历具有时间差'], sourceRequirement: ['wei_move_process'], refusalBoundary: commonRefusal, fallback: '本章把493—494理解为迁都推进过程中的不同节点，不把一项重大迁徙压缩成所有人同一天完成的动作。' },
    { id: 'wei_grottoes', exampleQuestion: '龙门石窟只是取代云冈吗？', answerPoints: ['两地可比较延续与变化', '不能写成简单淘汰'], sourceRequirement: ['wei_grotto_compare'], refusalBoundary: commonRefusal, fallback: '不应写成简单取代。两地材料可以帮助比较营造传统怎样延续、调整并进入新的环境。' },
    { id: 'wei_clothing_identity', exampleQuestion: '穿哪件衣服就说明是哪一族吗？', answerPoints: ['服饰是社会表达的一部分', '不能单独判定身份'], sourceRequirement: ['wei_costume_boundary'], refusalBoundary: commonRefusal, fallback: '不能凭一件衣服替一个人宣布全部身份。服饰可反映制度、场合与审美变化，但必须与姓名、籍贯、文本和生活语境一起判断。' },
    { id: 'wei_names', exampleQuestion: '改姓以后是不是旧来处就不存在了？', answerPoints: ['制度姓名与家庭记忆可并存', '个案不可推广为所有人'], sourceRequirement: ['wei_evidence_types'], refusalBoundary: commonRefusal, fallback: '姓名变化会影响公共生活，却不自动抹去家庭记忆和旧来处。本章只通过虚构家庭呈现这种张力，不把它当作所有人的相同经历。' },
    { id: 'wei_fictional_family', exampleQuestion: '阿洛一家是真实人物吗？', answerPoints: ['人物与作坊经历为虚构', '史实锚点另行标注'], sourceRequirement: ['wei_scope_split'], refusalBoundary: commonRefusal, fallback: '不是。阿洛、陆萤、慧生和作坊冲突是剧情虚构，用来承接迁都、墓志、石窟和制度变化等已标注的史实锚点。' },
    { id: 'wei_theme', exampleQuestion: '这一章为什么叫“两座故乡”？', answerPoints: ['共同生活不要求抹去来处', '交融是关系重组而非同质化'], sourceRequirement: ['wei_change_model'], refusalBoundary: commonRefusal, fallback: '因为新的共同生活可以同时容纳旧记忆与新关系。交融并不是所有人变得相同，而是在相处、调整与互相学习中重新组合生活。' },
  ],
  tang: [
    { id: 'tang_paint_photo', exampleQuestion: '《步辇图》能当现场照片看吗？', answerPoints: ['历史画有表现目的', '需与文献和作品研究互证'], sourceRequirement: ['tang_image_boundary'], refusalBoundary: commonRefusal, fallback: '不能。历史画能提供重要视觉材料，但不是现场照片；人物、事件与作品归属都要结合其他来源判断。' },
    { id: 'tang_wencheng_present', exampleQuestion: '文成公主在画里吗？', answerPoints: ['不在画中', '可通过相关事件进入画外关系'], sourceRequirement: ['tang_absent_search', 'tang_outside_chain'], refusalBoundary: commonRefusal, fallback: '她不在画面中。可以通过有来源的相关事件说明她与这次历史关系的联系，但不能把她想象进画里。' },
    { id: 'tang_envoy_name', exampleQuestion: '为什么必须写禄东赞的名字？', answerPoints: ['使臣是行动者而非符号', '名字连接会见、翻译与事件'], sourceRequirement: ['tang_relation_thread'], refusalBoundary: commonRefusal, fallback: '写出名字能让来使从模糊符号变回具体行动者，也让观众沿会见、翻译和相关事件继续追索关系。' },
    { id: 'tang_translation', exampleQuestion: '译者可以帮历史人物补一句心里话吗？', answerPoints: ['翻译传递已说出的内容', '未知内心必须留白'], sourceRequirement: ['tang_cast_boundary'], refusalBoundary: commonRefusal, fallback: '不能。译者连接语言，却不能替历史人物发明没有材料支持的私人心声。未知应明确留白。' },
    { id: 'tang_author', exampleQuestion: '这幅画的作者可以完全确定吗？', answerPoints: ['区分传统归属、作品研究与确定事实', '呈现研究层级'], sourceRequirement: ['tang_attribution_layers'], refusalBoundary: commonRefusal, fallback: '应按项目审核资料区分传统归属、后世记载和研究判断，不把仍需讨论的作者问题写成无争议事实。' },
    { id: 'tang_permanent_peace', exampleQuestion: '一次和亲以后是不是一直和平？', answerPoints: ['一次事件不能覆盖长期关系', '往来、协商、矛盾与冲突并存'], sourceRequirement: ['tang_relation_thread'], refusalBoundary: commonRefusal, fallback: '不是。一次会见或婚姻不能概括此后全部唐蕃关系；长期历史中既有往来与协商，也有矛盾和冲突。' },
    { id: 'tang_fictional_cast', exampleQuestion: '桑波说的话是史料原话吗？', answerPoints: ['三位主要角色为虚构', '真实历史人物不使用虚构私人对白'], sourceRequirement: ['tang_guide_line'], refusalBoundary: commonRefusal, fallback: '不是。桑波、许照、青禾是明确标注的虚构角色，用于展示校对与翻译工作；真实历史人物不会被安排虚构私人对白。' },
    { id: 'tang_theme', exampleQuestion: '为什么说画卷只画下“相见”？', answerPoints: ['画面保留一个节点', '关系由相见前后的多人行动延续'], sourceRequirement: ['tang_outside_chain'], refusalBoundary: commonRefusal, fallback: '画面保存的是一次相见的特定表达，真正的长期关系还包括出发、接待、翻译、协商、往返与后来复杂的共同历史。' },
  ],
  qing: [
    { id: 'qing_arrival_fiction', exampleQuestion: '乌娜一家是真实历史人物吗？', answerPoints: ['乌娜、宁成、巴图均为虚构', '抵达伊犁和接济安置是史实锚点'], sourceRequirement: ['qing_arrival_ledger'], refusalBoundary: commonRefusal, fallback: '不是。乌娜、宁成、巴图和受潮名册都是明确虚构的人物与冲突，用来承接1771年抵达伊犁、食衣接济、物资调运和分地安居等史实。' },
    { id: 'qing_relief_record', exampleQuestion: '名册没有名字，为什么还能先发粮？', answerPoints: ['剧情选择不等于真实行政个案', '已知、待核和行动应分栏记录'], sourceRequirement: ['qing_relief_first', 'qing_settlement_ledger'], refusalBoundary: commonRefusal, fallback: '这是剧情设置的伦理与证据判断：不能虚构姓名，也不能让档案空白否认眼前的人。方案是把在场丁口、名册受损和待复核责任分开记录。' },
    { id: 'qing_chengde', exampleQuestion: '所有东归者都到了承德吗？', answerPoints: ['大部众迁徙与首领活动分开', '承德不是所有人的终点'], sourceRequirement: ['qing_route_scopes'], refusalBoundary: commonRefusal, fallback: '不能这样写。大部众抵达伊犁一带，渥巴锡等首领后来赴承德；后续安置又是第三组空间关系，三条线不能合成所有人的共同路线。' },
    { id: 'qing_population', exampleQuestion: '到底有多少人东归？', answerPoints: ['来源口径不同', '人数、户数与时间点不可求平均'], sourceRequirement: ['qing_number_sources'], refusalBoundary: commonRefusal, fallback: '不同来源可能记录约数、人数、户数或不同时间点。本章保留原表述与出处差异，不用平均数制造一个从未被任何来源记录的唯一答案。' },
    { id: 'qing_motive', exampleQuestion: '东归只是因为思念故土吗？', answerPoints: ['故土认同重要', '同时存在政治军事压力、生计处境与长期联系'], sourceRequirement: ['qing_motive_plural'], refusalBoundary: commonRefusal, fallback: '故土认同是理解东归的重要线索，但不能替所有人安排同一种私人心理。政治军事压力、草场生计与长期联系等背景也需结合来源呈现。' },
    { id: 'qing_relief_network', exampleQuestion: '清政府怎样接济和安置东归部众？', answerPoints: ['食衣救急', '茶米棉布和牲畜调运', '分地安居'], sourceRequirement: ['qing_relief_chain'], refusalBoundary: commonRefusal, fallback: '史料记录了按口给食、按人授衣，并从不同地方筹措茶米、棉布、皮衣和马牛羊等物资，继而安排牧地。具体数量与分配细节必须按来源说明。' },
    { id: 'qing_not_passive', exampleQuestion: '归来者在这一章为什么也参与写簿？', answerPoints: ['参与写簿是合理重建', '用于避免把归来者只写成被动受助者'], sourceRequirement: ['qing_settlement_ledger'], refusalBoundary: commonRefusal, fallback: '具体共同写簿是剧情重建，不是已知现场。它表达的历史解释是：接济能解决眼前困难，长期生活仍需要归来者以自己的知识、劳动和关系参与重建。' },
    { id: 'qing_belonging', exampleQuestion: '这一章怎样体现“同心”？', answerPoints: ['万里东归体现故土认同与凝聚力', '四方接济和共同重建把认同变成生活'], sourceRequirement: ['qing_arrival_ledger', 'qing_relief_chain', 'qing_settlement_ledger'], refusalBoundary: commonRefusal, fallback: '“同心”既体现在万里东归所呈现的故土认同，也体现在抵达后多地筹措、长途转运、制度接纳和归来者共同重建。它不是差异消失，而是不同人群愿意为共同家园彼此承担。' },
  ],
  contemporary: [
    { id: 'now_recovery_wording', exampleQuestion: '为什么不能写“外界援助救活了羌绣”？', answerPoints: ['公共和社会支援提供了重要条件', '当地妇女也以学习、生产、授艺参与重建'], sourceRequirement: ['contemporary_recovery_chain', 'contemporary_many_hands'], refusalBoundary: commonRefusal, fallback: '这种写法只保留援助方，会把当地参与者写成被动接受者。更准确的关系是：支援提供政策、培训和市场条件，当地妇女通过学习、生产、授艺与组织协作恢复生计，双方行动缺一不可。' },
    { id: 'now_2008_facts', exampleQuestion: '二〇〇八年的羌绣帮扶哪些部分是史实？', answerPoints: ['羌绣列入第二批国家级非遗名录', '灾后开展保护、技能培训、就业帮扶和市场连接'], sourceRequirement: ['contemporary_recovery_chain'], refusalBoundary: commonRefusal, fallback: '羌绣在2008年列入第二批国家级非物质文化遗产名录；灾后相关项目开展保护、技能培训、居家生产、就业帮扶和销售连接。本章的资料箱、人物和具体订单则是剧情重建。' },
    { id: 'now_local_agency', exampleQuestion: '为什么说本地妇女不是被动受助者？', answerPoints: ['她们学习并完成生产', '部分参与者继续授艺和组织长期协作'], sourceRequirement: ['contemporary_many_hands'], refusalBoundary: commonRefusal, fallback: '支援创造了恢复条件，但针线生产、交活、改进和后来的授艺仍由当地参与者完成。她们既获得帮助，也用劳动和知识把项目继续向下连接，不能从叙事中被删掉。' },
    { id: 'now_shared_learning', exampleQuestion: '不同民族一起学羌绣，就会变成同一种身份吗？', answerPoints: ['共同研修不等于身份同化', '教师、学员、设计者和销售者承担不同责任'], sourceRequirement: ['contemporary_learning_network'], refusalBoundary: commonRefusal, fallback: '不会。不同地区、民族和专业的人可以一起学习，但其经验、能力和责任并不相同。会绣的人传授技艺，设计者、记录者和销售者在各自范围内协作，任何人都不能因短期学习替整个文化群体发言。' },
    { id: 'now_ai_average', exampleQuestion: 'AI生成统一“同心纹样”为什么不合适？', answerPoints: ['外观平均不能证明真实交往', '统一结果会遮蔽作者、学习阶段与具体选择'], sourceRequirement: ['contemporary_ai_boundary'], refusalBoundary: commonRefusal, fallback: '模型能提取视觉相似，却不能由此证明创作者彼此认识、协商或共同完成了作品。统一图还会抹掉作者、差异和学习过程；本章因此只让AI辅助转写、检索和关系整理。' },
    { id: 'now_exchange_kit', exampleQuestion: '“接针包”和普通材料包有什么不同？', answerPoints: ['由具体创作者带着问题发出', '远方学生以自己的材料回应并寄回'], sourceRequirement: ['contemporary_exchange_kit', 'contemporary_exchange_protocol'], refusalBoundary: commonRefusal, fallback: '接针包不是统一模仿教材。它包含署名起针片、本人说明、允许用途和一个真实问题；学生可以用布、纸、声音等自己的材料回应，双方分别落款，作品回到工坊后还要继续回信。' },
    { id: 'now_reply_boundary', exampleQuestion: '小满的剪纸为什么能参与共创，却不能叫羌绣？', answerPoints: ['两件作品围绕同一问题形成关系', '材料、技艺和作者身份仍分别标明'], sourceRequirement: ['contemporary_pilot_reply'], refusalBoundary: commonRefusal, fallback: '小满用家乡潮水线回应阿若关于“线怎样记录生活之地”的问题，因此两件作品发生了真实联系；但她没有完成长期羌绣学习，剪纸仍是剪纸，不能因参与共创就改名为羌绣。' },
    { id: 'now_theme', exampleQuestion: '这一章怎样体现“同心”？', answerPoints: ['支援与本地主体行动共同构成重建', '不同身份在持续往返中彼此需要而不消失差异'], sourceRequirement: ['contemporary_recovery_chain', 'contemporary_learning_network', 'contemporary_pilot_reply'], refusalBoundary: commonRefusal, fallback: '“同心”不是生成一张人人相似的图，而是不同人都以具体行动进入关系：有人提供条件，有人生产授艺，有人学习、购买、提问和回应。每个人的位置清楚，连接又能持续往返，共同体才真正形成。' },
  ],
}

