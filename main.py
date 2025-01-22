import subprocess
import json
import re
import sys

def run_nmap(target_ip, output_file):

    print(f"[+] Escaneando puertos abiertos de {target_ip}...")
    command = "sudo nmap -p- -sS --open --min-rate 5000 -n -Pn " + target_ip + " -oG " + output_file
    
    # Ejecutar nmap
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print(f"[+] Escaneo de puertos finalizado. Resultados en {output_file}")


def parse_nmap_grepable(file_path):
    ip_port_map = {}
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("Host:"):
                parts = line.split()
                ip = parts[1]
                # Buscar la sección "Ports: ..."
                ports_section = re.search(r"Ports: (.*)$", line)
                if ports_section:
                    ports = ports_section.group(1).split(",")
                    open_ports = []
                    for p in ports:
                        # Ejemplo de puerto en grepable: "21/open/tcp//ftp//"
                        p_info = p.split("/")
                        if len(p_info) > 1 and p_info[1] == "open":
                            port_number = p_info[0]
                            service = p_info[4] if len(p_info) > 4 else ""
                            open_ports.append({
                                "port": port_number,
                                "service": service
                            })
                    if open_ports:
                        ip_port_map[ip] = open_ports
    return ip_port_map

if __name__ == "__main__":
    # Recibir la ip objetivo por parametro
    if len(sys.argv) != 2:
        print("Uso: python main.py <target_ip>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    # 1. Ejecutar Nmap para escaneo de puertos abiertos
    run_nmap(target, "logs/nmap/nmap_results.txt")
    
    # 2. Parsear resultados
    results = parse_nmap_grepable("logs/nmap/nmap_results.txt")

    print(results)

    """
    # 3. Almacenar (podrías guardarlo en JSON, por ejemplo)
    with open("nmap_parsed.json", "w") as out:
        json.dump(results, out, indent=4)
    
    print("[+] Estructura parseada de Nmap:")
    print(json.dumps(results, indent=4))
    """