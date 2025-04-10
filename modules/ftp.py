import ftplib
import os
import sys
import io
import json

def ftp_grep_searchsploit(target_ip):
    print("[*] Searching for CVEs in the searchsploit output...")
    searchsploit_file = f"logs/{target_ip}/ftp/searchsploit.txt"
    try:
        with open(searchsploit_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error reading the file {searchsploit_file}: {e}")
        return

    cves = []
    # If result_exploit contains something, the word 'cve' is not needed
    for result in data.get("RESULTS_EXPLOIT", []):
        cve = result["Title"]
        cves.append(cve)

    if cves:
        print(f"[+] CVEs found: {', '.join(cves)}")
        report_path = f"logs/{target_ip}/report/ftp_cves.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as rep:
            for cve in cves:
                rep.write(f"\n{cve}")
    else:
        print("[-] No CVEs found in the searchsploit output.")

def ftp_searchsploit(target_ip):
    print("[*] Obtaining the FTP version from the Nmap output...")
    nmap_file = f"logs/{target_ip}/nmap/ports_services_versions.txt"
    try:
        with open(nmap_file, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[!] Error reading the file {nmap_file}: {e}")
        return

    ftp_version = None
    for line in lines:
        # Skip the header line and empty lines
        if line.startswith("PORT") or line.strip() == "":
            continue
        parts = line.split()
        if len(parts) >= 4 and parts[2].lower() == "ftp":
            # Assume the version may be composed of more than one word
            ftp_version = " ".join(parts[3:])
            break

    if ftp_version is None:
        print("[-] No FTP version information found in the Nmap file.")
        return

    print(f"[+] FTP version found: {ftp_version}")

    # Ensure the FTP logs directory exists
    ftp_dir = f"logs/{target_ip}/ftp"
    os.makedirs(ftp_dir, exist_ok=True)
    searchsploit_file = f"{ftp_dir}/searchsploit.txt"

    # Build and execute the searchsploit command
    cmd = f'searchsploit "{ftp_version}" -j > {searchsploit_file}'
    print(f"[*] Executing command: {cmd}")
    try:
        os.system(cmd)
        print(f"[+] Searchsploit result saved in {searchsploit_file}")
        ftp_grep_searchsploit(target_ip)
    except Exception as e:
        print(f"[!] Error executing searchsploit: {e}")

def check_ftp_write_permission(ftp, target_ip):
    print("[*] Checking FTP write permissions...")
    test_filename = "test_write_permission.txt"
    test_content = b"Test file for write permission check"
    try:
        ftp.storbinary(f"STOR {test_filename}", io.BytesIO(test_content))
        ftp.delete(test_filename)
        print("[+] Write permission enabled on FTP.")
        report_path = f"logs/{target_ip}/ftp/write_perm.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as rep:
            rep.write("The FTP server allows writing, which could enable the upload of malicious files.")
        os.system("cp " + report_path + " logs/" + target_ip + "/report/ftp_write_perm.txt")
    except ftplib.error_perm:
        print("[-] Write permissions not detected.")

def check_ftp_anonymous(target_ip):
    anonymous_file = f"logs/{target_ip}/ftp/anonymous.txt"
    print(f"[*] Checking anonymous FTP access on {target_ip}...")
    try:
        ftp = ftplib.FTP(target_ip)
        ftp.login("anonymous", "anonymous")
        print("[+] Anonymous login enabled!")

        check_ftp_write_permission(ftp, target_ip)

        os.makedirs(f"logs/{target_ip}/ftp", exist_ok=True)

        with open(anonymous_file, 'w') as f:
            f.write("Anonymous FTP login enabled")

        os.system("cp " + anonymous_file + " logs/" + target_ip + "/report/ftp_anonymous.txt")
        # Proceed to download files if access is successful
        dump_ftp_contents(ftp, target_ip)
        ftp.quit()
    except ftplib.error_perm:
        print("[-] Anonymous access is disabled.")
        # Start the mini-bruteforce case with user 'admin'
        mini_bruteforce(target_ip)
    except Exception as e:
        print(f"[!] Error connecting to FTP: {e}")

def mini_bruteforce(target_ip):
    print("[*] Starting mini bruteforce...")
    encontrado = False
    wordlist_path = "wordlists/misc/mini_bruteforcing_passwords.txt"
    try:
        with open(wordlist_path, 'r') as wl:
            passwords = [line.strip() for line in wl if line.strip()]
    except Exception as e:
        print(f"[!] Error reading mini bruteforce wordlist: {e}")
        return

    for pwd in passwords:
        try:
            ftp = ftplib.FTP(target_ip, timeout=5)
            ftp.login("admin", pwd)
            print(f"[+] Valid credentials found: admin:{pwd}")

            check_ftp_write_permission(ftp, target_ip)

            # Log weak credentials
            log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w") as logf:
                logf.write(f"Weak FTP credentials found: admin:{pwd} (obtained by brute force)")

            os.system("cp " + log_path + " logs/" + target_ip + "/report/ftp_credentials_found.txt")
            dump_ftp_contents(ftp, target_ip)
            ftp.quit()
            encontrado = True
            break
        except ftplib.error_perm:
            # Incorrect credentials; continue with the next attempt
            pass
        except Exception as e:
            print(f"[!] Error testing admin:{pwd} - {e}")

    # After mini-bruteforce, test admin:admin to see if we are blocked
    print("[*] Checking for attempt limitation...")
    limite_libre = False
    try:
        ftp = ftplib.FTP(target_ip, timeout=5)
        ftp.login("admin", "admin")
        # If it reaches here, it means the attempt was processed, even if the credentials are invalid,
        # which indicates that the server is still responding normally.
    except ftplib.error_perm as e:
        error_msg = str(e)
        # If the error contains "530" (usually "login incorrect"), it is assumed that there is no lockout
        if "530" in error_msg:
            print("[+] No attempt limit detected.")
            log_path = f"logs/{target_ip}/ftp/no_limit.txt"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w") as logf:
                logf.write("There is no attempt limit on FTP login.")
            os.system("cp " + log_path + " logs/" + target_ip + "/report/ftp_no_limit.txt")
            limite_libre = True
        else:
            print("[-] Error testing admin:admin: ", error_msg)
    except Exception as e:
        print(f"[!] Error testing admin:admin - {e}")

    # If no credentials were found in the mini-bruteforce and we are not blocked,
    # start the elaborate bruteforce.
    if limite_libre and not encontrado:
        ftp_elaborate_bruteforce(target_ip)
    elif not limite_libre:
        print("[!] Elaborate brute force will not be performed due to possible attempt limitation.")

def ftp_elaborate_bruteforce(target_ip):
    print("[*] Starting elaborate brute force...")
    custom_dir = f"wordlists/{target_ip}"
    # Variables for custom wordlists
    users_custom = []
    pwds_custom = []

    # If a custom directory exists, try to load the lists
    if os.path.isdir(custom_dir):
        user_file = os.path.join(custom_dir, "users.txt")
        pwd_file = os.path.join(custom_dir, "passwords.txt")
        if os.path.isfile(user_file):
            try:
                with open(user_file, 'r') as uf:
                    users_custom = [line.strip() for line in uf if line.strip()]
                print(f"[*] Loaded {len(users_custom)} users from {user_file}")
            except Exception as e:
                print(f"[!] Error reading {user_file}: {e}")
        if os.path.isfile(pwd_file):
            try:
                with open(pwd_file, 'r') as pf:
                    pwds_custom = [line.strip() for line in pf if line.strip()]
                print(f"[*] Loaded {len(pwds_custom)} passwords from {pwd_file}")
            except Exception as e:
                print(f"[!] Error reading {pwd_file}: {e}")

    # If at least one custom list is loaded, attempt brute force with them
    if users_custom or pwds_custom:
        print("[*] Trying custom combinations...")
        # Case 1: Both custom users and passwords are available
        if users_custom and pwds_custom:
            for user in users_custom:
                for pwd in pwds_custom:
                    try:
                        ftp = ftplib.FTP(target_ip, timeout=5)
                        ftp.login(user, pwd)
                        print(f"[+] Valid credentials found: {user}:{pwd}")

                        check_ftp_write_permission(ftp, target_ip)

                        log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, "w") as logf:
                            logf.write(
                                f"Weak FTP credentials found: {user}:{pwd} (obtained by brute force)")
                        os.system("cp " + log_path + " logs/" + target_ip + "/report/ftp_credentials_found.txt")
                        dump_ftp_contents(ftp, target_ip)
                        ftp.quit()
                        return
                    except ftplib.error_perm:
                        pass
                    except Exception as e:
                        print(f"[!] Error testing {user}:{pwd} - {e}")
        # Test users.txt with default passwords
        if users_custom:
            default_pw_path = "wordlists/misc/ftp-passwords.txt"
            try:
                with open(default_pw_path, 'r') as dpf:
                    pwds_custom = [line.strip() for line in dpf if line.strip()]
                print(
                    f"[*] Loaded {len(pwds_custom)} passwords from {default_pw_path} to combine with custom users")
            except Exception as e:
                print(f"[!] Error reading {default_pw_path}: {e}")
            for user in users_custom:
                for pwd in pwds_custom:
                    try:
                        ftp = ftplib.FTP(target_ip, timeout=5)
                        ftp.login(user, pwd)
                        print(f"[+] Valid credentials found: {user}:{pwd}")

                        check_ftp_write_permission(ftp, target_ip)

                        log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, "w") as logf:
                            logf.write(
                                f"Weak FTP credentials found: {user}:{pwd} (obtained by brute force)")
                        os.system("cp " + log_path + " logs/" + target_ip + "/report/ftp_credentials_found.txt")
                        dump_ftp_contents(ftp, target_ip)
                        ftp.quit()
                        return
                    except ftplib.error_perm:
                        pass
                    except Exception as e:
                        print(f"[!] Error testing {user}:{pwd} - {e}")

        # Try using each user as password (user:user)
        if users_custom:
            print("[*] Trying using each user as password (user:user)...")
            for user in users_custom:
                try:
                    ftp = ftplib.FTP(target_ip, timeout=5)
                    ftp.login(user, user)
                    print(f"[+] Valid credentials found: {user}:{user}")

                    check_ftp_write_permission(ftp, target_ip)

                    log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    with open(log_path, "w") as logf:
                        logf.write(f"Weak FTP credentials found: {user}:{user} (obtained by brute force)")
                    os.system("cp " + log_path + " logs/" + target_ip + "/report/ftp_credentials_found.txt")
                    dump_ftp_contents(ftp, target_ip)
                    ftp.quit()
                    return
                except ftplib.error_perm:
                    pass
                except Exception as e:
                    print(f"[!] Error testing {user}:{user} - {e}")

    print("[-] No valid credentials found using custom lists.")

    # If no results were obtained with the custom lists (or none exist), try the default list
    print("[*] Trying with the default FTP list...")
    default_users_path = "wordlists/misc/ftp-top_default_passlist.txt"
    try:
        with open(default_users_path, 'r') as df:
            combos = [line.strip() for line in df if line.strip()]
        print(f"[*] Loaded {len(combos)} combos from {default_users_path}")
        for combo in combos:
            try:
                user, pwd = combo.split(":", 1)
                ftp = ftplib.FTP(target_ip, timeout=5)
                ftp.login(user, pwd)
                print(f"[+] Valid credentials found: {user}:{pwd}")

                check_ftp_write_permission(ftp, target_ip)

                log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, "w") as logf:
                    logf.write(f"Weak FTP credentials found: {user}:{pwd} (obtained by brute force)")
                os.system("cp " + log_path + " logs/" + target_ip + "/report/ftp_credentials_found.txt")
                dump_ftp_contents(ftp, target_ip)
                ftp.quit()
                return
            except ftplib.error_perm:
                pass
            except Exception as e:
                print(f"[!] Error testing {combo} - {e}")
    except Exception as e:
        print(f"[!] Error reading default list {default_users_path}: {e}")

    print("[-] Elaborate brute force finished without finding valid credentials.")


def dump_ftp_contents(ftp, target_ip, remote_path="/", local_path=None):
    if local_path is None:
        local_path = f"logs/{target_ip}/ftp/dump/"
    os.makedirs(local_path, exist_ok=True)

    try:
        ftp.cwd(remote_path)
        file_list = []
        ftp.retrlines("LIST -a", file_list.append)

        for line in file_list:
            parts = line.split()
            if len(parts) < 4:
                continue  # Skip lines without relevant information

            # If the first column has 10 characters and starts with 'd', '-' or 'l', assume Linux format
            if len(parts[0]) == 10 and parts[0][0] in ["d", "-", "l"]:
                # Linux case
                is_dir = parts[0].startswith("d")
                name = " ".join(parts[8:])
            else:
                # Windows case
                is_dir = parts[2].upper() == "<DIR>"
                name = " ".join(parts[3:])

            if name in [".", ".."]:
                continue

            remote_item_path = f"{remote_path}/{name}".replace("//", "/")
            if is_dir:
                new_local_path = os.path.join(local_path, name)
                os.makedirs(new_local_path, exist_ok=True)
                dump_ftp_contents(ftp, target_ip, remote_item_path, new_local_path)
            else:
                local_file = os.path.join(local_path, name)
                try:
                    with open(local_file, "wb") as f:
                        ftp.retrbinary(f"RETR {remote_item_path}", f.write)
                    print(f"[+] File downloaded: {local_file}")
                except Exception as e:
                    print(f"[!] Error downloading {name}: {e}")
    except Exception as e:
        print(f"[!] Error listing files in {remote_path}: {e}")

def run_ftp(target):
    print("[*] Running FTP module...")
    check_ftp_anonymous(target)
    ftp_searchsploit(target)
    print("[+] FTP module completed.")

# Main test
if __name__ == "__main__":
    target = sys.argv[1]
    run_ftp(target)
