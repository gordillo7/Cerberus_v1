import subprocess
import os
import sys
import re
from modules.http_detect_scheme import get_scheme


def whatweb(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    tec_file = f"logs/{target_clean}/http/whatweb/tec.txt"
    os.makedirs(f"logs/{target_clean}/http/whatweb", exist_ok=True)

    scheme = get_scheme(target_ip) + "://"
    target_ip = scheme + target_ip

    command = [
        "whatweb",
        target_ip,
        "--log-object", tec_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[!] Error running whatweb:")
        print(result.stderr)
    else:
        print(f"[+] Analysis completed. Results in {tec_file}")


def cms_identification(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    cms_file = f"logs/{target_clean}/http/whatweb/cms.txt"
    tec_file = f"logs/{target_clean}/http/whatweb/tec.txt"
    cms_list = ["WordPress", "Joomla", "Drupal"]
    cms_detectado = "unknown"

    with open(tec_file, 'r') as f:
        lineas = f.readlines()

    for cms in cms_list:
        for linea in lineas:
            if re.search(cms, linea, re.IGNORECASE):
                cms_detectado = cms
                break
        if cms_detectado != "unknown":
            break

    with open(cms_file, 'w') as f:
        f.write(cms_detectado + "\n")

    print(f"[+] CMS detected: {cms_detectado}. Results in {cms_file}")

def run_http_whatweb(target):
    print("[*] Running CMS identification module...")
    whatweb(target)
    cms_identification(target)
    print("[+] CMS identification completed.")

# Test main
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_whatweb(target)