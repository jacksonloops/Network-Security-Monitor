from datetime import datetime, timezone
from threading import Lock
import json
import atexit
import os
import sys
import shutil
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
                os.fsync(self._fh.fileno())
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
    
    def get_size(self) -> int:
        """Get current file size"""
        try:
            return os.path.getsize(self.filepath)
        except Exception:
            return 0

_logger: Optional[TelemetryLogger] = None
_logger_lock = Lock()

def get_file_path() -> str:
    date = datetime.now().strftime("%d-%m-%Y")
    seq = 1
    
    # Ensure directories exist
    os.makedirs('spool', exist_ok=True)
    os.makedirs('spool/ready', exist_ok=True)
    
    # Find next available sequence number - check BOTH directories
    while (os.path.exists(f'spool/{date}_{seq}.jsonl') or 
           os.path.exists(f'spool/ready/{date}_{seq}.jsonl')):
        seq += 1
    
    file_path = f'spool/{date}_{seq}.jsonl'
    
    # Create empty file
    with open(file_path, 'w') as f:
        f.write('')
    
    return file_path

def rotate_logger() -> None:
    """Move current log file to ready directory and create new logger"""
    global _logger
    
    if _logger is None:
        return
    
    old_filepath = _logger.filepath
    
    # Close the logger first
    _logger.close()
    
    # Move file to ready directory if it exists
    if os.path.exists(old_filepath):
        filename = os.path.basename(old_filepath)
        ready_path = f'spool/ready/{filename}'
        shutil.move(old_filepath, ready_path)
    
    # Reset logger AFTER moving the file
    _logger = None

def get_logger() -> TelemetryLogger:
    global _logger
    
    if _logger is None:
        with _logger_lock:
            # Double-check after acquiring lock
            if _logger is None:
                filepath = get_file_path()
                _logger = TelemetryLogger(filepath)
    
    return _logger

def log_event(event: dict) -> None:
    logger = get_logger()
    logger.log_event(event)
    
    # Check if we need to rotate after logging
    if logger.get_size() > 1_000_000:
        with _logger_lock:
            # Double-check the logger hasn't been rotated by another thread
            if _logger is not None and _logger.get_size() > 1_000_000:
                rotate_logger()

