import sys
import subprocess
from urllib.parse import urlparse


def get_scheme(url):
    # If scheme is already defined, return it
    parsed = urlparse(url)
    if parsed.scheme:
        return parsed.scheme

    # Run "curl -I" command to fetch headers
    # Note: Using '-L' can follow redirects if needed; remove it if unnecessary.
    command = ["curl", "-I", url]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        output = result.stdout
    except subprocess.SubprocessError as e:
        print(f"Error executing curl: {e}")
        return None

    # Check for "Location:" header and determine scheme if https exists
    for line in output.splitlines():
        if line.lower().startswith("location:"):
            # Remove "Location:" and trim spaces
            location = line.split(":", 1)[1].strip()
            if location.startswith("https"):
                return "https"
            else:
                return "http"

    # If no Location header is found, check if output contains https anywhere
    if "https" in output.lower():
        return "https"
    return "http"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 modules/http_detect_scheme.py domain")
        sys.exit(1)
    domain = sys.argv[1]
    scheme = get_scheme(domain)
    if scheme:
        print(f"The domain uses {scheme}")
    else:
        print("Could not detect the scheme.")