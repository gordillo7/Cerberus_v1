from flask import Flask, render_template, jsonify, request, Response, send_from_directory
from pathlib import Path
from typing import cast
import shutil
import os, signal, subprocess, json, datetime, io, re
import google.generativeai as genai
from PyPDF2 import PdfReader

app = Flask(__name__)
app.current_scan_process = None

os.makedirs("logs", exist_ok=True)
os.makedirs("config", exist_ok=True)
os.makedirs("projects", exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    reports_count = len(list(Path('reports').glob('*.pdf'))) + len(list(Path('projects').glob('*/reports/*.pdf')))
    modules_count = len(
        [f for f in os.listdir('modules') if f.endswith('.py') and f != '__init__.py' and f != 'generate_report.py'])
    clients_count = len([f for f in os.listdir('projects') if f.endswith('.json')])
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
        if request.form.get('scanType') == 'project':
            command.append('-p')
        if request.form.get('comprehensive') == 'true':
            command.append('-ex')
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


# Token management function
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


# Projects API
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = []
    projects_dir = Path('projects')
    projects_dir.mkdir(exist_ok=True)

    for project_file in projects_dir.glob('*.json'):
        with open(project_file, 'r') as f:
            project = json.load(f)
            projects.append(project)

    return jsonify(projects)


@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    name = data.get('name')
    target = data.get('target')

    if not name or not target:
        return jsonify({'error': 'Name and target are required'}), 400

    project_id = str(datetime.datetime.now().timestamp()).replace('.', '')
    project = {
        'id': project_id,
        'name': name,
        'target': target,
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d')
    }

    project_file = Path(f'projects/{project_id}.json')
    with open(project_file, 'w') as f:
        json.dump(project, f)

    # Create project reports directory
    project_reports_dir = Path(f'projects/{project_id}/reports')
    project_reports_dir.mkdir(parents=True, exist_ok=True)

    return jsonify(project), 201


@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    project_file = Path(f'projects/{project_id}.json')

    if not project_file.exists():
        return jsonify({'error': 'Project not found'}), 404

    # Delete project file
    project_file.unlink()

    # Delete project directory if it exists
    project_dir = Path(f'projects/{project_id}')
    if project_dir.exists():
        shutil.rmtree(project_dir)

    return jsonify({'message': 'Project deleted successfully'}), 200


@app.route('/api/projects/<project_id>/reports', methods=['GET'])
def get_project_reports(project_id):
    reports_dir = Path(f'projects/{project_id}/reports')
    reports_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    for report in reports_dir.glob('*.pdf'):
        reports.append({'filename': report.name})

    return jsonify(reports)

@app.route('/projects/<project_id>/reports/<filename>')
def view_project_report(project_id, filename):
    directory = os.path.join("projects", project_id, "reports")
    return send_from_directory(directory, filename)


@app.route('/api/projects/<project_id>/reports/<filename>', methods=['DELETE'])
def delete_project_report(project_id, filename):
    try:
        report_path = Path(f'projects/{project_id}/reports') / filename
        if report_path.exists():
            report_path.unlink()
            return jsonify({'message': f'Report {filename} deleted successfully.'}), 200
        else:
            return jsonify({'error': 'Report not found.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Proxy Configuration
@app.route('/api/settings/proxy-config', methods=['GET', 'POST'])
def manage_proxy_config():
    config_file = Path('config/proxy.json')

    # Create config directory if it doesn't exist
    config_file.parent.mkdir(parents=True, exist_ok=True)

    if request.method == 'POST':
        data = request.get_json()

        # Write config to file
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        return jsonify({'message': 'Proxy configuration saved successfully.'}), 200

    else:  # GET request
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return jsonify(config), 200
        else:
            return jsonify({'enabled': False}), 200


@app.route("/api/settings/gemini-token", methods=["GET", "POST"])
def manage_gemini_token():
    config_file = Path('config/gemini_token.json')
    if request.method == "POST":
        data = request.get_json()
        token = data.get("token")
        if not token:
            return jsonify({"error": "Token is required"}), 400

        token_data = {"gemini_api_key": token}
        os.makedirs("config", exist_ok=True)
        try:
            with open(config_file, "w") as f:
                json.dump(token_data, f)
        except Exception as e:
            return jsonify({"error": f"Error saving token: {e}"}), 500

        return jsonify({"message": "Gemini API token saved successfully"}), 200
    else:
        # GET method: return token if already set
        if config_file.exists():
            with open(config_file, "r") as f:
                token_data = json.load(f)
            token = token_data.get("gemini_api_key", "")
        else:
            token = ""
        return jsonify({"token": token}), 200

def get_gemini_key():
    config_file = Path('config/gemini_token.json')
    if config_file.exists():
        with open(config_file, "r") as f:
            token_data = json.load(f)
        return token_data.get("gemini_api_key", "")
    return ""

@app.route("/api/projects/<project_id>/chat", methods=["POST"])
def project_chat(project_id):
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    gemini_key = get_gemini_key()
    if not gemini_key:
        return jsonify({"error": "Gemini API key not set"}), 400

    genai.configure(api_key=gemini_key)

    project_file = Path(f"projects/{project_id}.json")
    if not project_file.exists():
        return jsonify({"error": "Project not found"}), 404

    with open(project_file, 'r') as f:
        project_data = json.load(f)

    target = project_data.get("target", "").replace("/", "").replace(":", "")
    if not target:
        return jsonify({"error": "Target not found for project"}), 400

    # Last report versioning
    base_report_dir = Path(f"projects/{project_id}/reports")
    pattern = re.compile(r"v(\d+)" + re.escape(target) + r"\.pdf$")
    existing_versions = []

    for fname in os.listdir(base_report_dir):
        match = pattern.match(fname)
        if match:
            existing_versions.append((int(match.group(1)), fname))

    if not existing_versions:
        return jsonify({"error": "No versioned reports found for this project."}), 404

    latest_version, latest_filename = max(existing_versions, key=lambda x: x[0])
    latest_report_path = base_report_dir / latest_filename

    context = ""
    try:
        reader = PdfReader(str(latest_report_path))
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        context += f"\n\n--- Report: {latest_filename} ---\n{text[:10000]}"
    except Exception as e:
        return jsonify({"error": f"Failed to read PDF: {e}"}), 500

    prompt = f"""
You are a cybersecurity assistant integrated into an auditing tool. Below is the content of the latest report generated for this project:

{context}

The user has asked the following about the target or its weaknesses:
\"{user_input}\"

Provide a useful and detailed response.
"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True, port=5000)
