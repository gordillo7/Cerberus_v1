from flask import Flask, render_template, jsonify, request, Response, send_from_directory
from pathlib import Path
import os, signal, subprocess

app = Flask(__name__)
app.current_scan_process = None

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    reports_count = len(list(Path('informes').glob('*.pdf')))
    modules_count = len(
        [f for f in os.listdir('modules') if f.endswith('.py') and f != '__init__.py' and f != 'generar_reporte.py'])
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

@app.route('/api/reports/<filename>', methods=['DELETE'])
def delete_report(filename):
    try:
        report_path = Path('informes') / filename
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
            app.current_scan_process = None  # Se limpia al finalizar el escaneo
    return Response(generate(), mimetype='text/plain')

@app.route('/stopscan', methods=['POST'])
def stop_scan():
    if app.current_scan_process is not None:
        app.current_scan_process.send_signal(signal.SIGINT)  # Enviar señal de interrupción (Ctrl+C)
        return jsonify({'message': 'Escaneo detenido.'})
    else:
        return jsonify({'message': 'No hay escaneo en curso.'}), 404


if __name__ == '__main__':
    app.run(debug=True)
