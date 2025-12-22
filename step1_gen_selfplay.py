import json
import requests
import time
import re
from utils.file_utils import load_questions, write_jsonl

# ================= 配置区域 =================
# 请替换为你真实的 API Key
API_KEY = "sk-Pz9c6awbV846oRqlNOrkqsggMteTxoDRnGMsSf0RAni" 
API_URL = "https://live-turing.cn.llm.tcljd.com/api/v1/chat/completions"

# 模型选择
MODEL_USER = "qwen-max-latest"       # 扮演用户
MODEL_AGENT = "turing/deepseek-v3.1" # 扮演 AiMe (被测对象)
# ===========================================

class ModelAgent:
    """单个模型代理"""
    def __init__(self, name, model, system_prompt):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.history = []

    def generate(self, message):
        """发送消息并获取回复"""
        # 构建消息历史
        messages = [{"role": "system", "content": self.system_prompt}]
        for turn in self.history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.8, # 稍微调高，增加多样性
            "max_tokens": 1000
        }
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                # 记录历史 (Self-Play 关键：我的输出是下一次我的输入)
                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": content})
                return content
            else:
                print(f"❌ API Error: {resp.text}")
                return "..."
        except Exception as e:
            print(f"❌ Request Error: {e}")
            return "..."

    def clear_memory(self):
        self.history = []

def main():
    questions = load_questions("inputs/questions.txt")
    output_file = "outputs/raw/data_scheme_A.jsonl"
    results = []

    print(f"--- 🚀 方案 A (Self-Play) 开始 ---")

    # 1. 定义两个角色
    # User: 刁钻的“熊孩子”
    user_bot = ModelAgent(
        name="User",
        model=MODEL_USER,
        system_prompt="""
        【角色】你是一个5岁的男孩，性格敏感、倔强，认死理。
        【任务】
        1. 针对AiMe的安慰，你要表现出抗拒，不要轻易被说服。
        2. 每次回答要简短（15字以内），口语化，多用“哼”、“不管”、“就是这样”等词。
        3. 前3轮对话必须保持负面情绪。
        """
    )

    # Agent: 温柔的 AiMe
    aime_bot = ModelAgent(
        name="AiMe",
        model=MODEL_AGENT,
        system_prompt="""
        【角色】你是一个温柔、幽默的儿童陪伴机器人 AiMe。
        【任务】
        1. 用生动、共情的语言安抚孩子。
        2. 尝试转移注意力，或者用比喻来解释道理。
        """
    )

    # 2. 循环跑题
    for i, q in enumerate(questions):
        print(f"[{i+1}/{len(questions)}] 正在生成: {q}")
        
        user_bot.clear_memory()
        aime_bot.clear_memory()
        
        # 记录对话文本
        dialogue_text = ""
        
        # 第一轮：User 直接抛出问题 (Seed)
        current_msg = q 
        dialogue_text += f"【User】: {current_msg}\n"
        
        # 交互 4 轮 (User -> AiMe -> User -> AiMe ...)
        for turn in range(20):
            # AiMe 回复 User
            aime_reply = aime_bot.generate(current_msg)
            dialogue_text += f"【AiMe】: {aime_reply}\n"
            print(f"  AiMe: {aime_reply[:20]}...")
            
            # User 回复 AiMe (基于 AiMe 的话继续刁难)
            # 注意：User 模型要把 AiMe 的回复当做输入
            current_msg = user_bot.generate(aime_reply)
            dialogue_text += f"【User】: {current_msg}\n"
            print(f"  User: {current_msg[:20]}...")

        # 3. 保存结果
        results.append({
            "question": q,
            "scheme_type": "self_play",
            "dialogue_content": dialogue_text
        })
        time.sleep(1) # 歇一歇

    write_jsonl(results, output_file)
    print(f"✅ 方案 A 完成！保存至: {output_file}")

if __name__ == "__main__":
    main()