import os
import json
import sys
import requests


def get_api_token(token_name):
    config_path = 'config/api_tokens.json'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get(token_name, '')
    return ''


def save_result(domain, filename, content):
    dir_path = os.path.join('logs', domain, 'dns')
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def run_dnsdumpster(domain):
    print("Running DNSDumpster...")
    token = get_api_token('dnsdumpster')
    url = f'https://api.dnsdumpster.com/domain/{domain}'
    headers = {'X-API-Key': token}
    try:
        response = requests.get(url, headers=headers)
        result = response.text
    except Exception as e:
        result = f'Error: {e}'
    save_result(domain, 'dns_dumpster.json', result)


def run_mxtoolbox(domain):
    print("Running DMARC lookup...")
    token = get_api_token('mxtoolbox')
    url = f'https://api.mxtoolbox.com/api/v1/lookup/dmarc/{domain}'
    headers = {
        'Authorization': token,
        'Accept': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        result = response.text
    except Exception as e:
        result = f'Error: {e}'
    save_result(domain, 'dns_dmarc.json', result)


def run_apininja(domain):
    print("Running Whois lookup...")
    token = get_api_token('apininja')
    url = f'https://api.api-ninjas.com/v1/whois?domain={domain}'
    headers = {'X-Api-Key': token}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == requests.codes.ok:
            result = response.text
        else:
            result = f"Error: {response.status_code} {response.text}"
    except Exception as e:
        result = f'Error: {e}'
    save_result(domain, 'dns_whois.json', result)


def run_dns_recon(domain):
    run_dnsdumpster(domain)
    run_mxtoolbox(domain)
    run_apininja(domain)


if __name__ == '__main__':
    target = sys.argv[1]
    run_dns_recon(target)