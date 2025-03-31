import json
import os
import sys
from intelxapi import intelx


def get_intelx_api_token():
    config_file = os.path.join('config', 'api_tokens.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('intelx', '')
    return ''

def search_emails(target):
    api_key = get_intelx_api_token()
    ix = intelx(api_key)
    ix.API_ROOT = "https://free.intelx.io"
    results = ix.search(f"@{target}")

    output_dir = os.path.join("logs", target, "dns")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "email_osint.json")

    json_str = json.dumps(results, indent=4, ensure_ascii=False)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_str)

def search_emails_pb(target):
    api_key = get_intelx_api_token()
    ix = intelx(api_key)
    ix.API_ROOT = "https://free.intelx.io"
    results = ix.phonebooksearch(target)

    output_dir = os.path.join("logs", target, "dns")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "email_osint.json")

    json_str = json.dumps(results, indent=4, ensure_ascii=False)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_str)

if __name__ == "__main__":
    target = sys.argv[1]
    search_emails_pb(target)
