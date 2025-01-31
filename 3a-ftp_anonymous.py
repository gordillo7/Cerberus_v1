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
    except Exception as e:
        print(f"[!] Error al conectar con FTP: {e}")

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
            file_type = parts[0][0]  # Primer carácter indica tipo (d=directorio, -=archivo)

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
