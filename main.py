import subprocess
import re
import sys
import os
import ipaddress

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def initial_scan(target_ip, output_file):
    print(f"[+] Obteniendo puertos abiertos de {target_ip}...")

    # Asegurar que el directorio exista (mkdir -p logs/nmap)
    os.makedirs("logs/nmap", exist_ok=True)

    # Separamos los argumentos en una lista
    command = [
        "nmap",
        "-p-",  # Escanear todos los puertos
        "--open",  # Mostrar solo puertos abiertos
        "--min-rate", "5000",
        "-n",  # No hacer resolución DNS
        "-Pn",  # Tratar todos los hosts como "up"
        target_ip,
        "-oG",
        output_file
    ]

    # Ejecutar nmap con la lista de argumentos
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # Para recibir la salida como string en lugar de bytes
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
            # Buscamos líneas que empiecen con "Host:"
            if line.startswith("Host:"):
                # Ejemplo de línea grepable:
                # "Host: 127.0.0.1 ()   Ports: 21/open/tcp//ftp//, 80/open/tcp//http// ..."

                # Buscamos la sección "Ports: ..."
                match = re.search(r"Ports:\s+(.*)$", line)
                if match:
                    # Obtenemos el texto tras "Ports:"
                    ports_section = match.group(1)

                    # Separamos varios puertos abiertos por coma
                    # Ej: "21/open/tcp//ftp//, 80/open/tcp//http//"
                    ports_info = ports_section.split(",")

                    for p in ports_info:
                        # Cada p puede ser "21/open/tcp//ftp//"
                        p_split = p.split("/")
                        if len(p_split) > 1 and p_split[1] == "open":
                            port_number = p_split[0].strip()
                            ports.append(port_number)
    return ports

def hard_scan(target_ip, ports, output_file):
    print(f"[+] Escaneando puertos en detalle...")

    os.makedirs("logs/nmap", exist_ok=True)

    # Separamos los argumentos en una lista
    command = [
        "nmap",
        "-p" + ",".join(ports),  # Escanear solo los puertos abiertos
        "-sCV",
        target_ip,
        "-oN",
        output_file
    ]

    # Ejecutar nmap con la lista de argumentos
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # Para recibir la salida como string en lugar de bytes
    )

    if result.returncode != 0:
        print("[!] Error ejecutando nmap:")
        print(result.stderr)
    else:
        print(f"[+] Escaneo exhaustivo de puertos finalizado. Resultados en {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 main.py <target_ip>")
        sys.exit(1)

    target = sys.argv[1]
    if not is_valid_ip(target):
        print("[!] Dirección IP no válida. Intente nuevamente.")
        sys.exit(1)
    # 1. Ejecutar Nmap para escaneo de puertos abiertos
    initial_scan(target, "logs/nmap/nmap_results.txt")
    # 2. Extraer puertos
    open_ports = extract_ports("logs/nmap/nmap_results.txt")
    # 3. Escaneo sCV de servicios
    hard_scan(target, open_ports, "logs/nmap/nmap_services.txt")
