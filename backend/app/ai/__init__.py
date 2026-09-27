"""AI 层：Prompt 体系、LLM Provider、检索、重排、护栏、核验、编排。

设计原则（来自各章规格 §14–§16）：
- 5 段 Prompt 链，不写一个巨大 Prompt。
- 「No Context No Answer」：检索不到证据时不得让模型凭常识补全。
- 护栏（guards）是**确定性规则**，与 LLM 无关，任何时候都必须跑。
- 无 Key 时降级为兜底问答库，界面必须如实标注，绝不伪装成实时 AI。
"""
