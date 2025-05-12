import os, sys, time, ipaddress
from modules.dns_recon import run_dns_recon
from modules.ftp import run_ftp
from modules.generate_report import run_generate_report
from modules.http_fuzzing import run_http_fuzzing
from modules.http_joomla import run_http_joomla
from modules.http_screenshot import run_http_screenshot
from modules.http_subdomain import run_http_subdomain
from modules.http_webscan import run_http_webscan
from modules.http_whatweb import run_http_whatweb
from modules.http_wordpress import run_http_wordpress
from modules.http_wordpress_bruteforce import run_http_wordpress_bruteforce
from modules.http_wordpress_plugins import run_http_wordpress_plugins
from modules.nmap import run_nmap
from modules.osint_mail import run_osint_mail
from modules.ssh import run_ssh


def main():
    start_time = time.time()
    target = sys.argv[1]
    target_clean = target.replace("http://", "").replace("https://", "").rstrip("/")
    os.makedirs(f"logs/{target_clean}/report", exist_ok=True)
    run_nmap(target_clean)
    try:
        ipaddress.ip_address(target_clean)
    # Target is a domain
    except ValueError:
        run_dns_recon(target_clean)
        run_osint_mail(target_clean)
        run_http_subdomain(target_clean)
    if os.path.exists(f"logs/{target_clean}/nmap/ports.txt"):
        with open(f"logs/{target_clean}/nmap/ports.txt", "r") as f:
            ports = f.read().splitlines()
            if "80" in ports:
                if "-ex" in sys.argv:
                    run_http_webscan(target_clean, True)
                    run_http_fuzzing(target_clean, True)
                else:
                    run_http_webscan(target_clean, False)
                    run_http_fuzzing(target_clean, False)
                run_http_whatweb(target_clean)
                run_http_screenshot(target_clean)
                with open(f"logs/{target_clean}/http/whatweb/cms.txt", "r") as w:
                    cms = w.read()
                    if "WordPress" in cms:
                        run_http_wordpress(target_clean)
                        run_http_wordpress_plugins(target_clean)
                        run_http_wordpress_bruteforce(target_clean)
                    if "Joomla" in cms:
                        run_http_joomla(target_clean)
            if "21" in ports:
                run_ftp(target_clean)
            if "22" in ports:
                run_ssh(target_clean)

    # Check if the '-p' parameter is present and pass it to run_generate_report if so
    if "-p" in sys.argv:
        run_generate_report(target_clean, "-p")
    else:
        run_generate_report(target_clean)
    print(f"[*] Scan finished in {int((time.time() - start_time) // 60)} minute(s) and {int((time.time() - start_time) % 60)} second(s).")


if __name__ == "__main__":
    main()