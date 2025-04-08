import sys
import requests


def get_scheme(url):
    target = "http://" + url
    req = requests.get(target)
    return req.url.split(":")[0]


if __name__ == "__main__":
    domain = sys.argv[1]
    scheme = get_scheme(domain)
    if scheme:
        print(f"The domain uses {scheme}")
    else:
        print("Could not detect the scheme.")