import re
from typing import Dict, List, Any


class AnswerSynthesizer:
    def __init__(self):
        pass

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""

        lines = [line.strip() for line in text.splitlines()]
        cleaned = []

        skip_patterns = [
            r"for technical questions",
            r"item 57812",
            r"safety",
            r"welding tips",
            r"maintenance",
            r"controls",
            r"wire$",
            r"tig / stick",
        ]

        for line in lines:
            if not line:
                continue
            lower = line.lower()
            if any(re.search(pattern, lower) for pattern in skip_patterns):
                continue
            cleaned.append(line)

        text = " ".join(cleaned)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _extract_sentences(self, text: str) -> List[str]:
        text = self._clean_text(text)
        if not text:
            return []
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]

    def synthesize(self, plan: Dict[str, Any], render_output: Dict[str, Any]) -> str:
        intent = plan.get("intent", "general_qa")

        if intent == "specification":
            return self._synthesize_specification(plan)
        if intent == "procedure":
            return self._synthesize_procedure(plan)
        if intent == "troubleshooting":
            return self._synthesize_troubleshooting(plan)
        if intent == "diagram":
            return self._synthesize_diagram(plan)
        if intent == "controls_lookup":
            return self._synthesize_controls(plan)
        if intent == "selection_guidance":
            return self._synthesize_selection(plan)

        return self._synthesize_general(plan)

    def _synthesize_specification(self, plan):
        chunks = plan.get("chunks_to_use", [])
        if not chunks:
            return "I could not find specification details."

        text = chunks[0].get("text", "")

        # Extract key values
        def extract(pattern):
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else None

        power_input = extract(r"MIG Power Input\s+(.*?)\s+Current Input")
        current_input = extract(r"Current Input at Output\s+(.*?)\s+Welding Current")
        current_range = extract(r"Welding Current Range\s+(.*?)\s+Rated Duty")
        duty_cycle = extract(r"Rated Duty Cycles\s+(.*?)\s+Maximum OCV")

        answer_lines = ["## Answer"]

        if power_input:
            answer_lines.append(f"- Power input: {power_input}")
        if current_input:
            answer_lines.append(f"- Current input: {current_input}")
        if current_range:
            answer_lines.append(f"- Welding current range: {current_range}")
        if duty_cycle:
            answer_lines.append(f"- Duty cycle: {duty_cycle}")

        answer_lines.append("")
        answer_lines.append("In MIG mode at 240V, the welder supports higher current output and lower duty cycle at peak load.")

        primary = chunks[0]
        answer_lines.append("")
        answer_lines.append(
            f"**Source:** {primary.get('section_title')} (Page {primary.get('page_number')})"
        )

        return "\n".join(answer_lines)

    def _extract_numbered_steps(self, text: str) -> List[str]:
        lines = text.splitlines()
        steps = []
        current = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = re.match(r"^(\d+)[.)]?\s+(.*)", line)
            if match:
                if current:
                    steps.append(current.strip())
                current = f"{match.group(1)}. {match.group(2)}"
            else:
                if current and len(line) < 120:
                    current += f" {line}"

        if current:
            steps.append(current.strip())

        return steps

    def _synthesize_procedure(self, plan: Dict[str, Any]) -> str:
        chunks = plan.get("chunks_to_use", [])
        if not chunks:
            return "I could not find enough procedural detail to answer this question."

        all_steps = []
        for chunk in chunks:
            steps = self._extract_numbered_steps(chunk.get("text", ""))
            all_steps.extend(steps)

        if not all_steps:
            text = self._clean_text(" ".join(chunk.get("text", "") for chunk in chunks))
            return f"## Answer\n{text[:900]}"

        answer_lines = ["## Steps"]
        for step in all_steps[:12]:
            answer_lines.append(step)

        primary = chunks[0]
        answer_lines.append("")
        answer_lines.append(f"**Primary source:** {primary.get('section_title')} (Page {primary.get('page_number')})")
        return "\n".join(answer_lines)

    def _synthesize_troubleshooting(self, plan: Dict[str, Any]) -> str:
        chunks = plan.get("chunks_to_use", [])
        if not chunks:
            return "I could not find enough troubleshooting information to answer this question."

        answer_lines = ["## Troubleshooting summary"]

        for chunk in chunks[:3]:
            text = self._clean_text(chunk.get("text", ""))
            answer_lines.append(f"- {text[:350]}")

        primary = chunks[0]
        answer_lines.append("")
        answer_lines.append(f"**Primary source:** {primary.get('section_title')} (Page {primary.get('page_number')})")
        return "\n".join(answer_lines)

    def _synthesize_diagram(self, plan: Dict[str, Any]) -> str:
        chunks = plan.get("chunks_to_use", [])
        if not chunks:
            return "I could not find enough diagram-related information to answer this question."

        primary = chunks[0]
        text = self._clean_text(primary.get("text", ""))

        answer_lines = [
            "## Diagram explanation",
            text[:700],
            "",
            f"**Primary source:** {primary.get('section_title')} (Page {primary.get('page_number')})",
        ]
        return "\n".join(answer_lines)

    def _synthesize_controls(self, plan: Dict[str, Any]) -> str:
        chunks = plan.get("chunks_to_use", [])
        if not chunks:
            return "I could not find enough controls information to answer this question."

        primary = chunks[0]
        text = self._clean_text(primary.get("text", ""))

        answer_lines = [
            "## Controls overview",
            text[:800],
            "",
            f"**Primary source:** {primary.get('section_title')} (Page {primary.get('page_number')})",
        ]
        return "\n".join(answer_lines)

    def _synthesize_selection(self, plan: Dict[str, Any]) -> str:
        chunks = plan.get("chunks_to_use", [])
        if not chunks:
            return "I could not find enough selection guidance to answer this question."

        answer_lines = ["## Recommendation"]
        for chunk in chunks[:2]:
            text = self._clean_text(chunk.get("text", ""))
            answer_lines.append(f"- {text[:350]}")

        primary = chunks[0]
        answer_lines.append("")
        answer_lines.append(f"**Primary source:** {primary.get('section_title')} (Page {primary.get('page_number')})")
        return "\n".join(answer_lines)

    def _synthesize_general(self, plan: Dict[str, Any]) -> str:
        chunks = plan.get("chunks_to_use", [])
        if not chunks:
            return "I could not find enough relevant information to answer this question."

        primary = chunks[0]
        text = self._clean_text(primary.get("text", ""))

        return (
            "## Answer\n"
            f"{text[:900]}\n\n"
            f"**Primary source:** {primary.get('section_title')} (Page {primary.get('page_number')})"
        )