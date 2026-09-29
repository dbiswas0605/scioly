"""Errors raised by LLM parsing that routers translate into HTTP responses."""
from __future__ import annotations


class LlmNotConfiguredError(Exception):
    """No active LLM provider, or the active provider has no API key set."""


class LlmUnsupportedError(Exception):
    """The active provider or the uploaded file type isn't supported yet."""


class LlmRequestError(Exception):
    """The LLM provider was called but the request failed or returned
    something we couldn't use."""
