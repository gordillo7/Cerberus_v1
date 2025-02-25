import os
import sys
import time
from modules.ftp import run_ftp
from modules.generar_reporte import run_generar_reporte
from modules.http_joomla import run_http_joomla
from modules.http_screenshot import run_http_screenshot
from modules.http_subdomain import run_http_subdomain
from modules.http_whatweb import run_http_whatweb
from modules.http_wordpress import run_http_wordpress
from modules.http_wordpress_bruteforce import run_http_wordpress_bruteforce
from modules.http_wordpress_plugins import run_http_wordpress_plugins
from modules.nmap import run_nmap


def main():
    start_time = time.time()
    target = sys.argv[1]
    target_clean = target.replace("http://", "").replace("https://", "").rstrip("/")
    os.makedirs(f"logs/{target_clean}/reporte", exist_ok=True)
    run_nmap(target_clean)
    if os.path.exists(f"logs/{target_clean}/nmap/ports.txt"):
        with open(f"logs/{target_clean}/nmap/ports.txt", "r") as f:
            ports = f.read()
            if "80" in ports:
                run_http_subdomain(target_clean)
                # Se lanza con target en lugar de target_clean ya que whatweb asocia todos los dominios con http:// (dentro de la función se limpia)
                run_http_whatweb(target)
                run_http_screenshot(target_clean)
                with open(f"logs/{target_clean}/http/whatweb/cms.txt", "r") as w:
                    cms = w.read()
                    if "WordPress" in cms:
                        # Se lanza con target en lugar de target_clean ya que wpscan asocia todos los dominios con http:// (dentro de la función se limpia)
                        run_http_wordpress(target)
                        run_http_wordpress_plugins(target_clean)
                        # Se lanza con target en lugar de target_clean ya que whatweb asocia todos los dominios con http:// (dentro de la función se limpia)
                        run_http_wordpress_bruteforce(target)
                    if "Joomla" in cms:
                        # Se lanza con target en lugar de target_clean ya que joomscan asocia todos los dominios con http:// (dentro de la función se limpia)
                        run_http_joomla(target)
            if "21" in ports:
                run_ftp(target_clean)

    run_generar_reporte(target_clean)
    print(f"[*] Escaneo finalizado en {int((time.time() - start_time) // 60)} minuto(s) y {int((time.time() - start_time) % 60)} segundo(s).")

#Llamada a la función main
if __name__ == "__main__":
    main()