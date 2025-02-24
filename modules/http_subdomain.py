import sys
import os
import subprocess
import httpx

def enumerate_subdomains(domain):
    command = f"subfinder -d {domain} -silent"
    print(f"[+] Ejecutando comando: {command}")
    try:
        result = subprocess.run(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
        )
        if result.returncode != 0:
            print(f"[!] Error en comando subfinder: {result.stderr}")
            return []
        subdomains_raw = result.stdout.strip().splitlines()
    except Exception as e:
        print(f"[!] Excepción durante la ejecución de subfinder: {e}")
        return []
    valid_subdomains = []
    for sub in subdomains_raw:
        url = sub if sub.startswith("http://") or sub.startswith("https://") else f"http://{sub}"
        try:
            response = httpx.get(url, timeout=5)
            if 200 <= response.status_code < 400:
                valid_subdomains.append(sub)
                print(f"[+] Subdominio válido: {sub}")
            else:
                print(f"[-] {sub} respondió con el código de estado {response.status_code}")
        except httpx.RequestError:
            print(f"[-] {sub} no pudo ser alcanzado")

    return sorted(set(valid_subdomains))


def save_subdomains(domain, subdomains):
    output_dir = os.path.join("logs", domain, "http", "subdomain")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "subdomains.txt")
    with open(output_file, "w") as f:
        f.write(f"Se encontraron {len(subdomains)} subdominios para {domain}\n")
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