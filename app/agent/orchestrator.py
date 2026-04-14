import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from anthropic import Anthropic

from app.agent.prompts import build_system_prompt, build_user_prompt
from app.agent.query_router import QueryRouter
from app.agent.response_planner import ResponsePlanner

from app.vision.image_analysis import (
    analyze_user_images,
    build_retrieval_query,
    encode_image_for_claude,
)
from app.vision.figure_matcher import FigureMatcher

from app.retrieval.hybrid_search import HybridSearch

from app.renderers.table_renderer import TableRenderer
from app.renderers.diagram_renderer import DiagramRenderer
from app.renderers.image_renderer import ImageRenderer
from app.renderers.text_renderer import TextRenderer


class Orchestrator:
    def __init__(self):
        load_dotenv()

        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key) if api_key else None

        self.router = QueryRouter()
        self.hybrid_search = HybridSearch()
        self.figure_matcher = FigureMatcher()
        self.response_planner = ResponsePlanner()

        self.table_renderer = TableRenderer()
        self.diagram_renderer = DiagramRenderer()
        self.image_renderer = ImageRenderer()
        self.text_renderer = TextRenderer()

    def answer(
        self,
        query: str,
        image_paths: Optional[List[str]] = None,
        use_claude: bool = True,
    ) -> Dict[str, Any]:
        image_paths = image_paths or []

        visual_analysis = self._run_visual_analysis(query, image_paths)

        retrieval_query = build_retrieval_query(query, visual_analysis)

        router_output = self.router.route(
            query=query,
            visual_analysis=visual_analysis,
        )

        hybrid_results = self._run_hybrid_search(retrieval_query, top_k=8)

        manual_image_results = self._run_figure_matcher(
            query=query,
            visual_analysis=visual_analysis,
            router_output=router_output,
            top_k=3,
        )

        plan = self._run_response_planner(
            query=query,
            router_output=router_output,
            hybrid_results=hybrid_results,
            image_paths=image_paths,
            image_results=manual_image_results,
        )

        render_output = self._render(
            plan=plan,
            hybrid_results=hybrid_results,
            query=query,
            image_paths=image_paths,
        )

        pipeline_output = {
            "query": query,
            "router_output": router_output,
            "hybrid_results": hybrid_results,
            "manual_image_results": manual_image_results,
            "plan": plan,
            "render_output": render_output,
            "visual_analysis": visual_analysis,
            "image_paths": image_paths,
        }

        if use_claude and self.client:
            try:
                final_answer = self.generate_with_claude(
                    pipeline_output=pipeline_output,
                    model="claude-sonnet-4-6",
                    image_paths=image_paths,
                )
            except Exception as e:
                print("Claude failed, falling back to render output: {0}".format(e))
                final_answer = self._fallback_answer(render_output)
        else:
            final_answer = self._fallback_answer(render_output)

        pipeline_output["final_answer"] = final_answer
        return pipeline_output

    def generate_with_claude(
        self,
        pipeline_output: Dict[str, Any],
        model: str = "claude-sonnet-4-6",
        image_paths: Optional[List[str]] = None,
    ) -> str:
        if not self.client:
            raise ValueError("ANTHROPIC_API_KEY is not set. Claude generation is unavailable.")

        query = pipeline_output["query"]
        router_output = pipeline_output["router_output"]
        plan = pipeline_output["plan"]
        render_output = pipeline_output["render_output"]
        retrieved_chunks = pipeline_output["hybrid_results"][:8]
        visual_analysis = pipeline_output.get("visual_analysis", "")

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(
            query=query,
            router_output=router_output,
            plan=plan,
            render_output=render_output,
            retrieved_chunks=retrieved_chunks,
            visual_analysis=visual_analysis,
        )

        content = [{"type": "text", "text": user_prompt}]

        if image_paths:
            for image_path in image_paths:
                content.append(encode_image_for_claude(image_path))

        print("Using Claude model: {0}".format(model))

        response = self.client.messages.create(
            model=model,
            max_tokens=1400,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": content,
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

    def _run_visual_analysis(self, query: str, image_paths: List[str]) -> str:
        if not image_paths or not self.client:
            return ""

        try:
            return analyze_user_images(
                client=self.client,
                query=query,
                image_paths=image_paths,
                model="claude-haiku-4-5",
            )
        except Exception as e:
            print("Visual analysis failed: {0}".format(e))
            return ""

    def _run_hybrid_search(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        if hasattr(self.hybrid_search, "search"):
            return self.hybrid_search.search(query, top_k=top_k)

        if hasattr(self.hybrid_search, "retrieve"):
            return self.hybrid_search.retrieve(query, top_k=top_k)

        raise AttributeError("HybridSearch must expose search(...) or retrieve(...).")

    def _run_figure_matcher(
        self,
        query: str,
        visual_analysis: str,
        router_output: Dict[str, Any],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        desired_render = router_output.get("expected_output", "")
        intent = router_output.get("intent", "")

        if hasattr(self.figure_matcher, "match"):
            try:
                return self.figure_matcher.match(
                    query=query,
                    top_k=top_k,
                    visual_analysis=visual_analysis,
                    desired_render=desired_render,
                )
            except TypeError:
                try:
                    return self.figure_matcher.match(
                        query=query,
                        top_k=top_k,
                        visual_analysis=visual_analysis,
                    )
                except TypeError:
                    return self.figure_matcher.match(query, top_k=top_k)

        if intent in {"controls_lookup", "troubleshooting", "diagram", "procedure"}:
            return []

        return []

    def _run_response_planner(
        self,
        query: str,
        router_output: Dict[str, Any],
        hybrid_results: List[Dict[str, Any]],
        image_paths: List[str],
        image_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        image_results = image_results or []

        if hasattr(self.response_planner, "plan"):
            try:
                return self.response_planner.plan(
                    query=query,
                    router_output=router_output,
                    hybrid_results=hybrid_results,
                    image_paths=image_paths,
                    image_results=image_results,
                )
            except TypeError:
                try:
                    return self.response_planner.plan(
                        query,
                        router_output,
                        hybrid_results,
                        image_paths=image_paths,
                        image_results=image_results,
                    )
                except TypeError:
                    return self.response_planner.plan(query, router_output, hybrid_results)

        intent = router_output.get("intent", "general_lookup")
        primary_chunk_id = hybrid_results[0].get("chunk_id") if hybrid_results else None

        if intent == "specification":
            format_name = "table"
            answer_style = "concise_explanatory"
        elif intent == "procedure":
            if "polarity" in query.lower() or "wiring" in query.lower():
                format_name = "diagram"
                answer_style = "visual_instructional"
            else:
                format_name = "step_by_step"
                answer_style = "instructional"
        elif intent == "troubleshooting":
            format_name = "image_plus_text" if image_paths or image_results else "diagnostic"
            answer_style = "diagnostic"
        elif intent == "controls_lookup":
            format_name = "image_plus_text"
            answer_style = "component_explanatory"
        else:
            format_name = "text"
            answer_style = "general"

        return {
            "intent": intent,
            "format": format_name,
            "answer_style": answer_style,
            "primary_chunk_id": primary_chunk_id,
            "generation_mode": "claude" if self.client else "render_only",
            "num_image_results": len(image_paths) + len(image_results),
            "image_results": image_results,
        }

    def _render(
        self,
        plan: Dict[str, Any],
        hybrid_results: List[Dict[str, Any]],
        query: str = "",
        image_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        image_paths = image_paths or []
        format_name = plan.get("format", "text")

        if format_name == "table":
            return self._safe_render(
                self.table_renderer,
                plan,
                hybrid_results,
                query=query,
                image_paths=image_paths,
            )

        if format_name == "diagram":
            return self._safe_render(
                self.diagram_renderer,
                plan,
                hybrid_results,
                query=query,
                image_paths=image_paths,
            )

        if format_name == "image_plus_text":
            return self._safe_render(
                self.image_renderer,
                plan,
                hybrid_results,
                query=query,
                image_paths=image_paths,
            )

        return self._safe_render(
            self.text_renderer,
            plan,
            hybrid_results,
            query=query,
            image_paths=image_paths,
        )

    def _safe_render(
        self,
        renderer: Any,
        plan: Dict[str, Any],
        hybrid_results: List[Dict[str, Any]],
        query: str = "",
        image_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        image_paths = image_paths or []

        if hasattr(renderer, "render"):
            try:
                return renderer.render(
                    plan,
                    hybrid_results,
                    query=query,
                    image_paths=image_paths,
                )
            except TypeError:
                try:
                    return renderer.render(
                        plan,
                        hybrid_results,
                        query=query,
                    )
                except TypeError:
                    try:
                        return renderer.render(plan, hybrid_results)
                    except TypeError:
                        return renderer.render(plan)

        return {
            "format": plan.get("format", "text"),
            "content": self._basic_render_text(plan, hybrid_results),
        }

    def _basic_render_text(self, plan: Dict[str, Any], hybrid_results: List[Dict[str, Any]]) -> str:
        lines = []
        lines.append("Intent: {0}".format(plan.get("intent", "unknown")))
        lines.append("Format: {0}".format(plan.get("format", "text")))
        lines.append("")

        for idx, chunk in enumerate(hybrid_results[:5]):
            lines.append(
                "Source {0}: page {1} | {2}".format(
                    idx + 1,
                    chunk.get("page", chunk.get("page_number", "unknown")),
                    chunk.get("section_title", "unknown section"),
                )
            )
            lines.append(chunk.get("text", ""))
            lines.append("")

        return "\n".join(lines).strip()

    def _fallback_answer(self, render_output: Dict[str, Any]) -> str:
        if not isinstance(render_output, dict):
            return str(render_output)

        for key in ["final_text", "content", "text", "markdown", "ascii_diagram"]:
            if key in render_output and render_output[key]:
                return str(render_output[key])

        if render_output.get("render_type") == "diagram":
            diagram = render_output.get("diagram", {})
            if isinstance(diagram, dict) and diagram.get("ascii_diagram"):
                return diagram["ascii_diagram"]

        return str(render_output)


def main():
    orchestrator = Orchestrator()

    demo_queries = [
        {"query": "duty cycle MIG 240V", "image_paths": []},
        {"query": "polarity setup flux cored", "image_paths": []},
        {"query": "front panel controls", "image_paths": []},
        {"query": "wire spool installation", "image_paths": []},
        {"query": "welder does not function troubleshooting", "image_paths": []},
    ]

    for item in demo_queries:
        print("\n" + "=" * 100)
        print("QUERY: {0}".format(item["query"]))

        result = orchestrator.answer(
            query=item["query"],
            image_paths=item.get("image_paths", []),
            use_claude=True,
        )

        print("HYBRID INTENT: {0}".format(result["router_output"].get("intent")))
        print("use_claude: True")
        print("client: {0}".format(orchestrator.client))
        print("manual_image_results:", result.get("manual_image_results", []))
        print("\n[Final Answer]")
        print(result["final_answer"])
        print("\n[Plan Summary]")
        print(result["plan"])


if __name__ == "__main__":
    main()