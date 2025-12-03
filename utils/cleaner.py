# Perform the text cleaning process

import re
from typing import List

SIGNATURE_PATTERNS = [
    r"^\s*Regards,\s*$",
    r"^\s*Best,\s*$",
    r"^\s*Thanks,\s*$",
    r"^Sent from my",
]

def remove_signatures(text : str) -> str:
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines :
        if any(re.match(pat, line.strip(), re.I) for pat in SIGNATURE_PATTERNS):
            break 
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def collapse_whitespace(text: str) -> str:
    re.sub(r"[ \t]{2,}", " ", text)

def text_normalize(text: str)-> str:
    if not text:
        return ""
    strip_text = text.strip()
    clean_text = remove_signatures(strip_text)
    remove_punc_text = "\n".join([ln for ln in clean_text.splitlines() if not re.match(r"^[\-\*_]{3,}$", ln.strip())])

    #remove whitespace
    whitespace_free_text = collapse_whitespace(remove_punc_text)

    # remove long sequences of dashes or underscores
    text = re.sub(r"[-_]{3,}", "", whitespace_free_text)

    trim_each_line_text = "\n".join([ln.strip() for ln in text.splitlines() if ln.strip()])
    return trim_each_line_text
