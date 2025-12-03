from pydantic import BaseModel
from typing import List, Optional

class DiscoursePostModel(BaseModel):
    post_id: str
    topic_id: str
    topic_title: str
    author: str
    created_at: str
    url: str
    raw_html : str
    clean_text: str
    links: List[str] = []
    has_code: bool = False
    code_blocks: List[str] = []

    
