#!/usr/bin/env python3
import socket
from datetime import datetime
import sys
import time
from dataclasses import dataclass, asdict
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from telemetry import make_event, log_event
from detection import DetectionEngine
import uuid


@dataclass(frozen=True)
class PortScanResult:
        target: str
        host: Optional[str]
        port: int
        is_open: bool
        latency_ms: Optional[float]
        error: Optional[str] = None

def resolve_target(target: str) -> Tuple[Optional[str], str]:
        #normalize target str
        target = target.strip()
        if target == "":
                raise ValueError("Empty target.")
        # Inital check for 0.0.0.0 invalid ip
        if target == "0.0.0.0":
                raise ValueError("Invalid host IP.")
        # Checking if valid ip, if so return No domain name and ip. if invalid try host name DNS res
        try:
                _ = socket.inet_aton(target)
                return None, target
        except OSError:
                # get ip from domain name
                try:
                        ip = socket.gethostbyname(target)
                        hostname_or_none = target
                        return hostname_or_none, ip
                # halt if domain is invalid
                except socket.gaierror as e:
                        raise ValueError("DNS lookup failed.")

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

def scan_port(ip: str, port: int, target: Optional[str], host: Optional[str], timeout: float = 0.5) -> PortScanResult:
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
def tel_scan_port(ip: str, port: int, run_id: str, target: str, host: Optional[str], timeout: float = 0.5)-> PortScanResult:
    """Wrapper that scans a port and logs the port_scanned event"""
    # Call scan_port with single=False so it doesn't log events internally

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
def scan_ports(target: str, ports: list[int], timeout: float = 0.5, max_workers: int=300) -> list[PortScanResult]:
    """Scan multiple ports with threading"""
    res = []
    input_target = target
    # Resolve target
    host_or_ip = resolve_target(target)
    if host_or_ip[0] == None:
        host = None
        ip = host_or_ip[1]
    elif host_or_ip[0] != None:
        ip = host_or_ip[1]
        host = host_or_ip[0]
    
    # Generate single run_id for this scan session
    run_id = str(uuid.uuid4())
    
    # Log scan start
    log_event(make_event('scan_started', run_id=run_id, ip=ip, input=input_target, host=host, ports_total=len(ports)))
    start = time.perf_counter()

    # Start alert Detection engine
    engine = DetectionEngine(run_id=run_id,target=input_target)

    # Scan all ports concurrently using tel_scan_port
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(tel_scan_port, ip, p, run_id, input_target, host, timeout=timeout) for p in ports]
        for future in as_completed(futures):
            result = future.result()
            alerts = engine.process_result(result)
            if len(alerts) != 0:
                        for alert in alerts:
                                log_event((asdict(alert)))
            res.append(result)

    final_alerts = engine.finalize()
    if len(final_alerts) != 0:
        for alert in final_alerts:
                log_event((asdict(alert)))

    # Log scan end
    end = time.perf_counter()
    open_count = sum(1 for r in res if r.is_open)
    log_event(make_event('scan_ended', run_id=run_id, ip=ip, input=input_target, host=host, ports_total=len(ports), open_count=open_count, closed_count=len(ports) - open_count, duration_ms=round((end - start) * 1000, 2)))
    return sorted(res, key=lambda r: r.port)
                        
                
