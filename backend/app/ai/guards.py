"""确定性规则护栏。

**这是硬性要求：护栏不依赖 LLM，任何回答（不论来自真实模型还是兜底库）
都必须先过这里。** 命中任一条即触发重写；重写后仍违规则降级为兜底回答。

覆盖各章规格点名的红线：
1. 把六种书写系统等同六个民族 / 六种语言
2. 声称目睹 / 亲历
3. 单一动因（清代动因题）
4. 替全体发言
5. 精确 GPS 路线
6. 给出唯一精确人数
7. 唐代：文成公主 / 松赞干布出现在画中
8. 把历史画当照片
9. 当代：把 AI 图称为传统羌绣原作
10. 模拟在世传承人
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# 否定语境标记：命中这些前缀说明是在「否认」而非「主张」，不应判违规。
# 例：「这不是一张照片」「非传统羌绣原作」都是正确的表述。
NEGATION_MARKERS = (
    "非", "不", "没", "别", "勿", "无", "莫",
    "并非", "不是", "不能", "不应", "不得", "不可", "没有", "绝非", "而不是",
)


@dataclass
class GuardRule:
    """一条确定性护栏规则。"""

    code: str
    # 中文标签，会直接拼进重写指令，因此必须写清楚「哪里错了」
    label: str
    patterns: list[str] = field(default_factory=list)
    # 仅在这些章节生效；None 表示全章生效
    chapters: list[str] | None = None
    # 命中后的整改要求
    advice: str = "删除该表述，改为只陈述 <EVIDENCE> 支持的内容。"


@dataclass
class GuardHit:
    """一次命中。"""

    code: str
    label: str
    matched: str
    advice: str


# ============================================================
# 规则表
# ============================================================

GUARD_RULES: list[GuardRule] = [
    # ---------- 通用：文字 / 语言 / 族群不得一一对应（元代重点） ----------
    GuardRule(
        code="script_equals_ethnicity",
        label="把六种书写系统等同于六个民族或六种语言",
        patterns=[
            r"六种文字(分别)?(代表|就是|对应)(六|6)?个?(民族|族群|语言)",
            r"(六|6)个民族(的)?(文字|语言)",
            r"六种语言(分别)?(代表|就是|对应)",
            r"六体文字(就是|代表)(六|6)?个?(民族|语言)",
            r"一种文字(对应|代表)(一个|1个)?(民族|语言)",
        ],
        chapters=["yuan_yuntai"],
    ),
    GuardRule(
        code="script_language_ethnicity_mapping",
        label="把文字、语言、历史群体错误地一一对应",
        patterns=[
            r"这种文字(的|属于)(人|民族|族群)(都|全部|一律)",
            r"会写这种文字(的)?(人)?(就是|一定是)",
        ],
    ),
    # ---------- 通用：不得声称目睹 / 亲历 ----------
    GuardRule(
        code="claim_eyewitness",
        label="声称自己亲眼目睹或亲身经历过历史现场",
        patterns=[
            r"我(亲眼|親眼)",
            r"我(当时|当年)(看到|看见|听到|在场|就在)",
            r"我(经历过|亲历|親歷|见证了|目睹)",
            r"我(曾经|曾)(亲眼|亲历|经历)",
            r"(我|本人)(就)?(站|身)在(现场|那里|当场)",
            r"我(记得|还记得)(当时|那一天|那年)",
        ],
        advice="删除「亲眼 / 亲历 / 我当时看到」这类表述。第一人称只是数字叙事形式，不得虚构现场经历。",
    ),
    # ---------- 通用：不得替全体发言 ----------
    GuardRule(
        code="speak_for_all",
        label="替整个群体统一发言或统一心理",
        patterns=[
            r"所有(土尔扈特|蒙古|藏族|汉族|鲜卑|羌族|吐蕃|维吾尔)(人|部众|百姓|民众)?(都|均|全部)",
            r"所有(人|部众|百姓|民众)(都|均)(认为|觉得|相信|希望|想要)",
            r"每个人(都|均)(认为|觉得|相信|希望|想要)",
            r"全体(土尔扈特|部众|百姓|民众)(都|均|一致)",
            r"(他们|大家)全都(认为|觉得|相信|希望|想要)",
        ],
        advice="改为限定表述，例如「部分记载显示」「有材料提到」，不得代替整个群体声称统一态度。",
    ),
    # ---------- 通用：不得把历史画当照片 ----------
    GuardRule(
        code="artwork_as_photo",
        label="把历史绘画当作现场照片或实拍记录",
        patterns=[
            r"(就是|这是|属于|相当于)(一)?(张|幅)?(当时)??(的)?照片",
            r"(照片|相片)(般|一样)(的|地)(记录|还原|再现)",
            r"实拍(的)?(照片|影像|记录)",
            r"这是(当时|现场)(的)?(照片|实拍|摄影)",
            r"摄影(记录|作品)(般|一样)",
        ],
        advice="说明这是历史绘画（作品），不是现场照片；画面只能支持可观察信息，不能等同于历史现场的全部细节。",
    ),
    # ---------- 唐代：文成公主 / 松赞干布不在画中 ----------
    GuardRule(
        code="tang_depicted_wencheng",
        label="把文成公主描述为《步辇图》画中人物",
        patterns=[
            r"画(中|里|内)(的)?(那位|这位)?文成公主",
            r"文成公主(就)?(在|出现在)(画|画面|图)(中|里|内)",
            r"画(中|里)(的)?(宫女)?(就是|正是)文成公主",
        ],
        chapters=["tang_exchange"],
        advice="文成公主不在《步辇图》画面中，属于画外关联人物。改为「经由禄东赞与相关历史事件追溯」。",
    ),
    GuardRule(
        code="tang_depicted_songtsen",
        label="把松赞干布描述为《步辇图》画中人物",
        patterns=[
            r"画(中|里|内)(的)?松赞干布",
            r"松赞干布(就)?(在|出现在)(画|画面|图)(中|里|内)",
        ],
        chapters=["tang_exchange"],
        advice="松赞干布不在《步辇图》画面中，属于画外关联人物。",
    ),
    # ---------- 清代：单一动因 ----------
    GuardRule(
        code="qing_single_cause",
        label="把东归动因归结为唯一原因",
        patterns=[
            r"唯一(的)?(原因|理由|动机|动因)",
            r"就是(因为|由于)(这)?(一)?(个)?(原因|理由)",
            r"(根本|真正)(的)?(原因|原因只)(就)?是",
            r"(完全|全部)(是)?(因为|由于)(这)?(一)?(点|个)",
            r"(别无|没有)(其他|其它)(原因|理由)",
        ],
        chapters=["qing_return"],
        advice="不同来源记录了多重因素。改为分别说明各来源提到的因素，不得宣布存在唯一原因。",
    ),
    # ---------- 清代：路线不得精确化 ----------
    GuardRule(
        code="precise_gps_route",
        label="把历史迁徙路线描述成现代 GPS 式精确轨迹",
        patterns=[
            r"精确(的)?(路线|轨迹|坐标|路径)",
            r"(每天|每日)(走到|行进|抵达)",
            r"GPS(轨迹|定位|路线|坐标)",
            r"(路线|轨迹)(完全|十分|非常)(精确|准确|清晰)",
            r"精确到(每天|每一|公里|米)",
        ],
        advice="路线证据精度只到「较高置信廊道 / 大体区段」。改为说明该区段的 certainty 等级，不得描述成现代 GPS 轨迹。",
    ),
    # ---------- 清代：不得合并为一个精确人数 ----------
    GuardRule(
        code="single_exact_number",
        label="把多来源的历史数字合并为一个精确人数",
        patterns=[
            r"(精确|准确|确切|精准)(的)?(数字|人数|数值)",
            r"(正好|恰好|刚好)(是)?\d+",
            r"(一共|总共|合计)(就)?(是)?\d+(\.\d+)?万?人",
            r"\d+(\.\d+)?万?人(的)?(准确|精确|确切)(数字|人数|数值)",
        ],
        advice="<HISTORICAL_ESTIMATES> 中多个数值必须分别说明来源与统计口径，不得平均、合并或选一个「准确值」。",
    ),
    # ---------- 当代：AI 图不得称为传统羌绣原作 ----------
    GuardRule(
        code="ai_as_original_embroidery",
        label="把 AI 生成图称为传统羌绣原作或正宗羌绣",
        patterns=[
            r"(?<!非)传统羌绣原作",
            r"正宗(的)?羌绣",
            r"纯手工(的)?羌绣(原作|作品)",
            r"这是(真正的|真正的传统)?羌绣(原作|真品)",
            r"AI(复原|还原)(的)?(传统|正宗)?羌绣(原作)?",
            r"等同于(传统|真正的)羌绣",
        ],
        chapters=["contemporary_qiang_embroidery"],
        advice="AI 生成结果必须标注为「AI辅助文化创意作品 · 非传统羌绣原作」，不得说成传统羌绣原作或正宗羌绣。",
    ),
    GuardRule(
        code="digital_equals_handcraft",
        label="声称数字生成完成了真实手工针法",
        patterns=[
            r"(AI|数字|算法)(生成|绘制|完成)(了)?(真实|真正)??(的)?(手工)?针法",
            r"完成了(真实|真正)的(手工)?(针法|刺绣)",
        ],
        chapters=["contemporary_qiang_embroidery"],
        advice="数字生成不能等同于真实手工针法，改为说明这只是构图与色彩层面的 AI 辅助。",
    ),
    # ---------- 当代：不得模拟在世传承人 ----------
    GuardRule(
        code="impersonate_living_person",
        label="模拟在世传承人的身份或口吻",
        patterns=[
            r"我(就)?是(李兴秀|.*?)(传承人|绣娘)",
            r"我(作|担)为(.*?)(传承人|非遗传承人)",
            r"我是(国家级|省级|州级|县级)?(非遗)?传承人",
            r"以(.*?)(传承人)的(身份|口吻|人格)(跟|和|与)?(你|您)?(说|讲|聊)",
        ],
        chapters=["contemporary_qiang_embroidery"],
        advice="本系统不是任何传承人的数字分身，不得模拟在世传承人的人格、口吻或声音。",
    ),
    # ---------- 汉代：不得声称创造丝路 / 亲历文物 ----------
    GuardRule(
        code="han_created_silk_road",
        label="声称张骞个人创造了整条丝绸之路",
        patterns=[
            r"我(创(造|建)|开辟|打通)了(整条|全部|整个)?(丝绸之路|丝路)",
            r"丝绸之路(是)?(我|张骞)(一个人)?(创造|开辟|打通)的",
        ],
        chapters=["han_encounter"],
        advice="丝绸之路是长期发展的交通与交流网络，不得归功于单个人物。",
    ),
    GuardRule(
        code="han_possess_brocade",
        label="声称张骞见过 / 携带过五星锦",
        patterns=[
            r"我(见过|携带|赠送|参与制作)(过)?(「)?五星(出东方利中国)?(」)?(锦|织锦|锦护膊)",
            r"五星锦(是)?我(带|赠|送)",
        ],
        chapters=["han_encounter"],
        advice="除非 EVIDENCE 提供直接证据，不得把五星锦与张骞个人行为绑定；应区分人物事件与文物考古出土/断代。",
    ),
    # ---------- 北魏：不得一刀切归因 ----------
    GuardRule(
        code="wei_attribute_all_to_emperor",
        label="把所有北魏文化变化全部归功于孝文帝个人",
        patterns=[
            r"(所有|全部)(的)?(北魏)?(文化)?(变化|改革)(都|均)(是|由)(我|孝文帝)(一(个)?人)?",
            r"(汉化|融合)(完全|全部)(是)?(因为|由)(我|孝文帝)",
        ],
        chapters=["northern_wei_integration"],
        advice="文化变化是长期社会过程，需分别说明制度、服饰、艺术与社会证据，不得全部归功于个人。",
    ),
    GuardRule(
        code="wei_all_xianbei",
        label="替「所有鲜卑人」「所有汉人」声称统一态度",
        patterns=[
            r"所有(的)?(鲜卑|汉人|北魏)(人|居民)(都|均)",
            r"整个龙门石窟(都)?(是)?(在)?孝文帝(时期)?(完成|开凿)的",
        ],
        chapters=["northern_wei_integration"],
        advice="不得替整个群体发言，也不得声称整个龙门石窟都是孝文帝时期完成。",
    ),
    # ---------- 通用：把现代概念当作古人自觉目标 ----------
    GuardRule(
        code="modern_concept_as_ancient_goal",
        label="把现代概念直接说成历史人物的自觉目标",
        patterns=[
            r"(我|他|她|他们)(当时)?(就)?(已经)?(有|提出|追求|确立)(了)?(中华民族共同体意识|民族国家|国家认同)",
            r"(中华民族共同体意识)(是|由)(我|他|她)(当时)?(提出|确立|追求)的",
        ],
        advice="改为「从今天的研究视角看，这些遗存如何帮助理解历史上的交往与文化联系」，不得归为古人的自觉目标。",
    ),
]


# ============================================================
# 执行
# ============================================================


def _rules_for(chapter_id: str | None) -> list[GuardRule]:
    """筛选适用于该章的规则（chapters=None 表示全章生效）。"""
    return [
        rule
        for rule in GUARD_RULES
        if rule.chapters is None or (chapter_id and chapter_id in rule.chapters)
    ]


def _is_negated(text: str, start: int, window: int = 8) -> bool:
    """检查命中位置前若干字符是否是否定语境。

    「这不是一张照片」「非传统羌绣原作」都是正确表述，不能判违规。
    """
    prefix = text[max(0, start - window) : start]
    return any(marker in prefix for marker in NEGATION_MARKERS)


def check(answer: str, *, chapter_id: str | None = None, question: str = "") -> list[GuardHit]:
    """检查一段回答，返回全部命中的护栏项。

    纯确定性：不调用任何模型，同一输入永远同一输出。
    """
    if not answer:
        return []

    hits: list[GuardHit] = []
    seen_codes: set[str] = set()

    for rule in _rules_for(chapter_id):
        if rule.code in seen_codes:
            continue
        for pattern in rule.patterns:
            try:
                regex = re.compile(pattern)
            except re.error:
                continue
            for match in regex.finditer(answer):
                if _is_negated(answer, match.start()):
                    continue
                hits.append(
                    GuardHit(
                        code=rule.code,
                        label=rule.label,
                        matched=match.group(0),
                        advice=rule.advice,
                    )
                )
                seen_codes.add(rule.code)
                break
            if rule.code in seen_codes:
                break

    return hits


def build_violation_text(hits: list[GuardHit]) -> str:
    """把命中项拼成重写指令里的违规清单。"""
    if not hits:
        return ""
    lines = []
    for index, hit in enumerate(hits, start=1):
        lines.append(f"{index}. 【{hit.label}】违规片段：「{hit.matched}」")
        lines.append(f"   整改要求：{hit.advice}")
    return "\n".join(lines)


def has_blocking_hit(hits: list[GuardHit]) -> bool:
    """是否存在必须重写的命中。当前所有规则都是阻断级。"""
    return bool(hits)


def fallback_answer(chapter_id: str | None = None) -> str:
    """护栏重写后仍违规时的降级回答。"""
    return (
        "这个问题涉及的内容超出了当前已审核资料能够支持的范围，"
        "因此我不能给出确定回答。你可以换一个问法，"
        "或先查看界面中标注了来源的史料依据。"
    )
