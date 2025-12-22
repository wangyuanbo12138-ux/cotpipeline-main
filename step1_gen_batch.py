import json
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 直接导入已有的工具
from utils.file_utils import load_questions, write_jsonl

# ==========================================
# 模型配置（在这里添加或修改模型）
# ==========================================
MODELS_CONFIG = [
    {
        "name": "gemini-nano-bananapro",
        "model": "turing/gemini-3-pro-image",
        "api_url": "https://live-turing.cn.llm.tcljd.com/api/v1/chat/completions",
        "api_key": "sk-Pz9c6awbV846oRqlNOrkqsggMteTxoDRnGMsSf0RAni"
    },
    {
        "name": "deepseek-v3",
        "model": "turing/deepseek-v3",
        "api_url": "https://live-turing.cn.llm.tcljd.com/api/v1/chat/completions",
        "api_key": "sk-Pz9c6awbV846oRqlNOrkqsggMteTxoDRnGMsSf0RAni"
    },
    {
        "name": "deepseek-r1",
        "model": "turing/deepseek-r1",
        "api_url": "https://live-turing.cn.llm.tcljd.com/api/v1/chat/completions",
        "api_key": "sk-Pz9c6awbV846oRqlNOrkqsggMteTxoDRnGMsSf0RAni"
    },
    {
        "name": "chatgpt-5.1",
        "model": "turing/gpt-5.1",
        "api_url": "https://live-turing.cn.llm.tcljd.com/api/v1/chat/completions",
        "api_key": "sk-Pz9c6awbV846oRqlNOrkqsggMteTxoDRnGMsSf0RAni"
    },
]

# ==========================================
# Prompt 配置（可以在这里切换不同的 prompt）
# ==========================================
PROMPT_TEMPLATE = """prompt4修改升级版：陈鹤琴（Dr. Chen Heqin）儿童教育视角 AI 分身
我是一名长期从事儿童教育研究与实践的教育工作者。
在我看来，孩子的情绪有时候和他们所处的环境紧密相关。
当孩子在某个地方感到不安、压抑或想逃开时，
换一个环境，有时候比任何话语都更有效。
这不是逃避问题，
而是先让孩子离开让他们不舒服的地方，
到一个安全、中性的空间里，
他们才有可能重新打开。
因此，我的回应方式始终遵循三个原则：
第一，先识别孩子当前所处的环境是否让他们不舒服；
第二，提供一个安全、无压力的替代环境选项；
第三，确认孩子的意愿后再行动，不替孩子做决定。
【对话生成任务】
现在，请你基于以上儿童教育视角，
一次性生成一段【已经完成的】你与孩子之间的多轮对话。
这不是实时交互，
而是用于展示完整陪伴过程的对话样本。
【细分动作步骤】
1. 识别环境线索
从孩子的表达中识别与环境相关的关键词，
如：不要在这、想离开、这里好吵、不想待在这儿。
只通过关键词识别，不做过多推测。
2. 提供替代环境
选择一个安全、无压力、中性的环境作为选项，
如：去阳台站一会儿、到房间里待一下、去外面走走。
环境要具体，不要抽象。
3. 确认意愿
确定具体的转换动作，
并询问孩子是否真的愿意去，
不强迫，尊重孩子的选择。
4. 评估变化
环境转换后，重新评估孩子的状态，
如果情绪有所缓解，继续陪伴；
如果没有变化，考虑换其他策略。
5. 留出空间
在每次回应后加入一个问题，
邀请孩子表达现在的感觉或想法。
【生成要求】
- 对话总轮次为 6–7 轮（孩子与成人交替）
- 孩子先开口
- 孩子的话可以带有想离开、不想待着的表达
- 成人回应始终保持平静、不评判、提供选择而非命令
- 对话中要体现环境转换的过程
【输出要求】
- 只输出对话内容
- 不输出任何理念说明、分析或总结
- 严格使用以下 JSON 格式：
{
  "messages": [
    {"role": "user", "content": "孩子的话"},
    {"role": "assistant", "content": "成人的回应"}
  ]
}
"""

# ==========================================
# 生成器类
# ==========================================
class MultiModelGenerator:
    def __init__(self, model_config: dict):
        self.name = model_config["name"]
        self.model = model_config["model"]
        self.api_url = model_config["api_url"]
        self.api_key = model_config["api_key"]
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.lock = threading.Lock()
        self.request_count = 0
        
    def generate_single_dialogue(self, question: str):
        """针对单个问题生成多轮对话"""
        with self.lock:
            self.request_count += 1
        
        prompt = PROMPT_TEMPLATE
        
        try:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            # 增加重试机制
            response = None
            for attempt in range(3):
                try:
                    response = requests.post(
                        self.api_url, 
                        headers=self.headers, 
                        json=data, 
                        timeout=120  # 增加超时时间
                    )
                    if response.status_code == 200:
                        break
                except requests.exceptions.RequestException as e:
                    print(f"    [{self.name}] 请求重试 {attempt + 1}/3: {e}")
                    time.sleep(2)
            
            if response and response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # 清洗可能存在的 Markdown 标记
                content = content.replace("```json", "").replace("```", "").strip()
                
                try:
                    dialogues = json.loads(content)
                    if isinstance(dialogues, dict):
                        if "messages" in dialogues:
                            return dialogues["messages"]
                        return [dialogues] 
                    return dialogues
                except:
                    print(f"    [{self.name}] JSON解析失败，内容预览: {content[:80]}...")
                    return []
            else:
                status = response.status_code if response else "无响应"
                print(f"    [{self.name}] API 请求失败: {status}")
                return []
                
        except Exception as e:
            print(f"    [{self.name}] 请求异常: {e}")
            return []


def run_single_model(model_config: dict, questions: list, num_generations: int, output_dir: str):
    """运行单个模型的测试"""
    model_name = model_config["name"]
    output_file = f"{output_dir}/data_{model_name}.jsonl"
    
    print(f"\n{'='*50}")
    print(f"🤖 开始测试模型: {model_name}")
    print(f"{'='*50}")
    
    generator = MultiModelGenerator(model_config)
    all_results = []
    
    for i in range(num_generations):
        print(f"\n  [{model_name}] 第 {i+1}/{num_generations} 轮生成")
        for q in questions:
            print(f"    正在处理: {q[:25]}...")
            result = generator.generate_single_dialogue(q)
            
            if result:
                dialogue_text = ""
                for msg in result:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    display_role = "User" if role == "user" else "AiMe"
                    dialogue_text += f"【{display_role}】: {content}\n"
                
                all_results.append({
                    "question": q,
                    "model": model_name,
                    "generation_round": i + 1,
                    "scheme_type": "batch",
                    "dialogue_content": dialogue_text
                })
                print(f"    ✅ 完成")
            else:
                print(f"    ❌ 生成失败")
            
            # 添加小延迟，避免请求过快
            time.sleep(0.5)
    
    # 保存该模型的结果
    write_jsonl(all_results, output_file)
    print(f"\n  📁 [{model_name}] 保存完成: {output_file} (共 {len(all_results)} 条)")
    
    return model_name, len(all_results)


# ==========================================
# 主执行逻辑
# ==========================================
def main():
    # 配置
    questions_file = "inputs/questions.txt"
    output_dir = "outputs/raw"
    num_generations = 10  # 每个模型每个问题生成的次数
    
    print("=" * 60)
    print("🚀 多模型批量测试工具 - 陈鹤琴儿童教育视角")
    print("=" * 60)
    print(f"📋 测试模型数量: {len(MODELS_CONFIG)}")
    print(f"🔄 每个问题生成次数: {num_generations}")
    print(f"📂 输出目录: {output_dir}")
    
    # 加载问题
    questions = load_questions(questions_file)
    if not questions:
        print("❌ 没有找到问题，请检查 inputs/questions.txt")
        return
    
    print(f"❓ 问题数量: {len(questions)}")
    print(f"📊 预计总生成数: {len(MODELS_CONFIG) * len(questions) * num_generations} 条对话")
    print("\n" + "-" * 60)
    
    # 记录开始时间
    start_time = time.time()
    
    # 依次测试每个模型
    results_summary = []
    for model_config in MODELS_CONFIG:
        model_name, count = run_single_model(
            model_config, 
            questions, 
            num_generations, 
            output_dir
        )
        results_summary.append((model_name, count))
    
    # 计算总时间
    total_time = time.time() - start_time
    
    # 输出汇总
    print("\n" + "=" * 60)
    print("📊 测试完成汇总")
    print("=" * 60)
    for model_name, count in results_summary:
        print(f"  • {model_name}: {count} 条对话")
    print(f"\n⏱️  总耗时: {total_time/60:.1f} 分钟")
    print(f"📁 所有结果已保存至: {output_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()