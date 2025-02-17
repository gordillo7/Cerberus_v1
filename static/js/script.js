document.addEventListener('DOMContentLoaded', function() {
    // Navegación
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const pageTitle = document.querySelector('.page-title');

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

    /*
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
     */

    // Console de escaneo
    const scanConsole = {
        element: document.getElementById('scan-console'),
        output: document.getElementById('console-output'),
        addMessage(message) {
            const line = document.createElement('div');
            line.textContent = message;
            this.output.appendChild(line);
            this.element.scrollTop = this.element.scrollHeight;
        },
        clear() {
            this.output.innerHTML = '';
        }
    };

    // Function to start a full scan
    async function startFullScan(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        scanConsole.clear();
        scanConsole.addMessage(`[*] Iniciando escaneo completo para ${formData.get('target')}...`);

        const response = await fetch('/fullscan', {
            method: 'POST',
            body: formData
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;

        while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;
            if (value) {
                const chunk = decoder.decode(value, { stream: true });
                // Divide el chunk en líneas y agrega cada línea a la consola
                const lines = chunk.split('\n');
                lines.forEach(line => {
                    if (line.trim() !== '') {
                        scanConsole.addMessage(line);
                    }
                });
            }
        }
    }

    // Handle full scan form submission
    const fullScanForm = document.getElementById('fullScanForm');
    if (fullScanForm) {
        fullScanForm.addEventListener('submit', startFullScan);
    }

    function loadReports() {
        fetch('/api/reports')
            .then(response => response.json())
            .then(reports => {
                const reportsContainer = document.getElementById('reports-container');
                reportsContainer.innerHTML = reports.map(report => `
                    <div class="report-card">
                        <div class="report-preview-container" onclick="window.open('/report/${report.filename}', '_blank')">
                            <embed src="/report/${report.filename}#page=1" type="application/pdf" class="report-preview">
                        </div>
                        <div class="report-info">
                            <div class="report-title">${report.filename}</div>
                            <button class="delete-report" data-filename="${report.filename}">
                                <span class="material-icons">delete</span>
                            </button>
                        </div>
                    </div>
                `).join('');

                // Add event listeners for delete buttons
                const deleteButtons = reportsContainer.querySelectorAll('.delete-report');
                deleteButtons.forEach(button => {
                    button.addEventListener('click', function() {
                        deleteReport(this.dataset.filename);
                    });
                });
            });
    }

    function deleteReport(filename) {
        if (confirm(`¿Estás seguro de que quieres eliminar el informe ${filename}?`)) {
            fetch(`/api/reports/${filename}`, { method: 'DELETE' })
                .then(response => {
                    if (response.ok) {
                        loadReports();
                        updateStats();
                    } else {
                        alert('Error al eliminar el informe');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al eliminar el informe');
                });
        }
    }

    // Llamar a loadReports() al mostrar la página de informes:
    function showPage(pageId) {
        pages.forEach(page => page.style.display = 'none');
        document.getElementById(`${pageId}-page`).style.display = 'block';
        pageTitle.textContent = pageId.charAt(0).toUpperCase() + pageId.slice(1);

        navItems.forEach(item => item.classList.remove('active'));
        document.querySelector(`[data-page="${pageId}"]`).classList.add('active');

        if (pageId === 'dashboard') {
            updateStats();
            updateRecentScans();
        } else if (pageId === 'reports') {
            loadReports();
        }
    }


    // Inicialización
    showPage('dashboard');
    updateStats();
    updateRecentScans();
    loadModules();

    // Actualizar estadísticas cada 30 segundos
    setInterval(updateStats, 30000);
});