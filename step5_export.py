import os
from step0_config import DEFAULT_JUDGED_DIR, DEFAULT_FINAL_DIR
from utils.file_utils import read_jsonl, write_jsonl


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def choose_winner(item):
    score = item["score"]
    winner = score.get("winner", "")

    if winner == "qwen":
        return {
            "question": item["question"],
            "cot": item["qwen_cot"],
            "answer": item["qwen_answer"],
            "source_model": "qwen",
            "score": score
        }
    elif winner == "deepseek":
        return {
            "question": item["question"],
            "cot": item["deepseek_cot"],
            "answer": item["deepseek_answer"],
            "source_model": "deepseek",
            "score": score
        }
    else:
        return None


def main():
    ensure_dir(DEFAULT_FINAL_DIR)

    data = read_jsonl(DEFAULT_JUDGED_DIR + "judged_data.jsonl")

    final_data = []
    for item in data:
        chosen = choose_winner(item)
        if chosen:
            final_data.append(chosen)

    write_jsonl(DEFAULT_FINAL_DIR + "train_ready.jsonl", final_data)
    print("Step5 done! Output:", DEFAULT_FINAL_DIR + "train_ready.jsonl")


if __name__ == "__main__":
    main()
