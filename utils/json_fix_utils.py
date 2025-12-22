def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\u0000", "")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    text = text.replace("￼", "")

    return text.strip()
