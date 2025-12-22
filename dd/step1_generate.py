# step1_generate.py
import os
from pathlib import Path
from pydantic import ValidationError

# 导入配置和工具
from step0_config import GENERATION_PROMPT_TEMPLATE, DEFAULT_RAW_DIR, GENERATION_MODEL_NAME_QWEN, GENERATION_MODEL_NAME_DS
from utils.file_utils import load_questions, write_jsonl
from utils.api_utils import get_qwen_client, get_deepseek_client
from utils.pydantic_schema import CoT_Answer_Schema

# --- 核心函数：结构化调用 LLM ---
def structured_call(client, model_name: str, question: str) -> dict:
    """
    使用 instructor 调用模型，强制返回 CoT_Answer_Schema。
    """
    if client is None:
        return {"CoT": None, "Answer": None, "error": "Client not initialized or API_KEY missing."}
        
    # 构建 Prompt (使用 Step 0 中适配结构化输出的模板)
    prompt = GENERATION_PROMPT_TEMPLATE.format(question=question)
    
    try:
        # 核心调用：response_model 强制结构化输出
        # instructor 会在后台自动处理 JSON 解析和验证
        structured_response: CoT_Answer_Schema = client.chat.completions.create(
            model=model_name,
            response_model=CoT_Answer_Schema, 
            messages=[
                {"role": "system", "content": "You are a warm and empathetic child companion."}, # 简单的人设系统提示词
                {"role": "user", "content": prompt},
            ],
            # max_retries=1: 如果格式不对，instructor 会自动让模型重试一次
            max_retries=1 
        )
        
        # 返回一个纯字典，方便 JSON 序列化
        return {
            "CoT": structured_response.CoT,
            "Answer": structured_response.Answer,
            "error": None
        }
        
    except ValidationError as e:
        # Pydantic 验证失败（格式依旧不对）
        return {"CoT": None, "Answer": None, "error": f"Pydantic Validation Error: {str(e)}"}
    except Exception as e:
        # 其他 API 或网络错误
        return {"CoT": None, "Answer": None, "error": f"API Call Error: {type(e).__name__}: {str(e)}"}

def generate_sample(question):
    """为单个问题生成 Qwen 和 Deepseek 的结构化 CoT/Answer。"""
    
    # 1. 初始化客户端
    qwen_client = get_qwen_client()
    deepseek_client = get_deepseek_client()
    
    # 2. 结构化调用 Qwen 模型
    # 使用配置中的模型名 (如 qwen-max-latest)
    qwen_output = structured_call(qwen_client, GENERATION_MODEL_NAME_QWEN, question)
    
    # 3. 结构化调用 Deepseek 模型
    # 注意：这里直接使用字符串，保证不依赖 step0_config 是否更新了 DeepSeek 变量
    deepseek_output = structured_call(deepseek_client, GENERATION_MODEL_NAME_DS, question)
    
    # 4. 封装结果
    return {
        "question": question,
        "qwen_result": qwen_output,
        "deepseek_result": deepseek_output
    }

def main():
    # 1. 确保输出目录存在
    Path(DEFAULT_RAW_DIR).mkdir(parents=True, exist_ok=True)
    
    # 2. 加载问题
    questions_file = "inputs/questions.txt"
    questions = load_questions(questions_file)
    
    if not questions:
        print(f"❌ 错误：未加载任何问题。请检查 {questions_file} 文件是否存在且包含内容。")
        return
        
    print(f"--- 🚀 Step 1: 数据生成 (共 {len(questions)} 个问题) ---")
    print(f"Qwen 模型: {GENERATION_MODEL_NAME_QWEN}")
    print(f"DeepSeek 模型: {GENERATION_MODEL_NAME_DS}")

    # 3. 循环处理
    samples = []
    for i, q in enumerate(questions):
        print(f"[{i+1}/{len(questions)}] Processing: {q[:30]}...")
        samples.append(generate_sample(q))

    # 4. 保存结果
    output_path = os.path.join(DEFAULT_RAW_DIR, "raw_data.jsonl")
    write_jsonl(samples, output_path)
    
    print("---------------------------------------------------------")
    print("✅ Step 1 complete.")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()