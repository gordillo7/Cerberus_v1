import subprocess
import sys

def fuzzing(target):
    # Define the wordlist path
    wordlist = "wordlists/misc/fuzzing.txt"

    # Ensure the target URL is well-formed (adds trailing slash if missing)
    if not target.endswith("/"):
        target += "/"

    # Build the gobuster command as a list
    command = [
        "gobuster",
        "dir",
        "-u",
        target,
        "-w",
        wordlist,
        "-t", "120",
        "-o", f"logs/{target}/http/fuzzing.txt",
        "-f",
        "-q",
        "-z"
    ]

    print(f"[*] Running gobuster on {target} ...")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print(f"[!] Error executing gobuster: {result.stderr}")
    else:
        print(result.stdout)

def run_http_fuzzing(target):
    fuzzing(target)

if __name__ == "__main__":
    target = sys.argv[1]
    run_http_fuzzing(target)