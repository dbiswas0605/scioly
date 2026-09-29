"""LLM integration services: Anthropic Claude, OpenAI, and local models via
an OpenAI-compatible endpoint (Ollama, or MLX through a bridge like
`mlx_lm.server`).

`dispatcher.parse_paper_with_llm` is the entry point routers call — it
tries every enabled `llm_providers` row in priority order and falls back to
the next one on failure, so e.g. a local provider can be tried before
Anthropic without hand rolling a single "active" selection.
"""
