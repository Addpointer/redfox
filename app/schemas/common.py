"""Shared base model for all domain entities.

Pure Pydantic — no ORM / DB concerns here. Every entity gets a UUID
primary identity plus UTC-aware timestamps. Future DB mappers can reuse
``id`` / ``created_at`` / ``updated_at`` directly as columns.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from pydantic import AwareDatetime


def _utcnow():
  return datetime.now(timezone.utc)


class CommonBase(BaseModel):
  """Base class for all domain entities"""

  model_config = ConfigDict(extra="forbid", populate_by_name=True)
  id: UUID = Field(default_factory=uuid4, description="UUID4 Primary identity")
  created_at: AwareDatetime = Field(
    default_factory=_utcnow,
    description="Creation time (UTC)"
  )
  updated_at: AwareDatetime = Field(
    default_factory=_utcnow,
    description="Last-Updated time(UTC)"
  )