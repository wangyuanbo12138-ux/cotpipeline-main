import os
import json
from pathlib import Path

# ============================
# 读取 questions.txt
# ============================
def load_questions(file_path: str):
    """从 txt 文件读取问题，每行一个问题"""
    questions = []
    if not os.path.exists(file_path):
        return questions
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            q = line.strip()
            if q:
                questions.append(q)
    return questions

# ============================
# 读取 JSONL 文件 (Step 2, 3, 4, 5 通用)
# ============================
def read_jsonl(file_path: str):
    """读取 jsonl 文件，返回字典列表"""
    data = []
    if not os.path.exists(file_path):
        print(f"Warning: File not found: {file_path}")
        return data
        
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON at line {i+1}")
    return data

# 为了兼容性，也可以叫 load_jsonl
load_jsonl = read_jsonl

# ============================
# 写入 JSONL 文件
# ============================
def write_jsonl(data_list, output_path: str):
    """将每条数据写成一行 JSON"""
    # 自动创建父目录
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False))
            f.write("\n")

    print(f"写入完成：{output_path}（共 {len(data_list)} 条）")
