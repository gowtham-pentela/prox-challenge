<!--# Prox Founding Engineer Challenge

<img src="product.webp" alt="Vulcan OmniPro 220" width="400" /> <img src="product-inside.webp" alt="Vulcan OmniPro 220 — inside panel" width="400" />

## The Product

The [Vulcan OmniPro 220](https://www.harborfreight.com/omnipro-220-industrial-multiprocess-welder-with-120240v-input-57812.html) is a multiprocess welding system sold by Harbor Freight. It supports four welding processes (MIG, Flux-Cored, TIG, and Stick), runs on both 120V and 240V input, and has an LCD-based synergic control system.

Its owner's manual is 48 pages of dense technical content. Duty cycle matrices across multiple voltages and amperages, polarity setup procedures that differ per welding process, wire feed mechanisms with specific tensioner calibrations, wiring schematics, troubleshooting matrices, weld diagnosis diagrams, and a full parts list.

This is exactly the kind of product Prox exists for. Nobody knows how to use this machine straight out of the box but has time to read 48 page manual, but a complicated machine needs expert-level support.

Additional video: https://www.youtube.com/watch?v=kxGDoGcnhBw

## Your Job

Build a multimodal reasoning agent for the Vulcan OmniPro 220 using the Claude Agent SDK. The agent must be able to answer deep technical questions about this product accurately, helpfully, and not just in text.

The manuals are in the `files/` directory.

**There is no limit to how far you can go.** You can integrate voice. You can build a full interactive experience. Sky is the limit. The more ambitious and polished, the better.

## What We're Testing

### 1. Deep Technical Accuracy

Your agent needs to answer questions like these correctly:

- "What's the duty cycle for MIG welding at 200A on 240V?"
- "I'm getting porosity in my flux-cored welds. What should I check?"
- "What polarity setup do I need for TIG welding? Which socket does the ground clamp go in?"

We will test with questions that require cross-referencing multiple manual sections, understanding visual content (diagrams, schematics, charts), and handling ambiguous questions that need clarification from the user.

### 2. Multimodal Responses

This is the most important part. Your agent must not be text-only.

- If someone asks about polarity setup, the agent should draw or show a diagram of which cable goes in which socket, not just describe it.
- If the answer relates to a specific image in the manual (the wire feed mechanism, the front panel controls, the weld diagnosis examples), the agent should surface that image.
- If a question is complex enough, the agent should generate interactive content: a duty cycle calculator, a troubleshooting flowchart, a settings configurator that takes process + material + thickness and outputs recommended wire speed and voltage.

When something is too cognitively hard to explain in words, the agent should draw it. Real-time diagrams, interactive schematics, visual walkthroughs generated through code.

For your agent to handle these responses well you need to reverse engineer Claude artifacts. Here are two places where you can start:
- https://claude.ai/artifacts (see how Claude renders interactive artifacts in chat)
- https://www.reidbarber.com/blog/reverse-engineering-claude-artifacts

### 3. Tone and Helpfulness

Imagine your user just bought this welder and is standing in their garage trying to set it up. They're not an idiot, but they're not a professional welder either.

### 4. Knowledge Extraction Quality

The manual has a mix of text, tables, labeled diagrams, schematics, and decision matrices. Some critical information exists only in images (the welding process selection chart, the weld diagnosis photos, the wiring schematic). We want to see that your agent understands and presents the visual content, not just the text.

## Tech Requirements

- Use the [Anthropic Claude Agent SDK](https://docs.anthropic.com) as the foundation for your agent.
- The project must run locally with a single API key provided via `.env`.
- You are responsible for your own API costs during development.

## How to Present Your Work

**This matters.** Your submission is not just the code — it's how you present it.

- **Build a frontend.** The best way for us to evaluate your agent is if it has a clean, simple UI we can run immediately. This is realistically the only way to properly demo an agent like this.
- **Hosting is a plus.** If you host it somewhere we can access without cloning, that's a strong signal. Not required, but it removes friction and shows initiative.
- **Write a clear README.** Explain how your agent works, what design decisions you made, how knowledge is extracted and represented, and how to run it. Your documentation will be evaluated — we want to see how you think and communicate, not just how you code.
- **Video walkthrough is a huge plus.** Record yourself demoing the agent and explaining your approach. Walk through the hard questions, show how it handles multimodal responses, explain your architecture. This gives us a much richer picture of your work than code alone.

We should be running your agent within 2 minutes of cloning your repo:

```bash
git clone <your-fork>
cd <your-fork>
cp .env.example .env   # we plug in our own Anthropic API key
# your install command (npm install, uv install, etc.)
# your run command (npm run dev, python app.py, etc.)
```

If it takes longer than that to set up, that's a problem.

## What to Submit

1. Fork this repo.
2. Build your solution.
3. Submit your fork URL through the form at [useprox.com/join/challenge](https://useprox.com/join/challenge).

## What Happens Next

We review submissions on a rolling basis and respond to every single one within a few days. Good luck.
-->
# Vulcan OmniPro 220 Multimodal Agent

A **multimodal, intent-aware Retrieval-Augmented Generation (RAG) system** that answers technical questions about welding equipment using structured reasoning, hybrid search, and visual grounding.

---

## Overview

This project builds an intelligent assistant that can:

* Understand user intent (specifications, troubleshooting, setup, etc.)
* Retrieve relevant sections from technical manuals
* Combine keyword + vector search for accurate retrieval
* Ground answers using both **text and images**
* Generate structured responses (tables, steps, diagrams)
* Optionally use an LLM (Claude) for final answer synthesis

---

## System Architecture

The system follows a modular agent pipeline:

```text
User Query
   ↓
Query Router (intent + tags)
   ↓
Hybrid Search (keyword + vector + boosting)
   ↓
Response Planner (structure + chunk selection)
   ↓
Renderers (format-specific output)
   ↓
(Optional) LLM Generation (Claude)
   ↓
Final Answer + Visual References
```

---

## Key Components

### 1. Query Router

* Classifies query intent:

  * specification
  * procedure
  * troubleshooting
  * diagram
  * controls lookup
  * selection guidance
* Extracts:

  * process tags (MIG, TIG, Flux-cored)
  * voltage tags (120V, 240V)
* Determines:

  * expected output format (table, steps, etc.)

---

### 2. Hybrid Search

Combines:

* **Keyword search** (BM25-style relevance)
* **Vector search** (semantic similarity via FAISS)

Enhancements:

* Intent-aware boosting
* Tag-based boosting (process + voltage)

Example:

```
"duty cycle MIG 240V"
→ boosts:
  - specification chunks
  - MIG-related chunks
  - 240V-related chunks
```

---

### 3. Response Planner

* Selects:

  * primary chunk
  * supporting chunks
* Determines:

  * answer style (instructional, diagnostic, etc.)
  * output format
* Integrates:

  * visual references (images)

---

### 4. Vision Module

* Matches extracted images to queries
* Uses:

  * captions
  * nearby text
  * OCR context
* Returns:

  * relevant diagrams
  * UI panels
  * troubleshooting visuals

---

### 5. Renderers

Format-specific output generation:

| Intent          | Renderer             |
| --------------- | -------------------- |
| Specification   | Table                |
| Procedure       | Step-by-step         |
| Troubleshooting | Image + text         |
| Diagram         | Structured diagram   |
| Controls        | Visual + explanation |

---

### 6. Orchestrator

Central controller that:

* connects all modules
* manages pipeline execution
* optionally calls Claude API
* provides fallback responses

---

## Presentation Layer

Built using **Streamlit**

Features:

* Query input + sample queries
* Claude toggle
* Answer-first UI
* Evidence display
* Visual references
* Debug panels

---

## Project Structure

```text
prox-challenge/
│
├── app/
│   ├── agent/
│   │   ├── orchestrator.py        # main pipeline controller
│   │   ├── query_router.py        # intent classification
│   │   ├── response_planner.py    # chunk selection + structure
│   │   ├── prompts.py             # LLM prompts
│   │
│   ├── ingestion/
│   │   ├── parse_manual.py        # PDF parsing
│   │   ├── chunk_manual.py        # chunking logic
│   │   ├── extract_images.py      # image extraction
│   │   ├── extract_tables.py      # table extraction
│   │   ├── build_inventory.py     # metadata creation
│   │
│   ├── retrieval/
│   │   ├── keyword_search.py      # keyword-based search
│   │   ├── vector_store.py        # FAISS embeddings
│   │   ├── hybrid_search.py       # combined ranking logic
│   │   ├── metadata_filters.py
│   │
│   ├── vision/
│   │   ├── figure_matcher.py      # image retrieval
│   │   ├── image_analysis.py      # caption + enrichment
│   │
│   ├── renderers/
│   │   ├── text_renderer.py
│   │   ├── table_renderer.py
│   │   ├── image_renderer.py
│   │   ├── diagram_renderer.py
│   │
│   ├── main.py                   # Streamlit UI
│   ├── config.py
│   ├── schemas.py
│
├── data/
│   ├── indexes/
│   │   ├── chunks.faiss
│   │   ├── chunks_metadata.json
│   │
│   ├── processed/
│   │   ├── chunks/
│   │   ├── images/
│   │   ├── images_manifest.json
│   │   ├── pages/
│   │   ├── tables/
│
├── files/
│   ├── owner-manual.pdf
│   ├── quick-start-guide.pdf
│   ├── selection-chart.pdf
│
├── tests/
│   ├── smoke_test.py
│   ├── eval_questions.json
│
├── requirements.txt
├── README.md
└── .env
```

---

## Setup Instructions

### 1. Clone repo

```bash
git clone <repo-url>
cd prox-challenge
```

---

### 2. Create virtual environment

```bash
python3 -m venv proxy
source proxy/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Add Claude API key

Create `.env`:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

---

### 5. Run Streamlit app

```bash
streamlit run app/main.py
```

---

## 🧪 Testing

Run smoke tests:

```bash
python -m tests.smoke_test
```

---

## Example Queries

* `duty cycle MIG 240V`
* `polarity setup flux cored`
* `front panel controls`
* `wire spool installation`
* `welder does not function troubleshooting`
* `which process should I use for stainless steel`

---

## Design Decisions

### Why Hybrid Search?

* Keyword ensures precision
* Vector ensures semantic matching
* Combined with boosting → robust ranking

---

### Why Intent-Aware Routing?

Without intent:

* wrong chunk types dominate
* output format becomes inconsistent

With intent:

* stable behavior
* predictable outputs

---

### Why Structured Planning?

Separates:

* **what to retrieve**
* **how to answer**

This makes the system:

* explainable
* debuggable
* extensible

---

### Why Vision Integration?

Technical manuals rely heavily on:

* diagrams
* control panels
* wiring visuals

Text-only RAG is insufficient.

---
## Result
What the Agent Produces

Our agent dynamically:
- extracts structured tables from manuals
- generates step-by-step procedures
- synthesizes troubleshooting diagnostics

Below are real outputs:
<img src="result1.png" alt="Vulcan OmniPro 220"/>
<img src="result2.png" alt="Vulcan OmniPro 220"/>
<img src="result3.png" alt="Vulcan OmniPro 220"/>
<img src="result4.png" alt="Vulcan OmniPro 220"/>
<img src="result5.png" alt="Vulcan OmniPro 220"/>
<img src="result6.png" alt="Vulcan OmniPro 220"/>
<img src="result7.png" alt="Vulcan OmniPro 220"/>
<img src="result8.png" alt="Vulcan OmniPro 220"/>
<img src="result9.png" alt="Vulcan OmniPro 220"/>

---

## Future Improvements

* Better table rendering (true dataframe display)
* More advanced image understanding (multimodal embeddings)
* Feedback loop for ranking improvement
* Streaming responses with Claude
* Deployment (Docker + cloud)

---

## Summary

This project demonstrates:

* End-to-end RAG system design
* Hybrid retrieval with ranking optimization
* Intent-aware reasoning
* Multimodal integration (text + images)
* Clean separation of concerns (router, planner, renderer)

---
