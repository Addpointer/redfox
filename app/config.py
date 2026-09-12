"""Typed application configuration loaded from environment variables and `.env`.

Uses Pydantic Settings so every value is validated and typed at startup.
No credentials or secrets are hardcoded here — secrets must come from the
environment (or local `.env`, which ies gitignored). See `.env.example`.
"""


from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  """Application settings. Loaded once via :func:`get_settings`."""

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
    case_sensitive=False
  )

  app_name: str = Field(default="Redfox", description="Server application name")
  app_version: str = Field(default="0.2.0", description="Application version")
  app_env: Literal["development", "production", "staging", "test"] = Field(
    default="development", description="Deployment Environment"
  )
  debug: bool = Field(default=False, description="Enable debug mode")
  log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
    default="INFO", description="Root log level"
  ) 
  host: str = Field(default="0.0.0.0", description="Bind host")
  port: str = Field(default="8000", description="Bind port")


  cors_origins: list[str] = Field(
    default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
    description="Allowed cors origin. Comma seperated string or JSON in env."
  )
  cors_allow_credentials: bool = Field(default=True)
  cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
  cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"]) # Change it later to allow only specific headers


  llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
  llm_max_tokens: int = Field(default=1024, gt=0)

  ## llm_provider, llm_model, llm_base_url is not needed for now since we will preface multiple models

  ## Model providers are: Google, Bedrock, Tensormux
  
  
  google_gemini_api_key: SecretStr | None = Field(
    default=None,
    description="Google gemini api key"
  )
  google_project_id: str | None = Field(
    default=None,
    description="Google project in console"
  )
  google_cloud_location: Literal["global", "us-east1"] = Field(
    default="global",
    description="The location of inference for google models"
  )
  google_genai_use_enterprise: bool = Field(default=True)
  # Models under the google brand will be prefaced and hence not used as a secret

  tensormux_api_key: SecretStr | None = Field(default=None, description="Tensormux api key")
  tensormux_model: str = Field(default="zai-org/GLM-4.7-Flash") # only model served in tensormux so we will use it
  tensormux_base_url: str = Field(default="https://api.tensormux.com/v1")


  bedrock_api_key: SecretStr | None = Field(default=None, description="AWS Bedrock API KEY")
  bedrock_base_url: str = Field(
    default="https://bedrock-mantle.us-east-1.api.aws/v1",
    description="Bedrock base url for model inference"
  )
  bedrock_project_id: str = Field(
    default="default"
  ) # Bedrock works with the openai standard


  # Observability — Logfire
  logfire_enabled: bool = Field(
    default=True,
    description="Enable Logfire observability",
  )
  
  logfire_api_key: SecretStr | None = Field(
    default=None,
    description="Logfire write token",
  )
  
  logfire_service_name: str = Field(
    default="pointer-ai",
    description="Service name shown in Logfire",
  )
  
  logfire_environment: str = Field(
    default="local",
    description="Logfire environment name",
  )
  
  logfire_console: bool = Field(
    default=True,
    description="Enable Logfire console output",
  )
  
  logfire_send_to_logfire: bool = Field(
    default=True,
    description="Send traces to Logfire",
  )
  
  logfire_sample_rate: float = Field(
    default=1.0,
    ge=0.0,
    le=1.0,
    description="Trace sampling rate",
  )
  
  logfire_capture_logs: bool = Field(
    default=False,
    description="Capture Python logs as Logfire spans",
  )
  
  logfire_debug: bool = Field(
    default=False,
    description="Enable Logfire SDK debugging",
  )


  execution_provider: str | None = Field(
    default="e2b",
    description="Code/tool execution provider name"
  )
  execution_api_key: SecretStr | None = Field(
    default=None,
    description="API key for execution provider"
  )
  execution_base_url: str | None = Field(default=None)
  execution_timeout_seconds: int = Field(default=60, gt=0)


  database_url: str | None = Field(
    default=None,
    description="Full database URL, e.g. postgresql+asyncpg://user:pass@host:5432/db.",
  )
  database_host: str = Field(default="localhost")
  database_port: int = Field(default=5432)
  database_name: str | None = Field(default=None)
  database_user: str | None = Field(default=None)
  database_password: SecretStr | None = Field(default=None)
  database_echo: bool = Field(default=False, description="Echo SQL statements.")



  @field_validator("cors_origins", "cors_allow_methods", "cors_allow_headers", mode="before")
  @classmethod
  def _split_comma_separated(cls, value: object) -> object:
    """Accept comma separated strings and parse them as well as real lists from .env"""
    if isinstance(value, str):
      value = value.strip()
      if not value:
        return []
      if value.startswith("["):
        # We want to let pydantic parse the JSON-style lists like '["a", "b"]'.
        return value
      return [part.strip() for part in value.split(",") if part.strip()]
    return value

  @property
  def is_production(self) -> bool:
    return self.app_env == "production"

  @property
  def is_development(self) -> bool:
    return self.app_env == "development"


  @property
  def logfire_init_kwargs(self) -> dict:
    """Build kwargs for logfire.configure/init."""
  
    kwargs = {
      "service_name": self.logfire_service_name,
      "environment": self.logfire_environment,
      "console": self.logfire_console,
      "send_to_logfire": self.logfire_send_to_logfire,
      "min_level": "info",
    }
  
    if self.logfire_api_key is not None:
      kwargs["token"] = self.logfire_api_key.get_secret_value()
  
    return kwargs

  @property
  def neatlogs_init_kwargs(self) -> None:
    return


@lru_cache
def get_settings() -> Settings:
  """Return cached Settings instance"""

  return Settings()


settings = get_settings()


# Write the code for neatlogs observation