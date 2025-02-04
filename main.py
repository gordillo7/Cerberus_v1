import sys
from modulos.ftp import check_ftp_anonymous, ftp_searchsploit
from modulos.http_whatweb import whatweb, identificar_cms
from modulos.http_wordpress import run_wpscan, extract_usernames, process_directory_listings
from modulos.nmap import run_nmap

def main():
    target = sys.argv[1]
    run_nmap(target)
    whatweb(target)
    identificar_cms(target)
    run_wpscan(target)
    extract_usernames(target)
    process_directory_listings(target)
    check_ftp_anonymous(target)
    ftp_searchsploit(target)

#Llamada a la función main
if __name__ == "__main__":
    main()
