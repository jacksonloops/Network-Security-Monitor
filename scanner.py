#!/usr/bin/env python3
import socket
import sys
from dataclasses import dataclass
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

@dataclass(frozen=True)
class PortScanResult:
        port: int
        is_open: bool
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
                        if (left < 0 or left > 65535) or (right < 0 or right > 65535):
                                raise ValueError("Invalid port value.")
                        # Append ports if all checks pass
                        ports.update(range(left, right+1))

                # if single port found
                else:
                        if not t.isdigit():
                                raise ValueError("Non integer found.")
                        port = int(t)
                        if port < 0 or port > 65535:
                                raise ValueError("Invalid port value.")
                        ports.add(port)
                        
        return sorted(ports)

def scan_port(ip: str, port: int, timeout: float = 0.5) -> PortScanResult:
        try:
                # Create socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(timeout)
                        res = sock.connect_ex((ip, port))
                        # if we connect, return and show we connected
                        if res == 0:
                                return PortScanResult(port=port, is_open = True, error = None)
                        # connection failed
                        else:
                                return PortScanResult(port = port, is_open = False, error = "closed")
        # Connectoin timed out
        except socket.timeout:
                return PortScanResult(port = port, is_open = False, error = "timeout")
        # Error occured
        except OSError as e:
                return PortScanResult(port=port, is_open = False, error = str(e))
# Multi port scanner with Threads for concurrent scanning. uses scan_port.
def scan_ports(ip: str, ports: list[int], timeout: float = 0.5, max_workers: int=300) -> list[PortScanResult]:
        res = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(scan_port, ip, p, timeout) for p in ports]
                for future in as_completed(futures):
                        result = future.result()
                        res.append(result)
        return sorted(res, key=lambda r: r.port)
                        
                
