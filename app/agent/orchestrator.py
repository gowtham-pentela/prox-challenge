import json
import os
from pathlib import Path
from typing import Dict, Any

from anthropic import Anthropic
from dotenv import load_dotenv

from app.agent.prompts import build_system_prompt, build_user_prompt
from app.agent.query_router import QueryRouter
from app.agent.response_planner import ResponsePlanner
from app.renderers import TextRenderer, TableRenderer, ImageRenderer, DiagramRenderer
from app.retrieval.hybrid_search import HybridSearch
from app.vision.figure_matcher import FigureMatcher
from app.vision.image_analysis import ImageAnalysis


class AgentOrchestrator:
    def __init__(self):
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]
        env_path = project_root / ".env"

        print("Project root:", project_root)
        print("Env path:", env_path)
        print("Env exists:", env_path.exists())

        load_dotenv(dotenv_path=env_path, override=True)

        key = os.getenv("ANTHROPIC_API_KEY")
        print("Loaded key exists:", key is not None)
        print("Loaded key suffix:", key[-4:] if key else None)
        print("Loaded key prefix:", key[:15] if key else None)

        self.router = QueryRouter()
        self.hybrid_search = HybridSearch()
        self.planner = ResponsePlanner()
        self.figure_matcher = FigureMatcher()
        self.image_analysis = ImageAnalysis()

        self.anthropic_api_key = key
        self.client = Anthropic(api_key=self.anthropic_api_key) if self.anthropic_api_key else None
        print("Client created:", self.client is not None)

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

        hybrid_results = self.hybrid_search.search(
            query=query,
            router_output=router_output,
            top_k=10,
        )
        
        raw_image_results = self.figure_matcher.match(query, top_k=3)
        image_results = self.image_analysis.summarize_images(raw_image_results)

        plan = self.planner.plan(
            router_output=router_output,
            hybrid_results=hybrid_results,
            image_results=image_results,
        )

        renderer = self.get_renderer_for_format(plan["format"])
        render_output = renderer.render(plan)

        return {
            "query": query,
            "router_output": router_output,
            "hybrid_results": hybrid_results,
            "image_results": image_results,
            "plan": plan,
            "render_output": render_output,
        }

    def generate_with_claude(
        self,
        pipeline_output: Dict[str, Any],
        model: str = "claude-3-7-sonnet-20250219",
    ) -> str:
        if not self.client:
            raise ValueError("ANTHROPIC_API_KEY is not set. Claude generation is unavailable.")

        query = pipeline_output["query"]
        router_output = pipeline_output["router_output"]
        plan = pipeline_output["plan"]
        render_output = pipeline_output["render_output"]
        retrieved_chunks = pipeline_output["hybrid_results"][:8]

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(
            query=query,
            router_output=router_output,
            plan=plan,
            render_output=render_output,
            retrieved_chunks=retrieved_chunks,
        )

        response = self.client.messages.create(
            model=model,
            max_tokens=1400,
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

        final_text = "\n".join(parts).strip()

        if not final_text:
            raise ValueError("Claude returned an empty response.")

        return final_text

    def answer(self, query: str, use_claude: bool = True) -> Dict[str, Any]:
        pipeline_output = self.run_pipeline(query)

        print("use_claude:", use_claude)
        print("client:", self.client)

        generation_mode = "fallback"

        try:
            if use_claude and self.client:
                final_answer = self.generate_with_claude(pipeline_output)
                generation_mode = "claude"
            else:
                final_answer = self.build_fallback_answer(pipeline_output)
                generation_mode = "fallback"
        except Exception as e:
            print(f"Claude generation failed: {e}")
            final_answer = self.build_fallback_answer(pipeline_output)
            generation_mode = "fallback_after_claude_error"

        return {
            "query": query,
            "final_answer": final_answer,
            "generation_mode": generation_mode,
            "router_output": pipeline_output["router_output"],
            "plan": pipeline_output["plan"],
            "render_output": pipeline_output["render_output"],
            "hybrid_results": pipeline_output["hybrid_results"],
            "image_results": pipeline_output["image_results"],
        }

    def build_fallback_answer(self, pipeline_output: Dict[str, Any]) -> str:
        plan = pipeline_output["plan"]
        render_output = pipeline_output["render_output"]
        image_results = pipeline_output.get("image_results", [])
        intent = plan.get("intent")
        fmt = plan.get("format")
        primary = plan.get("primary_chunk")

        if not primary:
            return "I could not find enough relevant manual context to answer this question."

        section = primary.get("section_title", "Unknown Section")
        page = primary.get("page_number", "N/A")

        visual_note = ""
        if image_results:
            visual_note = "\n\nRelevant visual references:\n" + "\n".join(
                [
                    f"- Page {img.get('page_number')} | {img.get('section_title')} | {img.get('path')}"
                    for img in image_results
                ]
            )

        if fmt == "step_by_step":
            return (
                f"Intent: {intent}\n"
                f"Primary source: {section} (Page {page})\n\n"
                f"{render_output['content']}"
                f"{visual_note}"
            )

        if fmt == "table":
            rows = render_output.get("content", [])
            lines = [f"Intent: {intent}", f"Primary source: {section} (Page {page})", ""]
            for row in rows:
                lines.append(
                    f"- {row['section_title']} | Page {row['page_number']} | "
                    f"{row['content_type']}: {row['text_preview']}"
                )
            return "\n".join(lines) + visual_note

        if fmt == "diagram":
            diagram_content = json.dumps(
                render_output.get("content", {}),
                indent=2,
                ensure_ascii=False,
            )
            return (
                f"Intent: {intent}\n"
                f"Primary source: {section} (Page {page})\n\n"
                f"{diagram_content}"
                f"{visual_note}"
            )

        if fmt == "image_plus_text":
            content = render_output.get("content", [])
            lines = [f"Intent: {intent}", f"Primary source: {section} (Page {page})", ""]
            for block in content:
                lines.append(
                    f"- {block['section_title']} | Page {block['page_number']}: "
                    f"{block['text_preview']}"
                )
            if image_results:
                lines.append("")
                lines.append("Relevant visual references:")
                for img in image_results:
                    lines.append(
                        f"- Page {img.get('page_number')} | {img.get('section_title')} | {img.get('path')}"
                    )
            return "\n".join(lines)

        return (
            f"Intent: {intent}\n"
            f"Primary source: {section} (Page {page})\n\n"
            f"{render_output.get('content', '')}"
            f"{visual_note}"
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
        print(
            {
                "intent": result["plan"]["intent"],
                "format": result["plan"]["format"],
                "answer_style": result["plan"]["answer_style"],
                "primary_chunk_id": (
                    result["plan"]["primary_chunk"]["chunk_id"]
                    if result["plan"]["primary_chunk"]
                    else None
                ),
                "generation_mode": result["generation_mode"],
                "num_image_results": len(result.get("image_results", [])),
            }
        )


if __name__ == "__main__":
    main()