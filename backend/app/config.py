"""《同心千年》后端配置。

所有配置项从 `backend/.env` 读取（字段见 `.env.example`）。缺少 `.env`
时使用合理默认值，保证「克隆下来就能跑」：

- `LLM_API_KEY` 为空 → 自动进入「演示保障模式」（`demo_mode=True`），
  由预审核问答库作答，界面会明确标注，绝不伪装成实时 AI。
- `EMBEDDING_PROVIDER=none` 或 `EMBEDDING_API_KEY` 为空 → 检索自动切换到
  纯 Python 中文检索（字符 bigram + 关键词加权），不依赖任何外部服务。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 目录基准：backend/app/config.py → backend/ → 项目根
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
CONTENT_DIR = PROJECT_DIR / "content"


class Settings(BaseSettings):
    """环境配置单例。字段名小写，对应 .env 里的同名大写变量。"""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- 数据库 ----------
    # 注意端口是 5433（5432 已被本机另一个项目占用）
    database_url: str = "postgresql+psycopg://tongxin:tongxin_dev@localhost:5433/tongxin"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "tongxin_dev"
    neo4j_database: str = "neo4j"

    # ---------- LLM ----------
    llm_provider: str = "openai_compatible"  # openai_compatible | anthropic | mock
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-flash"
    llm_timeout_seconds: int = 30
    llm_max_tokens: int = 1200

    # ---------- Embedding ----------
    embedding_provider: str = "none"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    embedding_dim: int = 1024

    # ---------- 图像生成（当代章节 AI 共创） ----------
    # 留空时 /cocreation/jobs 返回预置演示样例（is_fallback_sample=true），
    # 界面固定标注「AI辅助文化创意作品 · 非传统羌绣原作」，不伪装成实时生成。
    image_provider: str = "none"
    image_base_url: str = ""
    image_api_key: str = ""
    image_model: str = ""

    # ---------- 检索参数 ----------
    retrieval_top_k: int = 12
    retrieval_final_k: int = 5
    # 相似度阈值不要跨模型硬编码，应在自己的验证集上标定
    retrieval_min_score: float = 0.18

    # ---------- 免密钥联网检索 ----------
    web_search_enabled: bool = True
    web_search_max_results: int = 5
    web_search_timeout_seconds: int = 8

    # ---------- 服务 ----------
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ---------- 派生属性 ----------

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS 白名单。逗号分隔字符串转列表。"""
        return [o.strip() for o in (self.cors_origins or "").split(",") if o.strip()]

    @property
    def llm_configured(self) -> bool:
        """是否配置了真实 LLM。provider=mock 时视为未配置。"""
        if self.llm_provider == "mock":
            return False
        return bool(self.llm_api_key and self.llm_api_key.strip())

    @property
    def demo_mode(self) -> bool:
        """演示保障模式：未配 Key 时为 True，界面必须显示对应标注。"""
        return not self.llm_configured

    @property
    def embedding_configured(self) -> bool:
        """是否配置了向量服务。未配置时走纯 Python 中文检索。"""
        if self.embedding_provider in ("", "none"):
            return False
        return bool(self.embedding_api_key and self.embedding_api_key.strip())

    @property
    def content_dir(self) -> Path:
        return CONTENT_DIR


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """带缓存的配置获取。测试时可用 get_settings.cache_clear() 重置。"""
    return Settings()


settings = get_settings()
