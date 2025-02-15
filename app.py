from flask import Flask, render_template, request, jsonify, Response
from pathlib import Path
import os
import time
import importlib
import inspect

app = Flask(__name__)

# Función para cargar dinámicamente los módulos y devolver sus metadatos
def load_modules():
    modules_list = []
    for file in os.listdir('modules'):
        if file.endswith('.py') and file != '__init__.py':
            mod = importlib.import_module(f'modules.{file[:-3]}')
            # Buscar en el módulo una clase que tenga atributos 'name' y 'description'
            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj) and hasattr(obj, 'name') and hasattr(obj, 'description'):
                    modules_list.append({
                        'id': file[:-3],
                        'name': obj.name,
                        'description': obj.description
                    })
                    break
    return modules_list

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
    # Ahora load_modules() devuelve una lista de diccionarios, que es serializable a JSON
    return jsonify(load_modules())

@app.route('/api/recent-scans')
def get_recent_scans():
    scans = [
        {'target': 'example.com', 'date': '2025-02-14T15:30:00', 'status': 'Completed'},
        {'target': 'test-site.org', 'date': '2025-02-14T13:15:00', 'status': 'Failed'},
    ]
    return jsonify(scans)

@app.route('/fullscan', methods=['POST'])
def fullscan():
    target = request.form['target']
    def generate():
        yield "[*] Iniciando escaneo para {}...\n".format(target)
        # load_modules() devuelve la lista de metadatos de cada módulo
        modules = load_modules()
        for mod in modules:
            mod_id = mod['id']
            mod_name = mod['name']
            yield "[*] Ejecutando módulo {}...\n".format(mod_name)
            try:
                # Importamos el módulo nuevamente usando su id
                mod_obj = importlib.import_module(f'modules.{mod_id}')
                for name, obj in inspect.getmembers(mod_obj):
                    if inspect.isclass(obj) and hasattr(obj, 'run'):
                        result = obj().run(target)
                        yield f"[+] Resultado de {mod_name}: {result}\n"
                        break
            except Exception as e:
                yield f"[!] Error al ejecutar {mod_name}: {str(e)}\n"
            yield "[+] Módulo {} completado.\n".format(mod_name)
        yield "[+] Escaneo completado. Generando informe...\n"
        time.sleep(1)
        yield "[+] Informe generado exitosamente.\n"
    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
