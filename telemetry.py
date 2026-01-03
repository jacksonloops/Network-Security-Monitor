from datetime import datetime, timezone
from threading import Lock
import json
import atexit
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Literal

@dataclass(frozen=True)
class AlertEvent:
        run_id: str
        rule_id: str
        severity: Literal["low", "medium", "high"]
        target: str
        port: int
        message: str
        evidence: str
        timestamp: str 
        event_type: str = field(default="alert", init=False)

def make_event(event_name: str, **extra) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event_name,
        **extra
    }

class TelemetryLogger:
    def __init__(self, filepath: str = "telemetry.jsonl"):
        self.filepath = filepath
        self._fh = open(self.filepath, "a", encoding="utf-8")
        self._lock = Lock()
        self._disabled = False
        atexit.register(self.close)

    def log_event(self, event: dict) -> None:
        if self._disabled:
            return
        line = json.dumps(event) + "\n"
        with self._lock:
            if self._disabled:
                return
            try:
                self._fh.write(line)
                self._fh.flush()
                os.fsync(self._fh.fileno())  # remove if your assignment doesn't require fsync
            except Exception as e:
                self._disabled = True
                try:
                    print(f"[telemetry disabled] {e}", file=sys.stderr)
                except Exception:
                    pass

    def close(self) -> None:
        with self._lock:
            try:
                if not self._fh.closed:
                    self._fh.close()
            except Exception:
                pass

_logger: Optional[TelemetryLogger] = None

def get_logger(filepath: str = "telemetry.jsonl") -> TelemetryLogger:
    global _logger
    if _logger is None:
        _logger = TelemetryLogger(filepath)
    return _logger

def log_event(event: dict) -> None:
    get_logger().log_event(event)

