import os
import sys
from modules.nmap import run_nmap


def main():
    target = sys.argv[1]
    os.makedirs(f"logs/{target}/reporte", exist_ok=True)
    run_nmap(target)


#Llamada a la función main
if __name__ == "__main__":
    main()