from flask import Flask, render_template, jsonify, request, Response, send_from_directory
from pathlib import Path
import os
import subprocess

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    reports_count = len(list(Path('informes').glob('*.pdf')))
    modules_count = len(
        [f for f in os.listdir('modules') if f.endswith('.py') and f != '__init__.py' and f != 'generar_reporte.py' and f != 'main.py'])
    clients_count = len([d for d in os.listdir('logs') if os.path.isdir(os.path.join('logs', d))])
    return jsonify({
        'reports_count': reports_count,
        'modules_count': modules_count,
        'clients_count': clients_count
    })


@app.route('/api/recent-scans')
def get_recent_scans():
    scans = [
        {'target': 'example.com', 'date': '2025-02-14T15:30:00', 'status': 'Completed'},
        {'target': 'test-site.org', 'date': '2025-02-14T13:15:00', 'status': 'Failed'},
    ]
    return jsonify(scans)

@app.route('/api/reports')
def get_reports():
    reports = []
    for report in Path('informes').glob('*.pdf'):
        reports.append({'filename': report.name})
    return jsonify(reports)

@app.route('/report/<filename>')
def view_report(filename):
    return send_from_directory('informes', filename)


@app.route('/fullscan', methods=['POST'])
def fullscan():
    # Obtiene el objetivo del formulario
    target = request.form.get('target', '').strip()

    # Construye el comando para ejecutar main.py, pasando target como argumento si se proporciona
    command = ['python', '-u', 'modules/main.py']
    if target:
        command.append(target)

    # Ejecuta el proceso y captura la salida en tiempo real
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    def generate():
        # Lee línea por línea la salida y la envía al cliente
        for line in iter(process.stdout.readline, ''):
            yield line

    return Response(generate(), mimetype='text/plain')


if __name__ == '__main__':
    app.run(debug=True)
