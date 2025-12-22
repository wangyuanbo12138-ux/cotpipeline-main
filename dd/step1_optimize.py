import os
import json
import time
from pathlib import Path
from pydantic import ValidationError

# 导入配置
from step0_config import (
    GENERATION_PROMPT_TEMPLATE,
    REFINEMENT_PROMPT_TEMPLATE,
    JUDGE_PROMPT_TEMPLATE,
    DEFAULT_RAW_DIR,
    GENERATION_MODEL_NAME_QWEN, # Qwen 模型名
    GENERATION_MODEL_NAME_DS,   # DeepSeek 模型名
    JUDGE_MODEL_NAME
)
from utils.file_utils import load_questions, write_jsonl
from utils.api_utils import get_qwen_client, get_deepseek_client, get_judge_client
from utils.pydantic_schema import CoT_Answer_Schema, JudgeSchema

# --- 核心流程封装：对单个模型进行"生成-评价-优化" ---
def process_single_model_optimization(model_name, client, model_id, question, judge_client):
    """
    输入：模型名称、客户端、模型ID、问题、裁判客户端
    输出：包含 V1, 评价, V2 的字典
    """
    print(f"  🤖 [{model_name}] 正在进行优化流程...")
    
    # --- Round 1: 初始生成 (V1) ---
    # print(f"    1️⃣  生成初始版本...")
    prompt_v1 = GENERATION_PROMPT_TEMPLATE.format(question=question)
    try:
        v1_resp = client.chat.completions.create(
            model=model_id,
            response_model=CoT_Answer_Schema,
            messages=[
                {"role": "system", "content": "You are AiMe, a warm child companion."},
                {"role": "user", "content": prompt_v1}
            ],
            temperature=0.7, # 正常温度
            max_retries=3
        )
    except Exception as e:
        print(f"    ❌ {model_name} V1 生成失败: {e}")
        return None

    # --- Round 2: 裁判点评 ---
    # print(f"    2️⃣  裁判正在挑刺...")
    # 构造给裁判看的内容
    formatted_output = f"【思维链】{v1_resp.CoT}\n【回答】{v1_resp.Answer}"
    judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
        output_a=formatted_output,
        output_b="（无对比项，请作为专家对模型A进行严格的单项评审，指出不足之处）"
    )
    
    try:
        critique_res = judge_client.chat.completions.create(
            model=JUDGE_MODEL_NAME,
            response_model=JudgeSchema,
            messages=[
                {"role": "system", "content": "You are a strict child psychology expert. Be critical."},
                {"role": "user", "content": judge_prompt}
            ],
            temperature=0.3, # 裁判要冷静
            max_retries=3
        )
    except Exception as e:
        print(f"    ❌ 裁判点评失败: {e}")
        return None
    
    # 提取修改意见
    feedback = f"共情不足点：{critique_res.accuracy_analysis}\n引导改进点：{critique_res.reasoning_analysis}"
    
    # --- Round 3: 优化修正 (V2) ---
    # print(f"    3️⃣  根据意见重写...")
    refine_prompt = REFINEMENT_PROMPT_TEMPLATE.format(
        question=question,
        critique=feedback
    )
    
    try:
        v2_resp = client.chat.completions.create(
            model=model_id,
            response_model=CoT_Answer_Schema,
            messages=[
                # 这里的 System Prompt 稍微改得强硬一点，要求它改变
                {"role": "system", "content": "You are AiMe. You MUST improve your answer significantly based on the expert feedback."},
                {"role": "user", "content": refine_prompt}
            ],
            temperature=0.8, # ★ 关键修改：调高温度，增加变化幅度
            max_retries=3
        )
    except Exception as e:
        print(f"    ❌ {model_name} V2 修正失败: {e}")
        v2_resp = None

    return {
        "model_name": model_name,
        "v1_initial": v1_resp.model_dump(),
        "critique": feedback,
        "v2_optimized": v2_resp.model_dump() if v2_resp else "Optimization Failed"
    }

def main():
    Path(DEFAULT_RAW_DIR).mkdir(parents=True, exist_ok=True)
    questions = load_questions("inputs/questions.txt")
    
    # 初始化所有客户端
    qwen_client = get_qwen_client()
    ds_client = get_deepseek_client()
    judge_client = get_judge_client()
    
    optimized_samples = []
    
    print(f"--- 🚀 开始双模型自我优化 (Dual Self-Correction) ---")
    print(f"优化目标: Qwen & DeepSeek")
    
    for i, q in enumerate(questions):
        print(f"\n[{i+1}/{len(questions)}] 处理问题: {q}")
        
        # 1. 优化 Qwen
        qwen_result = process_single_model_optimization(
            "Qwen", qwen_client, GENERATION_MODEL_NAME_QWEN, q, judge_client
        )
        
        # 2. 优化 DeepSeek
        ds_result = process_single_model_optimization(
            "DeepSeek", ds_client, GENERATION_MODEL_NAME_DS, q, judge_client
        )
        
        # 3. 整合结果
        if qwen_result and ds_result:
            record = {
                "question": q,
                "qwen_data": qwen_result,
                "deepseek_data": ds_result
            }
            optimized_samples.append(record)
            print("  ✅ 本题双模型优化完成！")
        
        # 避免速率限制
        time.sleep(1)

    # 保存
    output_path = os.path.join(DEFAULT_RAW_DIR, "dual_optimized_data.jsonl")
    write_jsonl(optimized_samples, output_path)
    print(f"\n💎 最终优化结果已保存至: {output_path}")
    print("您可以查看文件，对比 v1_initial 和 v2_optimized 的区别。")

if __name__ == "__main__":
    main()