import sys
import requests

def get_scheme(url):
    try:
        requests.get(f"https://{url}", timeout=5)
        return "https"
    except requests.exceptions.RequestException:
        return "http"

if __name__ == "__main__":
    domain = sys.argv[1]
    scheme = get_scheme(domain)
    if scheme:
        print(f"The domain uses {scheme}")
    else:
        print("Could not detect the scheme.")
