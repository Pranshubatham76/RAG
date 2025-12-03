"""
Text Cleaner - Normalize and clean text.

Purpose: Normalize, clean text, fix newline spacing, remove junk
Input: "Hello   World\n\n\nThis is a test."
Output: "Hello World\nThis is a test."
Returns to: chunker.py
"""
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Common signature patterns to remove
SIGNATURE_PATTERNS = [
    r"^\s*Regards,\s*$",
    r"^\s*Best,\s*$",
    r"^\s*Thanks,\s*$",
    r"^\s*Thank you,\s*$",
    r"^\s*Cheers,\s*$",
    r"^Sent from my",
    r"^On .* wrote:",
    r"^From:.*",
    r"^To:.*",
    r"^Subject:.*",
]


def remove_signatures(text: str) -> str:
    """
    Remove email signatures and common closing phrases from text.
    
    Args:
        text: Input text
        
    Returns:
        Text with signatures removed
    """
    if not text:
        return ""
    
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # Check if this line matches a signature pattern
        if any(re.match(pat, line.strip(), re.IGNORECASE) for pat in SIGNATURE_PATTERNS):
            # Stop processing from this point (signature found)
            break
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines).strip()


def collapse_whitespace(text: str) -> str:
    """
    Collapse multiple spaces/tabs into single space.
    
    Args:
        text: Input text
        
    Returns:
        Text with collapsed whitespace
    """
    # Replace multiple spaces/tabs with single space
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def normalize_text(text: Optional[str]) -> str:
    """
    Main text normalization function.
    
    Performs:
    1. Strip leading/trailing whitespace
    2. Remove signatures
    3. Remove separator lines (---, ***, ___, etc.)
    4. Collapse whitespace
    5. Remove long sequences of dashes/underscores
    6. Trim each line and remove empty lines
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Step 1: Strip
    normalized = text.strip()
    
    if not normalized:
        return ""
    
    # Step 2: Remove signatures
    normalized = remove_signatures(normalized)
    
    # Step 3: Remove separator lines (---, ***, ___, etc.)
    lines = normalized.splitlines()
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are just dashes, asterisks, or underscores
        if not re.match(r"^[\-\*_]{3,}$", stripped):
            filtered_lines.append(line)
    
    normalized = "\n".join(filtered_lines)
    
    # Step 4: Collapse whitespace
    normalized = collapse_whitespace(normalized)
    
    # Step 5: Remove long sequences of dashes/underscores
    normalized = re.sub(r"[-_]{3,}", "", normalized)
    
    # Step 6: Trim each line and filter empty lines
    final_lines = []
    for line in normalized.splitlines():
        trimmed = line.strip()
        if trimmed:  # Only keep non-empty lines
            final_lines.append(trimmed)
    
    return "\n".join(final_lines)

