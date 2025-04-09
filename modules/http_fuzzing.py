"""Falta sacar el reporte"""
import os
import sys
import subprocess
import json
from http_detect_scheme import get_scheme

def run_feroxbuster(target_ip):
    # Detect HTTP/HTTPS scheme and build the full URL
    scheme = get_scheme(target_ip) + "://"
    full_target = scheme + target_ip

    fuzz_dir = os.path.join("logs", target_ip, "http", "fuzzing")
    os.makedirs(fuzz_dir, exist_ok=True)
    output_file = os.path.join(fuzz_dir, "fuzz.json")

    cmd = [
        "feroxbuster",
        "--url", full_target,
        "--wordlist", "wordlists/misc/fuzzing.txt",
        "--depth", "2",
        "--silent",
        "--no-state",
        "--json",
        "-o", output_file
    ]

    print(f"[*] Starting directory fuzzing with Feroxbuster on {full_target}")
    try:
        # 180 seconds (3 minutes) timeout
        subprocess.run(cmd, check=True, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[+] Feroxbuster results saved to: {output_file}")
    except subprocess.TimeoutExpired:
        print("[*] Feroxbuster scan exceeded 5 minutes and has been terminated.")
        print(f"[+] Partial results are preserved in {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"[-] Feroxbuster encountered an execution error: {e}")

def run_http_fuzzing(target_ip):
    print(f"[*] Running HTTP fuzzing module for {target_ip}...")
    run_feroxbuster(target_ip)
    print("[+] HTTP fuzzing completed.")

if __name__ == "__main__":
    target_ip = sys.argv[1]
    run_http_fuzzing(target_ip)
