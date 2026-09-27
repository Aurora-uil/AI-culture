"""权利与 AIGC ORM 模型（当代章节）。

原则：权利状态与知识展示权限分离。元素能否进入 AI 共创由后台配置
（generation_policies）决定，不由 LLM 实时判断。
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime, Date

from app.models.content import Base


class RightsRecord(Base):
    """视觉资产的权利记录。每个资产都必须能回答：谁提供、能否展示、能否裁切、
    能否作为生成输入、能否用于训练、能否商用、是否需署名。"""

    __tablename__ = "rights_records"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    asset_id: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="SET NULL"))
    rights_holder: Mapped[str | None] = mapped_column(Text)
    rights_basis: Mapped[str | None] = mapped_column(Text)
    license_document_ref: Mapped[str | None] = mapped_column(Text)
    can_display: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_crop: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_transform: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_use_for_generation: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_use_for_training: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_download_original: Mapped[bool | None] = mapped_column(Boolean, default=False)
    commercial_use: Mapped[bool | None] = mapped_column(Boolean, default=False)
    attribution_required: Mapped[bool | None] = mapped_column(Boolean, default=False)
    attribution_text: Mapped[str | None] = mapped_column(Text)
    valid_from: Mapped[object | None] = mapped_column(Date)
    valid_until: Mapped[object | None] = mapped_column(Date)
    territory: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str | None] = mapped_column(Text, default="approved")


class GenerationPolicy(Base):
    """生成策略：ALLOW_COMBINATION / ALLOW_COLOR_VARIATION / ALLOW_SCALE_ONLY /
    DISPLAY_ONLY / REVIEW_REQUIRED / BLOCKED。"""

    __tablename__ = "generation_policies"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="CASCADE"))
    policy_type: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_operations: Mapped[list | None] = mapped_column(JSONB, default=list)
    blocked_operations: Mapped[list | None] = mapped_column(JSONB, default=list)
    review_note: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str | None] = mapped_column(Text, default="approved")


class CreationBasket(Base):
    """创作篮。"""

    __tablename__ = "creation_baskets"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    exploration_session_id: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text, default="open")
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CreationBasketItem(Base):
    """创作篮元素。rights_validated 由后台校验后写入，不由前端决定。"""

    __tablename__ = "creation_basket_items"

    basket_id: Mapped[str] = mapped_column(
        Text, ForeignKey("creation_baskets.id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[str] = mapped_column(
        Text, ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True
    )
    item_type: Mapped[str | None] = mapped_column(Text)
    rights_validated: Mapped[bool | None] = mapped_column(Boolean, default=False)
    generation_policy_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("generation_policies.id", ondelete="SET NULL")
    )
    added_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GenerationJob(Base):
    """生成任务。必须落库，保证可追溯。"""

    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    exploration_session_id: Mapped[str | None] = mapped_column(Text)
    basket_id: Mapped[str | None] = mapped_column(Text, ForeignKey("creation_baskets.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    application_type: Mapped[str | None] = mapped_column(Text)
    composition_option: Mapped[str | None] = mapped_column(Text)
    color_option: Mapped[str | None] = mapped_column(Text)
    user_text: Mapped[str | None] = mapped_column(Text)
    compiled_prompt_ref: Mapped[str | None] = mapped_column(Text)
    model_provider: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class GeneratedAsset(Base):
    """生成结果。label 为固定标签，不可省略、不可改写。"""

    __tablename__ = "generated_assets"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    generation_job_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("generation_jobs.id", ondelete="CASCADE")
    )
    asset_path: Mapped[str | None] = mapped_column(Text)
    thumbnail_path: Mapped[str | None] = mapped_column(Text)
    # 固定标签：AI辅助文化创意作品 · 非传统羌绣原作
    label: Mapped[str] = mapped_column(Text, nullable=False, default="AI辅助文化创意作品 · 非传统羌绣原作")
    is_fallback_sample: Mapped[bool | None] = mapped_column(Boolean, default=False)
    validation_status: Mapped[str | None] = mapped_column(Text, default="PASSED")
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GenerationProvenance(Base):
    """生成溯源：元素、针法参考、来源、权利记录、模型版本、AI 新增说明。"""

    __tablename__ = "generation_provenance"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    generated_asset_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("generated_assets.id", ondelete="CASCADE")
    )
    element_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    technique_reference_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    rights_record_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    prompt_template_version: Mapped[str | None] = mapped_column(Text)
    compiler_output_hash: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(Text)
    # 例：「AI新增：构图排列 / 数字背景 / 色彩组合」
    ai_added_note: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
