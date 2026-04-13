import json
import re

from app.config import CHUNKS_DIR


STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "at",
    "is", "are", "what", "how", "do", "i", "my", "with"
}


class KeywordSearch:
    def __init__(self):
        self.chunks = self.load_chunks()

    def load_chunks(self):
        path = CHUNKS_DIR / "chunks.jsonl"
        chunks = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))
        return chunks

    def tokenize(self, text: str):
        tokens = re.findall(r"[a-zA-Z0-9_+%-]+", text.lower())
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    def score_chunk(self, query: str, chunk: dict) -> int:
        query_tokens = self.tokenize(query)
        text = chunk["text"].lower()

        score = 0

        # Token match (base signal)
        for token in query_tokens:
            if token in text:
                score += 2

        # Metadata alignment (core signal)
        for topic in chunk.get("topics", []):
            if topic.replace("_", " ") in query:
                score += 4

        for process_tag in chunk.get("process_tags", []):
            if process_tag.replace("_", " ") in query:
                score += 3

        for voltage_tag in chunk.get("voltage_tags", []):
            if voltage_tag.replace("_", " ") in query:
                score += 3

        # Section alignment (semantic grouping)
        section_title = chunk.get("section_title")
        if section_title:
            section_tokens = self.tokenize(section_title)
            overlap = len(set(section_tokens) & set(query_tokens))
            score += overlap * 3

        # Content-type alignment
        content_type = chunk.get("content_type", "")

        if content_type == "specification":
            score += 2
        elif content_type == "procedure":
            score += 1
        elif content_type == "troubleshooting":
            score += 2

        # Source priority (owner manual wins)
        if chunk.get("source_priority") == "primary":
            score += 2

        return score

    def search(self, query: str, top_k: int = 5):
        scored = []

        for chunk in self.chunks:
            score = self.score_chunk(query, chunk)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]