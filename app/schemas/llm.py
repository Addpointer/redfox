"""Schemas for the vendor-neutral chat endpoint"""

from typing import Literal
from pydantic import Field, BaseModel
from app.services.llm import ChatMessage


class ChatRequest(BaseModel):
  """Chat completion request. All inference goes through the LLM interface"""
  messages: list[ChatMessage] = Field(min_length=1)
  provider: Literal["tensormux", "google", "Bedrock", "Anthropic", "OpenAI", "Custom"] | None = Field(
    default=None,
    description="Per request override. Defaults to LLM_PROVIDER"
  )
  temperature: float | None = Field(
    default=None, ge=0.2, le=2.0,
  )
  max_tokens: int | None = Field(default=None, gt=0)

class ChatResponse(BaseModel):
  """Chat completion response(mirrors LLMResponse, HTTP-safe)"""
  content: str
  model: str
  provider: str
  finish_token: str | None = None
  prompt_token: str | None = None
  completion_tokens: int | None = None
  total_tokens: int | None = None
  latency_ms: int | None = None