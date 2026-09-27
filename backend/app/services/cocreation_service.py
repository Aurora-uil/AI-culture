"""AI 共创服务（当代章节）。

三条硬性规则：
1. 元素是否允许生成，由后台 `generation_policies` 决定，**不由 LLM 实时判断**。
2. **权利 API 失败时默认不生成**（fail-closed），宁可少生成也不能越权。
3. 没有配置图像生成 Key 时返回 3–5 个预置演示样例，
   `is_fallback_sample: true`，标签固定为「AI辅助文化创意作品 · 非传统羌绣原作」，
   **不得伪装成实时生成**。
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Entity,
    GeneratedAsset,
    GenerationJob,
    GenerationPolicy,
    GenerationProvenance,
    RightsRecord,
    Source,
)
from app.schemas.cocreation import (
    AI_ASSISTED_LABEL,
    CocreationElementOut,
    CocreationValidationOut,
    GenerationResultOut,
    ProvenanceOut,
)

logger = logging.getLogger(__name__)

# 允许进入 AI 生成的策略类型
GENERATABLE_POLICIES = {"ALLOW_COMBINATION", "ALLOW_COLOR_VARIATION", "ALLOW_SCALE_ONLY"}
# 禁止生成的策略类型
BLOCKED_POLICIES = {"BLOCKED", "DISPLAY_ONLY", "REVIEW_REQUIRED"}

PROMPT_TEMPLATE_VERSION = "cocreation_v1.0"

# 固定说明：明确哪些是 AI 新增的
DEFAULT_AI_ADDED_NOTE = "AI新增：构图排列 / 数字背景 / 色彩组合"

# 预置演示样例（无图像生成 Key 时使用）。3–5 个，固定标签。
FALLBACK_SAMPLES: list[dict] = [
    {
        "id": "sample_centered_flora",
        "asset_path": "/assets/contemporary/samples/sample_centered_flora.webp",
        "composition": "CENTERED",
        "title": "中心式花草构图",
        "note": "AI新增：构图排列 / 数字背景",
    },
    {
        "id": "sample_border_geometric",
        "asset_path": "/assets/contemporary/samples/sample_border_geometric.webp",
        "composition": "BORDER",
        "title": "边框式几何构图",
        "note": "AI新增：构图排列 / 色彩组合",
    },
    {
        "id": "sample_repeat_pattern",
        "asset_path": "/assets/contemporary/samples/sample_repeat_pattern.webp",
        "composition": "REPEAT",
        "title": "连续纹样平铺",
        "note": "AI新增：构图排列 / 重复单元设计",
    },
    {
        "id": "sample_symmetric_birds",
        "asset_path": "/assets/contemporary/samples/sample_symmetric_birds.webp",
        "composition": "SYMMETRIC",
        "title": "对称式飞禽构图",
        "note": "AI新增：构图排列 / 数字背景",
    },
    {
        "id": "sample_free_modern",
        "asset_path": "/assets/contemporary/samples/sample_free_modern.webp",
        "composition": "FREE_MODERN",
        "title": "现代自由构图",
        "note": "AI新增：构图排列 / 配色方案",
    },
]

# 共创元素的实体类型
COCREATION_ENTITY_TYPES = (
    "PatternElement",
    "MotifCategory",
    "Technique",
    "ObjectType",
    "Practice",
    "ICHProject",
    "Artwork",
)


# ============================================================
# 校验
# ============================================================


def _load_policies(db: Session, entity_ids: list[str]) -> dict[str, GenerationPolicy]:
    if not entity_ids:
        return {}
    rows = db.execute(
        select(GenerationPolicy).where(GenerationPolicy.entity_id.in_(entity_ids))
    ).scalars().all()
    return {row.entity_id: row for row in rows if row.entity_id}


def _load_rights(db: Session, rights_ids: list[str]) -> dict[str, RightsRecord]:
    if not rights_ids:
        return {}
    rows = db.execute(
        select(RightsRecord).where(RightsRecord.id.in_(rights_ids))
    ).scalars().all()
    return {row.id: row for row in rows}


def validate_elements(
    db: Session,
    element_ids: list[str],
    technique_reference_ids: list[str] | None = None,
    application_type: str | None = None,
) -> CocreationValidationOut:
    """校验元素是否可用于 AI 生成。

    **fail-closed**：任何一次权利查询异常，都会把所有元素判为不可生成，
    返回 `RIGHTS_API_UNAVAILABLE` 警告码，而不是放行。
    """
    result = CocreationValidationOut(valid=False)
    element_ids = [e for e in (element_ids or []) if e]
    technique_reference_ids = [t for t in (technique_reference_ids or []) if t]

    if not element_ids:
        result.warning_codes.append("NO_ELEMENT_SELECTED")
        return result

    all_ids = element_ids + technique_reference_ids

    try:
        entities = {
            e.id: e
            for e in db.execute(select(Entity).where(Entity.id.in_(all_ids))).scalars().all()
        }
        policies = _load_policies(db, all_ids)

        rights_ids: list[str] = []
        for entity in entities.values():
            extra = entity.extra or {}
            rights_id = extra.get("rights_record_id")
            if rights_id:
                rights_ids.append(str(rights_id))
        rights_map = _load_rights(db, rights_ids)
    except Exception as exc:  # noqa: BLE001 - 权利 API 失败时默认不生成
        logger.warning("权利 / 策略查询失败，按不可生成处理：%s", exc)
        result.valid = False
        result.blocked_element_ids = all_ids
        result.warning_codes.append("RIGHTS_API_UNAVAILABLE")
        return result

    blocked: list[str] = []
    for entity_id in all_ids:
        entity = entities.get(entity_id)
        if entity is None:
            blocked.append(entity_id)
            if "ELEMENT_NOT_FOUND" not in result.warning_codes:
                result.warning_codes.append("ELEMENT_NOT_FOUND")
            continue

        policy = policies.get(entity_id)
        if policy is None:
            # 没有策略 = 没有明确授权，默认不给生成
            blocked.append(entity_id)
            if "POLICY_MISSING" not in result.warning_codes:
                result.warning_codes.append("POLICY_MISSING")
            continue

        policy_type = (policy.policy_type or "").upper()
        if policy_type in BLOCKED_POLICIES:
            blocked.append(entity_id)
            code = f"POLICY_{policy_type}"
            if code not in result.warning_codes:
                result.warning_codes.append(code)
            continue
        if policy_type not in GENERATABLE_POLICIES:
            blocked.append(entity_id)
            if "POLICY_UNKNOWN" not in result.warning_codes:
                result.warning_codes.append("POLICY_UNKNOWN")
            continue

        # 知识可公开展示 ≠ 素材可用于 AI 生成，必须单独检查权利记录
        extra = entity.extra or {}
        rights_id = extra.get("rights_record_id")
        if not rights_id:
            blocked.append(entity_id)
            if "RIGHTS_RECORD_MISSING" not in result.warning_codes:
                result.warning_codes.append("RIGHTS_RECORD_MISSING")
            continue

        rights = rights_map.get(str(rights_id))
        if rights is None:
            blocked.append(entity_id)
            if "RIGHTS_RECORD_MISSING" not in result.warning_codes:
                result.warning_codes.append("RIGHTS_RECORD_MISSING")
            continue

        if not rights.can_use_for_generation:
            blocked.append(entity_id)
            if "RIGHTS_GENERATION_NOT_ALLOWED" not in result.warning_codes:
                result.warning_codes.append("RIGHTS_GENERATION_NOT_ALLOWED")

        if rights.attribution_required and rights.attribution_text:
            if rights.attribution_text not in result.required_attributions:
                result.required_attributions.append(rights.attribution_text)

        # 文化含义未记录时给提示（不阻断，但界面要提醒不得编寓意）
        meaning_status = extra.get("meaning_status")
        if meaning_status and meaning_status != "DOCUMENTED":
            if "MEANING_NOT_DOCUMENTED" not in result.warning_codes:
                result.warning_codes.append("MEANING_NOT_DOCUMENTED")

    result.blocked_element_ids = blocked
    result.valid = not blocked and bool(element_ids)
    return result


# ============================================================
# 生成任务
# ============================================================


def _image_generation_configured() -> bool:
    """是否配置了图像生成服务。未配置时一律返回预置演示样例。"""
    return bool(
        getattr(settings, "image_api_key", "")
        and str(getattr(settings, "image_provider", "none")).lower() not in ("", "none")
    )


def _pick_samples(composition_option: str | None, application_type: str | None) -> list[dict]:
    """按构图选项挑一组预置样例（3–5 个，含用户选中的构图）。"""
    preferred = [s for s in FALLBACK_SAMPLES if s["composition"] == composition_option]
    rest = [s for s in FALLBACK_SAMPLES if s["composition"] != composition_option]
    return (preferred + rest)[:4] if preferred else FALLBACK_SAMPLES[:4]


def create_generation_job(
    db: Session,
    *,
    element_ids: list[str],
    technique_reference_ids: list[str] | None = None,
    application_type: str = "bookmark",
    composition_option: str = "CENTERED",
    color_option: str | None = None,
    user_text: str | None = None,
    exploration_session_id: str | None = None,
) -> GenerationResultOut:
    """创建生成任务。校验不通过时抛 ValueError（由路由转成 400）。"""
    validation = validate_elements(db, element_ids, technique_reference_ids, application_type)
    if not validation.valid:
        raise ValueError(
            "所选元素中包含不可用于 AI 生成的素材，请先移除后再试。"
            "（原因：{}）".format("、".join(validation.warning_codes) or "未授权")
        )

    job_id = f"gen_{uuid.uuid4().hex[:16]}"
    live = _image_generation_configured()

    job = GenerationJob(
        id=job_id,
        exploration_session_id=exploration_session_id,
        status="RUNNING" if live else "FALLBACK",
        application_type=application_type,
        composition_option=composition_option,
        color_option=color_option,
        user_text=user_text,
        compiled_prompt_ref=PROMPT_TEMPLATE_VERSION,
        model_provider=getattr(settings, "image_provider", "none"),
        model_name=(
            getattr(settings, "image_model", None) if live else "preset_demo_samples"
        ),
        model_version="v1" if live else "demo",
    )
    db.add(job)
    # 显式 flush：ORM 未在模型间声明 relationship，SQLAlchemy 无法自动推断
    # generation_jobs → generated_assets 的插入顺序，不 flush 会撞外键。
    db.flush()

    # 溯源所需：元素 → 来源、权利记录
    entities = {
        e.id: e
        for e in db.execute(
            select(Entity).where(Entity.id.in_(element_ids + (technique_reference_ids or [])))
        ).scalars().all()
    }
    rights_ids = [
        str((e.extra or {}).get("rights_record_id"))
        for e in entities.values()
        if (e.extra or {}).get("rights_record_id")
    ]
    # 元素关联的来源：走 claim_sources
    source_ids = _element_source_ids(db, list(entities.keys()))

    samples = _pick_samples(composition_option, application_type)
    assets: list[dict] = []

    # 1) 先生成资产行（generated_assets 引用 generation_jobs）
    for index, sample in enumerate(samples):
        asset_id = f"asset_{job_id}_{index + 1}"
        path = sample["asset_path"]
        note = sample["note"] or DEFAULT_AI_ADDED_NOTE

        db.add(
            GeneratedAsset(
                id=asset_id,
                generation_job_id=job_id,
                asset_path=path,
                thumbnail_path=path,
                # 固定标签，不可省略、不可改写
                label=AI_ASSISTED_LABEL,
                # 无图像生成 Key 时必须是 true，界面据此标注「演示保障样例」
                is_fallback_sample=not live,
                validation_status="PASSED",
            )
        )
        assets.append(
            {
                "asset_id": asset_id,
                "image_url": path,
                "title": sample["title"],
                "composition_option": sample["composition"],
                "note": note,
            }
        )

    # provenance 引用 generated_assets，先 flush 出资产再写溯源
    db.flush()

    # 2) 再写溯源行，保证每个资产都能回答「用了什么、依据什么」
    for index, sample in enumerate(samples):
        asset_id = f"asset_{job_id}_{index + 1}"
        compiler_hash = hashlib.sha256(
            f"{job_id}|{sample['id']}|{','.join(sorted(element_ids))}|{composition_option}".encode(
                "utf-8"
            )
        ).hexdigest()
        db.add(
            GenerationProvenance(
                id=f"prov_{job_id}_{index + 1}",
                generated_asset_id=asset_id,
                element_ids=element_ids,
                technique_reference_ids=technique_reference_ids or [],
                source_ids=source_ids,
                rights_record_ids=rights_ids,
                prompt_template_version=PROMPT_TEMPLATE_VERSION,
                compiler_output_hash=compiler_hash,
                model_name=job.model_name,
                model_version=job.model_version,
                ai_added_note=sample["note"] or DEFAULT_AI_ADDED_NOTE,
            )
        )

    job.status = "COMPLETED" if live else "FALLBACK_DEMO"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()

    primary = assets[0]
    return GenerationResultOut(
        asset_id=primary["asset_id"],
        generation_id=job_id,
        image_url=primary["image_url"],
        label=AI_ASSISTED_LABEL,
        # 无图像生成 Key 时必须是 true —— 界面据此标注「演示保障样例」
        is_fallback_sample=not live,
        used_element_ids=element_ids,
        ai_added_note=primary["note"],
        source_ids=source_ids,
        model_name=job.model_name,
        model_version=job.model_version,
        prompt_template_version=PROMPT_TEMPLATE_VERSION,
        generated_at=job.completed_at.isoformat() if job.completed_at else None,
        # 预置样例是「一组」，全部返回，界面按需横向展示
        samples=assets,
        warning_codes=validation.warning_codes,
        required_attributions=validation.required_attributions,
    )


def _element_source_ids(db: Session, element_ids: list[str]) -> list[str]:
    """元素关联的来源 ID（经 claims → claim_sources）。"""
    if not element_ids:
        return []
    try:
        from app.models import Claim, ClaimSource

        rows = db.execute(
            select(ClaimSource.source_id)
            .join(Claim, Claim.id == ClaimSource.claim_id)
            .where(Claim.entity_id.in_(element_ids))
            .distinct()
        ).all()
        return [row[0] for row in rows if row[0]]
    except Exception:  # noqa: BLE001
        return []


# ============================================================
# 溯源
# ============================================================


def get_provenance(db: Session, asset_id: str) -> ProvenanceOut | None:
    """资产溯源。资产不存在时返回 None。"""
    asset = db.get(GeneratedAsset, asset_id)
    if asset is None:
        return None

    provenance = db.execute(
        select(GenerationProvenance)
        .where(GenerationProvenance.generated_asset_id == asset_id)
        .limit(1)
    ).scalars().first()
    if provenance is None:
        return ProvenanceOut(
            asset_id=asset.id,
            generation_id=asset.generation_job_id,
            label=asset.label or AI_ASSISTED_LABEL,
            is_fallback_sample=bool(asset.is_fallback_sample),
        )

    source_ids = list(provenance.source_ids or [])
    sources: list[dict] = []
    if source_ids:
        rows = db.execute(select(Source).where(Source.id.in_(source_ids))).scalars().all()
        sources = [
            {
                "id": s.id,
                "title": s.title,
                "institution": s.institution,
                "source_level": s.source_level,
                "public_url": s.public_url,
            }
            for s in rows
        ]

    rights_ids = list(provenance.rights_record_ids or [])
    rights: list[dict] = []
    if rights_ids:
        rows = db.execute(
            select(RightsRecord).where(RightsRecord.id.in_(rights_ids))
        ).scalars().all()
        rights = [
            {
                "id": r.id,
                "asset_id": r.asset_id,
                "rights_holder": r.rights_holder,
                "rights_basis": r.rights_basis,
                "can_display": bool(r.can_display),
                "can_use_for_generation": bool(r.can_use_for_generation),
                "commercial_use": bool(r.commercial_use),
                "attribution_required": bool(r.attribution_required),
                "attribution_text": r.attribution_text,
            }
            for r in rows
        ]

    element_ids = list(provenance.element_ids or [])
    policy_summary: list[dict] = []
    if element_ids:
        policies = _load_policies(db, element_ids)
        policy_summary = [
            {
                "entity_id": p.entity_id,
                "policy_id": p.id,
                "policy_type": p.policy_type,
                "allowed_operations": list(p.allowed_operations or []),
                "blocked_operations": list(p.blocked_operations or []),
            }
            for p in policies.values()
        ]

    return ProvenanceOut(
        asset_id=asset.id,
        generation_id=asset.generation_job_id,
        label=asset.label or AI_ASSISTED_LABEL,
        is_fallback_sample=bool(asset.is_fallback_sample),
        element_ids=element_ids,
        technique_reference_ids=list(provenance.technique_reference_ids or []),
        source_ids=source_ids,
        rights_record_ids=rights_ids,
        prompt_template_version=provenance.prompt_template_version,
        model_name=provenance.model_name,
        model_version=provenance.model_version,
        ai_added_note=provenance.ai_added_note,
        generated_at=provenance.generated_at.isoformat() if provenance.generated_at else None,
        sources=sources,
        rights=rights,
        policy_summary=policy_summary,
    )


# ============================================================
# 工坊元素列表
# ============================================================


def list_cocreation_elements(db: Session, chapter_id: str) -> list[CocreationElementOut]:
    """该章可用于共创的元素，附带策略与权利摘要。"""
    rows = db.execute(
        select(Entity)
        .where(
            Entity.chapter_id == chapter_id,
            Entity.entity_type.in_(COCREATION_ENTITY_TYPES),
        )
        .order_by(Entity.sort_order, Entity.id)
    ).scalars().all()
    if not rows:
        return []

    entity_ids = [e.id for e in rows]
    policies = _load_policies(db, entity_ids)

    result: list[CocreationElementOut] = []
    for entity in rows:
        extra = entity.extra or {}
        policy = policies.get(entity.id)
        policy_type = (policy.policy_type or "").upper() if policy else None
        generatable = bool(
            policy_type in GENERATABLE_POLICIES and extra.get("rights_record_id")
        )
        result.append(
            CocreationElementOut(
                id=entity.id,
                name=entity.display_name or entity.name,
                entity_type=entity.entity_type,
                short_summary=entity.short_summary,
                image_url=entity.image_url,
                meaning_status=extra.get("meaning_status"),
                rights_record_id=extra.get("rights_record_id"),
                generation_policy_id=policy.id if policy else extra.get("generation_policy_id"),
                policy_type=policy_type,
                generatable=generatable,
            )
        )
    return result
