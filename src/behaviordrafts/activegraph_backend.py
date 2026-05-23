from __future__ import annotations

from dataclasses import dataclass
import importlib.util


@dataclass(frozen=True)
class ActiveGraphProbe:
    available: bool
    module: str
    reason: str


def probe_activegraph() -> ActiveGraphProbe:
    spec = importlib.util.find_spec("activegraph")
    if spec is None:
        return ActiveGraphProbe(False, "activegraph", "activegraph package is not installed or importable")
    return ActiveGraphProbe(True, "activegraph", "activegraph package import succeeded")


def require_activegraph() -> None:
    probe = probe_activegraph()
    if not probe.available:
        raise RuntimeError(
            "ActiveGraph integration is required for this run, but activegraph is unavailable: "
            f"{probe.reason}."
        )
