import os
import json
import sys
import requests
import datetime


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


def read_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}


def format_unix_timestamp(timestamp):
    try:
        dt = datetime.datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return 'Invalid timestamp'


def extract_dns_dumpster_info(domain):
    report = []
    json_path = os.path.join('logs', domain, 'dns', 'dns_dumpster.json')
    data = read_json(json_path)

    # MX records extraction with asn_name as provider from first ips element
    mx_records = data.get('mx', [])
    if mx_records:
        report.append("MX Records:")
        for mx in mx_records:
            mx_host = mx.get('host', 'N/A')
            ips = mx.get('ips', [])
            provider = 'Unknown'
            if ips and isinstance(ips, list):
                provider = ips[0].get('asn_name', 'Unknown')
            report.append(f"    MX Host: {mx_host}")
            report.append(f"    Email Provider: {provider}")
        report.append("#")

    # NS records extraction with asn_name as provider from first ips element
    ns_records = data.get('ns', [])
    if ns_records:
        report.append("NS Records:")
        for ns in ns_records:
            host = ns.get('host', 'N/A')
            ips = ns.get('ips', [])
            provider = 'Unknown'
            country = 'Unknown'
            if ips and isinstance(ips, list):
                provider = ips[0].get('asn_name', 'Unknown')
                country = ips[0].get('country', 'Unknown')
            report.append(f"    NS Server: {host} (Provider: {provider}, Located in: {country})")
        report.append("#")

    # TXT records
    txt_records = data.get('txt', [])
    if txt_records:
        report.append("TXT Records:")
        for txt in txt_records:
            report.append(f"    {txt}")

    return "\n".join(report)


def extract_dmarc_info(domain):
    report = []
    json_path = os.path.join('logs', domain, 'dns', 'dns_dmarc.json')
    try:
        data = json.loads(open(json_path, 'r', encoding='utf-8').read())
    except Exception:
        data = {}

    failed_records = data.get("Failed", [])
    if any(record.get("ID") == 441 for record in failed_records):
        status_line = ("The DMARC record is not public. This implies that there is no valid DMARC record found "
                       "for this domain, which could potentially allow email spoofing (the practice of forging email "
                       "headers to appear as if sent from a trusted domain). It is recommended to configure a public "
                       "DMARC record to enhance email security.")
    else:
        status_line = "A public DMARC record was found for the domain."

    report.append("DMARC Record Info:")
    report.append(f"    {status_line}")
    return "\n".join(report)


def extract_whois_info(domain):
    report = []
    json_path = os.path.join('logs', domain, 'dns', 'dns_whois.json')
    data = read_json(json_path)

    registrar = data.get('registrar', 'N/A')
    report.append("Whois Info:")
    report.append(f"    Registered with: {registrar}")

    creation_ts = data.get('creation_date')
    if isinstance(creation_ts, list):
        creation_ts = creation_ts[0]
    expiration_ts = data.get('expiration_date')
    if isinstance(expiration_ts, list):
        expiration_ts = expiration_ts[0]
    creation_date = format_unix_timestamp(creation_ts) if creation_ts else 'Unknown'
    expiration_date = format_unix_timestamp(expiration_ts) if expiration_ts else 'Unknown'
    report.append(f"    Domain created on: {creation_date}")
    report.append(f"    Domain expires on: {expiration_date}")

    if expiration_ts:
        try:
            expire_dt = datetime.datetime.fromtimestamp(int(expiration_ts))
            now = datetime.datetime.now()
            remaining = expire_dt - now
            if remaining.days < 90:
                report.append(
                    "    WARNING: The domain expires in less than three months. It is advisable to renew the domain as soon as possible to avoid potential domain hijacking.")
        except Exception:
            pass

    additional_fields = ['name', 'org', 'address', 'city', 'state', 'registrant_postal_code', 'country']
    details_report = []
    for field in additional_fields:
        value = data.get(field, 'N/A')
        if isinstance(value, str) and value.lower() != 'gdpr masked':
            details_report.append(f"        {field.capitalize()}: {value}")
    if details_report:
        report.append("    Additional registrant details:")
        report.extend(details_report)
    else:
        report.append("    No additional registrant information available (or masked for privacy).")
    return "\n".join(report)


def generate_dns_recon_report(domain):
    report_sections = []
    report_sections.append(extract_dns_dumpster_info(domain))
    report_sections.append("#")
    report_sections.append(extract_dmarc_info(domain))
    report_sections.append("#")
    report_sections.append(extract_whois_info(domain))

    report_content = "\n".join(report_sections)
    report_dir = os.path.join('logs', domain, 'report')
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, 'dns_recon.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"[+] DNS Recon log generated at: {report_file}")


def run_dns_recon(domain):
    print("[*] Running DNS Recon module...")
    run_dnsdumpster(domain)
    run_mxtoolbox(domain)
    run_apininja(domain)
    generate_dns_recon_report(domain)
    print("[+] DNS Recon module completed.")


if __name__ == '__main__':
    target = sys.argv[1]
    run_dns_recon(target)