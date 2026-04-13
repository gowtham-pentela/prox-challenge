# Prox Challenge Analysis

## Goal
Build a multimodal reasoning agent for the Vulcan OmniPro 220 manual.

## Required capabilities
- Accept text and image input
- Ground answers in the manual
- Handle procedures, matrices, diagrams, troubleshooting
- Render diagrams/tables/images when useful
- Use Claude Agent SDK

## Product approach
This will be a technical support agent, not generic PDF chat.

## Core architecture
- Manual extraction pipeline
- Hybrid retrieval
- Query classification
- Response planner
- Multimodal renderer

## Document roles
- owner-manual.pdf is the authoritative technical source
- quick-start-guide.pdf is a fast visual setup guide
- selection-chart.pdf is a visual decision support chart

## Retrieval strategy implication
Answers should prefer owner-manual evidence first, then enrich with quick-start or chart visuals when helpful.