import shutil
import subprocess
import os
import sys
import json
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from modules.http_detect_scheme import get_scheme


def run_wpscan(target_ip, domain=None):
    # If a domain is provided, use it instead of the IP
    if domain:
        target_ip = domain

    scheme = get_scheme(target_ip) + "://"
    target_ip = scheme + target_ip

    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    output_file = f"logs/{target_clean}/http/wordpress/wpscan.txt"
    print(f"[*] Running wpscan on {target_ip}...")
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
            print(f"[*] New URL detected: {new_url}. Re-running wpscan on the new URL...")
            run_wpscan(target_ip, new_url)
            return
        else:
            print("[!] Could not extract the new URL to re-run wpscan.")

    if result.stderr:
        print(f"[!] Error running WPScan on {target_ip}: {result.stderr}")
    else:
        print(f"[+] Initial WordPress scan completed. Results saved in {output_file}")


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
        os.system(f"echo 'Usernames found in WordPress:' > logs/{target_clean}/report/wordpress_usernames.txt")
        write_usernames(f"logs/{target_clean}/report/wordpress_usernames.txt", usernames)
    else:
        print("[!] No usernames were found in WordPress")


def dump_directory_listing(url, output_dir, visited_indexes, visited_files):
    if url in visited_indexes:
        return

    visited_indexes.add(url)
    print(f"[*] Analyzing directory: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')

        for link in links:
            href = link.get('href')
            if not href or href in ['/', '../']:
                continue

            full_url = urljoin(url, href)

            parsed_url = urlparse(full_url)
            if parsed_url.query:
                # If the URL contains a query (e.g., ?C=N;O=D), ignore it
                continue

            if href.endswith('/'):
                # It's another directory
                if full_url not in visited_indexes:
                    dump_directory_listing(full_url, output_dir, visited_indexes, visited_files)
            else:
                # Assume it's a file
                if full_url in visited_files:
                    continue
                visited_files.add(full_url)

                # Build the local path
                path = parsed_url.path.lstrip('/')
                local_path = os.path.join(output_dir, path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                try:
                    file_response = requests.get(full_url)
                    file_response.raise_for_status()
                    with open(local_path, 'wb') as f:
                        f.write(file_response.content)
                    print(f"[+] File saved: {local_path}")

                except Exception as e:
                    print(f"[!] Error downloading {full_url}: {e}")

    except requests.RequestException as e:
        print(f"[!] Error dumping directory content at {url}: {e}")


def process_directory_listings(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    input_file = f"logs/{target_clean}/http/wordpress/wpscan.txt"
    output_dir = f"logs/{target_clean}/http/wordpress/directory_listing_dump"
    visited_indexes = set()
    visited_files = set()
    with open(input_file, 'r') as file:
        data = json.load(file)
        for finding in data.get("interesting_findings", []):
            # If it contains "has listing enabled" in the "to_s" field, dump the directory
            if "has listing enabled" in finding.get("to_s", ""):
                os.makedirs(output_dir, exist_ok=True)
                with open(f"logs/{target_clean}/http/wordpress/directory_listing.txt", 'a') as f:
                    f.write(f"Directory listing enabled at {finding['url']}\n")

                shutil.copy(f"logs/{target_clean}/http/wordpress/directory_listing.txt",
                            f"logs/{target_clean}/report/wordpress_listing.txt")
                dump_directory_listing(finding["url"], output_dir, visited_indexes, visited_files)


def run_http_wordpress(target_ip):
    run_wpscan(target_ip)
    extract_usernames(target_ip)
    process_directory_listings(target_ip)


# Test main
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_wordpress(target)
