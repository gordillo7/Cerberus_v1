from flask import Flask, render_template, request, jsonify, Response
from pathlib import Path
import os
import time
import importlib
import inspect

app = Flask(__name__)

# Función para cargar dinámicamente los módulos
def load_modules():
    modules = []
    module_files = [f for f in os.listdir('modules') if f.endswith('.py') and f != '__init__.py']
    for file in module_files:
        module_name = file[:-3]  # Eliminar la extensión .py
        try:
            module = importlib.import_module(f'modules.{module_name}')
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, 'run'):
                    modules.append({
                        'id': module_name,
                        'name': obj.__name__,
                        'icon': getattr(obj, 'icon', 'extension'),  # Usa 'extension' como icono por defecto
                        'description': obj.__doc__ or f"Módulo {obj.__name__}"
                    })
                    break  # Asumimos que solo hay una clase principal por módulo
        except Exception as e:
            print(f"Error al cargar el módulo {module_name}: {str(e)}")
    return modules

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    reports_count = len(list(Path('informes').glob('*.pdf')))
    modules_count = len([f for f in os.listdir('modules') if f.endswith('.py') and f != '__init__.py'])
    clients_count = len([d for d in os.listdir('logs') if os.path.isdir(os.path.join('logs', d))])

    return jsonify({
        'reports_count': reports_count,
        'modules_count': modules_count,
        'clients_count': clients_count
    })

@app.route('/api/modules')
def get_modules():
    return jsonify(load_modules())

@app.route('/api/recent-scans')
def get_recent_scans():
    # Simulando datos de escaneos recientes
    scans = [
        {'target': 'example.com', 'date': '2025-02-14T15:30:00', 'status': 'Completed'},
        {'target': 'test-site.org', 'date': '2025-02-14T13:15:00', 'status': 'Failed'},
    ]
    return jsonify(scans)

"""
@app.route('/scan', methods=['POST'])
def scan():
    def generate():
        target = request.form['target']
        selected_modules = request.form.getlist('modules')

        yield "[*] Iniciando escaneo para {}...\n".format(target)

        modules = load_modules()
        for module in modules:
            if module['id'] in selected_modules:
                yield "[*] Ejecutando módulo {}...\n".format(module['name'])
                try:
                    module_obj = importlib.import_module(f'modules.{module["id"]}')
                    for name, obj in inspect.getmembers(module_obj):
                        if inspect.isclass(obj) and hasattr(obj, 'run'):
                            result = obj().run(target)
                            yield f"[+] Resultado de {module['name']}: {result}\n"
                            break
                except Exception as e:
                    yield f"[!] Error al ejecutar {module['name']}: {str(e)}\n"
                yield "[+] Módulo {} completado.\n".format(module['name'])

        yield "[+] Escaneo completado. Generando informe...\n"
        time.sleep(1)
        yield "[+] Informe generado exitosamente.\n"

    return Response(generate(), mimetype='text/plain')
"""

if __name__ == '__main__':
    app.run(debug=True)