#!/usr/bin/env python3
from scanner import resolve_target, parse_ports, scan_port, scan_ports

def main() -> None:

    ip = '127.0.0.1'

    """ Testing parse_ports in scanner.py """

    tests = ["hello", "20", "20-30", "30-20", "-1", "65536", "65355", "65344-65355",
             "1-hello", "0-1",
             "1--", "1,,", "1-2, 3-2",  "1-2,,2-4", "7990-8005", "5432", "22"]
    i = 0
    for strs in tests:
        i+=1
        print("test: ", i,",", strs.strip())
        try:
            ports = parse_ports(strs)
        except ValueError as e:
            print(f"Error occured: {e}")
            continue
        
        print("Ports found: ", ports)

        """ Testing resolve_target, scan_port, and scan_ports as scan_ports utilizes the other two funcs """

        res = scan_ports(ip, ports)
        open_ports = [r.port for r in res if r.is_open]
        closed_ports = len(ports) - len(open_ports)
        print("Scanned", len(ports), "ports against", ip,".")
        print("Open:", open_ports)
        print("Closed:", closed_ports)    

if __name__ == "__main__":
    main()
