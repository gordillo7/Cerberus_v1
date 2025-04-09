import sys
import requests

def get_scheme(url):
    try:
        requests.get(f"https://{url}", timeout=5)
        return "https"
    except requests.exceptions.RequestException:
        try:
            requests.get(f"http://{url}", timeout=5)
            return "http"
        except requests.exceptions.RequestException:
            return None

if __name__ == "__main__":
    domain = sys.argv[1]
    scheme = get_scheme(domain)
    if scheme:
        print(f"The domain uses {scheme}")
    else:
        print("Could not detect the scheme.")
