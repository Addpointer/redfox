# observability/logfire.py

from __future__ import annotations

import logging
import logfire

from typing import Any

from app.config import settings


logger = logging.getLogger(__name__)

_initialized = False

def init_logfire() -> None:
  """Initialize Logfire for redfox

  Safe to call once during application startup.
  """

  global _initialized

  if _initialized:
    return
  
  if not settings.logfire_enabled:
    logger.info("NeatLogs integration is disabled.")
    return

  try:
    logfire.configure(**settings.logfire_init_kwargs)
  except Exception:
    logger.exception("Failed to initialized logfire")
    raise

  _initialized = True
  logger.info(
    "Logfire initialized",
    extra={
      "service_name": settings.logfire_service_name
    }
  )

def shutdown_logfire() -> None:
  """Flush and shutdown logfire during application shutdown"""
  global _initialized

  if not _initialized:
    return

  try:
    logfire.force_flush()
  finally:
    logfire.shutdown()
    _initialized = False


# def wrap_client(client: Any, **metadata: Any) -> Any:
#   """Wrap an LLM client with logfire when observability is enabled.
  
#       Logfire handles the actual LLM span creation. The metadata is attached
#       to the workflow root so future redfox traces can be filtered by provider,
#       route, or other application-specific dimensions.
#   """

#   if not settings.logfire_enabled:
#     return client

#   if not _initialized:
#     raise RuntimeError(
#       "Logfire has not been initialized"
#       "Call initialize_logfire() during application startup"
#     )

#   return logfire.instrument_*(client, **metadata)
