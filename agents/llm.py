"""Provider-agnostic chat model factory.

The LLM provider is env-driven (free-tier friendly — user preference, see
CLAUDE.md "Resolved decisions"). Never import a provider SDK directly in
node code; always go through get_chat_model().

.env:
    LLM_PROVIDER=groq            # or: anthropic
    LLM_MODEL=llama-3.3-70b-versatile
    GROQ_API_KEY=...             # free at https://console.groq.com/keys
"""

import os

DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "anthropic": "claude-haiku-4-5",
}


def model_name() -> str:
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    return os.environ.get("LLM_MODEL") or DEFAULT_MODELS.get(provider, "")


def get_chat_model(temperature: float = 0.0):
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model_name(), temperature=temperature)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name(), temperature=temperature)
    raise ValueError(
        f"Unsupported LLM_PROVIDER={provider!r} — use 'groq' or 'anthropic', "
        f"or add the provider to agents/llm.py")
