"""Bedrock provider (OpenAI-compatible API, default model ChatGPT-Astra).

Bedrock exposes an OpenAI-compatible ``/v1/chat/completions`` endpoint,
so this provider is a thin adapter over the ``openai`` SDK with all
connection details (base URL, key, model) supplied by the caller —
in production, resolved from environment variables by
``app.services.llm.factory``. Nothing is hardcoded except safe public
defaults (endpoint path, model id).
"""


"""
Add stream=True, to the openai client later in streams and astream for better streaming options
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Iterator

from app.services.observability.neatlogs import wrap_client

from app.services.llm.base import (
  ChatMessage,
  ChatRole,
  LLMConfigError,
  LLMError,
  LLMProvider,
  LLMProviderError,
  LLMResponse,
  LLMUsage,
  StreamChunk,
)


PROVIDER_NAME="bedrock"


class BedrockProvider(LLMProvider):
  """LLM Provider backed by Bedrock OpenAI compatible endpoint."""

  def __init__(
    self,
    *,
    api_key: str | None,
    base_url: str | None,
    project_id: str | None,
    model: str | None,
    temperature: float | None,
    max_tokens: int | None,
    timeout_seconds: float = 60.0,
  ) -> None:
    if not api_key:
      raise LLMConfigError(
        "Bedrock API Key is missing. Set BEDROCK_API_KEY "
        "in the environment"
      )

    self._api_key = api_key
    self._base_url = base_url
    self._model = model
    self._max_tokens = max_tokens
    self._temperature = temperature
    self._timeout_seconds = timeout_seconds
    self._project_id = project_id

  @property
  def name(self) -> str:
    return PROVIDER_NAME

  @property
  def getmodel(self) -> str | None:
    return self._model

  def _client(self):
    from openai import OpenAI

    client = OpenAI(
      api_key=self._api_key,
      base_url=self._base_url,
      timeout=self._timeout_seconds,
      project=self._project_id
    )

    return wrap_client(
      client,
      provider=PROVIDER_NAME,
      model=self._model
    )

  def _aclient(self):
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
      api_key=self._api_key,
      base_url=self._base_url,
      project=self._project_id,
      timeout=self._timeout_seconds
    )

    return wrap_client(
      client,
      provider=PROVIDER_NAME,
      model=self._model
    )

  def _payload(
    self,
    messages: list[ChatMessage],
    model: str | None,
    temperature: float | None,
    max_tokens: int | None
  ) -> dict:
    payload: dict = {
      "model": model or self._model,
      "messages": [
        {"role": m.role.value, "content": m.content}
        for m in messages
      ]
    }

    resolved_temp = (
      temperature if temperature is not None else self._temperature
    )
    resolved_max = (
      max_tokens if max_tokens is not None else self._max_tokens
    )
          
    if resolved_temp is not None:
      payload["temperature"] = resolved_temp
          
    if resolved_max is not None:
      payload["max_tokens"] = resolved_max
          
    return payload

  

  @staticmethod
  def _to_response(
    result: object, model: str, latency_ms: int
  ) -> LLMResponse:
    # Duck-typed mapping so we don't hard-depend on openai response types.
    choice = result.choices[0]  # type: ignore[attr-defined]
    content = (choice.message.content or "").strip()
    finish = getattr(choice, "finish_reason", None)
    usage = None
    raw_usage = getattr(result, "usage", None)
    if raw_usage is not None:
      prompt_tokens = getattr(raw_usage, "prompt_tokens", None)
      completion_tokens = getattr(raw_usage, "completion_tokens", None)
      total_tokens = getattr(raw_usage, "total_tokens", None)
      usage = LLMUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
      )
    print(
      "Bedrock raw response:",
      result,
    )
    return LLMResponse(
      content=content,
      model=getattr(result, "model", None) or model,  # type: ignore[attr-defined]
      provider=PROVIDER_NAME,
      finish_reason=finish,
      usage=usage,
    )

  def chat(
    self,
    messages: list[ChatMessage],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
  ) -> LLMResponse:
    if not messages:
      raise ValueError("messages must not be empty")
    resolved_model = model or self._model
    payload = self._payload(messages, model, temperature, max_tokens)
    started = time.perf_counter()
    try:
      result = self._client().chat.completions.create(**payload)
    except LLMError:
      raise
    except Exception as exc:
      raise LLMProviderError(
        f"Bedrock chat completion failed: {exc}",
        provider=PROVIDER_NAME,
        model=str(resolved_model),
      ) from exc
    latency_ms = int((time.perf_counter() - started) * 1000)
    return self._to_response(result, str(resolved_model), latency_ms)

  async def achat(
    self,
    messages: list[ChatMessage],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
  ) -> LLMResponse:
    if not messages:
      raise ValueError("messages must not be empty")
    resolved_model = model or self._model
    payload = self._payload(messages, model, temperature, max_tokens)
    started = time.perf_counter()
    try:
      result = await self._aclient().chat.completions.create(**payload)
    except LLMError:
      raise
    except Exception as exc:
      raise LLMProviderError(
        f"Bedrock chat completion failed: {exc}",
        provider=PROVIDER_NAME,
        model=str(resolved_model),
      ) from exc
    latency_ms = int((time.perf_counter() - started) * 1000)
    return self._to_response(result, str(resolved_model), latency_ms)

  def stream(
    self,
    messages: list[ChatMessage],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
  ) -> Iterator[StreamChunk]:
    if not messages:
      raise ValueError("messages must not be empty")
    resolved_model = model or self._model
    payload = self._payload(messages, model, temperature, max_tokens)
    payload["stream"] = True
    try:
      chunks = self._client().chat.completions.create(stream=True, **payload)
      for chunk in chunks:
        delta = (chunk.choices[0].delta.content or "") if chunk.choices else ""
        if delta:
          yield StreamChunk(
            delta=delta, provider=PROVIDER_NAME, model=str(resolved_model)
          )
    except LLMError:
      raise
    except Exception as exc:
      raise LLMProviderError(
        f"Bedrock stream failed: {exc}",
        provider=PROVIDER_NAME,
        model=str(resolved_model),
      ) from exc

  async def astream(
    self,
    messages: list[ChatMessage],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[StreamChunk]:
    if not messages:
      raise ValueError("messages must not be empty")
    resolved_model = model or self._model
    payload = self._payload(messages, model, temperature, max_tokens)
    payload["stream"] = True
    try:
      stream = await self._aclient().chat.completions.create(stream=True, **payload)
      async for chunk in stream:
        delta = (chunk.choices[0].delta.content or "") if chunk.choices else ""
        if delta:
          yield StreamChunk(
            delta=delta, provider=PROVIDER_NAME, model=str(resolved_model)
          )
    except LLMError:
      raise
    except Exception as exc:
      raise LLMProviderError(
        f"TensorMux stream failed: {exc}",
        provider=PROVIDER_NAME,
        model=str(resolved_model),
      ) from exc