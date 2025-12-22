import os
import time
import json
import glob
from pathlib import Path
from pydantic import BaseModel, Field

# 导入你现有的工具
from utils.file_utils import read_jsonl, write_jsonl
from utils.api_utils import get_judge_client

# ================= 配置区域 =================

# 1. 定义打分结构
class ScoreSchema(BaseModel):
    """针对整段对话的综合打分"""
    score: int = Field(..., description="对话整体质量评分 (0-10分)。")
    analysis: str = Field(..., description="简要分析对话的优缺点。")

# 2. 整体评分标准
HOLISTIC_CRITERIA = """
你是一名资深的对话系统评估专家。请阅读以下【完整的对话记录】，并对其质量进行整体打分 (0-10分)。

【对话背景】
用户 (User) 是一个有情绪困扰的孩子。
AiMe 是一个温柔的陪伴机器人，任务是安抚并引导孩子。

【评分维度】
1. **真实感 (Realism)**：对话是否流畅自然？User 的反应是否真实？
2. **人设一致性 (Persona)**：AiMe 是否始终保持温柔、耐心？
3. **引导效果 (Effectiveness)**：AiMe 是否成功接住了孩子的情绪？

【评分标准】
- **9-10分**：卓越，像真实的人类对话，逻辑连贯，完美安抚了孩子。
- **7-8分**：良好，流畅自然，人设稳得住。
- **5-6分**：及格，能看懂，但"AI味"重。
- **0-4分**：差劲，逻辑混乱或人设崩塌。

【待评估的完整对话】
{dialogue_content}
"""

# ================= 核心逻辑 =================

def score_whole_dialogue(client, dialogue_text):
    """将整段对话喂给裁判，获取一个综合分"""
    prompt = HOLISTIC_CRITERIA.format(dialogue_content=dialogue_text)
    
    try:
        result = client.chat.completions.create(
            model="qwen-max-latest", 
            response_model=ScoreSchema,
            messages=[
                {"role": "system", "content": "You are a strict dialogue judge."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_retries=2
        )
        return result.score, result.analysis
    except Exception as e:
        print(f"  ❌ 打分出错: {e}")
        return 0, f"Error: {str(e)}"

def process_file(file_path, output_path):
    print(f"\n>>> 正在评估文件: {file_path}")
    data = read_jsonl(file_path)
    
    if not data:
        print(f"❌ 警告：文件为空或不存在: {file_path}")
        return 0

    client = get_judge_client()
    scored_data = []
    scores = []
    
    for i, sample in enumerate(data):
        q_text = sample.get('question', '未知问题')
        dialogue_text = sample.get('dialogue_content', '')
        
        if not dialogue_text or len(dialogue_text) < 10:
            print(f"[{i+1}] ⚠️ 对话过短，跳过")
            continue

        print(f"[{i+1}/{len(data)}] 正在打分: {q_text[:10]}...")
        
        score, analysis = score_whole_dialogue(client, dialogue_text)
        print(f"  ★ 得分: {score} | 评语: {analysis[:30]}...")
        
        sample['holistic_score'] = score
        sample['holistic_analysis'] = analysis
        scored_data.append(sample)
        scores.append(score)
        
        time.sleep(0.5)

    write_jsonl(scored_data, output_path)
    
    if scores:
        avg_score = round(sum(scores) / len(scores), 2)
    else:
        avg_score = 0
        
    print(f"--------------------------------------------------")
    print(f"✅ 文件评估完成！")
    print(f"📂 输入: {os.path.basename(file_path)}")
    print(f"📊 平均分: {avg_score}")
    print(f"--------------------------------------------------")
    return avg_score

def main():
    Path("outputs/judged").mkdir(parents=True, exist_ok=True)
    
    print(f"--- 🏆 Step 4: 整体质量打分 (自动扫描所有文件) ---")

    # ========== 关键修改：自动扫描所有文件 ==========
    raw_files = glob.glob("outputs/raw/data_*.jsonl")
    
    if not raw_files:
        print("❌ 没有找到任何 outputs/raw/data_*.jsonl 文件！")
        return
    
    print(f"\n📁 找到 {len(raw_files)} 个文件待处理:")
    for f in sorted(raw_files):
        print(f"   - {os.path.basename(f)}")
    print("-" * 50)
    
    # 存储所有结果
    all_results = {}
    
    for input_file in sorted(raw_files):
        # 自动生成输出文件名: data_xxx.jsonl -> holistic_score_xxx.jsonl
        basename = os.path.basename(input_file)
        output_name = basename.replace("data_", "holistic_score_")
        output_file = f"outputs/judged/{output_name}"
        
        # 跳过已经处理过的文件（可选，注释掉这3行就会重新处理所有文件）
        # if os.path.exists(output_file):
        #     print(f"⏭️ 跳过已存在: {output_file}")
        #     continue
        
        avg_score = process_file(input_file, output_file)
        all_results[basename] = avg_score
    
    # ========== 打印最终汇总 ==========
    print(f"\n{'='*60}")
    print(f"📊 所有文件评估结果汇总")
    print(f"{'='*60}")
    
    for filename, score in sorted(all_results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {filename}: {score} 分")
    
    print(f"{'='*60}")
    
    # 找出最高分
    if all_results:
        best_file = max(all_results, key=all_results.get)
        print(f"🏆 最高分: {best_file} ({all_results[best_file]} 分)")

if __name__ == "__main__":
    main()