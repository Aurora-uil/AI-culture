# 待内容组核验清单

> 本文件由 `backend/scripts/gen_review_todo.py` 自动生成，请勿手改。

项目里有一部分数据是**由工程实现方依据章节规格文档补写**的 —— 规格没有给 URL、没有给坐标、没有给来源分级，而接口又必须返回完整结构。

这些数据的处理原则是：

1. 一律标 `review_status: draft` 或 `review`，**不标 approved**；
2. 每条都带 `content_team_todo` 字段，写明具体要核验什么；
3. **不进入 AI 检索**（检索门禁只放行 approved）；
4. 界面上以「待核验」状态呈现，不冒充已确认史实。

**当前合计待核验条目：400 条**

---

## 一、来源状态（优先处理）

来源状态直接决定内容能不能被 AI 检索到。

- `draft`（实现方补写，**书目与 URL 均待补**）：**8 条**
- `review`（已有基本信息，待核验准确性）：**14 条**

### draft 来源

| 章节 | 来源 ID | 标题 | 等级 | 公开链接 |
|---|---|---|---|---|
| 汉代 | `src_xjmuseum_five_star` | 新疆维吾尔自治区博物馆（官网） | S | http://www.xjmuseum.com.cn/ |
| 元代 | `src_bjgov_juyongguan` | 居庸关长城 | S | **缺失** |
| 元代 | `src_bjww_yuntai_chronology` | 居庸关云台的年代与形制（北京市文物局公开资料） | S | **缺失** |
| 元代 | `src_bjww_yuntai_inscriptions` | 居庸关云台券洞题刻与佛教造像（北京市文物局公开介绍） | S | **缺失** |
| 元代 | `src_academic_scripts_overview` | 元代多文字并用与居庸关云台题刻研究（综述，待补具体篇目） | A | **缺失** |
| 元代 | `src_academic_phagspa` | 八思巴字研究（待补具体篇目） | A | **缺失** |
| 元代 | `src_academic_tangut_in_yuan` | 元代西夏文的存续与使用研究（待补具体篇目） | A | **缺失** |
| 元代 | `src_academic_yuntai_inscription_reading` | 居庸关云台题刻内容与释读研究（待补具体篇目） | A | **缺失** |

### review 来源

| 章节 | 来源 ID | 标题 | 等级 | 公开链接 |
|---|---|---|---|---|
| 汉代 | `src_chnmuseum_silk_road` | 丝绸之路（中国国家博物馆线上虚拟展） | S | http://www.chnmuseum.cn/Portals/0/web/vr/sczl/pc/ |
| 汉代 | `src_chnmuseum_qin_han` | 「秦汉文明」展（中国国家博物馆） | S | https://www.chnmuseum.cn/Portals/0/web/zt/20170916qhwm/pc/index.html |
| 汉代 | `src_ncha_niya` | 新疆民丰尼雅遗址 | S | http://www.ncha.gov.cn/art/2022/3/18/art_2590_41.html |
| 汉代 | `src_rmrb_five_star` | 方寸织锦绣 千年互鉴史（博物视界） | B | https://paper.people.com.cn/rmrb/pc/content/202608/07/content_30173630.html |
| 汉代 | `src_han_shu_xiyu_zhuan` | 《汉书·西域传》 | A | https://ctext.org/han-shu/zh |
| 北魏 | `src_shanxi_wenwuju_yungang` | 云冈石窟（全国重点文物保护单位介绍） | S | https://wwj.shanxi.gov.cn/wwzy/wwlb/bkydww/qgzdwwbhdw/dypgb/202109/t20210908_1981155.shtml |
| 北魏 | `src_people_daily_hwb_yungang` | 云冈石窟：昙曜五窟的开凿 | B | http://paper.people.com.cn/hwbwap/html/2021-06/07/content_3052196.htm |
| 北魏 | `src_cssn_longmen_music` | 龙门石窟造像中的音乐人文图景 | A | https://www.cssn.cn/ysx/202601/t20260115_5969392.shtml |
| 北魏 | `src_gmw_yungang_cave12` | 千年前的乐团在这座洞窟中永生 | B | https://epaper.gmw.cn/wzb/html/2021-01/30/nw.D110000wzb_20210130_3-05.htm |
| 北魏 | `src_baike_beiwei_move` | 北魏迁都洛阳（词条） | C | https://baike.baidu.com/item/%E5%8C%97%E9%AD%8F%E9%81%B7%E9%83%BD%E6%B4%9B%E9%99%BD/15515453 |
| 唐代 | `src_dpm_yuankan_xie_2018` | 关于《步辇图》研究的几个问题 | A | https://www.dpm.org.cn/Uploads/File/2018/10/11/u5bbeb83a68a07.pdf |
| 唐代 | `src_dpm_yuankan_costume_2006` | 唐代礼官服色考——兼论《步辇图》的服色问题 | A | https://www.dpm.org.cn/embroiders/talk/207462.html |
| 当代 | `src_samr_qiang_standard_project` | 《羌族刺绣》国家标准制定项目公开信息 | A | **缺失** |
| 当代 | `src_wenchuan_qiang_copyright_2026` | 汶川县羌绣版权保护实践 | S | **缺失** |

> 说明：`source_level` 为空的来源，其全部 chunk 会被 RAG 过滤器永久排除。
> 元代与当代两章的来源等级由实现方按各章 §17.3 定义补全，需内容组确认。

## 二、分章待核验明细

### 汉代 · 相遇　（39 条：Claim 14、实体 10、知识切片 8、关系 4、物品流动 3）

| 类型 | ID | 名称 | 状态 | 待核验事项 |
|---|---|---|---|---|
| 实体 | `period_western_han` | 西汉 | review | — |
| 实体 | `place_dunhuang` | 敦煌 | review | — |
| 实体 | `place_yumen_pass` | 玉门关 | review | — |
| 实体 | `region_central_asia` | 中亚 | review | — |
| 实体 | `flow_horses` | 马匹 | review | — |
| 实体 | `flow_plants_food` | 植物与食物 | review | — |
| 实体 | `flow_objects_technology` | 器物与工艺 | review | — |
| 实体 | `concept_changan_tianshan_corridor` | 长安—天山廊道交通网络 | review | — |
| 实体 | `concept_silk_road_society_culture` | 丝路沿线社会与文化 | review | — |
| 实体 | `concept_hanjin_textile_technology` | 汉晋纺织技术与文化信息 | review | — |
| Claim | `claim_period_western_han_context` | 张骞第一次出使西域发生在西汉时期，派遣者是西汉皇帝汉武帝。 | review | — |
| Claim | `claim_changan_part_of_network` | 汉长安城未央宫遗址作为“丝绸之路：长安—天山廊道的路网”的组成部分，于2014年 | review | — |
| Claim | `claim_hexi_part_of_network` | 河西走廊处于长安—天山廊道交通网络所覆盖的空间范围之内。 | review | — |
| Claim | `claim_corridor_unesco_listing` | “丝绸之路：长安—天山廊道的路网”于2014年列入《世界遗产名录》，由中国、哈萨 | review | — |
| Claim | `claim_niya_sino_japanese_survey` | 1988年及1990年代，中日双方组成联合学术考察队，对尼雅遗址进行了多次调查与 | review | — |
| Claim | `claim_fivestar_inscription_interpretation_disputed` | 涉及“五星出东方利中国”铭文及其与同墓残片、相关军事文献对应关系的解释，属于研究 | review | — |
| Claim | `claim_fivestar_inscription_astrology_reading` | 一种解释认为，铭文中的“五星”指金、木、水、火、土五大行星，“中国”在当时指黄河 | review | — |
| Claim | `claim_fivestar_inscription_modern_meaning_guard` | “五星出东方利中国”铭文不应被解释成现代政治含义；其历史语境中的“中国”指黄河中 | review | — |
| Claim | `claim_fivestar_armguard_type` | 据同墓出土的弓、箭、箭箙等物推测，该锦护膊是射箭时所用的护臂用具。 | review | — |
| Claim | `claim_fivestar_supports_textile_study` | 该锦护膊可以用于研究汉晋时期的纺织技术、纹样体系与文字使用。 | review | — |
| Claim | `claim_niya_supports_society_culture_study` | 尼雅遗址出土的建筑遗迹、墓葬、文书与器物，可以用于研究丝路沿线的社会与文化。 | review | — |
| Claim | `claim_dunhuang_corridor_node` | 敦煌位于河西走廊西端，处于长安—天山廊道交通网络所覆盖的空间范围之内。 | review | — |
| Claim | `claim_yumen_pass_gateway` | 玉门关是汉代在河西走廊西端设置的关隘，在后世叙述中常被用来表述中原通往西域方向的 | review | — |
| Claim | `claim_central_asia_geographic_note` | “中亚”是现代地理学的区域概念，并非汉代文献中的原始地名，不应与现代国界一一对应 | review | — |
| 关系 | `rel_changan_part_of_corridor` | — | review | — |
| 关系 | `rel_hexi_part_of_corridor` | — | review | — |
| 关系 | `rel_niya_supports_society_culture` | — | review | — |
| 关系 | `rel_fivestar_supports_textile_technology` | — | review | — |
| 知识切片 | `chunk_han_018` | — | review | — |
| 知识切片 | `chunk_han_021` | — | review | — |
| 知识切片 | `chunk_han_036` | — | review | — |
| 知识切片 | `chunk_han_037` | — | review | — |
| 知识切片 | `chunk_han_038` | — | review | — |
| 知识切片 | `chunk_han_047` | — | review | — |
| 知识切片 | `chunk_han_049` | — | review | — |
| 知识切片 | `chunk_han_050` | — | review | — |
| 物品流动 | `flow_horses` | 马匹 | review | 待核验：需补充汉代马匹交流的学术来源，再逐条建立事实主张；在此之前本类别不进入 AI 检索。 |
| 物品流动 | `flow_plants_food` | 植物与食物 | review | 待核验：需补充汉代物种交流的学术来源，再逐条建立事实主张；在此之前本类别不进入 AI 检索。 |
| 物品流动 | `flow_objects_technology` | 器物与工艺 | review | 待核验：需补充汉代器物与工艺交流的学术来源，再逐条建立事实主张；在此之前本类别不进入 AI 检索。 |

### 北魏 · 交融　（89 条：Claim 24、知识切片 21、关系 18、实体 17、证据条目 7、兜底问答 2）

| 类型 | ID | 名称 | 状态 | 待核验事项 |
|---|---|---|---|---|
| 实体 | `person_empress_dowager_feng` | 冯太后 | review | — |
| 实体 | `person_yuanyu` | 元羽 | review | — |
| 实体 | `place_datong` | 大同（今） | review | — |
| 实体 | `cave_tanyao_five` | 昙曜五窟 | review | — |
| 实体 | `cave_longmen_guyang` | 古阳洞 | review | — |
| 实体 | `event_northern_wei_luoyang_period` | 北魏洛阳时期 | review | — |
| 实体 | `policy_language_court` | 朝堂语言相关规定 | review | — |
| 实体 | `artifact_attendant_figurine_yuanshao` | 侍从陶俑 | review | — |
| 实体 | `artifact_xianbei_style_figurine` | 鲜卑风格陶俑（北朝比较材料） | review | — |
| 实体 | `evidence_yungang_architecture` | 云冈窟形与建筑形象（证据） | review | — |
| 实体 | `evidence_yungang_style_exchange` | 云冈不同阶段的样式变化（证据） | review | — |
| 实体 | `evidence_yungang_music` | 云冈伎乐与乐器雕刻（证据） | review | — |
| 实体 | `evidence_longmen_inscriptions` | 龙门北魏阶段造像题记（证据） | review | — |
| 实体 | `evidence_longmen_costume` | 龙门北魏阶段服饰形象（证据） | review | — |
| 实体 | `evidence_longmen_music` | 龙门北魏阶段伎乐与乐器雕刻（证据） | review | — |
| 实体 | `evidence_yuanyu_epitaph` | 元羽墓志（证据） | review | — |
| 实体 | `group_xianbei` | 鲜卑（群体泛称） | review | — |
| Claim | `claim_wei_period_386_534` | 北魏是公元386年至534年间存在于中国北方的王朝。 | review | §2.1 已列为第一版基础事实，但仍需内容组指定正式史料或权威工具书来源（如《魏书》本纪、中国历史大辞典）并补录来源定位。 |
| Claim | `claim_wei_capital_pingcheng` | 北魏前期曾以平城为都城。 | review | 需补充「平城作为都城的具体起讫年份」的正式来源；本平台只表述为「前期都城」，不给出未经审核的具体迁入年份。 |
| Claim | `claim_pingcheng_location_datong` | 北魏平城位于今山西省大同市一带。 | review | 需核定「平城遗址与今大同市行政范围」的规范表述，避免把古代都城范围直接等同于现代行政区划。 |
| Claim | `claim_wei_end_534` | 北魏于公元534年前后结束，本章时间范围以386—534年为界。 | review | 王朝终结的具体年份与事件表述需内容组依据正式史料核定后再上线。 |
| Claim | `claim_move_capital_494` | 部分资料依传统纪年以「太和十八年」，即494年作为北魏迁都洛阳的时间表述。 | review | 494年一侧目前仅有普通网络材料作为占位来源，正式上线前必须替换为文物主管部门或权威学术来源。 |
| Claim | `claim_yungang_has_tanyao` | 昙曜五窟是云冈石窟最早开凿的一组大型洞窟，通常指第16至20窟。 | review | 洞窟编号对应关系需内容组依据云冈研究院正式资料复核，并确认UNESCO页面中「Five Caves of Tan Yao」表述的中文对应写法。 |
| Claim | `claim_tanyao_460` | 据《魏书·释老志》相关记载，北魏和平初年（约460年）文成帝下诏，由沙门统昙曜主 | review | 需内容组据《魏书·释老志》原文核定引文与年份表述，并补充正式学术来源。 |
| Claim | `claim_tanyao_five_emperors` | 研究者一般认为昙曜五窟的五尊大像与北魏五位皇帝相对应，该解释属于学术讨论，不是洞 | review | 需补充支持该对应关系的学术论文来源，并在文案中保持「研究者一般认为」的措辞。 |
| Claim | `claim_yungang_music_cave12` | 云冈第12窟因集中雕刻大量伎乐天与乐器形象，被称为「音乐窟」，是研究北魏音乐与乐 | review | 需核定洞窟编号、伎乐天数量与乐器种类的具体数字，并补充云冈研究院正式资料。 |
| Claim | `claim_yungang_music_instruments_mix` | 云冈乐舞雕刻中的乐器包含中原传统乐器与经丝路传入的乐器，可理解为多种音乐因素在同 | review | 乐器分类与「多种音乐因素并存」的表述需音乐史方向研究者复核。 |
| Claim | `claim_yungang_architecture_imitation` | 云冈石窟的窟形与雕刻中包含摹拟木构建筑与毡帐形式的形象，是观察北魏建筑与外来因素 | review | 需补充建筑史方向的正式学术来源，并核定「毡帐形式」等术语的规范表述。 |
| Claim | `claim_guyang_earliest` | 古阳洞是龙门石窟中开凿较早、内容较为丰富的洞窟之一，保存北魏时期的造像、龛饰与题 | review | 「开凿最早」的表述需内容组依据龙门石窟研究院正式资料核定，避免与宾阳洞等其他早期洞窟的先后关系冲突。 |
| Claim | `claim_longmen_inscriptions_20pin` | 龙门石窟北魏阶段保存大量造像题记，其中「龙门二十品」多数出自古阳洞，是研究北朝书 | review | 「二十品中十九品出自古阳洞」等具体数字需内容组依据龙门石窟研究院或权威出版物核定。 |
| Claim | `claim_longmen_music_guyang` | 龙门北魏阶段洞窟中保存伎乐天与乐器雕刻，古阳洞是其中较有代表性的一处，其乐器组合 | review | 需核定具体龛号、伎乐天数量与乐器种类；补充正式学术论文来源。 |
| Claim | `claim_longmen_architecture_kan` | 龙门北魏阶段窟龛中出现仿木构的屋形龛与柱、斗栱等建筑形象，是观察北朝木构建筑形象 | review | 需补充建筑史方向的正式学术来源，并核定「屋形龛」「一斗三升」等术语与具体龛号。 |
| Claim | `claim_yuanyu_epitaph_501` | 元羽卒于501年，墓志为观察北魏后期身份书写提供材料。 | review | 501年等具体年份需内容组据中国国家博物馆藏品页原文复核，并补录来源定位。 |
| Claim | `claim_epitaph_native_place_change` | 元羽墓志相关内容涉及籍贯书写的变化，可与迁都后的制度调整对照观察。 | review | 「籍贯变化」的具体内容需内容组据墓志释文核定，避免用现代行政区划概念替代当时的籍贯表述。 |
| Claim | `claim_figurine_yuanshao_528` | 中国国家博物馆藏侍从陶俑出自洛阳元邵墓，属北魏后期文物。 | review | 出土地点、墓葬年代与器物尺寸需内容组据中国国家博物馆藏品页原文核定；在与元邵本人身份相关的表述上应保持谨慎。 |
| Claim | `claim_figurine_costume_features` | 侍从陶俑的服饰形象为观察北魏后期服饰形制（如小冠、上衣下裤等着装组合）提供了实物 | review | 服饰部位的描述用词需内容组据藏品说明与服饰史研究核定，避免把一件俑的着装写成全体居民的日常穿着。 |
| Claim | `claim_language_court_content` | 本章将「朝堂语言相关规定」作为独立政策节点建模；其具体诏令条文、年份与适用范围需 | review | 本节规格仅给出政策 ID，未给出内容。需内容组补充《魏书》等史料依据后再填写正文，当前不得展示具体条文细节。 |
| Claim | `claim_xiaowen_language_court_rel` | 朝堂语言相关规定与北魏孝文帝时期的制度调整相关。 | review | 该关系的事实基础需在政策内容核定后确认。 |
| Claim | `claim_group_xianbei_boundary` | 「鲜卑」是后世与史料中使用的群体泛称，其内部包含不同部族与政治群体；本章不使用「 | review | 群体称谓的定义与使用边界需内容组与历史审核人确认，需补充民族史方向的学术来源。 |
| Claim | `claim_evidence_longmen_costume_observation` | 龙门北魏阶段窟龛中的供养人形象与造像衣饰，是可供观察当时服饰形制的图像证据。 | review | 需补充服饰史方向的学术来源，并核定具体龛位与服饰部位描述。 |
| Claim | `claim_curatorial_inscription_pair` | 本平台将博物馆藏墓志文字与龙门造像题记并置，用于说明北魏时期文字材料的多样性，两 | review | 该对照组的比较维度需内容组确认。 |
| 关系 | `rel_wei_capital_pingcheng` | — | review | 平城作为都城的具体起讫年份需内容组依据正式来源核定。 |
| 关系 | `rel_pingcheng_in_datong` | — | review | 古今地名对应关系的规范表述需内容组核定；不得由现代行政区划推断古代都城范围。 |
| 关系 | `rel_xiaowen_language_court` | — | review | 该政策节点在规格文档中只有 ID，无内容；关系的事实基础须在政策内容核定后确认。 |
| 关系 | `rel_yungang_has_tanyao` | — | review | 洞窟编号与「早期阶段」的分期表述需内容组依据云冈研究院正式资料核定。 |
| 关系 | `rel_tanyao_in_yungang` | — | review | 同 rel_yungang_has_tanyao，待洞窟编号核定。 |
| 关系 | `rel_guyang_in_longmen` | — | review | 「开凿较早」的分期表述需核定。 |
| 关系 | `rel_yungang_has_evidence_arch` | — | review | 建筑类证据的窟位、术语与来源需内容组核定。 |
| 关系 | `rel_yungang_has_evidence_music` | — | review | 音乐类证据的洞窟编号、伎乐天数量与乐器种类需核定。 |
| 关系 | `rel_longmen_has_evidence_inscriptions` | — | review | 题记数量与代表题记编号需核定。 |
| 关系 | `rel_longmen_has_evidence_costume` | — | review | 服饰类证据的具体龛位与描述需核定，并补充服饰史来源。 |
| 关系 | `rel_longmen_has_evidence_music` | — | review | 音乐类证据的具体龛号与乐器种类需核定。 |
| 关系 | `rel_epitaph_has_evidence` | — | review | 墓志释文与具体内容需内容组核定后定稿。 |
| 关系 | `rel_figurine_has_evidence` | — | review | 服饰部位描述需依据馆方资料核定。 |
| 关系 | `rel_yungang_music_supports_exchange` | — | review | 需音乐史方向研究者复核乐器分类与并存表述。 |
| 关系 | `rel_curatorial_style_pair` | — | review | 该对照组的可比性需内容组确认，若证据类型差异过大应改为分别展示。 |
| 关系 | `rel_curatorial_music_pair` | — | review | 需音乐史方向研究者确认该对照组的比较维度。 |
| 关系 | `rel_curatorial_architecture_pair` | — | review | 建筑类龙门侧证据的独立性与描述需内容组核定。 |
| 关系 | `rel_curatorial_inscription_pair` | — | review | 该对照组的比较维度需内容组确认。 |
| 知识切片 | `chunk_wei_001` | — | review | 王朝起讫年份需内容组依据正式史料或权威工具书补充来源与定位。 |
| … | | | | 另有 29 条，见 `content/northern_wei/` |

### 唐代 · 交流　（52 条：知识切片 18、实体 16、Claim 11、关系 7）

| 类型 | ID | 名称 | 状态 | 待核验事项 |
|---|---|---|---|---|
| 实体 | `period_tang` | 唐代 | review | 本条介绍依据规格文档与故宫藏品页的时代著录补写，规格文档 §26 仅列出该实体ID。唐代断代起止、与本章相关的贞观纪年换算须由内容组复核后转 approved。 |
| 实体 | `person_li_daozong` | 李道宗 | review | 1) 核验李道宗在641年唐蕃和亲中的具体角色与职衔；2) 补充权威来源（博物馆/学术）；3) 确认第一版是否将其纳入核心关系网络，或仅作为可选节点；4) 规格文档 §43「下次开发会议需定下来的10件事」未就该人物的呈现程度作出决定。 |
| 实体 | `figure_introductory_official` | 引见官员 | review | 1) 待规格文档 §43 第3项决策确定该角色做 Entity 还是 Annotation；2) 画卷热点坐标待按最终高清图重新标注；3) 复核故宫藏品页对该人物的表述原文；4) 若后续研究对「引见官员」的身份提出具体观点，须单独作为 scholarly_…… |
| 实体 | `figure_inner_attendant` | 内官 | review | 1) 待规格文档 §43 第3项决策确定建模方式；2) 热点坐标待按最终高清图重新标注；3) 「内官」在唐代职官语境中的具体所指须由内容组核验后再决定是否展开说明，当前不作展开。 |
| 实体 | `group_palace_women` | 宫女群体 | review | 1) 人数与分工须复核故宫藏品页原文；2) 热点范围与唐太宗热点重叠，待前端确定点击层级；3) 待 §43 第3项决策确定建模方式；4) 坐标待按最终高清图重新标注。 |
| 实体 | `place_changan` | 长安 | review | 1) 补充长安与唐蕃使节接待相关的权威来源；2) 核验是否需要在第一版给出具体宫城或殿名（规格文档未指定，不得自行推定）；3) 补写内容复核后转 approved。 |
| 实体 | `region_tubo` | 吐蕃 | review | 1) 补充吐蕃政权与唐蕃交往的权威来源；2) 核验区域表述与命名规范；3) 补写内容复核后转 approved。 |
| 实体 | `event_princess_wencheng_journey` | 文成公主入吐蕃行程 | review | 1) 补充行程相关的权威来源；2) 确认第一版是否给出任何地理节点（当前一律不给出）；3) 核验李道宗等护送相关人物是否纳入（关联 person_li_daozong，该实体亦待核验）。 |
| 实体 | `concept_diplomatic_mission` | 唐蕃使节活动 | review | 1) 补充权威来源；2) 确认第一版是否统计使节次数（规格文档未要求，建议不做）；3) 补写内容复核后转 approved。 |
| 实体 | `concept_personnel_exchange` | 唐蕃人员往来 | review | 1) 补充权威来源；2) 补写内容复核后转 approved。 |
| 实体 | `concept_political_marriage` | 政治婚姻（和亲） | review | 1) 补充和亲研究的权威来源；2) 复核「政治婚姻」这一命名是否需要在UI中同时给出「和亲」的说明；3) 补写内容复核后转 approved。 |
| 实体 | `concept_long_term_tang_tubo_relations` | 长期唐蕃关系 | review | 1) 需补充一则权威来源（博物馆/学术专著或专题研究）以支撑「关系存在不同阶段、也包含冲突」这一范围说明；2) 该概念在规格文档 US-06 中被要求存在，正式上线前须完成审核，否则回答「是不是一直和平」时检索不到支撑材料。 |
| 实体 | `concept_artwork_historical_evidence` | 艺术作品作为历史证据 | review | 1) 建议补充一则艺术史/图像史料学的方法论来源，使该方法说明不止依赖项目内部表述；2) 补写内容复核后转 approved。 |
| 实体 | `concept_cultural_exchange` | 文化交流 | review | 1) 补权威来源；2) 补写内容复核后转 approved。 |
| 实体 | `concept_tang_figure_painting` | 唐代历史人物画 | review | 1) 该实体为满足规格文档 §28.2 三元组而新建（§26 实体清单未列出），须经内容组确认命名与收录；2) 补权威艺术史来源；3) 补写内容复核后转 approved。 |
| 实体 | `concept_political_exchange` | 政治交往 | review | 1) 该实体为满足规格文档 §28.2 三元组而新建（§26 实体清单未列出），须经内容组确认命名与收录；2) 补权威来源；3) 补写内容复核后转 approved。 |
| Claim | `claim_bunian_dimensions_record` | 故宫博物院藏品页著录《步辇图》为绢本设色、纵38.5厘米、横129厘米；故宫名画 | review | 同一作品的横向尺寸在故宫两处官方页面不一致，须向院方核对后确定唯一权威值；在核定前，任何AI回答都不得给出单一确定尺寸。 |
| Claim | `claim_bunian_related_depicted_scene_period` | 作品被编目的时代（唐）与画面所表现事件的年代（据故宫资料系于641年前后）是两个 | review | 该表述由实现者依据两条故宫资料的时间信息整理而成，须经内容审核确认后再转 approved。 |
| Claim | `claim_bunian_supports_artwork_evidence` | 《步辇图》可作为讨论图像史料与历史现场关系的材料：画面可支持观察层面的描述，历史 | review | 本条为项目方法说明性质，所引来源为《步辇图》研究论文。建议补充一则图像史料学方法论来源，使其不止依赖单篇论文与项目内部表述。 |
| Claim | `claim_artwork_not_photograph` | 历史画是理解历史的重要图像材料，但画面表现、艺术创作和历史现场之间不能简单画等号 | review | 本条对应规格文档 §2.4 的固定内容边界，属项目方法说明。建议补充一则图像史料学或博物馆图像研究方法来源，使其具备独立的公开来源支撑。 |
| Claim | `claim_artwork_not_all_participants` | 画中人物不等于当日现场所有参与者；画面中的人数与在场名单只是本幅画面的呈现方式。 | review | 同上，属项目方法说明，须经内容审核并考虑补充公开方法论来源。 |
| Claim | `claim_costume_not_ethnicity` | 服饰特征不等于单一民族身份；画面中的艺术表现不能独立证明历史人物的全部社会身份， | review | 服色与身份的关系本身在研究中存在讨论（参见所引《唐代礼官服色考》）。本条须由内容审核确认表述边界：只说明「服饰不能直接推出民族身份」，不讨论具体服色等级结论。 |
| Claim | `claim_costume_study_note` | 《步辇图》中的礼官服色是相关研究的讨论对象之一，例如有研究讨论画面中礼官服色应为 | review | 须复核论文原文的具体论点、页码与结论范围后再定稿；引用时不得把该文观点写成唐代服色制度定论。 |
| Claim | `claim_641_not_all_relations` | 641年相关婚姻事件是长期唐蕃关系中的一个节点，不能代表此后全部唐蕃关系，也不能 | review | 本条是规格文档 §2.5 与用户故事 US-06 要求的范围说明，但当前来源只能支持641年事件本身，不足以支撑「此后关系存在不同阶段」。须补充唐蕃关系通史性或专题性权威来源后转 approved。 |
| Claim | `claim_long_term_relations_complex` | 唐与吐蕃的关系具有长期性与复杂性，使节往来、婚姻关系、人员流动与文化联系是其中的 | review | 与上一条同因：需补充唐蕃关系权威来源。该条直接支撑AI回答「是不是一直和平」，须优先完成审核。 |
| Claim | `claim_tang_tubo_not_only_marriage` | 婚姻与使节交往只是唐蕃关系的一部分，不能把整个唐蕃关系简化为「只有一次和亲」或「 | review | 需补充唐蕃关系权威来源后转 approved。 |
| Claim | `claim_modern_concept_not_tang_goal` | 现代语境中的「中华民族共同体意识」是当代概念，不能表述为唐太宗、禄东赞、文成公主 | review | 该条不绑定外部来源，须由内容审核与项目史学研究确认表述，并决定是否在正式版本中补充一则公开的史学方法论来源。 |
| 关系 | `rel_bunian_depicts_introductory_official` | — | review | 该边依赖「引见官员」的建模方式（Entity 还是 Annotation，见规格文档 §43 第3项）。若最终改为 Annotation，本边应改为标注数据而非图谱边。 |
| 关系 | `rel_bunian_depicts_inner_attendant` | — | review | 同 rel_bunian_depicts_introductory_official：待 §43 第3项决策确定建模方式。 |
| 关系 | `rel_bunian_depicts_palace_women` | — | review | 同 rel_bunian_depicts_introductory_official：待 §43 第3项决策确定建模方式。该边终点为群体实体，不得据此为任何一位宫女建立个人身份，更不得指向文成公主。 |
| 关系 | `rel_wencheng_participated_journey` | — | review | 行程事件的介绍文字待核验（规格文档 §26 仅给出实体ID），本边随该实体一并转 approved。 |
| 关系 | `rel_wencheng_journey_related_641` | — | review | 同 rel_wencheng_participated_journey：随行程事件实体核验后转 approved。 |
| 关系 | `rel_641_related_long_term` | — | review | 待确认是否在 Neo4j 中新增 ASSOCIATED_WITH 类型，或统一使用 RELATED_TO。 |
| 关系 | `rel_bunian_supports_artwork_evidence` | — | review | 该边支撑「历史画不是现场照片」的固定提示，建议补充一则图像史料学方法论来源后转 approved。 |
| 知识切片 | `chunk_tang_002` | — | review | — |
| 知识切片 | `chunk_tang_009` | — | review | — |
| 知识切片 | `chunk_tang_010` | — | review | — |
| 知识切片 | `chunk_tang_027` | — | review | — |
| 知识切片 | `chunk_tang_029` | — | review | — |
| 知识切片 | `chunk_tang_032` | — | review | — |
| 知识切片 | `chunk_tang_034` | — | review | — |
| 知识切片 | `chunk_tang_038` | — | review | — |
| 知识切片 | `chunk_tang_043` | — | review | — |
| 知识切片 | `chunk_tang_044` | — | review | — |
| 知识切片 | `chunk_tang_045` | — | review | — |
| 知识切片 | `chunk_tang_046` | — | review | — |
| 知识切片 | `chunk_tang_047` | — | review | — |
| 知识切片 | `chunk_tang_048` | — | review | — |
| 知识切片 | `chunk_tang_049` | — | review | — |
| 知识切片 | `chunk_tang_050` | — | review | — |
| 知识切片 | `chunk_tang_051` | — | review | — |
| 知识切片 | `chunk_tang_054` | — | review | — |

### 元代 · 共存　（13 条：实体 6、Claim 3、关系 2、知识切片 2）

| 类型 | ID | 名称 | 状态 | 待核验事项 |
|---|---|---|---|---|
| 实体 | `concept_multiscript_coexistence` | 多文字共存 | review | 本实体为 §28.1／§28.2 中出现、但 §26「第一批实体 ID」未定义的概念，由实现方补建。待内容组确认：中文显示名（多文字共存／多文字并用）、概念定义表述、是否与 concept_multiscript_inscription 合并、以及应当归属…… |
| 实体 | `concept_ethnic_cultural_exchange` | 多民族文化交流 | review | 本实体为 §28.1／§28.2 中出现、但 §26「第一批实体 ID」未定义的概念，由实现方补建。待内容组确认：中文显示名是否沿用官方表述原文、与 concept_cultural_exchange 的分工、以及是否需要在回答中限定为「官方公开介绍的表述」。 |
| 实体 | `concept_yuan_religion_study` | 元代宗教史 | review | 本实体为 §28.1／§28.2 中出现、但 §26「第一批实体 ID」未定义的概念，由实现方补建。待内容组确认：中文显示名（元代宗教史／元代佛教研究）、概念定义表述，以及应当绑定的学术来源与 claim（当前仅依据官方公开介绍的研究价值表述与一条解释性 …… |
| 实体 | `concept_ancient_script_study` | 古代文字研究 | review | 本实体为 §28.1／§28.2 中出现、但 §26「第一批实体 ID」未定义的概念，由实现方补建。待内容组确认：中文显示名（古代文字研究／古文字研究）、概念定义表述，以及应当绑定的学术来源与 claim（当前仅依据官方公开介绍的研究价值表述与一条解释性 …… |
| 实体 | `text_pagoda_merit_record` | 造塔功德相关记录 | review | §28.1 明确要求：本关系进入正式库前需内容组按具体题刻和权威释读再做 claim-level 审核。待补：对应的具体题刻位置、以何种文字刻写、权威释读出处（书目与页码）、以及是否应当拆分为多条 claim。审核完成前本实体与相关 chunk 保持 re…… |
| 实体 | `text_dharani_group` | 陀罗尼相关文本 | review | §28.1 明确要求：本关系进入正式库前需内容组按具体题刻和权威释读再做 claim-level 审核。待补：对应题刻位置、涉及哪些书写系统、权威释读出处（书目与页码）、以及多条咒语是否应各自建节点。审核完成前本实体与相关 chunk 保持 review …… |
| Claim | `claim_yuntai_protected_site` | 居庸关云台为全国重点文物保护单位。 | review | 实现方仅写到「全国重点文物保护单位」这一层级，未写公布批次与年份。待内容组按文物主管部门正式名录核验公布批次、年份与名录中的正式名称后，可转为 approved 并补充完整表述。 |
| Claim | `claim_six_scripts_contain_dharani` | 云台券洞题刻中包含佛教咒语（陀罗尼）类文本。 | review | §28.1 要求按具体题刻与权威释读做 claim-level 审核。待补：对应题刻位置、涉及书写系统、权威释读出处。审核通过后转 approved。 |
| Claim | `claim_six_scripts_contain_merit_record` | 云台券洞题刻中包含造塔功德相关记录。 | review | §28.1 要求按具体题刻与权威释读做 claim-level 审核。待补：对应题刻位置、涉及书写系统、权威释读出处。审核通过后转 approved。 |
| 关系 | `rel_six_scripts_contains_dharani` | — | review | §28.1 原文：最后两条（CONTAINS_TEXT）进入正式库前，需要内容组按具体题刻和权威释读再做 claim-level 审核。待补：对应具体题刻、涉及书写系统、权威释读出处（书目与页码）。审核通过前本边保持 review，不进入 AI 检索与图谱…… |
| 关系 | `rel_six_scripts_contains_merit_record` | — | review | §28.1 原文：最后两条（CONTAINS_TEXT）进入正式库前，需要内容组按具体题刻和权威释读再做 claim-level 审核。待补：对应具体题刻、涉及书写系统、权威释读出处（书目与页码）。审核通过前本边保持 review，不进入 AI 检索与图谱…… |
| 知识切片 | `chunk_yuan_036` | — | review | — |
| 知识切片 | `chunk_yuan_037` | — | review | — |

### 清代 · 归属　（36 条：实体 12、关系 12、Claim 10、历史数字 1、时间轴事件 1）

| 类型 | ID | 名称 | 状态 | 待核验事项 |
|---|---|---|---|---|
| 实体 | `person_tulishen` | 图理琛 | review | — |
| 实体 | `person_tsebek_dorji` | 策伯克多尔济 | review | — |
| 实体 | `institution_ili_governance` | 伊犁地方军政机构 | review | — |
| 实体 | `region_xinjiang_settlement` | 安置地区 | review | — |
| 实体 | `place_putuo_zongcheng_temple` | 普陀宗乘之庙 | review | — |
| 实体 | `event_tulishen_mission_1712` | 图理琛使团 | review | — |
| 实体 | `event_torghut_ennoblement` | 封爵赐印 | review | — |
| 实体 | `artifact_torghut_relief_jade_book` | 青玉御制《优恤土尔扈特部众记》册 | review | — |
| 实体 | `artifact_torghut_silver_seal` | 土尔扈特银印 | review | — |
| 实体 | `artifact_torghut_tribute_quiver` | 铁柄皮鞘番属刀 | review | — |
| 实体 | `concept_frontier_governance` | 清代边疆治理 | review | — |
| 实体 | `concept_personal_cultural_footprint` | 我的文化足迹 | review | — |
| Claim | `claim_tulishen_mission` | 故宫博物院藏品资料在介绍土尔扈特西迁背景时提到1712年清朝使团与土尔扈特的联系 | review | — |
| Claim | `claim_tulishen_mission_part_of_contacts` | 图理琛使团是清代前期土尔扈特与清朝长期联系的一部分。具体年份与过程尚待核验。 | review | — |
| Claim | `claim_ili_governance_associated_settlement` | 伊犁地方军政机构参与了东归部众的接应与安置事务。该表述尚待内容团队依据权威资料核 | review | — |
| Claim | `claim_qing_court_bestowed_silver_seal` | 中国国家博物馆相关资料介绍，东归之后清廷对相关首领封爵赐印，土尔扈特银印为相关实 | review | — |
| Claim | `claim_relief_jade_book_bears_text` | 故宫博物院专题《民本邦宁》著录的青玉刘秉恬书御制《优恤土尔扈特部众记》册，载录御 | review | — |
| Claim | `claim_putuo_zongcheng_holds_stele` | 据故宫资料记载，普陀宗乘之庙等地保存或曾保存与御制文字相关的碑刻。当前保存状况与 | review | — |
| Claim | `claim_putuo_zongcheng_located_chengde` | 普陀宗乘之庙位于承德。 | review | — |
| Claim | `claim_relief_jade_book_studies_relief` | 该青玉册可用于研究清廷记录赈济与安置的方式，以及御制文本的物质载体形式。 | review | — |
| Claim | `claim_silver_seal_studies_settlement` | 土尔扈特银印可用于研究东归之后清廷与土尔扈特之间的行政关系。它不能用于推断总人数 | review | — |
| Claim | `claim_estimate_departure_households` | 部分资料以「三万多户」为口径统计东归部众。该口径的对应来源需内容团队补充后方可对 | review | — |
| 关系 | `rel_silver_seal_associated_ennoblement` | — | review | □ 须补录银印官方定名、印文与颁赐信息后，方可从 review 升为 approved。 |
| 关系 | `rel_tulishen_mission_sent_to_torghut` | — | review | □ 须核对使团年份、往返时间与规范名称后方可升为 approved。 |
| 关系 | `rel_relief_settlement_supports_study_frontier` | — | review | □ 目标实体 concept_frontier_governance 为实现者补写节点（§26 未列出），须确认保留或改写。 |
| 关系 | `rel_belonging_curatorial_footprint` | — | review | □ 目标实体 concept_personal_cultural_footprint 为实现者补写节点（§26 未列出），须确认是否作为图谱节点保留。 |
| 关系 | `rel_tulishen_mission_associated_contacts` | — | review | □ 须核对使团信息后方可升为 approved。 |
| 关系 | `rel_ili_governance_associated_settlement` | — | review | □ 须核实该机构规范名称与具体职能后方可升为 approved。 |
| 关系 | `rel_qing_court_bestowed_silver_seal` | — | review | □ 须核实颁赐对象与时间后方可升为 approved。 |
| 关系 | `rel_relief_jade_book_bears_relief_record` | — | review | □ 须补录该册官方定名与著录信息后方可升为 approved。 |
| 关系 | `rel_putuo_zongcheng_holds_return_stele` | — | review | □ 须核实碑刻名称、文字种类与现状（「保存/曾保存」的准确表述）后方可升为 approved。 |
| 关系 | `rel_putuo_zongcheng_located_chengde` | — | review | □ 须补充来源原文定位后方可升为 approved。 |
| 关系 | `rel_relief_jade_book_studies_relief_settlement` | — | review | □ 须补录该册著录信息后方可升为 approved。 |
| 关系 | `rel_silver_seal_studies_settlement` | — | review | □ 须补录银印著录信息后方可升为 approved。 |
| 历史数字 | `estimate_departure_households_30k` | 东归出发人数 | review | □ 「三万多户」在 §2.2 中被列为口径之一，但未给出对应来源；须定位权威来源原文后方可升为 approved。 |
| 时间轴事件 | `tl_qing_seal_1775` | 相关土尔扈特银印等后续物证 | review | □ §9.1 只写「1775 相关土尔扈特银印等后续物证」，须核实该年份对应的具体物证与来源后方可升为 approved。 |

### 当代 · 传承　（171 条：实体 43、生成策略 37、关系 35、Claim 24、权利记录 22、知识切片 6、兜底问答 4）

| 类型 | ID | 名称 | 状态 | 待核验事项 |
|---|---|---|---|---|
| 实体 | `motif_fruit` | 蔬果 | review | — |
| 实体 | `motif_geometric` | 几何构图 | review | — |
| 实体 | `object_apron` | 围腰 | review | — |
| 实体 | `object_embroidery_shoes` | 绣花鞋 | review | — |
| 实体 | `object_sleeve_cover` | 袖套 | review | — |
| 实体 | `object_headscarf` | 头巾 | review | — |
| 实体 | `object_sachet` | 香包 | review | — |
| 实体 | `object_insole` | 鞋垫 | review | — |
| 实体 | `practice_copyright_protection` | 版权保护实践 | review | — |
| 实体 | `pattern_qiang_001` | 花草题材纹样元素 Q-001 | review | — |
| 实体 | `pattern_qiang_002` | 花草题材纹样元素 Q-002 | review | — |
| 实体 | `pattern_qiang_003` | 花草题材纹样元素 Q-003 | review | — |
| 实体 | `pattern_qiang_004` | 花草题材纹样元素 Q-004 | review | — |
| 实体 | `pattern_qiang_005` | 蔬果题材纹样元素 Q-005 | review | — |
| 实体 | `pattern_qiang_006` | 蔬果题材纹样元素 Q-006 | review | — |
| 实体 | `pattern_qiang_007` | 蔬果题材纹样元素 Q-007 | review | — |
| 实体 | `pattern_qiang_008` | 飞禽走兽题材纹样元素 Q-008 | review | — |
| 实体 | `pattern_qiang_009` | 飞禽走兽题材纹样元素 Q-009 | review | — |
| 实体 | `pattern_qiang_010` | 飞禽走兽题材纹样元素 Q-010 | review | — |
| 实体 | `pattern_qiang_011` | 人物题材纹样元素 Q-011 | review | — |
| 实体 | `pattern_qiang_012` | 人物题材纹样元素 Q-012 | review | — |
| 实体 | `pattern_qiang_013` | 几何构图纹样元素 Q-013 | review | — |
| 实体 | `pattern_qiang_014` | 几何构图纹样元素 Q-014 | review | — |
| 实体 | `pattern_qiang_015` | 几何构图纹样元素 Q-015 | review | — |
| 实体 | `rights_pattern_qiang_001` | pattern_qiang_001 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_002` | pattern_qiang_002 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_003` | pattern_qiang_003 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_004` | pattern_qiang_004 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_005` | pattern_qiang_005 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_006` | pattern_qiang_006 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_007` | pattern_qiang_007 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_008` | pattern_qiang_008 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_009` | pattern_qiang_009 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_010` | pattern_qiang_010 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_011` | pattern_qiang_011 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_012` | pattern_qiang_012 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_013` | pattern_qiang_013 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_014` | pattern_qiang_014 权利记录 | review | — |
| 实体 | `rights_pattern_qiang_015` | pattern_qiang_015 权利记录 | review | — |
| 实体 | `pattern_demo_flora_01` | 花草题材（数字示意图） | review | — |
| 实体 | `pattern_demo_bird_01` | 飞禽走兽题材（数字示意图） | review | — |
| 实体 | `pattern_demo_geometric_01` | 几何构图（数字示意图） | review | — |
| 实体 | `pattern_demo_composite_01` | 组合构图（数字示意图） | review | — |
| Claim | `claim_motif_flora_split_note` | 本平台把官方表述的「花草蔬果」拆分为「花草植物」与「蔬果」两个细分类别，这一拆分 | review | — |
| Claim | `claim_motif_geometric_no_official_source` | 实施规格 §2.1 列出的官方题材类型表述为「花草蔬果、飞禽走兽、人物等」，未见 | review | — |
| Claim | `claim_rel_practice_copyright_supports` | 汶川县政府公开信息显示，当地已经开展羌绣相关的版权保护实践，涉及数字化保存、版权 | review | — |
| Claim | `claim_samr_standard_project_status` | 截至本规格编写时，全国标准信息公共服务平台显示《羌族刺绣》为推荐性国家标准制定项 | review | — |
| Claim | `claim_samr_standard_project_scope` | 上述标准制定项目公开页面显示，其公开范围涉及羌族刺绣的运用范围、种类与纹样类型、 | review | — |
| Claim | `claim_samr_standard_project_digital` | 上述标准制定项目公开页面还提到对常见针法进行系统分类，并计划提供相关针法、纹样等 | review | — |
| Claim | `claim_samr_standard_project_caveat` | 在正式标准发布生效之前，《羌族刺绣》只能表述为「国家标准制定项目公开信息」，不得 | review | — |
| Claim | `claim_object_types_from_spec` | 围腰、绣花鞋、袖套、头巾、香包、鞋垫等绣品类型出自实施规格 §8.4 与用户故事 | review | — |
| Claim | `claim_pattern_qiang_001_registered` | pattern_qiang_001 为实现方登记的花草题材纹样元素条目，使用临时 | review | — |
| Claim | `claim_pattern_qiang_002_registered` | pattern_qiang_002 为实现方登记的花草题材纹样元素条目，使用临时 | review | — |
| Claim | `claim_pattern_qiang_003_registered` | pattern_qiang_003 为实现方登记的花草题材纹样元素条目，使用临时 | review | — |
| Claim | `claim_pattern_qiang_004_registered` | pattern_qiang_004 为实现方登记的花草题材纹样元素条目，使用临时 | review | — |
| Claim | `claim_pattern_qiang_005_registered` | pattern_qiang_005 为实现方登记的蔬果题材纹样元素条目，其类别为 | review | — |
| Claim | `claim_pattern_qiang_006_registered` | pattern_qiang_006 为实现方登记的蔬果题材纹样元素条目，具体传统 | review | — |
| Claim | `claim_pattern_qiang_007_registered` | pattern_qiang_007 为实现方登记的蔬果题材纹样元素条目，具体传统 | review | — |
| Claim | `claim_pattern_qiang_008_registered` | pattern_qiang_008 为实现方登记的飞禽走兽题材纹样元素条目，题材 | review | — |
| Claim | `claim_pattern_qiang_009_registered` | pattern_qiang_009 为实现方登记的飞禽走兽题材纹样元素条目，具体 | review | — |
| … | | | | 另有 111 条，见 `content/contemporary/` |

## 三、建议优先处理的三项

1. **元代来源链接** —— 规格文档未提供来源附录，现有来源的书目信息与 URL 均由实现方补写，无法核验。
2. **元代五处题刻热点坐标** —— 规格只给出了「藏文」一处的坐标，其余五处为实现方按 2400×1350 画布拟定的初值；放入真实场景图后必须重新标注（见 `content/ASSETS.md`）。
3. **当代素材授权** —— 现有 15 个纹样元素全部为「仅可展示」，共创流程靠 4 个**项目自绘的演示元素**（`pattern_demo_*`）支撑。正式上线前应替换为已授权的传世纹样素材，或经传承实践方确认。

---

处理完上述条目后，把对应内容的 `review_status` 改为 `approved`，再重新执行 `seed_postgres.py` 与 `seed_neo4j.py`，内容即进入 AI 检索。
