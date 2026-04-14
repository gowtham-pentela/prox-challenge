from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class UserInput:
    query: str
    image_paths: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RetrievalResult:
    chunk_id: str
    text: str
    score: float
    page: Optional[int] = None
    source_file: Optional[str] = None
    section_title: Optional[str] = None
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RouterOutput:
    intent: str
    visual_analysis_used: bool = False
    image_evidence_present: bool = False
    query_type: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class PlanOutput:
    intent: str
    format: str
    answer_style: str
    primary_chunk_id: Optional[str] = None
    generation_mode: str = "render_then_claude"
    num_image_results: int = 0
    notes: Optional[str] = None