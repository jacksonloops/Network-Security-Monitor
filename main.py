#!/usr/bin/env python3
from scanner import scan_ports, scan_ports_no_log
from typing import Optional, Tuple
import socket
from ports import QUICK_PORTS, TOP_1000_PORTS, FULL_PORTS
import time
def main() -> None:

    def get_scan_type() -> str:
        # Get scan type from user
        print("Choose type of scan:")
        scan_type = input("1. Quick scan\n2. 1000 most common ports\n3. Scan all ports\n").strip()

        while scan_type not in ('1', '2', '3'):
            print("Incorrect option, please select again:")
            scan_type = input("1. Quick scan\n2. 1000 most common ports\n3. Scan all ports\n\n").strip()
        return scan_type
    
    def get_log_choice() -> str:
        # Get logging or no logging option from user
        print("\nNow select logging choice:")
        log_choice = input("1. Scan without logging \n2. Scan with logging\n").strip()

        while log_choice not in ('1', '2'):
            print("Incorrect option, please select again:")
            log_choice = input("1. Scan without logging \n2. Scan with logging\n").strip()
        return log_choice

    def resolve_target() -> str:
        target = input("Enter IP or hostname you would like to scan:\n").strip()

        while True:

            if not target:
                target = input("Empty ip or domain, please try again:\n").strip()
                continue
            # Inital check for 0.0.0.0 invalid ip
            if target == "0.0.0.0":
                target = input("Invalid host IP, please try again:\n").strip()
                continue
            # Check if valid IP
            try:
                socket.inet_aton(target)
                ip = target
                return ip
            except OSError:
                pass

            # Try DNS resolution
            try:
                ip = socket.gethostbyname(target)
                return ip
            except socket.gaierror:
                target = input("DNS lookup failed. Please enter a valid IP or hostname:\n").strip()

    scan_type = get_scan_type()
    log_choice = get_log_choice()
    ip = resolve_target()

    # Quick Scan
    if scan_type == '1':
        if log_choice == '1':
            # quick scan with no logging
            print("\nScan type: Quick scan\nLogging: Off\nResolved requested IP:", ip)
            print("Scanning... (Press CRTL+c to stop.)")
            try:
                while True:
                    scan_ports_no_log(ip, QUICK_PORTS)
                    time.sleep(30)

            except KeyboardInterrupt:
                print("\nStopping scanner. Goodbye.")
        else:
            print("\nScan type: Quick scan\nLogging: On\nResolved requested IP:", ip)
            print("Scanning... (Press CRTL+c to stop.)")
            try:
                while True:
                    scan_ports(ip, QUICK_PORTS)
                    time.sleep(30)

            except KeyboardInterrupt:
                print("\nStopping scanner. Goodbye.")

    # Most common 1000k ports scan
    elif scan_type == '2':
        if log_choice == '1':
            print("\nScan type: 1000 most common\nLogging: Off\nResolved requested IP:", ip)
            print("Scanning... (Press CRTL+c to stop.)")
            try:
                while True:
                    scan_ports_no_log(ip, TOP_1000_PORTS)
                    time.sleep(30)

            except KeyboardInterrupt:
                print("\nStopping scanner. Goodbye.")
        else:
            print("\nScan type: 1000 most common\nLogging: On\nResolved requested IP:", ip)
            print("Scanning... (Press CRTL+c to stop.)")
            try:
                while True:
                    scan_ports(ip, TOP_1000_PORTS)
                    time.sleep(30)

            except KeyboardInterrupt:
                print("\nStopping scanner. Goodbye.")
            
    # Full Scan
    elif scan_type == '3':
        if log_choice == '1':
            print("\nScan type: Full scan\nLogging: Off\nResolved requested IP:", ip)
            print("Scanning... (Press CRTL+c to stop.)")
            try:
                while True:
                    scan_ports_no_log(ip, FULL_PORTS)
                    time.sleep(30)

            except KeyboardInterrupt:
                print("\nStopping scanner. Goodbye.")
        else:
            print("\nScan type: Full scan\nLogging: On\nResolved requested IP:", ip)
            print("Scanning... (Press CRTL+c to stop.)")
            try:
                while True:
                    scan_ports(ip, FULL_PORTS)
                    time.sleep(30)

            except KeyboardInterrupt:
                print("\nStopping scanner. Goodbye.")
    
if __name__ == "__main__":
    main()
