import os
import sys
import subprocess
import json

def generate_nuclei_report(target):
    # Define the paths for the directories and files
    webscan_dir = os.path.join("logs", target, "http", "webscan")
    results_file = os.path.join(webscan_dir, "nuclei_results.json")
    report_dir = os.path.join("logs", target, "report")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, "nuclei_webscan.txt")

    # Check if the results file exists
    if not os.path.exists(results_file):
        print(f"[-] The results file was not found at {results_file}")
        return

    # Load the JSON content from the results file
    try:
        with open(results_file, "r", encoding="utf-8") as f:
            results = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[-] Error decoding the JSON: {e}")
        return

    if not results:
        print("[-] No vulnerabilities found in the Nuclei results.")
        return

    # Build the report with visual formatting
    report_lines = []
    divider = "=" * 80
    for entry in results:
        info = entry.get("info", {})
        name = info.get("name", "N/A")
        severity = info.get("severity", "N/A")
        description = info.get("description", "N/A")
        impact = info.get("impact", "N/A")
        remediation = info.get("remediation", "N/A")
        references = info.get("reference", [])
        ref_text = "\n".join(f"- {ref}" for ref in references) if references else "N/A"
        classification = info.get("classification", {})
        cve_ids = classification.get("cve-id", [])
        cve_text = ", ".join(cve_ids) if cve_ids else "N/A"
        cwe_ids = classification.get("cwe-id", [])
        cwe_text = ", ".join(cwe_ids) if cwe_ids else "N/A"
        host = entry.get("host", "N/A")
        port = entry.get("port", "N/A")

        vulnerability_text = f"""{divider}
Vulnerability: {name}
Severity: {severity}
CVE: {cve_text}
CWE: {cwe_text}
Host: {host} - Port: {port}

Description:
{description}

Impact:
{impact}

Remediation:
{remediation}

References:
{ref_text}
{divider}
"""
        report_lines.append(vulnerability_text)

    # Write the formatted content to the report file
    report_content = "\n".join(report_lines)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"[+] Nuclei report generated at: {report_file}")


def run_webscan(target):
    """subdomains = []
    subdomains_file = os.path.join("logs", target, "http", "subdomain", "subdomains.txt")
    if not os.path.exists(subdomains_file):
        print(f"[-] Subdomains file not found")
    else:
        print("[*] Reading subdomains...")
        with open(subdomains_file, "r", encoding="utf-8") as f:
            subdomains = [line.strip() for line in f if line.strip()]

    # Add target domain if not present
    if target not in subdomains:
        subdomains.append(target)"""

    # Create directory for webscan results
    output_dir = os.path.join("logs", target, "http", "webscan")
    os.makedirs(output_dir, exist_ok=True)

    """
    # Create temporary file with complete list of subdomains
    temp_list_file = os.path.join(output_dir, "temp_subdomains.txt")
    with open(temp_list_file, "w", encoding="utf-8") as f:
        for sub in subdomains:
            f.write(sub + "\n")
    """
    # Build nuclei command
    nuclei_results_file = os.path.join(output_dir, "nuclei_results.json")
    """cmd = [
        "nuclei",
        "-l", temp_list_file,
        "-s", "low,medium,high,critical,unknown",
        "-je", nuclei_results_file
    ]"""
    cmd = [
        "nuclei",
        "-u", target,
        "-s", "low,medium,high,critical,unknown",
        "-je", nuclei_results_file
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
        print(f"[+] Web scan results saved to {nuclei_results_file}")
    except Exception as e:
        print(f"[-] Error running Nuclei: {e}")

    """# Remove temporary file
    try:
        os.remove(temp_list_file)
    except Exception as e:
        print(f"[-] Error removing temporary file: {e}")"""

def run_http_webscan(target):
    print(f"[*] Starting web scan module")
    run_webscan(target)
    generate_nuclei_report(target)
    print("[+] Web scan module completed.")

if __name__ == "__main__":
    target = sys.argv[1]
    run_http_webscan(target)