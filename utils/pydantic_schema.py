from pydantic import BaseModel, Field

class CoT_Answer_Schema(BaseModel):
    CoT: str = Field(..., description="思考过程：分析情绪、制定策略。")
    Answer: str = Field(..., description="给孩子的最终回复。")
    
class JudgeSchema(BaseModel):
    """儿童陪伴场景的裁判评估结果"""
    
    # 借用 accuracy_analysis 字段来存“情绪共情分析”
    accuracy_analysis: str = Field(..., description="【情绪共情分析】：评估模型是否接纳了孩子情绪，是否温暖。")
    
    # 借用 reasoning_analysis 字段来存“引导技巧分析”
    reasoning_analysis: str = Field(..., description="【引导与安全分析】：评估回复是否有趣、安全、符合儿童心理。")
    
    reason: str = Field(..., description="综合判定理由。")
    winner: str = Field(..., description="胜者: 'model_a', 'model_b', or 'tie'。")