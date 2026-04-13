import os
import json
from typing import Dict, Any

from dotenv import load_dotenv
from anthropic import Anthropic

from app.agent.query_router import QueryRouter
from app.agent.response_planner import ResponsePlanner
from app.agent.prompts import build_system_prompt, build_user_prompt
from app.retrieval.hybrid_search import HybridSearch
from app.renderers import TextRenderer, TableRenderer, ImageRenderer, DiagramRenderer


class AgentOrchestrator:
    def __init__(self):
        load_dotenv()

        self.router = QueryRouter()
        self.hybrid_search = HybridSearch()
        self.planner = ResponsePlanner()

        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.anthropic_api_key) if self.anthropic_api_key else None

    def get_renderer_for_format(self, format_name: str):
        if format_name == "table":
            return TableRenderer()
        if format_name == "diagram":
            return DiagramRenderer()
        if format_name == "image_plus_text":
            return ImageRenderer()
        if format_name == "step_by_step":
            return TextRenderer()
        return TextRenderer()

    def run_pipeline(self, query: str) -> Dict[str, Any]:
        router_output = self.router.route(query)
        hybrid_results = self.hybrid_search.search(query, top_k=5)
        plan = self.planner.plan(router_output, hybrid_results)

        renderer = self.get_renderer_for_format(plan["format"])
        render_output = renderer.render(plan)

        return {
            "query": query,
            "router_output": router_output,
            "hybrid_results": hybrid_results,
            "plan": plan,
            "render_output": render_output,
        }

    def generate_with_claude(self, pipeline_output: Dict[str, Any], model: str = "claude-sonnet-4-5") -> str:
        if not self.client:
            raise ValueError("ANTHROPIC_API_KEY is not set. Claude generation is unavailable.")

        query = pipeline_output["query"]
        router_output = pipeline_output["router_output"]
        plan = pipeline_output["plan"]
        render_output = pipeline_output["render_output"]

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(
            query=query,
            router_output=router_output,
            plan=plan,
            render_output=render_output,
        )

        response = self.client.messages.create(
            model=model,
            max_tokens=1200,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )

        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)

        return "\n".join(parts).strip()

    def answer(self, query: str, use_claude: bool = True) -> Dict[str, Any]:
        pipeline_output = self.run_pipeline(query)

        final_answer = None
        if use_claude and self.client:
            final_answer = self.generate_with_claude(pipeline_output)
        else:
            final_answer = self.build_fallback_answer(pipeline_output)
        print("use_claude:", use_claude)
        print("client:", self.client)
        return {
            "query": query,
            "final_answer": final_answer,
            "router_output": pipeline_output["router_output"],
            "plan": pipeline_output["plan"],
            "render_output": pipeline_output["render_output"],
        }

    def build_fallback_answer(self, pipeline_output: Dict[str, Any]) -> str:
        plan = pipeline_output["plan"]
        render_output = pipeline_output["render_output"]
        intent = plan.get("intent")
        fmt = plan.get("format")
        primary = plan.get("primary_chunk")

        if not primary:
            return "I could not find enough relevant manual context to answer this question."

        section = primary.get("section_title", "Unknown Section")
        page = primary.get("page_number", "N/A")

        if fmt == "step_by_step":
            return (
                f"Intent: {intent}\n"
                f"Primary source: {section} (Page {page})\n\n"
                f"{render_output['content']}"
            )

        if fmt == "table":
            rows = render_output.get("content", [])
            lines = [f"Intent: {intent}", f"Primary source: {section} (Page {page})", ""]
            for row in rows:
                lines.append(
                    f"- {row['section_title']} | Page {row['page_number']} | {row['content_type']}: {row['text_preview']}"
                )
            return "\n".join(lines)

        if fmt == "diagram":
            diagram_content = json.dumps(render_output.get("content", {}), indent=2, ensure_ascii=False)
            return (
                f"Intent: {intent}\n"
                f"Primary source: {section} (Page {page})\n\n"
                f"{diagram_content}"
            )

        if fmt == "image_plus_text":
            content = render_output.get("content", [])
            lines = [f"Intent: {intent}", f"Primary source: {section} (Page {page})", ""]
            for block in content:
                lines.append(
                    f"- {block['section_title']} | Page {block['page_number']}: {block['text_preview']}"
                )
            return "\n".join(lines)

        return (
            f"Intent: {intent}\n"
            f"Primary source: {section} (Page {page})\n\n"
            f"{render_output.get('content', '')}"
        )


def main():
    orchestrator = AgentOrchestrator()

    queries = [
        "duty cycle MIG 240V",
        "polarity setup flux cored",
        "front panel controls",
        "wire spool installation",
        "welder does not function troubleshooting",
    ]

    for query in queries:
        print("\n" + "=" * 100)
        print(f"QUERY: {query}")

        result = orchestrator.answer(query, use_claude=True)

        print("\n[Final Answer]")
        print(result["final_answer"])

        print("\n[Plan Summary]")
        print({
            "intent": result["plan"]["intent"],
            "format": result["plan"]["format"],
            "answer_style": result["plan"]["answer_style"],
            "primary_chunk_id": result["plan"]["primary_chunk"]["chunk_id"] if result["plan"]["primary_chunk"] else None,
        })


if __name__ == "__main__":
    main()