from dataclasses import dataclass, field
from typing import Any, Dict
import uuid


@dataclass
class Event:
    event_type: str
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
