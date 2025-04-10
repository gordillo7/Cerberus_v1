import subprocess
import re
import sys
import os

def initial_scan(target_ip):
    output_file = f"logs/{target_ip}/nmap/initial_scan.txt"
    print(f"[*] Getting open ports for {target_ip}...")
    os.makedirs(f"logs/{target_ip}/nmap", exist_ok=True)

    command = [
        "nmap",
        "-p-",
        "--open",
        "--min-rate", "5000",
        "-n",
        "-Pn",
        target_ip,
        "-oG",
        output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[!] Error running nmap:")
        print(result.stderr)
    else:
        print(f"[+] Initial scan completed. Results in {output_file}")

def extract_ports(target_ip):
    file_path = f"logs/{target_ip}/nmap/initial_scan.txt"
    ports = []
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("Host:"):
                match = re.search(r"Ports:\s+(.*)$", line)
                if match:
                    ports_section = match.group(1)
                    ports_info = ports_section.split(",")

                    for p in ports_info:
                        p_split = p.split("/")
                        if len(p_split) > 1 and p_split[1] == "open":
                            port_number = p_split[0].strip()
                            ports.append(port_number)
    with open(f"logs/{target_ip}/nmap/ports.txt", "w") as f:
        for port in ports:
            f.write(port + "\n")
    return ports

def hard_scan(target_ip, ports):
    output_file = f"logs/{target_ip}/nmap/ports_services_versions_temp.txt"
    print(f"[*] Scanning ports in detail...")
    os.makedirs(f"logs/{target_ip}/nmap", exist_ok=True)

    command = [
        "nmap",
        "-p" + ",".join(ports),
        "-sV",
        "-Pn",
        target_ip,
        "-oN",
        output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[!] Error running nmap:")
        print(result.stderr)

def clear_report(target_ip):
    report_file = f"logs/{target_ip}/nmap/ports_services_versions_temp.txt"
    output_file = f"logs/{target_ip}/nmap/ports_services_versions.txt"
    found_interesting_line = False

    with open(report_file, 'r') as f:
        lines = f.readlines()

    with open(output_file, 'w') as f:
        for line in lines:
            if re.search(r"PORT\s+STATE\s+SERVICE\s+VERSION", line):
                found_interesting_line = True
            if found_interesting_line:
                if re.search(r"^\d+/tcp\s+", line) or re.search(r"PORT\s+STATE\s+SERVICE\s+VERSION", line):
                    f.write(line)

    print(f"[+] Detailed port scan completed. Results in {output_file}")
    os.remove(report_file)
    os.makedirs(f"logs/{target_ip}/report", exist_ok=True)
    os.system(f"cp {output_file} logs/{target_ip}/report/nmap.txt")

def run_nmap(target_ip):
    print("[*] Running nmap module...")
    initial_scan(target_ip)
    open_ports = extract_ports(target_ip)
    hard_scan(target_ip, open_ports)
    clear_report(target_ip)
    print(f"[+] Nmap module completed.")

# Test main
if __name__ == "__main__":
    target = sys.argv[1]
    run_nmap(target)
