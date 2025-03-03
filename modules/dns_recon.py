import subprocess
from pathlib import Path
import sys


def run_dnsrecon(target):
    # Create the directory logs/target/dns
    output_dir = Path("logs") / target / "dns"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define the output file path
    output_file = output_dir / "dns_recon.txt"

    # Build the command and run dnsrecon with the axfr type
    command = ["dnsrecon", "-d", target, "-t", "axfr"]

    # Open the output file and redirect the stdout of the command to it
    with output_file.open("w") as f:
        result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

    # Check for errors in the execution of dnsrecon
    if result.returncode != 0:
        print("[!] Error running dnsrecon:")
        print(result.stderr)
    else:
        print(f"[+] dnsrecon completed successfully. Results saved in {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: dns_recon.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    run_dnsrecon(target)