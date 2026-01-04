# config/runtime_env.py
# 这个文件 不 import CrewAI、不 import LLM、不 import 工具
import os
from dotenv import load_dotenv

def setup_runtime_env():
    # 允许 OpenMP 重复加载（解决 numpy / torch 冲突）
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    # 禁用 CrewAI 遥测，防止 Signal 报错
    os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

    # LiteLLM 超时
    os.environ["LITELLM_REQUEST_TIMEOUT"] = "600"

    # 加载 .env
    load_dotenv()



