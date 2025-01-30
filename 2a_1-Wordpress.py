import subprocess
import os
import sys

def run_wpscan(target_ip, output_file):
    print(f"[+] Ejecutando wpscan en {target_ip}...")
    os.makedirs(f"logs/{target_ip}/http/wpscan", exist_ok=True)

    command = [
        "wpscan",
        "--url", target_ip,
        "--output", output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[!] Error ejecutando wpscan:")
        print(result.stderr)
    else:
        print(f"[+] Análisis wpscan finalizado. Resultados en {output_file}")

# Main de prueba
if __name__ == "__main__":
    target = sys.argv[1]
    run_wpscan(target, f"logs/{target}/http/wpscan/wpscan.txt")
