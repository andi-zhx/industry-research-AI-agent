"""
config 包统一出口

用途：
- 聚合导出运行环境、网络、LLM 等配置能力
- 方便外部模块按需引用
"""

from .runtime_env import setup_runtime_env
from .network import setup_network
from .llm import get_deepseek_llm

__all__ = [
    "setup_runtime_env",
    "setup_network",
    "get_deepseek_llm"
]
