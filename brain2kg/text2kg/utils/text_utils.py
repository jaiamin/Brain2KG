

def preprocess_text(text: str):
    # remove quotations (single and double)
    text = text.replace('\'', '')
    text = text.replace('"', '')
    return text