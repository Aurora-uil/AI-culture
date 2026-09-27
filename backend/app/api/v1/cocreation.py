"""AI 共创接口（当代章节）。

硬性要求：
- 元素是否允许生成由后台 `generation_policies` + `rights_records` 决定。
- **权利校验失败时默认不生成**（fail-closed）。
- 没有配置图像生成 Key 时返回预置演示样例，`is_fallback_sample: true`，
  标签固定为「AI辅助文化创意作品 · 非传统羌绣原作」，**不得伪装成实时生成**。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.schemas.cocreation import (
    CocreationValidationOut,
    GenerationResultOut,
    ProvenanceOut,
)
from app.services import cocreation_service

logger = logging.getLogger(__name__)

router = APIRouter()

BLOCKED_MESSAGE = "所选元素中包含不可用于 AI 生成的素材，请先移除后再试。"
NOT_FOUND_MESSAGE = "这件作品的生成记录已经不存在了。"


class ValidateRequest(BaseModel):
    element_ids: list[str] = Field(default_factory=list)
    technique_reference_ids: list[str] = Field(default_factory=list)
    application_type: str | None = None
    composition_option: str | None = None


class JobRequest(BaseModel):
    exploration_session_id: str | None = None
    element_ids: list[str] = Field(default_factory=list)
    technique_reference_ids: list[str] = Field(default_factory=list)
    application_type: str = "bookmark"
    composition_option: str = "CENTERED"
    color_option: str | None = None
    user_text: str | None = None


@router.post(
    "/cocreation/validate",
    response_model=CocreationValidationOut,
    summary="共创元素权利校验",
)
def validate_cocreation(
    payload: ValidateRequest, db: Session = Depends(get_db)
) -> CocreationValidationOut:
    """检查元素是否都有允许生成的策略与权利记录。

    不允许的进 `blocked_element_ids`。权利查询异常时**全部判为不可生成**，
    并返回 `RIGHTS_API_UNAVAILABLE` 警告码。
    """
    return cocreation_service.validate_elements(
        db,
        payload.element_ids,
        payload.technique_reference_ids,
        payload.application_type,
    )


@router.post("/cocreation/jobs", response_model=GenerationResultOut, summary="创建生成任务")
def create_job(payload: JobRequest, db: Session = Depends(get_db)) -> GenerationResultOut:
    """创建生成任务并落库。

    未配置图像生成服务时返回 3–5 个预置演示样例，
    `is_fallback_sample: true`，标签为固定的「AI辅助文化创意作品 · 非传统羌绣原作」。
    """
    try:
        return cocreation_service.create_generation_job(
            db,
            element_ids=payload.element_ids,
            technique_reference_ids=payload.technique_reference_ids,
            application_type=payload.application_type,
            composition_option=payload.composition_option,
            color_option=payload.color_option,
            user_text=payload.user_text,
            exploration_session_id=payload.exploration_session_id,
        )
    except ValueError as exc:
        # 校验不通过：给出中文原因，不生成任何资产
        detail = str(exc) or BLOCKED_MESSAGE
        raise HTTPException(status_code=400, detail=detail) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("创建生成任务失败：%s", exc)
        raise HTTPException(
            status_code=503, detail="生成服务暂时不可用，请稍后重试。"
        ) from exc


@router.get(
    "/cocreation/provenance/{asset_id}",
    response_model=ProvenanceOut,
    summary="生成溯源",
)
def get_provenance(asset_id: str, db: Session = Depends(get_db)) -> ProvenanceOut:
    """每个生成结果都可回答：用了哪些元素、哪些来源、哪些权利记录、哪个模型。"""
    provenance = cocreation_service.get_provenance(db, asset_id)
    if provenance is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return provenance
