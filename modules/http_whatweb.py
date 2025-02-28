import subprocess
import os
import sys
import re


def whatweb(target_ip):
    print("[*] Running whatweb...")
    def run_whatweb(scheme):
        target = f"{scheme}://{target_ip}"
        target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
        tec_file = f"logs/{target_clean}/http/whatweb/tec.txt"
        os.makedirs(f"logs/{target_clean}/http/whatweb", exist_ok=True)

        command = [
            "whatweb",
            target,
            "--log-object", tec_file
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print(f"[!] Error running whatweb with {scheme}:")
            print(result.stderr)
        else:
            print(f"[+] whatweb analysis completed with {scheme}. Results in {tec_file}")

        return tec_file

    tec_file = run_whatweb("http")
    if os.path.exists(tec_file) and os.path.getsize(tec_file) == 0:
        print("[*] No results with http, trying https...")
        run_whatweb("https")


def cms_identification(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    cms_file = f"logs/{target_clean}/http/whatweb/cms.txt"
    tec_file = f"logs/{target_clean}/http/whatweb/tec.txt"
    cms_list = ["WordPress", "Joomla", "Drupal"]
    cms_detected = "unknown"

    with open(tec_file, 'r') as f:
        lines = f.readlines()

    for cms in cms_list:
        for line in lines:
            if re.search(cms, line, re.IGNORECASE):
                cms_detected = cms
                break
        if cms_detected != "unknown":
            break

    with open(cms_file, 'w') as f:
        f.write(cms_detected + "\n")

    print(f"[+] CMS detected: {cms_detected}. Results in {cms_file}")


def run_http_whatweb(target):
    whatweb(target)
    cms_identification(target)


# Test main
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_whatweb(target)