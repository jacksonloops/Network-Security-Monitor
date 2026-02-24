#!/usr/bin/env python3
from models import PortScanResult
from telemetry import AlertEvent
from datetime import datetime, timezone

REMOTE_ADMIN_PORTS = {22, 3389, 5900}
REMOTE_DATABASE_PORTS = {3306, 5432, 6379}

""" Detection Engine that takes in stream of PortScanResults and checks for violations """
class DetectionEngine:
    def __init__(self, run_id: str, target: str, *, open_port_threshold: int = 10):
        self.run_id = run_id
        self.target = target
        self.open_port_threshold = open_port_threshold
        self.open_ports: set[int] = set() 

    """ Processes result to check for remote admin ports being at risk """

    def process_result(self, result: PortScanResult) -> list[AlertEvent]:
        alerts: list[AlertEvent] = []

        if result.is_open:
             self.open_ports.add(result.port)

        if result.is_open and result.port in REMOTE_ADMIN_PORTS:
            alerts.append(AlertEvent(
                run_id=self.run_id,
                rule_id = 'OPEN_REMOTE_ADMIN_PORT',
                severity='high',
                target=result.target,
                port=result.port,
                message=f"High-risk remote administration port {result.port} is open",
                evidence=f"Check for if {result.port} open was found {result.is_open}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            ))

        if result.is_open and result.port in REMOTE_DATABASE_PORTS:
            alerts.append(AlertEvent(
                run_id=self.run_id,
                rule_id = 'OPEN_REMOTE_DATABASE_PORT',
                severity='high',
                target=result.target,
                port=result.port,
                message=f"High-risk remote database port {result.port} is open",
                evidence=f"Check for if {result.port} open was found {result.is_open}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            ))

        return alerts

    """ Checks for excessive amount of open_ports and returns an alert if so """

    def finalize(self) -> list[AlertEvent]:
        alerts: list[AlertEvent] = []

        if len(self.open_ports) > self.open_port_threshold:
            alerts.append(AlertEvent(
                run_id=self.run_id,
                rule_id="EXCESSIVE_OPEN_PORTS",
                severity="medium",
                target=self.target,
                port=-1,  # or 0; see note below
                message=f"Excessive exposure: {len(self.open_ports)} open ports (threshold {self.open_port_threshold})",
                evidence=f"open_ports={sorted(self.open_ports)}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            ))

        return alerts
