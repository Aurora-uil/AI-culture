"""Prompt 体系。

- `system_prompts.SYSTEM_PROMPTS`：六章各自的 Prompt A（主角色 System Prompt），
  原文抄录自各章实施规格的 §15。
- `common`：通用的 Prompt B（问题改写）/ C（证据相关性）/ D（事实核验）/ E（探索总结）。
"""

from app.ai.prompts.common import (
    MODE_FACTUAL,
    MODE_NARRATIVE,
    PROMPT_B_REWRITE,
    PROMPT_C_RELEVANCE,
    PROMPT_D_VALIDATE,
    PROMPT_E_SUMMARY,
    GUARD_REWRITE_SUFFIX,
    build_evidence_block,
    build_rewrite_prompt,
)
from app.ai.prompts.system_prompts import (
    DEFAULT_PROMPT_A,
    PROMPT_VERSION,
    SYSTEM_PROMPTS,
    get_system_prompt,
)

__all__ = [
    "SYSTEM_PROMPTS",
    "DEFAULT_PROMPT_A",
    "PROMPT_VERSION",
    "get_system_prompt",
    "PROMPT_B_REWRITE",
    "PROMPT_C_RELEVANCE",
    "PROMPT_D_VALIDATE",
    "PROMPT_E_SUMMARY",
    "GUARD_REWRITE_SUFFIX",
    "MODE_NARRATIVE",
    "MODE_FACTUAL",
    "build_evidence_block",
    "build_rewrite_prompt",
]
