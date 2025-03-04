import subprocess
from pathlib import Path
import sys

def run_dnsrecon(target):
    # Create the directory logs/target/dns
    output_dir = Path("logs") / target / "dns"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define the output file
    output_file = output_dir / "dns_recon.txt"

    # Build the command and run dnsrecon with the axfr type
    command = ["dnsrecon", "-d", target, "-t", "axfr"]

    # Execute the command, redirecting stdout to the file
    with output_file.open("w") as f:
        result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

    # Check if there were errors running dnsrecon
    if result.returncode != 0:
        print("[!] Error running dnsrecon:")
        print(result.stderr)
    else:
        print(f"[+] dnsrecon completed successfully. Results saved in {output_file}")

def parse_dnsrecon_log(target):
    log_file = Path("logs") / target / "dns" / "dns_recon.txt"
    if not log_file.exists():
        print(f"[!] Log file not found: {log_file}")
        return None

    with log_file.open("r") as f:
        lines = f.readlines()

    # Initialize lists for each type of record
    mx_records = []
    txt_records = []

    # Iterate through each line and extract the relevant information
    for line in lines:
        line = line.strip()
        # Process only lines that start with "[+]" or "[*]"
        if line.startswith("[+]") or line.startswith("[*]"):
            if "MX" in line:
                mx_records.append(line)
            # TXT records
            if "TXT" in line:
                txt_records.append(line)

    return {
        "mx": mx_records,
        "txt": txt_records
    }

def generate_dns_report(target):
    parsed_data = parse_dnsrecon_log(target)
    if parsed_data is None:
        print("[!] No data available to generate the report.")
        return

    report_lines = []
    report_lines.append("--DNS Recon Report--\n")

    # MX records
    report_lines.append("MX records found:")
    if parsed_data["mx"]:
        for rec in parsed_data["mx"]:
            report_lines.append("  " + rec)
    else:
        report_lines.append("  No MX records found.")

    # TXT records
    report_lines.append("\nTXT records found:")
    if parsed_data["txt"]:
        for rec in parsed_data["txt"]:
            report_lines.append("  " + rec)
    else:
        report_lines.append("  No TXT records found.")

    report_dir = Path("logs") / target / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "dns_recon.txt"
    with report_file.open("w") as f:
        f.write("\n".join(report_lines))

    print(f"[+] DNS Recon report generated at {report_file}")

def run_dns_recon(target):
    run_dnsrecon(target)
    generate_dns_report(target)

if __name__ == "__main__":
    target = sys.argv[1]
    run_dns_recon(target)
