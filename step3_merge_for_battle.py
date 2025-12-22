import os
from utils.file_utils import read_jsonl, write_jsonl

def main():
    print(f"--- ⚔️ Step 3: 组装竞技场数据 (Battle Merge) ---")
    
    # 1. 定义输入和输出路径
    # 这两个文件分别来自你刚才运行的两个 step1 脚本
    file_a = "outputs/raw/data_scheme_A.jsonl"  # 方案 A: 交互式 Self-Play
    file_b = "outputs/raw/data_scheme_B.jsonl"  # 方案 B: 批量 Batch 生成
    
    # 输出给 step4_judge.py 用的文件
    output_file = "outputs/extracted/battle_data.jsonl"

    # 2. 检查文件是否存在
    if not os.path.exists(file_a) or not os.path.exists(file_b):
        print(f"❌ 错误：找不到输入文件！")
        print(f"   请检查是否已运行 step1_gen_selfplay.py 和 step1_gen_batch.py")
        if not os.path.exists(file_a): print(f"   缺失: {file_a}")
        if not os.path.exists(file_b): print(f"   缺失: {file_b}")
        return

    # 3. 读取数据
    print(f"正在读取文件...")
    data_a = read_jsonl(file_a)
    data_b = read_jsonl(file_b)
    print(f"  - 方案 A 数据量: {len(data_a)} 条")
    print(f"  - 方案 B 数据量: {len(data_b)} 条")

    # 4. 建立索引 (Hash Map) 以便快速匹配
    # 使用 strip() 去除可能存在的首尾空格，防止匹配失败
    dict_a = {item['question'].strip(): item['dialogue_content'] for item in data_a}
    dict_b = {item['question'].strip(): item['dialogue_content'] for item in data_b}

    battle_data = []
    matched_count = 0
    
    # 5. 遍历并配对
    # 我们以方案 A 的问题为基准，去方案 B 里找同样的题
    for q_text, content_a in dict_a.items():
        if q_text in dict_b:
            content_b = dict_b[q_text]
            
            # 构造裁判需要的格式
            # 这里的字段名 output_a 和 output_b 必须和 step4_judge.py 里的一致
            battle_data.append({
                "question": q_text,
                "output_a": content_a,
                "output_b": content_b,
                "model_a_name": "Scheme A (Self-Play)",
                "model_b_name": "Scheme B (Batch)"
            })
            matched_count += 1
        else:
            print(f"⚠️ 未匹配警告: 问题 '{q_text[:15]}...' 在方案 B 中找不到对应结果。")

    # 6. 保存结果
    if battle_data:
        write_jsonl(battle_data, output_file)
        print(f"\n✅ 组装成功！")
        print(f"   共生成 {matched_count} 组对决数据。")
        print(f"   结果已保存至: {output_file}")
        print(f"   👉 下一步：请运行 python step4_judge.py")
    else:
        print(f"\n❌ 组装失败：没有匹配到任何相同的问题。请检查 inputs/questions.txt 是否一致。")

if __name__ == "__main__":
    main()