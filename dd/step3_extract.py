import os
from pathlib import Path
# 1. 导入 CLEAN_DIR
from step0_config import DEFAULT_CLEAN_DIR, DEFAULT_EXTRACT_DIR
# 2. 使用通用的读取工具
from utils.file_utils import read_jsonl, write_jsonl 

def extract_and_format(sample):
    """
    从结构化的数据中提取内容，并为裁判模型准备格式。
    """
    # 1. 获取 Qwen 的结果
    q_res = sample.get('qwen_result', {})
    q_cot = q_res.get('CoT') or "无 CoT"
    q_ans = q_res.get('Answer') or "无答案"
    
    # 2. 获取 DeepSeek 的结果
    d_res = sample.get('deepseek_result', {})
    d_cot = d_res.get('CoT') or "无 CoT"
    d_ans = d_res.get('Answer') or "无答案"
    
    # 3. 构造裁判模型需要的对比文本
    output_a_text = f"【思维链 CoT】\n{q_cot}\n\n【最终答案 Answer】\n{q_ans}"
    output_b_text = f"【思维链 CoT】\n{d_cot}\n\n【最终答案 Answer】\n{d_ans}"
    
    return {
        "question": sample['question'],
        
        # 原始字段（保留备查）
        "model_a_name": "Qwen",
        "model_a_cot": q_cot,
        "model_a_answer": q_ans,
        
        "model_b_name": "DeepSeek",
        "model_b_cot": d_cot,
        "model_b_answer": d_ans,
        
        # 核心字段（给 Step 4 裁判用的）
        "output_a": output_a_text,
        "output_b": output_b_text
    }

def main():
    # --- 关键修改：读取 Step 2 (Clean) 的输出 ---
    input_file = os.path.join(DEFAULT_CLEAN_DIR, "clean_data.jsonl")
    output_file = os.path.join(DEFAULT_EXTRACT_DIR, "extracted_data.jsonl")
    
    print(f"--- 🚀 Step 3: 数据抽取与格式化 ---")
    print(f"读取上一步(Step 2)文件: {input_file}")
    
    # 1. 加载数据
    data = read_jsonl(input_file)
    if not data:
        print(f"❌ 错误：未找到 Step 2 的数据: {input_file}")
        print("请先运行 Step 2: python step2_clean.py")
        return

    extracted_data = []
    
    # 2. 批量处理
    for i, sample in enumerate(data):
        try:
            processed = extract_and_format(sample)
            extracted_data.append(processed)
        except Exception as e:
            print(f"⚠️ 处理第 {i+1} 条数据时出错: {e}")

    # 3. 保存结果
    write_jsonl(extracted_data, output_file)
    
    print("---------------------------------------------------------")
    print(f"✅ Step 3 完成！已提取 {len(extracted_data)} 条数据。")
    print(f"结果保存在: {output_file}")

if __name__ == "__main__":
    main()