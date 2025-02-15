import json
import sys
import os
import subprocess
import requests
import shutil

def extract_vulnerable_plugins(target_ip):
    input_file = f"logs/{target_ip}/http/wordpress/wpscan.txt"
    output_file = f"logs/{target_ip}/http/wordpress/vulnerable_plugins.txt"

    # Abrir y parsear el JSON de entrada
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)  # Carga el contenido como diccionario

    vulnerable_plugins = []

    # 'data["plugins"]' contiene un diccionario de plugins,
    # donde cada key es el nombre del plugin, y el value su info.
    for plugin_name, plugin_info in data.get("plugins", {}).items():
        for vulnerability in plugin_info.get("vulnerabilities", []):
            cves = vulnerability.get("references", {}).get("cve", [])
            if cves:
                vulnerable_plugins.append({
                    "plugin_name": plugin_name,
                    "cves": cves
                })

    if vulnerable_plugins:
        print(f"[+] {len(vulnerable_plugins)} vulnerabilides en plugins encontradas. Reportado en {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            for plugin in vulnerable_plugins:
                f.write(f"Plugin: {plugin['plugin_name']}\n")
                f.write("CVE:\n")
                for cve in plugin['cves']:
                    f.write(f"  - {cve}\n")
                f.write("\n")

        shutil.copy(output_file, f"logs/{target_ip}/reporte/wordpress_vulnerable_plugins.txt")
    else:
        print("[!] No se encontraron plugins vulnerables en Wordpress")

def parse_vulnerable_plugins(file_path):
    """
    Parsea el archivo vulnerable_plugins.txt y devuelve una lista de diccionarios con el formato:
      { "plugin_name": <nombre>, "cves": [<CVE1>, <CVE2>, ...] }
    """
    plugins = []
    current_plugin = None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("Plugin:"):
                    # Comienza una nueva entrada de plugin
                    plugin_name = line.split(":", 1)[1].strip()
                    current_plugin = {"plugin_name": plugin_name, "cves": []}
                    plugins.append(current_plugin)
                elif line.startswith("CVE:"):
                    # Línea informativa, se ignora
                    continue
                elif line.startswith("-"):
                    # Se espera que sea una línea con el CVE, por ejemplo: "- 2015-6668"
                    cve = line.strip("- ").strip()
                    if current_plugin is not None and cve:
                        current_plugin["cves"].append(cve)
                # Se pueden ignorar líneas en blanco u otras
        return plugins
    except Exception as e:
        print(f"[!] Error al parsear {file_path}: {e}")
        return []

def search_exploits_on_github(cve_id, max_repos=10):
    """
    Realiza una búsqueda en GitHub para repositorios que contengan el CVE y la palabra 'exploit'
    Se limita la búsqueda a 'max_repos' resultados.
    """
    url = f"https://api.github.com/search/repositories?q={cve_id}&per_page={max_repos}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            if items:
                print(f"[+] Se encontraron {len(items)} repositorios para el CVE {cve_id}.")
                return items
            else:
                print(f"[!] No se encontraron repositorios para el CVE {cve_id}.")
                return []
        else:
            print(f"[!] Error en la búsqueda de GitHub para {cve_id}: Código {response.status_code}")
            return []
    except Exception as e:
        print(f"[!] Excepción durante la búsqueda en GitHub para {cve_id}: {e}")
        return []

def clone_repository(repo_url, dest_dir):
    """
    Clona el repositorio dado en el directorio destino.
    """
    try:
        result = subprocess.run(["git", "clone", repo_url, dest_dir], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[+] Repositorio clonado desde {repo_url}")
            return True
        else:
            print(f"[!] Error al clonar {repo_url}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[!] Excepción al clonar {repo_url}: {e}")
        return False

def find_python_file(directory):
    """
    Recorre el directorio y devuelve la ruta del primer archivo .py que encuentre.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                return os.path.join(root, file)
    return None

"""
def run_python_exploit(exploit_path, target_ip):
    try:
        print(f"[+] Ejecutando el exploit {exploit_path} contra {target_ip}...")
        result = subprocess.run(["python", exploit_path, target_ip], capture_output=True, text=True)
        print("[+] Salida del exploit:")
        print(result.stdout)
        if result.stderr:
            print("[!] Errores en la ejecución del exploit:")
            print(result.stderr)
    except Exception as e:
        print(f"[!] Excepción al ejecutar el exploit {exploit_path}: {e}")
"""

def process_cve(cve, target_ip, max_repos=10):
    """
    Busca exploits en GitHub para el CVE dado, clona el repositorio y, en caso de encontrar un archivo .py, lo ejecuta.
    Si en ninguno de los repositorios (hasta max_repos) se encuentra un archivo Python, informa que no se puede verificar la vulnerabilidad.
    """
    repos = search_exploits_on_github(cve, max_repos)
    if not repos:
        print(f"[!] No se pudo verificar la vulnerabilidad {cve}: no se encontró ningún exploit en GitHub.")
        return

    # Ordenamos los repositorios por popularidad (stargazers_count) de forma descendente
    sorted_repos = sorted(repos, key=lambda repo: repo.get("stargazers_count", 0), reverse=True)

    exploit_found = False
    for repo in sorted_repos:
        repo_url = repo.get("clone_url")
        if not repo_url:
            continue

        exp_dir = f"logs/{target_ip}/http/wordpress/cve_exploits/{cve}/{repo.get('full_name').replace('/', '_')}"
        print(f"[*] Clonando {repo_url} en {exp_dir}...")
        if clone_repository(repo_url, exp_dir):
            # Borrar el .git del repositorio clonado
            shutil.rmtree(os.path.join(exp_dir, ".git"))
            # Buscar un archivo Python en el repositorio clonado
            python_file = find_python_file(exp_dir)
            if python_file:
                #run_python_exploit(python_file, target_ip)
                exploit_found = True
                break  # Se encontró y lanzó un exploit; salimos del bucle
            else:
                print(f"[!] No se encontró archivo Python en el repositorio {repo.get('full_name')}.")
                shutil.rmtree(exp_dir)
        else:
            shutil.rmtree(exp_dir)

    if not exploit_found:
        print(
            f"[!] No se pudo verificar la vulnerabilidad {cve}: no se encontró un exploit Python en {max_repos} repositorios.")

def wordpress_plugins(target_ip):
    # Ruta del archivo vulnerable_plugins.txt
    file_path = f"logs/{target_ip}/http/wordpress/vulnerable_plugins.txt"
    if not os.path.exists(file_path):
        print(f"[!] El archivo {file_path} no existe.")
        return

    # Parseamos el archivo para obtener la lista de plugins y sus CVEs
    plugins = parse_vulnerable_plugins(file_path)
    if not plugins:
        print("[!] No se encontraron plugins vulnerables en el archivo.")
        return

    # Para cada plugin y cada uno de sus CVEs, se intenta buscar y lanzar el exploit
    for plugin in plugins:
        plugin_name = plugin.get("plugin_name")
        cves = plugin.get("cves", [])
        for cve in cves:
            print(f"\n[*] Procesando CVE {cve} para el plugin '{plugin_name}'")
            process_cve(cve, target_ip, max_repos=10)

def run_http_wordpress_plugins(target_ip):
    extract_vulnerable_plugins(target_ip)
    wordpress_plugins(target_ip)

# Main de prueba
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_wordpress_plugins(target)