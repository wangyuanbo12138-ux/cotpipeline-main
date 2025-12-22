import os
import re
import time
import json
from pathlib import Path
from pydantic import BaseModel, Field

# 复用已有的工具
from utils.file_utils import read_jsonl, write_jsonl
from utils.api_utils import get_judge_client

# ================= 配置区域 =================

# 1. 定义打分的数据结构 (直接写在这里，不用改 utils 文件了)
class ScoreSchema(BaseModel):
    """针对单个 QA 对的打分结果"""
    score: int = Field(..., description="根据评分标准给出的分数 (0-10分)。")
    analysis: str = Field(..., description="对该轮对话质量的简要分析。")

# 2. 评分标准 Prompt
SCORING_CRITERIA = """
你是一个严格的对话质量打分员。请对【AiMe】的回复进行打分 (0-10分)。

【评分标准】
- **10分 (完美)**：回复极具共情力，逻辑清晰，且巧妙地引导了话题或解决了用户的潜在情绪。
- **8-9分 (优秀)**：回复自然得体，人设保持良好，无明显瑕疵。
- **6-7分 (合格)**：回复中规中矩，能接上话，但缺乏亮点或略显机械。
- **4-5分 (平庸)**：回复有“AI味”，说教感强，或者逻辑有小漏洞。
- **0-3分 (差劲)**：完全答非所问，逻辑混乱，或者人设崩塌（如突然变成了冷漠的机器）。

【当前对话上下文】
{context}

【用户 User 说】
{user_query}

【模型 AiMe 回复】
{aime_response}
"""

# ================= 核心逻辑 =================

def parse_dialogue_to_turns(dialogue_text):
    """
    把长文本拆解为每一轮。
    兼容格式：
    1. 【User】: ... 【AiMe】: ...
    2. User: ... AiMe: ...
    """
    turns = []
    
    # 尝试匹配 【User】 这种格式
    pattern1 = re.compile(r"【User】:\s*(.*?)\s*\n\s*【AiMe】:\s*(.*?)\s*(?=\n【User】|$)", re.DOTALL)
    matches = pattern1.findall(dialogue_text)
    
    # 如果没匹配到，尝试匹配 User: 这种格式 (Batch 生成有时会漏掉【】)
    if not matches:
        pattern2 = re.compile(r"User:\s*(.*?)\s*\n\s*AiMe:\s*(.*?)\s*(?=\nUser|$)", re.DOTALL)
        matches = pattern2.findall(dialogue_text)

    for m in matches:
        turns.append({
            "user": m[0].strip(),
            "aime": m[1].strip()
        })
    return turns

def score_one_turn(client, context, user, aime):
    """调用裁判给单个 Turn 打分"""
    prompt = SCORING_CRITERIA.format(
        context=context if context else "(这是对话的第一句)",
        user_query=user,
        aime_response=aime
    )
    
    try:
        # 使用 Qwen 或 DeepSeek 做裁判都可以
        result = client.chat.completions.create(
            model="qwen-max-latest", 
            response_model=ScoreSchema,
            messages=[
                {"role": "system", "content": "You are a critical dialogue quality evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_retries=2
        )
        return result.score, result.analysis
    except Exception as e:
        print(f"  ❌ 打分出错: {e}")
        return 0, "Error"

def process_file(file_path, output_path):
    print(f"正在处理文件: {file_path}")
    data = read_jsonl(file_path)
    if not data:
        print("❌ 数据为空，请检查路径或先运行 Step 1")
        return

    client = get_judge_client()
    scored_data = []
    
    for i, sample in enumerate(data):
        # 兼容不同来源的 question 字段
        q_text = sample.get('question', '未知问题')
        print(f"\n[{i+1}/{len(data)}] 正在评估对话: {q_text[:10]}...")
        
        dialogue_text = sample.get('dialogue_content', '')
        if not dialogue_text:
            print("  ⚠️ 对话内容为空，跳过")
            continue

        turns = parse_dialogue_to_turns(dialogue_text)
        
        if not turns:
            print(f"  ⚠️ 无法解析对话格式 (正则未匹配)，跳过。")
            print(f"  (调试) 文本前50字: {dialogue_text[:50]}")
            continue
            
        turn_scores = []
        history_context = "" 
        detailed_turns = []

        for t_idx, turn in enumerate(turns):
            user_text = turn['user']
            aime_text = turn['aime']
            
            # 打分
            score, reason = score_one_turn(client, history_context, user_text, aime_text)
            turn_scores.append(score)
            
            print(f"  - 第 {t_idx+1} 轮得分: {score} | 评语: {reason[:15]}...")
            
            detailed_turns.append({
                "turn_index": t_idx + 1,
                "user": user_text,
                "aime": aime_text,
                "score": score,
                "analysis": reason
            })
            
            history_context += f"User: {user_text}\nAiMe: {aime_text}\n"

        # 使用内置平均避免依赖 numpy
        avg_score = round(sum(turn_scores) / len(turn_scores), 2) if turn_scores else 0
        print(f"  ✅ 该对话平均分: {avg_score}")
        
        sample['avg_score'] = avg_score
        sample['turn_details'] = detailed_turns
        scored_data.append(sample)
        
        time.sleep(0.5)

    write_jsonl(scored_data, output_path)
    
    # 计算整体平均分
    all_avgs = [s['avg_score'] for s in scored_data]
    final_avg = round(sum(all_avgs) / len(all_avgs), 2) if all_avgs else 0
    print("="*60)
    print(f"📄 文件 {os.path.basename(file_path)} 处理完成！")
    print(f"📊 综合平均分: {final_avg}")
    print("="*60)

def main():
    import glob
    
    Path("outputs/judged").mkdir(parents=True, exist_ok=True)
    
    # 自动扫描所有 jsonl 文件
    raw_files = glob.glob("outputs/raw/*.jsonl")
    
    print(f"找到 {len(raw_files)} 个文件待处理:")
    for f in raw_files:
        print(f"  - {f}")
    print("-" * 50)
    
    for input_f in raw_files:
        # 自动生成输出文件名: data_xxx.jsonl -> score_xxx.jsonl
        filename = os.path.basename(input_f).replace("data_", "score_")
        output_f = f"outputs/judged/{filename}"
        process_file(input_f, output_f)

if __name__ == "__main__":
    main()