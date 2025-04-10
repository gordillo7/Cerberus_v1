import os
import subprocess
import sys
import re
from modules.http_detect_scheme import get_scheme

def joomscan(target_ip):
    scheme = get_scheme(target_ip) + "://"
    target_ip = scheme + target_ip
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    output_file = f"logs/{target_clean}/http/joomla/joomscan.txt"

    # Create the directory to store the logs if it doesn't exist
    os.makedirs(f"logs/{target_clean}/http/joomla", exist_ok=True)

    # Basic command for joomscan. Adjust the parameters as needed.
    command = [
        "joomscan",
        "-u", target_ip
    ]

    # Run joomscan and capture the output
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Regular expression to remove ANSI codes
    ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
    clean_output = ansi_escape.sub('', result.stdout)

    # Save the clean output to the log file
    with open(output_file, "w") as f:
        f.write(clean_output)

    # Check if there were errors during execution
    if result.returncode != 0:
        print(f"[!] Error running joomscan (return code {result.returncode}):")
        print(result.stderr)
    else:
        print(f"[+] Joomla analysis finished. Results in {output_file}")


def extract_joomscan_report(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    input_path = os.path.join("logs", target_clean, "http", "joomla", "joomscan.txt")
    output_dir = os.path.join("logs", target_clean, "report")
    output_path = os.path.join(output_dir, "joomscan.txt")

    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(input_path, "r") as infile:
            lines = [line.rstrip() for line in infile.readlines()]
    except Exception as e:
        print(f"[-] Error reading log file: {e}")
        return

    keys = {
        "[+] Detecting Joomla Version": "Joomla Version",
        "[+] Core Joomla Vulnerability": "Core Vulnerability",
        "[+] admin finder": "Admin Page",
        "[+] Finding common backup files name": "Backup File",
        "[+] Finding common log files name": "Log Files",
        "[+] Checking user registration": "User Registration",
        "[+] Checking sensitive config.php.x file": "Sensitive Config"
    }

    sections = {}

    i = 0
    while i < len(lines):
        line = lines[i]
        for key, section_name in keys.items():
            if line.startswith(key):
                info_lines = []
                j = i + 1
                while j < len(lines) and lines[j] and not any(lines[j].startswith(k) for k in keys):
                    current_line = lines[j]
                    if current_line.startswith("[++]"):
                        current_line = current_line[len("[++]"):].lstrip()
                    info_lines.append(current_line)
                    j += 1
                sections[section_name] = "\n".join(info_lines) if info_lines else "Not found"
                i = j - 1
                break
        i += 1

    final_report = (
        "1. Joomla Version\n"
        f"{sections.get('Joomla Version', 'Not found')}\n\n"
        "2. Core Vulnerability\n"
        f"{sections.get('Core Vulnerability', 'Not found')}\n\n"
        "3. Admin Page\n"
        f"{sections.get('Admin Page', 'Not found')}\n\n"
        "4. Backup File\n"
        f"{sections.get('Backup File', 'Not found')}\n\n"
        "5. Log Files\n"
        f"{sections.get('Log Files', 'Not found')}\n\n"
        "6. User Registration\n"
        f"{sections.get('User Registration', 'Not found')}\n\n"
        "7. Sensitive Config Files\n"
        f"{sections.get('Sensitive Config', 'Not found')}\n"
    )

    try:
        with open(output_path, "w") as outfile:
            outfile.write(final_report)
        print(f"[+] Joomla log saved in {output_path}")
    except Exception as e:
        print(f"[-] Error writing report: {e}")


def run_http_joomla(target):
    print("[*] Running Joomla module...")
    joomscan(target)
    extract_joomscan_report(target)
    print("[+] Joomla module completed.")

# Test main
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_joomla(target)
