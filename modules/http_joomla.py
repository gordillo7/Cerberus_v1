import os
import subprocess
import sys
import re

def joomscan(target_ip):
    target_clean = target_ip.replace("http://", "").replace("https://", "").rstrip("/")
    output_file = f"logs/{target_clean}/http/joomla/joomscan.txt"
    print(f"[+] Ejecutando joomscan en {target_clean}...")

    # Crear el directorio para guardar los logs si no existe
    os.makedirs(f"logs/{target_clean}/http/joomla", exist_ok=True)

    # Comando básico para joomscan. Ajusta los parámetros según tus necesidades.
    command = [
        "joomscan",
        "-u", target_ip
    ]

    # Ejecutar joomscan y capturar la salida
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Expresión regular para eliminar códigos ANSI
    ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
    clean_output = ansi_escape.sub('', result.stdout)

    # Guardar la salida limpia en el archivo de log
    with open(output_file, "w") as f:
        f.write(clean_output)

    # Verificar si hubo errores en la ejecución
    if result.returncode != 0:
        print(f"[!] Error ejecutando joomscan (código de retorno {result.returncode}):")
        print(result.stderr)
    else:
        print(f"[+] Análisis joomscan finalizado. Resultados en {output_file}")

def run_http_joomla(target):
    joomscan(target)

# Main de prueba
if __name__ == "__main__":
    target = sys.argv[1]
    run_http_joomla(target)