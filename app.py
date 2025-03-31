from flask import Flask, render_template, jsonify, request, Response, send_from_directory
from pathlib import Path
from typing import cast
import os, signal, subprocess, json, datetime, io

app = Flask(__name__)
app.current_scan_process = None

os.makedirs("logs", exist_ok=True)
os.makedirs("config", exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    reports_count = len(list(Path('reports').glob('*.pdf')))
    modules_count = len(
        [f for f in os.listdir('modules') if f.endswith('.py') and f != '__init__.py' and f != 'generate_report.py'])
    clients_count = len([d for d in os.listdir('logs') if os.path.isdir(os.path.join('logs', d))])
    return jsonify({
        'reports_count': reports_count,
        'modules_count': modules_count,
        'clients_count': clients_count
    })


@app.route('/api/recent-scans')
def get_recent_scans():
    log_file = Path('logs/scans.log')
    scans = []
    if log_file.exists():
        with log_file.open('r') as f:
            for line in f:
                try:
                    scan = json.loads(line.strip())
                    scans.append(scan)
                except json.JSONDecodeError:
                    continue
        scans.sort(key=lambda x: x.get('date', ''), reverse=True)
    return jsonify(scans[:3])

@app.route('/api/reports')
def get_reports():
    reports = []
    for report in Path('reports').glob('*.pdf'):
        reports.append({'filename': report.name})
    return jsonify(reports)

@app.route('/report/<filename>')
def view_report(filename):
    return send_from_directory('reports', filename)

@app.route('/api/reports/<filename>', methods=['DELETE'])
def delete_report(filename):
    try:
        report_path = Path('reports') / filename
        if report_path.exists():
            report_path.unlink()
            return jsonify({'message': f'Report {filename} deleted successfully.'}), 200
        else:
            return jsonify({'error': 'Report not found.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fullscan', methods=['POST'])
def fullscan():
    target = request.form.get('target', '').strip()
    command = ['python3', '-u', 'main.py']
    if target:
        command.append(target)
    app.current_scan_process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    def generate():
        try:
            for line in iter(app.current_scan_process.stdout.readline, ''):
                yield line
        finally:
            if app.current_scan_process:
                app.current_scan_process.stdout.close()
                return_code = app.current_scan_process.wait()
                status = "Completed" if return_code == 0 else "Aborted"
                scan_record = {
                    "target": target,
                    "date": datetime.datetime.now().isoformat(),
                    "status": status
                }
                with open("logs/scans.log", "a") as f:
                    f.write(json.dumps(scan_record) + "\n")
                app.current_scan_process = None
    return Response(generate(), mimetype='text/plain')

@app.route('/stopscan', methods=['POST'])
def stop_scan():
    if app.current_scan_process is not None:
        app.current_scan_process.send_signal(signal.SIGINT)
        return jsonify({'message': 'Scan aborted.'})
    else:
        return jsonify({'message': 'No scan is running.'}), 404


# API Token Management - Generic function
def get_token_from_config(token_name):
    config_file = Path('config/api_tokens.json')
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get(token_name, '')
    return ''

# API Token Management - WPScan
@app.route('/api/settings/wpscan-token', methods=['GET', 'POST'])
def manage_wpscan_token():
    return manage_token('wpscan')

# API Token Management - DNSDumpster
@app.route('/api/settings/dnsdumpster-token', methods=['GET', 'POST'])
def manage_dnsdumpster_token():
    return manage_token('dnsdumpster')

# API Token Management - MX ToolBox
@app.route('/api/settings/mxtoolbox-token', methods=['GET', 'POST'])
def manage_mxtoolbox_token():
    return manage_token('mxtoolbox')

# API Token Management - APINinja Whois
@app.route('/api/settings/apininja-token', methods=['GET', 'POST'])
def manage_apininja_token():
    return manage_token('apininja')

# API Token Management - IntelligenceX
@app.route('/api/settings/intelx-token', methods=['GET', 'POST'])
def manage_intelx_token():
    return manage_token('intelx')

# Generic token management function
def manage_token(token_name):
    config_file = Path('config/api_tokens.json')

    # Create config file if it doesn't exist
    if not config_file.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({}, cast(io.TextIOBase, f))

    if request.method == 'POST':
        data = request.get_json()
        token = data.get('token', '').strip()

        # Read existing config
        config = {}
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # Update token
        config[token_name] = token

        # Save config
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, cast(io.TextIOBase, f))

        return jsonify({'message': f'{token_name.capitalize()} API token saved successfully.'}), 200

    else:  # GET request
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            token = config.get(token_name, '')
        else:
            token = ''
        return jsonify({'token': token}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
