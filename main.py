#!/usr/bin/env python3
from scanner import resolve_target, parse_ports, scan_port, scan_ports

def main() -> None:
    # Get scan type from user
    print("Choose type of scan:")
    scan_type = input("1. Quick scan\n2. 1000 most common ports\n3. Scan all ports\n")
    scan_type.strip()

    while scan_type != '1' and scan_type != '2' and scan_type != '3':
        print("Incorrect option, please select again:")
        scan_type = input("1. Quick scan\n2. 1000 most common ports\n3. Scan all ports\n\n")
        scan_type.strip()

    # Get logging or no logging option from user
    print("\nNow select logging choice:")
    log_choice = input("1. Scan without logging \n2. Scan with logging\n")
    log_choice.strip()

    while log_choice != '1' and log_choice != '2':
        print("Incorrect option, please select again:")
        log_choice = input("1. Scan without logging \n2. Scan with logging\n")
    
    # Quick Scan
    if scan_type == '1':
        if log_choice == '1':
            # quick scan with no logging
            print("Quick scan with no logging.")
        else:
            print("Quick scan with logging.")
    # Most common 1000k ports scan
    elif scan_type == '2':
        if log_choice == '1':
            # quick scan with no logging
            print("1000 port scan with no logging")
        else:
            print("1000 port scan with logging")
            
    # Full Scan
    elif scan_type == '3':
        if log_choice == '1':
            # quick scan with no logging
            print("Full port scan with no logging")
        else:
            print("Full port scan with logging")
    
if __name__ == "__main__":
    main()
