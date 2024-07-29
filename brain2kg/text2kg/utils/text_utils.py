import re

def preprocess_text(text: str):
    # remove quotations (single and double)
    text = re.sub(r'["\']', '', text)
    return text