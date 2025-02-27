import os
import subprocess
import sys
import re

def joomscan(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    output_file = f"logs/{target_clean}/http/joomla/joomscan.txt"
    print(f"[+] Running joomscan on {target_clean}...")

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
        print(f"[+] joomscan analysis finished. Results in {output_file}")

def run_http_joomla(target):
    joomscan(target)

# Test main
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_joomla(target)
