import subprocess
import os
import sys
import re

def whatweb(target_ip):
    print(f"[+] Ejecutando whatweb en {target_ip}...")
    tecnologias_file = f"logs/{target_ip}/http/whatweb/tecnologias.txt"
    os.makedirs(f"logs/{target_ip}/http/whatweb", exist_ok=True)

    command = [
        "whatweb",
        target_ip,
        "--log-object", tecnologias_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[!] Error ejecutando whatweb:")
        print(result.stderr)
    else:
        print(f"[+] Análisis whatweb finalizado. Resultados en {tecnologias_file}")

def identificar_cms(target_ip):
    cms_file = f"logs/{target_ip}/http/whatweb/cms.txt"
    tecnologias_file = f"logs/{target_ip}/http/whatweb/tecnologias.txt"
    cms_list = ["WordPress", "Joomla", "Drupal"]
    cms_detectado = "unknown"

    with open(tecnologias_file, 'r') as f:
        lineas = f.readlines()

    for cms in cms_list:
        for linea in lineas:
            if re.search(cms, linea, re.IGNORECASE):
                cms_detectado = cms
                break
        if cms_detectado != "unknown":
            break

    with open(cms_file, 'w') as f:
        f.write(cms_detectado + "\n")

    print(f"[+] CMS detectado: {cms_detectado}. Resultados en {cms_file}")

# Main de prueba
if __name__ == "__main__":
    target = sys.argv[1]
    whatweb(target)
    identificar_cms(target)
