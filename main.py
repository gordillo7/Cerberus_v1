import os
import sys
from modulos.ftp import check_ftp_anonymous, ftp_searchsploit
from modulos.generar_reporte import generar_reporte
from modulos.http_subdomain import run_subdomain
from modulos.http_whatweb import whatweb, identificar_cms
from modulos.http_wordpress import run_wpscan, extract_usernames, process_directory_listings
from modulos.http_wordpress_plugins import extract_vulnerable_plugins, run_wordpress_plugins
from modulos.nmap import run_nmap

def main():
    target = sys.argv[1]
    os.makedirs(f"logs/{target}/reporte", exist_ok=True)
    run_nmap(target)
    whatweb(target)
    identificar_cms(target)
    run_wpscan(target)
    extract_usernames(target)
    process_directory_listings(target)
    extract_vulnerable_plugins(target)
    run_wordpress_plugins(target)
    run_subdomain(target)
    check_ftp_anonymous(target)
    ftp_searchsploit(target)
    generar_reporte(target)

#Llamada a la función main
if __name__ == "__main__":
    main()
