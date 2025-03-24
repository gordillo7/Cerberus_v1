import os
import sys
import json
import mysql.connector


def log_result(target, content):
    log_path = f"logs/{target}/mysql/credentials_found.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as logf:
        logf.write(content)
    # Copy to report folder
    os.system("cp " + log_path + " logs/" + target + "/report/mysql_credentials_found.txt")

def mysql_bruteforce(target, port: int = 3306):
    print("[*] Starting MySQL brute force on port 3306...")
    found = False
    valid_credentials = None

    # 1. Wordlist path for MySQL default credentials
    wordlist_path = "wordlists/misc/mysql-betterdefaultpasslist.txt"
    if not found:
        try:
            with open(wordlist_path, "r") as f:
                lines = [line.strip() for line in f if line.strip() and ":" in line]
        except Exception as e:
            print(f"[!] Error reading {wordlist_path}: {e}")
            lines = []

        for line in lines:
            user, pwd = line.split(":", 1)
            try:
                con = mysql.connector.connect(host=target, port=port, user=user, password=pwd, connection_timeout=5)
                print(f"[+] Valid credentials found: {user}:{pwd}")
                valid_credentials = f"Weak MySQL credentials found: {user}:{pwd} (found via default passlist)"
                con.close()
                found = True
                break
            except mysql.connector.Error:
                pass

    # 2. Check for custom users file and try with passwords from the default passlist
    custom_users_path = f"wordlists/{target}/users.txt"
    if not found and os.path.exists(custom_users_path):
        try:
            with open(custom_users_path, "r") as f:
                custom_users = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"[!] Error reading {custom_users_path}: {e}")
            custom_users = []

        # Extract only the password part from each line in the default passlist
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
                    con = mysql.connector.connect(host=target, port=port, user=user, password=pwd, connection_timeout=5)
                    print(f"[+] Valid credentials found: {user}:{pwd}")
                    valid_credentials = f"Weak MySQL credentials found: {user}:{pwd} (found via custom users list)"
                    con.close()
                    found = True
                    break
                except mysql.connector.Error:
                    pass
            if found:
                break

    if valid_credentials:
        log_result(target, valid_credentials)
    else:
        print("[-] No valid MySQL credentials found.")

def mysql_grep_searchsploit(target):
    print("[*] Searching for CVEs in the searchsploit output...")
    searchsploit_file = f"logs/{target}/mysql/searchsploit.txt"
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
        report_path = f"logs/{target}/report/mysql_cves.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as rep:
            for cve in cves:
                rep.write(f"\n{cve}")
    else:
        print("[-] No CVEs found in the searchsploit output.")

def mysql_searchsploit(target):
    print("[*] Obtaining the MySQL version from the Nmap output...")
    nmap_file = f"logs/{target}/nmap/ports_services_versions.txt"
    try:
        with open(nmap_file, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[!] Error reading the file {nmap_file}: {e}")
        return

    mysql_version = None
    for line in lines:
        if line.startswith("PORT") or line.strip() == "":
            continue
        parts = line.split()
        # Look for port 3306 and service mysql (case-insensitive check)
        if len(parts) >= 4 and parts[0].startswith("3306") and "mysql" in parts[2].lower():
            mysql_version = " ".join(parts[3:])
            break

    if mysql_version is None:
        print("[-] No MySQL version information found in the Nmap file.")
        return

    print(f"[+] MySQL version found: {mysql_version}")

    mysql_dir = f"logs/{target}/mysql"
    os.makedirs(mysql_dir, exist_ok=True)
    searchsploit_file = f"{mysql_dir}/searchsploit.txt"

    cmd = f'searchsploit "{mysql_version}" -j > {searchsploit_file}'
    print(f"[*] Executing command: {cmd}")
    try:
        os.system(cmd)
        print(f"[+] Searchsploit result saved in {searchsploit_file}")
        mysql_grep_searchsploit(target)
    except Exception as e:
        print(f"[!] Error executing searchsploit: {e}")

def run_db_mysql(target):
    mysql_bruteforce(target)
    mysql_searchsploit(target)

if __name__ == "__main__":
    run_db_mysql(sys.argv[1])