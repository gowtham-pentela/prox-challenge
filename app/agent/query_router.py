import re
from typing import Dict, List


PROCESS_PATTERNS = {
    "mig": [r"\bmig\b"],
    "flux_cored": [r"\bflux[- ]?cored\b", r"\bflux\b", r"\bgasless\b"],
    "tig": [r"\btig\b"],
    "stick": [r"\bstick\b"],
}

VOLTAGE_PATTERNS = {
    "120v": [r"\b120\s?v\b", r"\b120vac\b", r"\b120 vac\b"],
    "240v": [r"\b240\s?v\b", r"\b240vac\b", r"\b240 vac\b"],
}


class QueryRouter:
    def __init__(self):
        pass

    def normalize(self, query: str) -> str:
        query = query.lower().strip()
        query = re.sub(r"\s+", " ", query)
        return query

    def detect_process_tags(self, query: str) -> List[str]:
        tags = []
        for tag, patterns in PROCESS_PATTERNS.items():
            if any(re.search(pattern, query) for pattern in patterns):
                tags.append(tag)
        return tags

    def detect_voltage_tags(self, query: str) -> List[str]:
        tags = []
        for tag, patterns in VOLTAGE_PATTERNS.items():
            if any(re.search(pattern, query) for pattern in patterns):
                tags.append(tag)
        return tags

    def detect_intent(self, query: str) -> str:
        q = query.lower()

        # Highest priority: specification-style questions
        if any(term in q for term in [
            "duty cycle",
            "power input",
            "current range",
            "current",
            "voltage",
            "rating",
            "amp",
            "amps",
            "amperage",
            "ocv",
            "capacity",
            "wire speed",
            "spec",
            "specification",
            "materials",
        ]):
            return "specification"

        # Troubleshooting
        if any(term in q for term in [
            "not working",
            "does not function",
            "does not work",
            "won't",
            "problem",
            "issue",
            "troubleshoot",
            "troubleshooting",
            "fault",
            "error",
            "possible causes",
            "likely solutions",
            "why is",
            "failure",
        ]):
            return "troubleshooting"

        # Procedure / setup
        if any(term in q for term in [
            "how do i",
            "how to",
            "install",
            "installation",
            "setup",
            "set up",
            "load",
            "replace",
            "attach",
            "steps",
            "procedure",
            "configure",
            "wire spool",
            "feed roller",
        ]):
            return "procedure"

        # Diagram / polarity / connection
        if any(term in q for term in [
            "diagram",
            "schematic",
            "polarity",
            "wiring",
            "connection",
            "connector",
            "positive",
            "negative",
            "layout",
        ]):
            return "diagram"

        # Controls lookup
        if any(term in q for term in [
            "front panel",
            "interior controls",
            "control",
            "button",
            "knob",
            "socket",
            "switch",
            "display",
        ]):
            return "controls_lookup"

        # Selection guidance
        if any(term in q for term in [
            "which process",
            "which welding",
            "what process",
            "which one should i use",
            "what should i use",
            "best process",
            "best welding",
            "use for",
            "selection",
            "chart",
        ]):
            return "selection_guidance"

        return "general_qa"

    def infer_output_mode(self, intent: str) -> str:
        if intent == "specification":
            return "table"
        if intent == "procedure":
            return "step_by_step"
        if intent == "troubleshooting":
            return "image_plus_text"
        if intent == "diagram":
            return "diagram"
        if intent == "controls_lookup":
            return "image_plus_text"
        if intent == "selection_guidance":
            return "table"
        return "text"

    def infer_visual_needs(self, intent: str) -> Dict[str, bool]:
        return {
            "needs_table": intent in {"specification", "selection_guidance"},
            "needs_diagram": intent == "diagram",
            "needs_image": intent in {"controls_lookup", "troubleshooting"},
        }

    def route(self, query: str) -> Dict:
        normalized_query = self.normalize(query)

        process_tags = self.detect_process_tags(normalized_query)
        voltage_tags = self.detect_voltage_tags(normalized_query)
        intent = self.detect_intent(normalized_query)
        expected_output = self.infer_output_mode(intent)
        visual_flags = self.infer_visual_needs(intent)

        return {
            "query": query,
            "normalized_query": normalized_query,
            "intent": intent,
            "expected_output": expected_output,
            "process_tags": process_tags,
            "voltage_tags": voltage_tags,
            **visual_flags,
        }


def main():
    router = QueryRouter()

    test_queries = [
        "duty cycle MIG 240V",
        "polarity setup flux cored",
        "front panel controls",
        "wire spool installation",
        "welder does not function troubleshooting",
        "which process should I use for stainless steel",
        "best welding for stainless steel",
        "what should I use for stainless steel",
        "positive and negative polarity for flux cored",
    ]

    for query in test_queries:
        print("\n---")
        print(router.route(query))


if __name__ == "__main__":
    main()