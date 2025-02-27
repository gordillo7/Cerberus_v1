import json
import sys
import os
import subprocess
import requests

def extract_vulnerable_plugins(target_ip):
    input_file = f"logs/{target_ip}/http/wordpress/wpscan.txt"
    output_file = f"logs/{target_ip}/http/wordpress/vulnerable_plugins.txt"

    # Open and parse the input JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)  # Load the content as a dictionary

    vulnerable_plugins = []

    # 'data["plugins"]' contains a dictionary of plugins,
    # where each key is the plugin name and the value is its info.
    for plugin_name, plugin_info in data.get("plugins", {}).items():
        for vulnerability in plugin_info.get("vulnerabilities", []):
            cves = vulnerability.get("references", {}).get("cve", [])
            if cves:
                vulnerable_plugins.append({
                    "plugin_name": plugin_name,
                    "cves": cves
                })

    if vulnerable_plugins:
        print(f"[+] {len(vulnerable_plugins)} vulnerabilities in plugins found. Reported in {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            for plugin in vulnerable_plugins:
                f.write(f"Plugin: {plugin['plugin_name']}\n")
                f.write("CVE:\n")
                for cve in plugin['cves']:
                    f.write(f"  - {cve}\n")
                f.write("\n")

        os.system(f"cp {output_file} logs/{target_ip}/report/wordpress_vulnerable_plugins.txt")
    else:
        print("[!] No vulnerable plugins were found in WordPress")

def parse_vulnerable_plugins(file_path):
    """
    Parses the vulnerable_plugins.txt file and returns a list of dictionaries in the format:
      { "plugin_name": <name>, "cves": [<CVE1>, <CVE2>, ...] }
    """
    plugins = []
    current_plugin = None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("Plugin:"):
                    # Start a new plugin entry
                    plugin_name = line.split(":", 1)[1].strip()
                    current_plugin = {"plugin_name": plugin_name, "cves": []}
                    plugins.append(current_plugin)
                elif line.startswith("CVE:"):
                    # Informational line, ignore it
                    continue
                elif line.startswith("-"):
                    # Expected to be a line with the CVE, e.g.: "- 2015-6668"
                    cve = line.strip("- ").strip()
                    if current_plugin is not None and cve:
                        current_plugin["cves"].append(cve)
                # Blank or other lines can be ignored
        return plugins
    except Exception as e:
        print(f"[!] Error parsing {file_path}: {e}")
        return []

def search_exploits_on_github(cve_id, max_repos=10):
    """
    Searches GitHub for repositories containing the CVE and the word 'exploit'
    Limited to 'max_repos' results.
    """
    url = f"https://api.github.com/search/repositories?q={cve_id}&per_page={max_repos}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            if items:
                print(f"[+] Found {len(items)} repositories for CVE {cve_id}.")
                return items
            else:
                print(f"[!] No repositories found for CVE {cve_id}.")
                return []
        else:
            print(f"[!] Error searching GitHub for {cve_id}: Code {response.status_code}")
            return []
    except Exception as e:
        print(f"[!] Exception during GitHub search for {cve_id}: {e}")
        return []

def clone_repository(repo_url, dest_dir):
    """
    Clones the given repository into the destination directory.
    """
    try:
        result = subprocess.run(["git", "clone", repo_url, dest_dir], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[+] Repository cloned from {repo_url}")
            return True
        else:
            print(f"[!] Error cloning {repo_url}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[!] Exception while cloning {repo_url}: {e}")
        return False

def find_python_file(directory):
    """
    Traverses the directory and returns the path of the first .py file found.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                return os.path.join(root, file)
    return None

"""
def run_python_exploit(exploit_path, target_ip):
    try:
        print(f"[+] Running exploit {exploit_path} against {target_ip}...")
        result = subprocess.run(["python", exploit_path, target_ip], capture_output=True, text=True)
        print("[+] Exploit output:")
        print(result.stdout)
        if result.stderr:
            print("[!] Errors during exploit execution:")
            print(result.stderr)
    except Exception as e:
        print(f"[!] Exception while running exploit {exploit_path}: {e}")
"""

def process_cve(cve, target_ip, max_repos=10):
    """
    Searches for exploits on GitHub for the given CVE, clones the repository, and if a .py file is found, runs it.
    If no Python file is found in any of the repositories (up to max_repos), reports that the vulnerability cannot be verified.
    """
    repos = search_exploits_on_github(cve, max_repos)
    if not repos:
        print(f"[!] Could not verify vulnerability {cve}: no exploit found on GitHub.")
        return

    # Sort repositories by popularity (stargazers_count) in descending order
    sorted_repos = sorted(repos, key=lambda repo: repo.get("stargazers_count", 0), reverse=True)

    exploit_found = False
    for repo in sorted_repos:
        repo_url = repo.get("clone_url")
        if not repo_url:
            continue

        exp_dir = f"logs/{target_ip}/http/wordpress/cve_exploits/{cve}/{repo.get('full_name').replace('/', '_')}"
        print(f"[*] Cloning {repo_url} into {exp_dir}...")
        if clone_repository(repo_url, exp_dir):
            # Remove the .git folder from the cloned repository
            os.system(f"rm -rf {exp_dir}/.git")
            # Search for a Python file in the cloned repository
            python_file = find_python_file(exp_dir)
            if python_file:
                #run_python_exploit(python_file, target_ip)
                exploit_found = True
                break  # An exploit was found and launched; exit the loop
            else:
                print(f"[!] No Python file found in repository {repo.get('full_name')}.")
                os.system(f"rm -rf logs/{target_ip}/http/wordpress/cve_exploits/{cve}")
        else:
            os.system(f"rm -rf logs/{target_ip}/http/wordpress/cve_exploits/{cve}")

    if not exploit_found:
        print(f"[!] Could not verify vulnerability {cve}: no Python exploit found in {max_repos} repositories.")

def wordpress_plugins(target_ip):
    # Path of the vulnerable_plugins.txt file
    file_path = f"logs/{target_ip}/http/wordpress/vulnerable_plugins.txt"
    if not os.path.exists(file_path):
        #print(f"[!] The file {file_path} does not exist.")
        return

    # Parse the file to obtain the list of plugins and their CVEs
    plugins = parse_vulnerable_plugins(file_path)
    if not plugins:
        print("[!] No vulnerable plugins were found in the file.")
        return

    # For each plugin and each of its CVEs, attempt to search and launch the exploit
    for plugin in plugins:
        plugin_name = plugin.get("plugin_name")
        cves = plugin.get("cves", [])
        for cve in cves:
            print(f"\n[*] Processing CVE {cve} for plugin '{plugin_name}'")
            process_cve(cve, target_ip, max_repos=10)

def run_http_wordpress_plugins(target_ip):
    extract_vulnerable_plugins(target_ip)
    wordpress_plugins(target_ip)

# Test main
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_wordpress_plugins(target)
