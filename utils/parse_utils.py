import re


def extract_cot_answer(text: str):
    if not text:
        return "", ""

    cot_match = re.search(r"CoT:(.*?)(Answer:)", text, re.S)
    ans_match = re.search(r"Answer:(.*)", text, re.S)

    cot = cot_match.group(1).strip() if cot_match else ""
    ans = ans_match.group(1).strip() if ans_match else ""

    return cot, ans
