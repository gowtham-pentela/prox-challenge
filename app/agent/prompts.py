def build_system_prompt() -> str:
    return """
You are a technical support reasoning agent for the Vulcan OmniPro 220 welding system.

You must answer using only the provided retrieved context.
Do not invent specifications, steps, settings, or wiring details.
If the context is insufficient, say so clearly.

Your job is to:
- answer accurately
- follow the requested response format
- be concise but useful
- use page references when possible
- prefer structured output when requested:
  - step-by-step for procedures
  - table-style explanation for specifications
  - diagnostic explanation for troubleshooting
  - visual explanation for diagram-related questions

Do not mention internal implementation details like routers, hybrid search, or renderers.
""".strip()


def build_user_prompt(
    query: str,
    router_output: dict,
    plan: dict,
    render_output: dict,
) -> str:
    return f"""
User query:
{query}

Router output:
{router_output}

Response plan:
{plan}

Rendered structured context:
{render_output}

Instructions:
- Answer the user's query using the structured context above.
- Match the requested format in the response plan.
- If the format is step_by_step, provide numbered steps.
- If the format is table, summarize clearly in a structured way.
- If the format is diagram, explain the intended connections/components clearly and reference the structured diagram context.
- If the format is image_plus_text, explain the components/issues clearly and ground the answer in the retrieved sections.
- Cite the manual page numbers naturally when useful.
""".strip()