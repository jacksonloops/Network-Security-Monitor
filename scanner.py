#!/usr/bin/env python3
import socket
import time
from dataclasses import asdict
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from telemetry import make_event, log_event
from detection import DetectionEngine
import uuid
from models import PortScanResult

def resolve_target(target: str) -> Tuple[Optional[str], str]:
        target = target.strip()
        if not target:
                raise ValueError("Empty target.")
        # Inital check for 0.0.0.0 invalid ip
        if target == "0.0.0.0":
                raise ValueError("Invalid host IP.")
        try:
                _ = socket.inet_aton(target)
                return None, target
        except OSError:
                try:
                        ip = socket.gethostbyname(target)
                        hostname_or_none = target
                        return hostname_or_none, ip
                except socket.gaierror as e:
                        raise ValueError("DNS lookup failed.")
# saved for later if user wants to define specific ports to scan
def parse_ports(spec: str) -> list[int]:
        
        # Normalize ports str
        spec = spec.strip()
        ports = set()
        # Check for empty ports
        if spec == "":
                raise ValueError("Empty port value.")
        
        tokens = spec.split(',')
        for token in tokens:
                # Check for invalid syntax
                if token == "":
                        raise ValueError("Invalid input.")
                t = token.strip()
                # Port range handler
                if '-' in t:
                        # Make sure only one -
                        if t.count('-') != 1:
                                raise ValueError("Invalid input.")
                        # Validate port range and port values
                        left, right = t.split('-')
                        if not left.isdigit() or not right.isdigit():
                                raise ValueError("Non integer found.")
                        left = int(left)
                        right = int(right)
                        if left > right:
                                raise ValueError("Invalid port range.")
                        if (left < 1 or left > 65535) or (right < 1 or right > 65535):
                                raise ValueError("Invalid port value.")
                        # Append ports if all checks pass
                        ports.update(range(left, right+1))

                # if single port found
                else:
                        if not t.isdigit():
                                raise ValueError("Non integer found.")
                        port = int(t)
                        if port < 1 or port > 65535:
                                raise ValueError("Invalid port value.")
                        ports.add(port)
                        
        return sorted(ports)

def scan_port(ip: str, port: int, target: Optional[str], host: Optional[str], timeout: float = 0.2) -> PortScanResult:
    try:
        start = time.perf_counter()
        
        # Create socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            end = time.perf_counter()
            
            latency = round((end - start) * 1000, 2)  # Convert to ms
            
            # Port is open
            if result == 0:

                return PortScanResult(
                    port=port, 
                    is_open=True, 
                    error=None, 
                    target=target, 
                    host=host, 
                    latency_ms=latency
                )
            
            # Port is closed
            else:
                
                return PortScanResult(
                    port=port, 
                    is_open=False, 
                    error="closed",
                    target=target,
                    host=host,
                    latency_ms=latency
                )
    
    # Connection timed out
    except socket.timeout:
        end = time.perf_counter()
        latency = round((end - start) * 1000, 2)
        
        return PortScanResult(
            port=port, 
            is_open=False, 
            error="timeout",
            target=target,
            host=host,
            latency_ms=latency
        )
    
    # Error occurred
    except OSError as e:
        end = time.perf_counter()
        latency = round((end - start) * 1000, 2)
        
        return PortScanResult(
            port=port, 
            is_open=False, 
            error=str(e),
            target=target,
            host=host,
            latency_ms=latency
        )

# Telemetry wrapper for multi-port scans
def tel_scan_port(ip: str, port: int, run_id: str, target: str, host: Optional[str], timeout: float = 0.2)-> PortScanResult:
    """Wrapper that scans a port and logs the port_scanned event"""

    result = scan_port(ip, port, target, host, timeout=timeout)
    # Log the port_scanned event
    log_event(make_event('port_scanned', 
                        run_id=run_id, 
                        ip=ip, 
                        input=result.target, 
                        host=result.host,
                        port=result.port,
                        is_open=result.is_open, 
                        latency_ms=result.latency_ms, 
                        error=result.error))

    return result

# Multi port scanner with Threads for concurrent scanning
def scan_ports(
    target: str,
    ports: list[int],
    timeout: float = 0.2,
    max_workers: int = 100
) -> list[PortScanResult]:
    """Scan multiple ports with threading and telemetry logging."""

    results: list[PortScanResult] = []
    input_target = target
    host, ip = resolve_target(target)

    run_id = str(uuid.uuid4())
    start = time.perf_counter()

    log_event(
        make_event(
            "scan_started",
            run_id=run_id,
            ip=ip,
            input=input_target,
            host=host,
            ports_total=len(ports),
        )
    )

    engine = DetectionEngine(run_id=run_id, target=input_target)
    interrupted = False
    executor = ThreadPoolExecutor(max_workers=max_workers)

    try:
        futures = [
            executor.submit(
                tel_scan_port,
                ip,
                port,
                run_id,
                input_target,
                host,
                timeout,
            )
            for port in ports
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            alerts = engine.process_result(result)
            if alerts:
                for alert in alerts:
                    log_event(asdict(alert))
                    print(f"[!] ALERT: {alert.alert_type}")

    except KeyboardInterrupt:
        interrupted = True
        print("\n[+] Interrupt received. Stopping scan...")
        executor.shutdown(wait=False, cancel_futures=True)
        raise

    finally:
        executor.shutdown(wait=False, cancel_futures=True)

        final_alerts = engine.finalize()
        for alert in final_alerts:
            log_event(asdict(alert))

        end = time.perf_counter()
        open_count = sum(1 for r in results if r.is_open)

        log_event(
            make_event(
                "scan_ended",
                run_id=run_id,
                ip=ip,
                input=input_target,
                host=host,
                ports_total=len(ports),
                open_count=open_count,
                closed_count=len(results) - open_count,
                duration_ms=round((end - start) * 1000, 2),
                interrupted=interrupted,
            )
        )

    return sorted(results, key=lambda r: r.port)

def scan_ports_no_log(
    target: str,
    ports: list[int],
    timeout: float = 0.2,
    max_workers: int = 100
) -> list[PortScanResult]:
    """Scan multiple ports with threading and detection, without telemetry logging."""

    results: list[PortScanResult] = []
    input_target = target
    host, ip = resolve_target(target)

    run_id = str(uuid.uuid4())
    engine = DetectionEngine(run_id=run_id, target=input_target)

    executor = ThreadPoolExecutor(max_workers=max_workers)

    try:
        futures = [
            executor.submit(
                scan_port,
                ip,
                port,
                input_target,
                host,
                timeout,
            )
            for port in ports
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            alerts = engine.process_result(result)
            if alerts:
                for alert in alerts:
                    print(f"[!] ALERT: {alert.alert_type}")

    except KeyboardInterrupt:
        print("\n[+] Interrupt received. Stopping scan...")
        executor.shutdown(wait=False, cancel_futures=True)
        raise

    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    return sorted(results, key=lambda r: r.port)
                        
                
