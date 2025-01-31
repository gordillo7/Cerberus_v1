import subprocess
import os
import sys
import json
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

def run_wpscan(target_ip, output_file):
    print(f"[+] Ejecutando wpscan en {target_ip}...")
    os.makedirs(f"logs/{target_ip}/http/wpscan", exist_ok=True)

    command = [
        "wpscan",
        "--url", target_ip,
        "-e", "vp,vt,u",
        "--format", "json",
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

# Función para escribir en un archivo sin sobrescribir
def write_usernames(output_file, usernames):
    existing_usernames = set()
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Leer los nombres de usuario existentes
    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            for line in file:
                existing_usernames.add(line.strip())

    # Añadir los nuevos nombres de usuario
    with open(output_file, 'a') as file:
        for username in usernames:
            if username not in existing_usernames:
                file.write(username + '\n')


def extract_usernames(input_file, output_f1, output_f2):
    usernames = set()

    # Abrir y parsear el JSON de entrada
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)  # Carga el contenido como diccionario

    # 'data["users"]' contiene un diccionario de usuarios,
    # donde cada key es el nombre de usuario, y el value su info.
    for username, user_info in data.get("users", {}).items():
        # Verificamos si fueron encontrados por "Wp Json Api (Aggressive Detection)"
        if user_info.get("found_by") == "Wp Json Api (Aggressive Detection)":
            usernames.add(username)

    if usernames:
        print(f"[+] {len(usernames)} nombres de usuario encontrados en Wordpress. Reportados en {output_f1} y {output_f2}")
        write_usernames(output_f1, usernames)
        write_usernames(output_f2, usernames)
    else:
        print("[!] No se encontraron nombres de usuario en Wordpress")

def is_possible_directory(url):
    """
    Intenta detectar si la URL apunta a un directorio o a un fichero.
    1) HEAD: si es 403/401 -> es muy probable que sea un directorio (acceso denegado).
    2) Si 200 y 'text/html' en Content-Type, hacemos GET para ver si parece un 'Index of...'.
    3) En cualquier otro caso, lo tratamos como fichero.
    """
    try:
        # Primero, HEAD:
        r = requests.head(url, allow_redirects=True, timeout=5)

        # 403 o 401 (Forbidden/Unauthorized) => Posiblemente un directorio sin permiso de listing
        if r.status_code in [401, 403]:
            return True

        # 200 + text/html => Podría ser un directorio con listado habilitado o un HTML cualquiera
        if r.status_code == 200:
            ctype = r.headers.get('Content-Type', '').lower()
            if 'text/html' in ctype:
                # Hacemos GET para comprobar si se ve algo tipo "Index of /"
                rr = requests.get(url, timeout=5)
                if "Index of /" in rr.text or "Index of" in rr.text or "Parent Directory" in rr.text:
                    return True
    except:
        # Si la petición falla, asumimos que NO es directorio (para no romper el flujo).
        pass

    return False

def dump_directory_listing(url, output_dir, visited_indexes=None, visited_files=None):
    """
    Descarga recursivamente el contenido de un índice de directorio.
    - visited_indexes: set con las URLs de páginas de índice ya procesadas.
    - visited_files: set con las URLs de archivos ya descargados.
    """
    if visited_indexes is None:
        visited_indexes = set()
    if visited_files is None:
        visited_files = set()

    # Si ya procesamos este índice (página con "Index of..."), no lo parseamos de nuevo
    if url in visited_indexes:
        return
    visited_indexes.add(url)

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')

        for link in links:
            href = link.get('href')
            # Evitamos enlaces vacíos o enlaces especiales como '../'
            if not href or href in ['/', '../']:
                continue

            full_url = urljoin(url, href)
            path = urlparse(full_url).path.lstrip('/')
            local_path = os.path.join(output_dir, path)

            # Si termina en '/', asumimos que es un subdirectorio
            if href.endswith('/'):
                # Creamos la carpeta local
                os.makedirs(local_path, exist_ok=True)
                # Recursión sobre ese subdirectorio
                dump_directory_listing(
                    full_url,
                    output_dir,
                    visited_indexes,
                    visited_files
                )
            else:
                # Si no termina en '/', comprobamos si es directorio vía heurística
                if is_possible_directory(full_url):
                    os.makedirs(local_path, exist_ok=True)
                    dump_directory_listing(
                        full_url,
                        output_dir,
                        visited_indexes,
                        visited_files
                    )
                else:
                    # Es un archivo
                    # Evitamos descargar si ya lo descargamos antes
                    if full_url in visited_files:
                        continue
                    visited_files.add(full_url)

                    try:
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)
                        file_response = requests.get(full_url)
                        file_response.raise_for_status()

                        with open(local_path, 'wb') as file:
                            file.write(file_response.content)
                        print(f"[+] Archivo guardado: {local_path}")

                    except IsADirectoryError:
                        # A veces pasa que el servidor lo trata como directorio
                        print(f"[!] {local_path} resultó ser un directorio. Recursionamos.")
                        os.makedirs(local_path, exist_ok=True)
                        dump_directory_listing(
                            full_url,
                            output_dir,
                            visited_indexes,
                            visited_files
                        )
                    except Exception as e:
                        print(f"[!] Error descargando {full_url}: {e}")

    except requests.RequestException as e:
        print(f"[!] Error al dumpear el contenido del directorio en {url}: {e}")

def process_directory_listings(input_file, output_dir):
    with open(input_file, 'r') as file:
        data = json.load(file)
        for finding in data.get("interesting_findings", []):
            # si contiene "has listing enabled" en el campo "to_s", dumpeamos
            if "has listing enabled" in finding.get("to_s", ""):
                dump_directory_listing(finding["url"], output_dir)
                print(f"[+] Dumpeo de directorios guardado en {output_dir}")

# Main de prueba
if __name__ == "__main__":
    target = sys.argv[1]
    output_file1 = "logs/10.10.143.44/http/wpscan/users.txt"
    output_file2 = "wordlists/10.10.143.44/users.txt"

    run_wpscan(target, f"logs/{target}/http/wpscan/wpscan.txt")
    extract_usernames(
        f"logs/{target}/http/wpscan/wpscan.txt",
        output_file1,
        output_file2
    )
    process_directory_listings(
        f"logs/{target}/http/wpscan/wpscan.txt",
        f"logs/{target}/http/wpscan/directory_listing_dump"
    )
