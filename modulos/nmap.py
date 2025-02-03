import subprocess
import re
import sys
import os

def initial_scan(target_ip, output_file):
    print(f"[+] Obteniendo puertos abiertos de {target_ip}...")
    os.makedirs(f"../logs/{target_ip}/nmap", exist_ok=True)

    command = [
        "nmap",
        "-p-",
        "--open",
        "--min-rate", "5000",
        "-n",
        "-Pn",
        target_ip,
        "-oG",
        output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[!] Error ejecutando nmap:")
        print(result.stderr)
    else:
        print(f"[+] Escaneo inicial finalizado. Resultados en {output_file}")

def extract_ports(file_path):
    ports = []
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("Host:"):
                match = re.search(r"Ports:\s+(.*)$", line)
                if match:
                    ports_section = match.group(1)
                    ports_info = ports_section.split(",")

                    for p in ports_info:
                        p_split = p.split("/")
                        if len(p_split) > 1 and p_split[1] == "open":
                            port_number = p_split[0].strip()
                            ports.append(port_number)
    return ports

def hard_scan(target_ip, ports, output_file):
    print(f"[+] Escaneando puertos en detalle...")
    os.makedirs(f"../logs/{target_ip}/nmap", exist_ok=True)

    command = [
        "nmap",
        "-p" + ",".join(ports),
        "-sV",
        "-Pn",
        target_ip,
        "-oN",
        output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[!] Error ejecutando nmap:")
        print(result.stderr)

def limpiar_reporte_nmap(archivo_reporte, archivo_salida):
    con_linea_interes = False

    with open(archivo_reporte, 'r') as f:
        lineas = f.readlines()

    with open(archivo_salida, 'w') as f:
        for linea in lineas:
            if re.search(r"PORT\s+STATE\s+SERVICE\s+VERSION", linea):
                con_linea_interes = True
            if con_linea_interes:
                if re.search(r"^\d+/tcp\s+open\s", linea) or re.search(r"PORT\s+STATE\s+SERVICE\s+VERSION", linea):
                    f.write(linea)

    print(f"[+] Escaneo exhaustivo de puertos finalizado. Resultados en {archivo_salida}")
    os.remove(archivo_reporte)

def run_nmap():
    target = sys.argv[1]
    # 1. Ejecutar Nmap para escaneo de puertos abiertos
    initial_scan(target, f"../logs/{target}/nmap/initial_scan.txt")
    # 2. Extraer puertos
    open_ports = extract_ports(f"../logs/{target}/nmap/initial_scan.txt")
    # 3. Escaneo sCV de servicios
    hard_scan(target, open_ports, f"../logs/{target}/nmap/ports_services_versions_temp.txt")
    limpiar_reporte_nmap(f"../logs/{target}/nmap/ports_services_versions_temp.txt", "../logs/" + target + "/nmap/ports_services_versions.txt")

#Main de prueba
if __name__ == "__main__":
    run_nmap()
