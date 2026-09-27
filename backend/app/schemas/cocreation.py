"""AI 共创（当代）出参模型。

硬性要求：没有配置图像生成 Key 时返回预置演示样例，
`is_fallback_sample: true`，标签固定为「AI辅助文化创意作品 · 非传统羌绣原作」，
不得伪装成实时生成。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# 固定标签，不可省略、不可改写
AI_ASSISTED_LABEL = "AI辅助文化创意作品 · 非传统羌绣原作"


class CocreationValidationOut(BaseModel):
    """对应前端 `CocreationValidation`。"""

    valid: bool = False
    blocked_element_ids: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    required_attributions: list[str] = Field(default_factory=list)


class GenerationResultOut(BaseModel):
    """对应前端 `GenerationResult`。"""

    asset_id: str
    generation_id: str
    image_url: str | None = None
    label: str = AI_ASSISTED_LABEL
    is_fallback_sample: bool = True
    used_element_ids: list[str] = Field(default_factory=list)
    ai_added_note: str = ""
    source_ids: list[str] = Field(default_factory=list)
    model_name: str | None = None
    model_version: str | None = None
    prompt_template_version: str | None = None
    generated_at: str | None = None
    # 无图像生成 Key 时返回一组预置样例，界面可横向展示
    samples: list[dict] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    required_attributions: list[str] = Field(default_factory=list)


class ProvenanceOut(BaseModel):
    """`GET /cocreation/provenance/{asset_id}` 返回体。"""

    asset_id: str
    generation_id: str | None = None
    label: str = AI_ASSISTED_LABEL
    is_fallback_sample: bool = True
    element_ids: list[str] = Field(default_factory=list)
    technique_reference_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    rights_record_ids: list[str] = Field(default_factory=list)
    prompt_template_version: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    ai_added_note: str | None = None
    generated_at: str | None = None
    # 溯源来源明细，便于界面直接展示
    sources: list[dict] = Field(default_factory=list)
    rights: list[dict] = Field(default_factory=list)
    policy_summary: list[dict] = Field(default_factory=list)


class CocreationElementOut(BaseModel):
    """`GET /chapters/{id}/cocreation-elements` 的元素。"""

    id: str
    name: str = ""
    entity_type: str = "PatternElement"
    short_summary: str | None = None
    image_url: str | None = None
    meaning_status: str | None = None
    rights_record_id: str | None = None
    generation_policy_id: str | None = None
    policy_type: str | None = None
    generatable: bool = False
