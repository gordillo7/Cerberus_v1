import sys
from modulos.ftp import check_ftp_anonymous
from modulos.http_whatweb import whatweb, identificar_cms
from modulos.http_wordpress import run_wpscan, extract_usernames, process_directory_listings
from modulos.nmap import run_nmap

def main():
    target = sys.argv[1]
    tecnologias_file = f"/logs/{target}/http/whatweb/tecnologias.txt"
    cms_file = f"/logs/{target}/http/whatweb/cms.txt"
    output_file1 = f"/logs/{target}/http/wpscan/users.txt"
    output_file2 = f"wordlists/{target}/users.txt"
    anonymous_file = f"/logs/{target}/ftp/anonymous.txt"

    run_nmap()
    whatweb(target, tecnologias_file)
    identificar_cms(tecnologias_file, cms_file)
    run_wpscan(target, f"/logs/{target}/http/wpscan/wpscan.txt")
    extract_usernames(f"/logs/{target}/http/wpscan/wpscan.txt", output_file1, output_file2)
    process_directory_listings(f"/logs/{target}/http/wpscan/wpscan.txt",
                               f"/logs/{target}/http/wpscan/directory_listing_dump")
    check_ftp_anonymous(target, anonymous_file)

#Llamada a la función main
if __name__ == "__main__":
    main()
