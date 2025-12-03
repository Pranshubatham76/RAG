# Parse the HTML file and extract the text content.

from bs4 import BeautifulSoup
from typing import Dict, Any, List
import ftfy
from cleantext import clean
import re


def html_to_text(cooked_html : str) -> Dict[str, Any]:
    if not cooked_html:
        return {
            "text": "",
            "links" : [],
            "has_code" : False,
            "code_blocks" : []
        }
    
    cooked_html = ftfy.fix_text(cooked_html)
    
    soup = BeautifulSoup(cooked_html, "html.parser")

    # Extract and remove the clode block first

    code_blocks = [
        pre.get_text('\n') for pre in soup.find_all(['pre', "code"])
    ]

    for tag in soup.find_all(["pre", "code"]):
        tag.decompose()

    # Extract links
    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            links.append(href)
        a.replace_with(a.get_text())


    # Remove images, buttons. forms, scripts
    for tagname in ["img", "button", "form", "script", "style", "svg", "iframe"]:
        for tag in soup.find_all(tagname):
            tag.decompose()
    
    text = soup.get_text(separator='\n')

    # use cleantext to clean up the text
    text = clean(
        text, 
        fix_unicode = False,
        to_ascii = False,
        lower = False,
        no_line_breaks = False,
        no_urls = False,
        no_emails = True,
        replace_with_url = "",
        replace_with_email = "",
    )

    # Normalization of whitespaces
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    text = re.sub(r"[ \t]{2,}", " ", text)

    return {
        "text" : text,
        "links" : links,
        "has_code" : len(code_blocks) > 0,
        "code_blocks" : code_blocks,
    }