#!/usr/bin/env python3
from netsec.scanner import resolve_target, parse_ports, scan_port, scan_ports

def main() -> None:
    # Testing resolve_target
    target = "google.com"
    try:
        hostname, ip = resolve_target(target)
    except ValueError as e:
        print(f"Error occured: {e}")
        return
    
    print(f"Target: {target}")
    print(f"Resolved IP: {ip}")

    # testing parse_ports
    tests = ["hello", "20", "20-30", "30-20", "-1", "65536", "65355", "65344-65355",
             "1-hello", "0-1",
             "1--", "1,,", "1-2, 3-2",  "1-2,,2-4"]
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

    ip, port = '127.0.0.1', 80
    try:
        res = scan_port(ip, port)
        print(res)
    except ValueError as e:
        print(f"Error occured {e}")
        return

    try:
        res = scan_ports(ip, ports)
        open_ports = [r.port for r in res if r.is_open]
        closed_ports = len(ports) - len(open_ports)
        print("Scanned", len(ports), "ports against", ip,".")
        print("Open:", open_ports)
        print("Closed:", closed_ports)
        
    except ValueError as e:
        print(f"Error occured {e}.")
        return



    

if __name__ == "__main__":
    main()

    
          
