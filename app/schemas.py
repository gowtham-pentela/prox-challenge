from pydantic import BaseModel
from typing import List, Optional, Dict

class ManualPage(BaseModel):
    page_number: int
    text: str
    section_title: Optional[str] = None
    metadata: Dict = {}

class ManualChunk(BaseModel):
    chunk_id: str
    page_number: int
    section_title: Optional[str]
    content_type: str
    topics: List[str]
    process_tags: List[str]
    voltage_tags: List[str]
    text: str
    source_path: Optional[str] = None 

class ManualTable(BaseModel):
    table_id: str
    page_number: int
    section_title: Optional[str]
    content_type: str = "table"
    topics: List[str]
    process_tags: List[str]
    voltage_tags: List[str]
    headers: List[str]
    rows: List[List[str]]
    raw_text: str 

class ManualImage(BaseModel):
    image_id: str
    page_number: int
    section_title: Optional[str]
    content_type: str = "image"
    topics: List[str]
    process_tags: List[str]
    voltage_tags: List[str]
    image_path: str
    caption: Optional[str] = None
    nearby_text: Optional[str] = None

class InventoryEntry(BaseModel):
    page_start: int
    page_end: int
    section_title: str
    content_types: List[str]
    topics: List[str]
    notes: Optional[str] = None