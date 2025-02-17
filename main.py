import os
import sys
import time
from modules.ftp import run_ftp
from modules.generar_reporte import run_generar_reporte
from modules.http_joomla import run_http_joomla
from modules.http_subdomain import run_http_subdomain
from modules.http_whatweb import run_http_whatweb
from modules.http_wordpress import run_http_wordpress
from modules.http_wordpress_bruteforce import run_http_wordpress_bruteforce
from modules.http_wordpress_plugins import run_http_wordpress_plugins
from modules.nmap import run_nmap


def main():
    #Calcula el tiempo de ejecución
    start_time = time.time()
    target = sys.argv[1]
    os.makedirs(f"logs/{target}/reporte", exist_ok=True)
    run_nmap(target)
    if os.path.exists(f"logs/{target}/nmap/ports.txt"):
        with open(f"logs/{target}/nmap/ports.txt", "r") as f:
            ports = f.read()
            if "21" in ports:
                run_ftp(target)
            if "80" in ports:
                run_http_subdomain(target)
                run_http_whatweb(target)
                with open(f"logs/{target}/http/whatweb/cms.txt", "r") as w:
                    cms = w.read()
                    if "WordPress" in cms:
                        run_http_wordpress(target)
                        run_http_wordpress_plugins(target)
                        run_http_wordpress_bruteforce(target)
                    if "Joomla" in cms:
                        run_http_joomla(target)

    run_generar_reporte(target)
    print(f"[*] Escaneo finalizado en {time.time() - start_time:.2f} segundos.")

#Llamada a la función main
if __name__ == "__main__":
    main()