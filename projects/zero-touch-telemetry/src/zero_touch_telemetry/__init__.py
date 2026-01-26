"""Zero-Touch Telemetry for Kubernetes."""
from .cli import main
from .discovery import discover_services
from .planner import ZeroTouchPlanner

__all__ = ["main", "discover_services", "ZeroTouchPlanner"]
