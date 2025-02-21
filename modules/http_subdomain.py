import sys
import os
import requests
from bs4 import BeautifulSoup

def enumerate_subdomains(domain):
    query = "%25." + domain
    url = f"https://crt.sh/?q={query}&exclude=expired"
    print(f"[+] Obteniendo detalles de crt.sh para el dominio: {domain}")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Error al obtener datos de crt.sh: {e}")
        return []

    print("[+] Extrayendo subdominios de la respuesta")
    soup = BeautifulSoup(response.content, "html.parser")
    subdomains = []
    # Se asume que la columna 5 de la tabla contiene los dominios
    for cell in soup.select("table tr td:nth-of-type(5)"):
        text = cell.get_text().strip()
        # Se ignoran las entradas con asterisco
        if "*" not in text:
            subdomains.append(text)

    # Elimina duplicados y ordena la lista
    unique_subdomains = sorted(set(subdomains))
    return unique_subdomains


def save_subdomains(domain, subdomains):
    output_dir = os.path.join("logs", domain, "http", "subdomain")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "subdomains.txt")

    with open(output_file, "w") as f:
        f.write(f"Se han enumerado {len(subdomains)} subdominios para {domain}\n")
        for subdomain in subdomains:
            f.write(subdomain + "\n")

    os.system(f"cp {output_file} logs/{domain}/reporte/http_subdomains.txt")
    print(f"[+] Subdominios guardados en: {output_file}")


def subdomain(domain):
    subdomains = enumerate_subdomains(domain)
    if subdomains:
        print(f"[+] Se encontraron {len(subdomains)} subdominios")
        save_subdomains(domain, subdomains)
    else:
        print("[!] No se encontraron subdominios.")

def run_http_subdomain(domain):
    subdomain(domain)

if __name__ == "__main__":
    domain = sys.argv[1]
    run_http_subdomain(domain)
