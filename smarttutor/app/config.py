"""
Model configuration for SmartTutor.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class ModelConfig:
    """Centralized model and provider configuration."""

    HKUST_AZURE_API_KEY = os.getenv("HKUST_AZURE_API_KEY", "")
    HKUST_AZURE_ENDPOINT = os.getenv("HKUST_AZURE_ENDPOINT", "https://hkust.azure-api.net")
    HKUST_AZURE_DEPLOYMENT_NAME = os.getenv("HKUST_AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")
    HKUST_AZURE_API_VERSION = os.getenv("HKUST_AZURE_API_VERSION", "2025-02-01-preview")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://api.openai.com")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    # Use a public model by default; task-specific access can vary by team.
    MATH_MODEL = os.getenv("MATH_MODEL", "gpt-4o-mini")
    HISTORY_MODEL = os.getenv("HISTORY_MODEL", "gpt-4o")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    MODEL_TEMPERATURE = 0.7
    MODEL_MAX_TOKENS = 2000

    @classmethod
    def is_openai_configured(cls) -> bool:
        return bool(cls.OPENAI_API_KEY)

    @classmethod
    def is_azure_configured(cls) -> bool:
        return bool(cls.AZURE_OPENAI_API_KEY)

    @classmethod
    def is_hkust_azure_configured(cls) -> bool:
        return bool(cls.HKUST_AZURE_API_KEY)

    @classmethod
    def is_deepseek_configured(cls) -> bool:
        return bool(cls.DEEPSEEK_API_KEY)

    @classmethod
    def get_active_provider(cls) -> str:
        if cls.is_hkust_azure_configured():
            return "hkust_azure"
        if cls.is_openai_configured():
            return "openai"
        if cls.is_azure_configured():
            return "azure"
        if cls.is_deepseek_configured():
            return "deepseek"
        return None

    @classmethod
    def get_model_name(cls, task: str = "default") -> str:
        if task == "math":
            return cls.MATH_MODEL
        if task == "history":
            return cls.HISTORY_MODEL
        return cls.DEFAULT_MODEL


config = ModelConfig()
