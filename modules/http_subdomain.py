import sys
import os
import subprocess
import httpx

def get_valid_url(sub):
    # If the subdomain already starts with http:// or https://, test it directly.
    if sub.startswith("http://") or sub.startswith("https://"):
        schemes = [""]
    else:
        schemes = ["https://", "http://"]
    for prefix in schemes:
        url = f"{prefix}{sub}" if prefix else sub
        try:
            response = httpx.get(url, timeout=5)
            if 200 <= response.status_code < 400:
                return url
        except httpx.RequestError:
            continue
    return None

def enumerate_subdomains(domain):
    command = f"subfinder -d {domain} -silent"
    try:
        result = subprocess.run(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
        )
        if result.returncode != 0:
            print(f"[!] Error in subfinder command: {result.stderr}")
            return []
        subdomains_raw = result.stdout.strip().splitlines()
    except Exception as e:
        print(f"[!] Exception during subfinder execution: {e}")
        return []
    valid_subdomains = []
    for sub in subdomains_raw:
        url = get_valid_url(sub)
        if url:
            valid_subdomains.append(sub)
            print(f"[+] Valid subdomain: {sub}")
        else:
            print(f"[-] {sub} did not respond with a valid status code")
    return sorted(set(valid_subdomains))

def save_subdomains(domain, subdomains):
    output_dir = os.path.join("logs", domain, "http", "subdomain")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "subdomains.txt")
    with open(output_file, "w") as f:
        for subdomain in subdomains:
            f.write(subdomain + "\n")
    os.system(f"cp {output_file} logs/{domain}/report/http_subdomains.txt")
    print(f"[+] Subdomains saved in: {output_file}")

def subdomain(domain):
    subdomains = enumerate_subdomains(domain)
    if subdomains:
        print(f"[+] Found {len(subdomains)} subdomains")
        save_subdomains(domain, subdomains)
    else:
        print("[!] No subdomains were found.")

def run_http_subdomain(domain):
    print("[*] Running subdomain enumeration module...")
    subdomain(domain)
    print("[*] Subdomain enumeration module completed.")

if __name__ == "__main__":
    domain = sys.argv[1]
    run_http_subdomain(domain)
