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


INTENT_RULES = {
    "troubleshooting": [
        r"\bproblem\b",
        r"\bissue\b",
        r"\bnot working\b",
        r"\bdoes not function\b",
        r"\bwon't\b",
        r"\btroubleshoot(?:ing)?\b",
        r"\bfault\b",
        r"\berror\b",
        r"\bpossible causes\b",
        r"\blikely solutions\b",
        r"\bwhy is\b",
    ],
    "procedure": [
        r"\bhow do i\b",
        r"\bhow to\b",
        r"\binstall\b",
        r"\binstallation\b",
        r"\bsetup\b",
        r"\bset up\b",
        r"\bload\b",
        r"\breplace\b",
        r"\bconnect\b",
        r"\battach\b",
        r"\bsteps\b",
    ],
    "specification": [
        r"\bduty cycle\b",
        r"\bpower input\b",
        r"\bcurrent\b",
        r"\bvoltage\b",
        r"\bocv\b",
        r"\bwire speed\b",
        r"\bcapacity\b",
        r"\bcurrent range\b",
        r"\bspec\b",
        r"\bspecification\b",
        r"\bmaterials\b",
    ],
    "controls_lookup": [
        r"\bfront panel\b",
        r"\binterior controls\b",
        r"\bcontrol\b",
        r"\bbutton\b",
        r"\bknob\b",
        r"\bsocket\b",
        r"\bswitch\b",
        r"\bdisplay\b",
    ],
    "diagram": [
        r"\bdiagram\b",
        r"\bschematic\b",
        r"\bpolarity\b",
        r"\bwire it\b",
        r"\bconnect it\b",
        r"\bconnection\b",
        r"\bwiring\b",
        r"\bshow me\b",
    ],
    "selection_guidance": [
        r"\bwhich process\b",
        r"\bwhich welding\b",
        r"\bwhat process\b",
        r"\bwhich one should i use\b",
        r"\bselection\b",
        r"\bchart\b",
    ],
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
        intent_scores = {intent: 0 for intent in INTENT_RULES}

        for intent, patterns in INTENT_RULES.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    intent_scores[intent] += 1

        best_intent = max(intent_scores, key=intent_scores.get)

        if intent_scores[best_intent] == 0:
            return "general_qa"

        # Resolve ties by business priority.
        # Diagram beats procedure because many "connect/setup" questions
        # are better answered visually.
        priority = [
            "troubleshooting",
            "diagram",
            "specification",
            "procedure",
            "controls_lookup",
            "selection_guidance",
        ]

        highest_score = max(intent_scores.values())
        candidates = [intent for intent, score in intent_scores.items() if score == highest_score]

        for preferred_intent in priority:
            if preferred_intent in candidates:
                return preferred_intent

        return best_intent

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
    ]

    for query in test_queries:
        print("\n---")
        print(router.route(query))


if __name__ == "__main__":
    main()