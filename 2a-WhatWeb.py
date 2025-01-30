import subprocess
import os
import sys
import re

def whatweb(target_ip, output_file):
    print(f"[+] Ejecutando whatweb en {target_ip}...")
    os.makedirs(f"logs/{target_ip}/http/whatweb", exist_ok=True)

    command = [
        "whatweb",
        target_ip,
        "--log-object", output_file
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
        print(f"[+] Análisis whatweb finalizado. Resultados en {output_file}")

def identificar_cms(archivo_tecnologias, archivo_cms):
    cms_list = ["WordPress", "Joomla", "Drupal", "Magento", "Shopify"]
    cms_detectado = "unknown"

    with open(archivo_tecnologias, 'r') as f:
        lineas = f.readlines()

    for cms in cms_list:
        for linea in lineas:
            if re.search(cms, linea, re.IGNORECASE):
                cms_detectado = cms
                break
        if cms_detectado != "unknown":
            break

    with open(archivo_cms, 'w') as f:
        f.write(cms_detectado + "\n")

    print(f"[+] CMS detectado: {cms_detectado}. Resultados en {archivo_cms}")

# Main de prueba
if __name__ == "__main__":
    target = sys.argv[1]
    tecnologias_file = f"logs/{target}/http/whatweb/tecnologias.txt"
    cms_file = f"logs/{target}/http/whatweb/cms.txt"
    whatweb(target, tecnologias_file)
    identificar_cms(tecnologias_file, cms_file)
