#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class PortScanResult:
        target: str
        host: Optional[str]
        port: int
        is_open: bool
        latency_ms: Optional[float]
        error: Optional[str] = None