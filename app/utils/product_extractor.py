# import re
#
# def extract_product_name(text: str) -> str:
#     # 1. Look for "product_name = XYZ" line
#     match = re.search(r"product_name\s*=\s*(.+)", text)
#     if match:
#         return match.group(1).strip()
#
#     # 2. Fallback: capture first two title words
#     words = re.findall(r"\b[A-Z][a-z]+\b", text)
#     return " ".join(words[:2]) if words else "Unknown"
import re

def extract_product_name(text: str) -> str:
    # 1. Look for "product_name = XYZ" line (case-insensitive, strip punctuation)
    match = re.search(r"product_name\s*=\s*(.+)", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        # Clean up if there's trailing punctuation or linebreak
        name = re.split(r"[.\n]", name)[0].strip()
        return name

    # 2. Fallback disabled (return Unknown)
    return "Unknown"
