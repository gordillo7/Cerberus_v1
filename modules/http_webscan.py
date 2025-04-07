import os
import sys
import subprocess


def run_webscan(target):
    subdomains = []
    subdomains_file = os.path.join("logs", target, "http", "subdomain", "subdomains.txt")
    if not os.path.exists(subdomains_file):
        print(f"[-] Subdomains file not found")
    else:
        print("[*] Reading subdomains...")
        with open(subdomains_file, "r", encoding="utf-8") as f:
            subdomains = [line.strip() for line in f if line.strip()]

    # Add target domain if not present
    if target not in subdomains:
        subdomains.append(target)

    # Create directory for webscan results
    output_dir = os.path.join("logs", target, "http", "webscan")
    os.makedirs(output_dir, exist_ok=True)

    # Create temporary file with complete list of subdomains
    temp_list_file = os.path.join(output_dir, "temp_subdomains.txt")
    with open(temp_list_file, "w", encoding="utf-8") as f:
        for sub in subdomains:
            f.write(sub + "\n")
    print(f"[+] Temporary subdomains list created at {temp_list_file}")

    # Build nuclei command
    nuclei_results_file = os.path.join(output_dir, "nuclei_results.json")
    cmd = [
        "nuclei",
        "-l", temp_list_file,
        "-s", "low,medium,high,critical,unknown",
        "-je", nuclei_results_file
    ]
    print("[*] Running Nuclei...")
    try:
        subprocess.run(cmd, capture_output=True, text=True)
        print(f"[+] Nuclei results saved to {nuclei_results_file}")
    except Exception as e:
        print(f"[-] Error running Nuclei: {e}")

    # Remove temporary file
    try:
        os.remove(temp_list_file)
        print("[+] Temporary file removed.")
    except Exception as e:
        print(f"[-] Error removing temporary file: {e}")

def run_http_webscan(target):
    print(f"[*] Starting web scan for {target}...")
    run_webscan(target)
    print("[+] Web scan completed.")

if __name__ == "__main__":
    target = sys.argv[1]
    run_http_webscan(target)