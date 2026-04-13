from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ManualPage(BaseModel):
    page_number: int
    source_file: str
    text: str
    section_title: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class ManualChunk(BaseModel):
    chunk_id: str
    page_number: int
    source_file: str
    section_title: Optional[str] = None
    content_type: str
    topics: List[str] = Field(default_factory=list)
    process_tags: List[str] = Field(default_factory=list)
    voltage_tags: List[str] = Field(default_factory=list)
    text: str
    source_path: Optional[str] = None


class ManualTable(BaseModel):
    table_id: str
    page_number: int
    source_file: str
    section_title: Optional[str] = None
    content_type: str = "table"
    topics: List[str] = Field(default_factory=list)
    process_tags: List[str] = Field(default_factory=list)
    voltage_tags: List[str] = Field(default_factory=list)
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    raw_text: str


class ManualImage(BaseModel):
    image_id: str
    page_number: int
    source_file: str
    section_title: Optional[str] = None
    content_type: str = "image"
    topics: List[str] = Field(default_factory=list)
    process_tags: List[str] = Field(default_factory=list)
    voltage_tags: List[str] = Field(default_factory=list)
    image_path: str
    caption: Optional[str] = None
    nearby_text: Optional[str] = None


class InventoryEntry(BaseModel):
    page_start: int
    page_end: int
    source_file: str
    section_title: str
    content_types: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    notes: Optional[str] = None