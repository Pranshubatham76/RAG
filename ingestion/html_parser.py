"""
HTML Parser - Extract readable text from HTML.

Purpose: Convert HTML → raw readable text
Input: content="<p>Hello <b>World</b></p>"
Output: "Hello World"
Returns to: cleaner.py
"""
from bs4 import BeautifulSoup
from typing import Dict, Any
import ftfy
from cleantext import clean
import re
import logging

logger = logging.getLogger(__name__)


def html_to_text(cooked_html: str) -> Dict[str, Any]:
    """
    Parse HTML content and extract clean text.
    
    Args:
        cooked_html: HTML string from Discourse post
        
    Returns:
        Dictionary with:
            - text: Cleaned text content
            - links: List of URLs found in the post
            - has_code: Boolean indicating if code blocks were present
            - code_blocks: List of code block contents
    """
    if not cooked_html:
        return {
            "text": "",
            "links": [],
            "has_code": False,
            "code_blocks": []
        }
    
    try:
        # Fix encoding issues
        cooked_html = ftfy.fix_text(cooked_html)
        
        soup = BeautifulSoup(cooked_html, "html.parser")
        
        # Extract code blocks first (before removing them)
        code_blocks = []
        for pre in soup.find_all(['pre', 'code']):
            code_text = pre.get_text('\n')
            if code_text.strip():
                code_blocks.append(code_text)
        
        # Remove code blocks from DOM
        for tag in soup.find_all(["pre", "code"]):
            tag.decompose()
        
        # Extract links before removing anchor tags
        links = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if href:
                # Resolve relative URLs
                if href.startswith('/'):
                    # Could prepend base URL here if needed
                    pass
                links.append(href)
            # Replace anchor with its text content
            a.replace_with(a.get_text())
        
        # Remove non-content elements
        for tagname in ["img", "button", "form", "script", "style", "svg", "iframe", "nav", "header", "footer"]:
            for tag in soup.find_all(tagname):
                tag.decompose()
        
        # Extract text with line breaks preserved
        text = soup.get_text(separator='\n')
        
        # Use cleantext library for additional cleaning (if available)
        # Note: cleantext API may vary by version, so we use basic cleaning
        try:
            # Try with minimal parameters
            text = clean(text)
        except Exception:
            # If cleantext fails, just use the text as-is (already cleaned by BeautifulSoup)
            pass
        
        # Normalize whitespace
        # Replace multiple newlines with double newline
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        # Replace multiple spaces/tabs with single space
        text = re.sub(r"[ \t]{2,}", " ", text)
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return {
            "text": text,
            "links": links,
            "has_code": len(code_blocks) > 0,
            "code_blocks": code_blocks
        }
        
    except Exception as e:
        logger.exception(f"Error parsing HTML: {e}")
        # Fallback: return empty result
        return {
            "text": "",
            "links": [],
            "has_code": False,
            "code_blocks": []
        }

