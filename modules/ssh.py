import os
import sys
import json
import paramiko

def log_result(target, content):
    log_path = f"logs/{target}/ssh/credentials_found.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as logf:
        logf.write(content)
    # Copy to report folder
    os.system("cp " + log_path + " logs/" + target + "/report/ssh_credentials_found.txt")

def ssh_bruteforce(target, port: int = 22):
    print("[*] Starting SSH brute force on port 22...")
    found = False
    valid_credentials = None

    # 1. Use the default wordlist for SSH
    wordlist_path = "wordlists/misc/ssh-betterdefaultpasslist.txt"
    try:
        with open(wordlist_path, "r") as f:
            lines = [line.strip() for line in f if line.strip() and ":" in line]
    except Exception as e:
        print(f"[!] Error reading {wordlist_path}: {e}")
        lines = []

    for line in lines:
        user, pwd = line.split(":", 1)
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(target, port=port, username=user, password=pwd, timeout=5)
            print(f"[+] Valid credentials found: {user}:{pwd}")
            valid_credentials = f"Weak SSH credentials found: {user}:{pwd} (via default password list)"
            client.close()
            found = True
            break
        except paramiko.AuthenticationException:
            # Incorrect credentials
            pass
        except paramiko.SSHException:
            # SSH connection error (e.g., too many attempts or banner issues)
            pass
        except Exception as e:
            # Other errors
            pass

    # 2. Attempt with custom users if the file exists
    custom_users_path = f"wordlists/{target}/users.txt"
    if not found and os.path.exists(custom_users_path):
        try:
            with open(custom_users_path, "r") as f:
                custom_users = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"[!] Error reading {custom_users_path}: {e}")
            custom_users = []

        # Extract only the password part from the default wordlist
        passwords = []
        try:
            with open(wordlist_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if ":" in line:
                        _, pwd = line.split(":", 1)
                        passwords.append(pwd)
        except Exception as e:
            print(f"[!] Error reading passwords from {wordlist_path}: {e}")

        for user in custom_users:
            for pwd in passwords:
                if not pwd:
                    continue
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(target, port=port, username=user, password=pwd, timeout=5)
                    print(f"[+] Valid credentials found: {user}:{pwd}")
                    valid_credentials = f"Weak SSH credentials found: {user}:{pwd} (via custom users list)"
                    client.close()
                    found = True
                    break
                except paramiko.AuthenticationException:
                    pass
                except paramiko.SSHException:
                    pass
                except Exception as e:
                    pass
            if found:
                break

    if valid_credentials:
        log_result(target, valid_credentials)
    else:
        print("[-] No valid SSH credentials found.")

def ssh_grep_searchsploit(target):
    print("[*] Searching for CVEs in the searchsploit output...")
    searchsploit_file = f"logs/{target}/ssh/searchsploit.txt"
    try:
        with open(searchsploit_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error reading the file {searchsploit_file}: {e}")
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
    print("[*] Retrieving SSH version from Nmap output...")
    nmap_file = f"logs/{target}/nmap/ports_services_versions.txt"
    try:
        with open(nmap_file, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[!] Error reading the file {nmap_file}: {e}")
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

    ssh_dir = f"logs/{target}/ssh"
    os.makedirs(ssh_dir, exist_ok=True)
    searchsploit_file = f"{ssh_dir}/searchsploit.txt"

    cmd = f'searchsploit "{ssh_version}" -j > {searchsploit_file}'
    print(f"[*] Executing command: {cmd}")
    try:
        os.system(cmd)
        print(f"[+] Searchsploit result saved in {searchsploit_file}")
        ssh_grep_searchsploit(target)
    except Exception as e:
        print(f"[!] Error executing searchsploit: {e}")

def run_ssh(target):
    ssh_bruteforce(target)
    ssh_searchsploit(target)

if __name__ == "__main__":
    run_ssh(sys.argv[1])
