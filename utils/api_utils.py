# utils/api_utils.py
import os
import openai
import instructor

# ==========================================================
# 配置：使用 OpenAI SDK 调用你的企业平台 API
# ==========================================================

# 你的 API Key (从你旧文件中提取)
USER_API_KEY = "sk-rQCEwpkI9pMS3CnCiagb6LtQtuImWXKDkqwLzdA1mh2" 

# 企业平台统一 URL (OpenAI SDK 需要 base_url 指向 /v1)
API_BASE_URL = "https://live-turing.cn.llm.tcljd.com/api/v1" 


# --- 核心客户端初始化函数 ---
def get_patched_client(api_key: str, base_url: str):
    """初始化并对客户端打补丁，使其支持结构化输出"""
    if not api_key:
        print("Error: API_KEY is missing.")
        return None
    
    try:
        # 使用 OpenAI SDK 初始化客户端，指向您的企业平台
        client = openai.OpenAI(
            api_key=api_key, 
            base_url=base_url
        )
    except Exception as e:
        print(f"Error initializing client: {e}")
        return None

    # 使用 instructor 打补丁，启用 response_model 参数
    patched_client = instructor.patch(client)
    return patched_client

# --- 模型客户端获取函数 (Step 1 需要导入这些) ---
def get_qwen_client():
    """获取 Qwen 模型客户端"""
    return get_patched_client(USER_API_KEY, API_BASE_URL)

def get_deepseek_client():
    """获取 Deepseek 模型客户端"""
    return get_patched_client(USER_API_KEY, API_BASE_URL)

def get_judge_client():
    """获取裁判模型客户端 (Step 4 & Optimize 专用)"""
    # 之前报错就是因为缺了这个！
    return get_patched_client(USER_API_KEY, API_BASE_URL)