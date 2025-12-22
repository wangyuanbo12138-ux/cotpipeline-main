import os
from step0_config import DEFAULT_RAW_DIR, DEFAULT_CLEAN_DIR
# 现在 file_utils 已经修复，可以正常导入 read_jsonl 了
from utils.file_utils import read_jsonl, write_jsonl

def main():
    # 1. 准备路径
    input_file = os.path.join(DEFAULT_RAW_DIR, "raw_data.jsonl")
    output_file = os.path.join(DEFAULT_CLEAN_DIR, "clean_data.jsonl")
    
    print(f"--- 🧹 Step 2: 数据清洗 (Pass-through) ---")
    
    # 2. 读取 Step 1 生成的数据
    # 由于 Step 1 使用了 instructor，这里读到的数据已经是完美的结构化数据
    raw_data = read_jsonl(input_file)
    
    if not raw_data:
        print(f"❌ 未找到原始数据: {input_file}")
        print("请先运行 Step 1。")
        return

    print(f"读取到 {len(raw_data)} 条原始数据。")
    print("由于 Step 1 已使用 instructor 保证了 JSON 格式正确性，")
    print("Step 2 将直接验证并传递数据...")

    cleaned_data = []
    for i, sample in enumerate(raw_data):
        # 这里可以做一些简单的逻辑检查，比如确保 CoT 不为空
        # 但一般 instructor 已经保证了 Schema 符合要求
        if sample.get('qwen_result') and sample.get('deepseek_result'):
            cleaned_data.append(sample)
        else:
            print(f"⚠️ 第 {i+1} 条数据缺失结果，已跳过。")

    # 3. 保存到 clean 目录
    write_jsonl(cleaned_data, output_file)
    
    print("---------------------------------------------------------")
    print(f"✅ Step 2 完成！有效数据: {len(cleaned_data)} 条")
    print(f"输出路径: {output_file}")

if __name__ == "__main__":
    main()