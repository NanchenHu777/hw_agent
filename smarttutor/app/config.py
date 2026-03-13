"""
SmartTutor - 作业辅导智能体
配置模型 - 支持多模型（HKUST Azure）
"""

import os
from dotenv import load_dotenv

load_dotenv()


class ModelConfig:
    """模型配置类"""
    
    # HKUST Azure 配置
    HKUST_AZURE_API_KEY = os.getenv("HKUST_AZURE_API_KEY", "")
    HKUST_AZURE_ENDPOINT = os.getenv("HKUST_AZURE_ENDPOINT", "https://hkust.azure-api.net")
    HKUST_AZURE_API_VERSION = os.getenv("HKUST_AZURE_API_VERSION", "2025-02-01-preview")
    
    # 模型选择
    MATH_MODEL = os.getenv("MATH_MODEL", "o1-mini")        # 数学模型
    HISTORY_MODEL = os.getenv("HISTORY_MODEL", "gpt-4o")   # 历史模型
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini") # 默认模型
    
    # DeepSeek 配置（可选备选）
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # 默认模型设置
    TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    MODEL_TEMPERATURE = 0.7
    MODEL_MAX_TOKENS = 2000
    
    @classmethod
    def is_hkust_azure_configured(cls) -> bool:
        return bool(cls.HKUST_AZURE_API_KEY)
    
    @classmethod
    def is_deepseek_configured(cls) -> bool:
        return bool(cls.DEEPSEEK_API_KEY)
    
    @classmethod
    def is_azure_configured(cls) -> bool:
        return False  # 标准 Azure 暂不使用
    
    @classmethod
    def get_active_provider(cls) -> str:
        """获取当前使用的API提供商"""
        if cls.is_hkust_azure_configured():
            return "hkust_azure"
        elif cls.is_deepseek_configured():
            return "deepseek"
        return None
    
    @classmethod
    def get_model_name(cls, task: str = "default") -> str:
        """获取指定任务的模型名称"""
        if task == "math":
            return cls.MATH_MODEL
        elif task == "history":
            return cls.HISTORY_MODEL
        return cls.DEFAULT_MODEL


# 全局配置
config = ModelConfig()
