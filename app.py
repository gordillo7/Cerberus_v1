from flask import Flask, render_template, request, jsonify
import os
import sys

# Añadir el directorio actual al path de Python para poder importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar los módulos de pentesting
from modules import http_joomla, http_wordpress_bruteforce, http_wordpress_plugins, nmap, ftp, http_whatweb, \
    http_wordpress, generar_reporte, http_subdomain

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    target = request.form['target']
    modules = request.form.getlist('modules')
    results = {}

    if 'nmap' in modules:
        results['nmap'] = nmap.run_nmap(target)
    if 'whatweb' in modules:
        results['whatweb'] = http_whatweb.whatweb(target)
    if 'wordpress' in modules:
        results['wordpress'] = http_wordpress.run_wpscan(target)
    if 'joomla' in modules:
        results['joomla'] = http_joomla.run_joomscan(target)
    if 'subdomain' in modules:
        results['subdomain'] = http_subdomain.run_subdomain(target)
    if 'ftp' in modules:
        results['ftp'] = ftp.check_ftp_anonymous(target)
    if 'wordpress_bruteforce' in modules:
        results['wordpress_bruteforce'] = http_wordpress_bruteforce.run_wordpress_bruteforce(target)
    if 'wordpress_plugins' in modules:
        results['wordpress_plugins'] = http_wordpress_plugins.extract_vulnerable_plugins(target)

    generar_reporte.generar_reporte(target)

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)