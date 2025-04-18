import subprocess
import os
import sys
import json
import re
from modules.http_detect_scheme import get_scheme

def get_wpscan_api_token():
    config_file = os.path.join('config', 'api_tokens.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('wpscan', '')
    return ''

def get_proxy_argument():
    proxy_config_path = os.path.join("config", "proxy.json")
    if os.path.exists(proxy_config_path):
        with open(proxy_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if config.get("enabled", False):
            protocol = config.get("protocol", "http")
            host = config.get("host", "")
            port = config.get("port", "")
            if host and port:
                return ["--proxy", f"{protocol}://{host}:{port}"]
    return []

def run_wpscan(target_ip, domain=None):
    # If a domain is provided, use it instead of the IP
    if domain:
        target_ip = domain

    scheme = get_scheme(target_ip) + "://"
    target_ip = scheme + target_ip

    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    output_file = f"logs/{target_clean}/http/wordpress/wpscan.txt"
    os.makedirs(f"logs/{target_clean}/http/wordpress", exist_ok=True)

    command = [
        "wpscan",
        "--url", target_ip,
        "-e", "vp,vt,u",
        "--no-banner",
        "--update",
        "--format", "json",
        "--output", output_file
    ]

    proxy_args = get_proxy_argument()
    if proxy_args:
        command.extend(proxy_args)

    # Add API token if available
    api_token = get_wpscan_api_token()
    if api_token:
        command.extend(["--api-token", api_token])
        print("[*] Using WPScan API token for enhanced scanning capabilities")
    else:
        print("[!] No WPScan API token found. Consider adding one in Settings for better results")

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Attempt to read the output file's content
    try:
        with open(output_file, "r") as f:
            content = f.read()
    except Exception as e:
        content = ""
        print(f"[!] Could not read the output file: {e}")

    # If redirection is detected, re-run wpscan with the new URL
    if "scan_aborted" in content and "redirects to" in content:
        print("[*] Analyzing output to extract the new URL...")
        match = re.search(r"redirects to:?\s*(\S+)", content, re.IGNORECASE)
        if match:
            new_url = match.group(1).rstrip('/.')
            print(f"[+] New URL detected: {new_url}. Re-running on the new URL...")
            run_wpscan(target_ip, new_url)
            return
        else:
            print("[!] Could not extract the new URL to re-run wpscan.")

    if result.stderr:
        print(f"[!] Error running WPScan on {target_ip}: {result.stderr}")
    else:
        print(f"[+] WordPress scan completed. Results saved in {output_file}")


# Function to write to a file without overwriting
def write_usernames(output_file, usernames):
    existing_usernames = set()
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Read existing usernames
    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            for line in file:
                existing_usernames.add(line.strip())

    # Add new usernames
    with open(output_file, 'a') as file:
        for username in usernames:
            if username not in existing_usernames:
                file.write(username + '\n')


def extract_usernames(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    usernames = set()
    input_file = f"logs/{target_clean}/http/wordpress/wpscan.txt"

    # Open and parse the input JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)  # Load content as a dictionary

    # 'data["users"]' contains a dictionary of users,
    # where each key is the username and the value is its info.
    for username, user_info in data.get("users", {}).items():
        usernames.add(username)

    if usernames:
        print(f"[+] {len(usernames)} usernames found in WordPress.")
        write_usernames(f"logs/{target_clean}/http/wordpress/users.txt", usernames)
        write_usernames(f"wordlists/{target_clean}/users.txt", usernames)
        write_usernames(f"logs/{target_clean}/report/wordpress_usernames.txt", usernames)
    else:
        print("[!] No usernames were found in WordPress")


def directory_listing(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    input_file = f"logs/{target_clean}/http/wordpress/wpscan.txt"
    with open(input_file, 'r') as file:
        data = json.load(file)
        for finding in data.get("interesting_findings", []):
            # If it contains "has listing enabled" in the "to_s" field, report it
            if "has listing enabled" in finding.get("to_s", ""):
                with open(f"logs/{target_clean}/http/wordpress/directory_listing.txt", 'a') as f:
                    f.write(f"Directory listing enabled at {finding['url']}. This could lead to information disclosure.\n")

                os.system("cp " + f"logs/{target_clean}/http/wordpress/directory_listing.txt" + f" logs/{target_clean}/report/wordpress_listing.txt")


def run_http_wordpress(target_ip):
    print("[*] Running WordPress module...")
    run_wpscan(target_ip)
    extract_usernames(target_ip)
    directory_listing(target_ip)
    print("[+] WordPress module completed.")


# Test main
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_wordpress(target)
