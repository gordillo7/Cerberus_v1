import os
import sys
import subprocess
import json
from modules.http_detect_scheme import get_scheme


def run_feroxbuster(target_ip, ex_mode=False):
    # Detect HTTP/HTTPS scheme and build the full URL
    scheme = get_scheme(target_ip) + "://"
    full_target = scheme + target_ip

    fuzz_dir = os.path.join("logs", target_ip, "http", "fuzzing")
    os.makedirs(fuzz_dir, exist_ok=True)
    output_file = os.path.join(fuzz_dir, "fuzz.json")

    depth_value = "2" if ex_mode else "1"
    cmd = [
        "feroxbuster",
        "--url", full_target,
        "--wordlist", "wordlists/misc/fuzzing.txt",
        "--depth", depth_value,
        "--silent",
        "--no-state",
        "--json",
        "-o", output_file
    ]

    # If ex_mode is enabled, timeout is 10 minutes, otherwise 3 minutes
    timeout_value = 600 if ex_mode else 180
    try:
        subprocess.run(cmd, check=True, timeout=timeout_value, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[+] Fuzzing results saved to: {output_file}")
    except subprocess.TimeoutExpired:
        print(f"[*] Fuzzing scan exceeded {timeout_value} seconds and has been terminated.")
        print(f"[+] Partial results are preserved in {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"[-] Feroxbuster encountered an execution error: {e}")

def generate_fuzz_report(target_ip):
    fuzz_json_path = os.path.join("logs", target_ip, "http", "fuzzing", "fuzz.json")
    if not os.path.exists(fuzz_json_path):
        print(f"[-] fuzz.json not found at {fuzz_json_path}")
        return

    try:
        with open(fuzz_json_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[-] Error reading fuzz.json: {e}")
        return

    # Filter only "response" entries with status=200 or status=301
    valid_responses = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if (
                data.get("type") == "response"
                and data.get("status") in [200, 301]
            ):
                valid_responses.append(data)
        except json.JSONDecodeError:
            continue

    if not valid_responses:
        print("[-] No valid responses found in fuzz.json.")
        return

    # Prepare report file
    report_dir = os.path.join("logs", target_ip, "report")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, "fuzzing.txt")

    report_lines = [
        f"Found {len(valid_responses)} valid URLs",
    ]

    # Add each URL in a visually formatted manner
    for entry in valid_responses:
        url = entry.get("url", "N/A")

        report_lines.append(f"URL: {url}")

    # Write the final report
    try:
        with open(report_file, "w", encoding="utf-8") as rf:
            rf.write("\n".join(report_lines))
        print(f"[+] Fuzzing log saved to: {report_file}")
    except Exception as e:
        print(f"[-] Error writing fuzzing report: {e}")

def run_http_fuzzing(target_ip, ex_mode=False):
    print(f"[*] Running web fuzzing module...")
    run_feroxbuster(target_ip, ex_mode)
    generate_fuzz_report(target_ip)
    print("[+] Web fuzzing module completed.")

if __name__ == "__main__":
    args = sys.argv[1:]
    ex_mode = False
    if "-ex" in args:
        ex_mode = True
        args.remove("-ex")
    if not args:
        print("[-] Target not provided")
        sys.exit(1)
    target_ip = args[0]
    run_http_fuzzing(target_ip, ex_mode)
