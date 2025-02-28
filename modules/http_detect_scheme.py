import sys
import requests
from urllib.parse import urlparse

def get_scheme(url):
    parsed = urlparse(url)
    if parsed.scheme:
        return parsed.scheme
    else:
        url_https = f"https://{url}"
        url_http = f"http://{url}"

        try:
            response = requests.head(url_http, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                return "http"
        except requests.exceptions.RequestException:
            pass

        try:
            response = requests.head(url_https, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                return "https"
        except requests.exceptions.RequestException:
            pass

        return None

if __name__ == "__main__":
    domain = sys.argv[1]
    scheme = get_scheme(domain)
    if scheme:
        print(f"The domain uses {scheme}")
    else:
        print("Could not detect the scheme.")
