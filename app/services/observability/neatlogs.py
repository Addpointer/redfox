# observability/neatlogs.py

from __future__ import annotations

import logging
import neatlogs

from typing import Any

from app.config import settings


logger = logging.getLogger(__name__)

_initialized = False

def init_neatlogs() -> None:
  """Initialize neatlogs for redfox

  Safe to call once during application startup.
  """

  global _initialized

  if _initialized:
    return
  
  if not settings.neatlogs_enabled:
    logger.info("NeatLogs integration is disabled.")
    return

  try:
    neatlogs.init(**settings.neatlogs_init_kwargs)
  except Exception:
    logger.exception("Failed to initialized neatlogs")
    raise

  _initialized = True
  logger.info(
    "neatlogs initialized",
    extra={
      "service_name": settings.neatlogs_workspace_name
    }
  )

def shutdown_neatlogs() -> None:
  """Flush and shutdown neatlogs during application shutdown"""
  global _initialized

  if not _initialized:
    return

  try:
    neatlogs.flush()
  finally:
    neatlogs.shutdown()
    _initialized = False


def wrap_client(client: Any, **metadata: Any) -> Any:
  """Wrap an LLM client with neatlogs when observability is enabled.
  
      neatlogs handles the actual LLM span creation. The metadata is attached
      to the workflow root so future redfox traces can be filtered by provider,
      route, or other application-specific dimensions.
  """

  if not settings.neatlogs_enabled:
    return client

  if not _initialized:
    raise RuntimeError(
      "neatlogs has not been initialized"
      "Call initialize_neatlogs() during application startup"
    )

  return neatlogs.wrap(client, **metadata)
