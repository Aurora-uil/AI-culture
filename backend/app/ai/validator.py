"""答案核验。

- **guards 一定跑**（确定性规则，与 LLM 无关）。
- Prompt D 事实核验：配置了 LLM 时才跑；无 LLM 时跳过并把结论标为
  「未做模型核验」，绝不假称已核验。
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from app.ai import guards
from app.ai.prompts.common import PROMPT_D_VALIDATE
from app.ai.retriever import RetrievedChunk
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """核验结果。"""

    passed: bool = True
    guard_hits: list[guards.GuardHit] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    citation_errors: list[str] = field(default_factory=list)
    rewrite_required: bool = False
    # 无 LLM 时为 False —— 表示「未做模型核验」，界面不应声称已核验
    llm_checked: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def violation_text(self) -> str:
        """拼给重写指令用的违规说明。"""
        parts = []
        guard_text = guards.build_violation_text(self.guard_hits)
        if guard_text:
            parts.append(guard_text)
        if self.unsupported_claims:
            parts.append(
                "证据外主张：\n"
                + "\n".join(f"- {claim}" for claim in self.unsupported_claims[:5])
            )
        if self.citation_errors:
            parts.append(
                "引用问题：\n"
                + "\n".join(f"- {error}" for error in self.citation_errors[:5])
            )
        return "\n".join(parts)


def _parse_verdict(raw: str) -> dict | None:
    """解析 Prompt D 的 JSON 输出。"""
    if not raw:
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def check_citations(
    answer_citation_ids: list[str], chunks: list[RetrievedChunk]
) -> list[str]:
    """引用编号真实性检查：不得创造不存在的来源编号。

    这一项是确定性的，即使没有 LLM 也一定跑。
    """
    available = {chunk.id for chunk in chunks}
    return [
        f"引用了未提供的编号：{citation_id}"
        for citation_id in answer_citation_ids
        if citation_id not in available
    ]


async def validate(
    answer: str,
    chunks: list[RetrievedChunk],
    *,
    chapter_id: str | None = None,
    question: str = "",
    citation_ids: list[str] | None = None,
    provider=None,
) -> ValidationResult:
    """完整核验流程。"""
    result = ValidationResult()

    # 1) 确定性护栏 —— 永远执行
    result.guard_hits = guards.check(answer, chapter_id=chapter_id, question=question)
    if result.guard_hits:
        result.passed = False
        result.rewrite_required = True

    # 2) 引用编号真实性 —— 永远执行
    result.citation_errors = check_citations(citation_ids or [], chunks)
    if result.citation_errors:
        result.passed = False
        result.rewrite_required = True

    # 3) Prompt D 事实核验 —— 仅在有 LLM 时执行
    if provider is not None and settings.llm_configured and answer:
        try:
            verdict = _parse_verdict(
                await provider.complete(
                    [
                        {"role": "system", "content": PROMPT_D_VALIDATE},
                        {"role": "user", "content": _build_prompt(answer, chunks)},
                    ],
                    max_tokens=800,
                    json_mode=True,
                    chapter_id=chapter_id,
                )
            )
            if verdict is None:
                result.notes.append("模型核验结果无法解析，已跳过该项。")
            else:
                result.llm_checked = True
                unsupported = verdict.get("unsupported_claims") or []
                if isinstance(unsupported, list):
                    result.unsupported_claims = [str(c) for c in unsupported if c]
                result.citation_errors.extend(
                    str(e) for e in (verdict.get("citation_errors") or []) if e
                )
                if verdict.get("pass") is False or result.unsupported_claims:
                    result.passed = False
                if verdict.get("rewrite_required"):
                    result.passed = False
                    result.rewrite_required = True
        except Exception as exc:  # noqa: BLE001 - 核验失败不应阻断回答
            logger.warning("Prompt D 核验失败（跳过模型核验）：%s", exc)
            result.notes.append("模型核验未能完成，本次回答仅通过规则护栏检查。")
    else:
        result.notes.append("当前未配置模型，本次回答仅通过规则护栏检查。")

    return result


def _build_prompt(answer: str, chunks: list[RetrievedChunk]) -> str:
    lines = ["<EVIDENCE>"]
    for chunk in chunks:
        lines.append(f"[{chunk.id}] {chunk.title}")
        lines.append(chunk.text)
        lines.append("")
    lines.append("</EVIDENCE>")
    lines.append("")
    lines.append("<ANSWER>")
    lines.append(answer)
    lines.append("</ANSWER>")
    lines.append("")
    lines.append("可用的 citation_id 列表：" + ", ".join(c.id for c in chunks))
    return "\n".join(lines)
