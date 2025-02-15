document.addEventListener('DOMContentLoaded', function() {
    // Navegación
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const pageTitle = document.querySelector('.page-title');

    function showPage(pageId) {
        pages.forEach(page => page.style.display = 'none');
        document.getElementById(`${pageId}-page`).style.display = 'block';
        pageTitle.textContent = pageId.charAt(0).toUpperCase() + pageId.slice(1);

        navItems.forEach(item => item.classList.remove('active'));
        document.querySelector(`[data-page="${pageId}"]`).classList.add('active');

        if (pageId === 'dashboard') {
            updateStats();
            updateRecentScans();
        }
    }

    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            showPage(this.dataset.page);
        });
    });

    // Botón "Nuevo Escaneo"
    document.querySelector('[data-action="new-scan"]').addEventListener('click', function() {
        showPage('scanner');
    });

    // Función para actualizar las estadísticas
    function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            animateNumber('reports-count', data.reports_count);
            animateNumber('modules-count', data.modules_count);
            animateNumber('clients-count', data.clients_count);
        });
    }

    // Función para animar números
    function animateNumber(elementId, final) {
        const element = document.getElementById(elementId);
        const start = parseInt(element.textContent);
        const duration = 2000;
        const step = (final - start) / (duration / 16);
        let current = start;

        function animate() {
            current += step;
            if ((step > 0 && current >= final) || (step < 0 && current <= final)) {
                element.textContent = final;
            } else {
                element.textContent = Math.round(current);
                requestAnimationFrame(animate);
            }
        }

        animate();
    }

    // Función para actualizar los escaneos recientes
    function updateRecentScans() {
        fetch('/api/recent-scans')
            .then(response => response.json())
            .then(scans => {
                const scansList = document.getElementById('recent-scans-list');
                scansList.innerHTML = scans.map(scan => `
                    <div class="scan-item">
                        <div class="scan-info">
                            <div class="scan-target">${scan.target}</div>
                            <div class="scan-date">${new Date(scan.date).toLocaleString()}</div>
                        </div>
                        <div class="scan-status ${scan.status.toLowerCase()}">${scan.status}</div>
                    </div>
                `).join('');
            });
    }

    // Terminal de escaneo
    const terminal = {
        element: document.getElementById('scan-terminal'),
        output: document.getElementById('terminal-output'),
        show() {
            this.element.classList.remove('hidden');
        },
        hide() {
            this.element.classList.add('hidden');
        },
        addMessage(message) {
            const line = document.createElement('div');
            line.textContent = message;
            this.output.appendChild(line);
            this.output.scrollTop = this.output.scrollHeight;
        },
        clear() {
            this.output.innerHTML = '';
        }
    };

    document.querySelector('.minimize-btn').addEventListener('click', () => {
        terminal.element.classList.toggle('minimized');
    });

    // Cargar módulos disponibles
    function loadModules() {
        fetch('/api/modules')
            .then(response => response.json())
            .then(modules => {
                const modulesGrid = document.getElementById('modules-list');
                modulesGrid.innerHTML = modules.map(module => `
                    <label class="module-checkbox">
                        <input type="checkbox" name="modules" value="${module.id}">
                        <span class="material-icons">${module.icon}</span>
                        ${module.name}
                    </label>
                `).join('');
            });
    }

    // Manejar el formulario de escaneo
    const scanForm = document.getElementById('scanForm');
    if (scanForm) {
        scanForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);

            terminal.show();
            terminal.clear();
            terminal.addMessage(`[*] Iniciando escaneo para ${formData.get('target')}`);

            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    body: formData
                });

                const reader = response.body.getReader();

                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;

                    const text = new TextDecoder().decode(value);
                    terminal.addMessage(text);
                }

                terminal.addMessage('[+] Escaneo completado. Informe generado.');
            } catch (error) {
                terminal.addMessage(`[!] Error: ${error.message}`);
            }
        });
    }

    // Inicialización
    showPage('dashboard');
    updateStats();
    updateRecentScans();
    loadModules();

    // Actualizar estadísticas cada 30 segundos
    setInterval(updateStats, 30000);
});