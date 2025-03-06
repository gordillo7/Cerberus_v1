document.addEventListener('DOMContentLoaded', function() {
    // Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const pageTitle = document.querySelector('.page-title');

    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            showPage(this.dataset.page);
        });
    });

    // "New Scan" Button
    document.querySelector('[data-action="new-scan"]').addEventListener('click', function() {
        showPage('scanner');
    });

    // Function to update statistics
    function updateStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                animateNumber('reports-count', data.reports_count);
                animateNumber('modules-count', data.modules_count);
                animateNumber('clients-count', data.clients_count);
            });
    }

    // Function to animate numbers
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

    // Function to update recent scans
    function updateRecentScans() {
        fetch('/api/recent-scans')
            .then(response => response.json())
            .then(scans => {
                const scansList = document.getElementById('recent-scans-list');
                if (scans.length === 0) {
                    scansList.innerHTML = '<div class="scan-item">No recent scans</div>';
                } else {
                    scansList.innerHTML = scans.map(scan => `
                        <div class="scan-item">
                            <div class="scan-info">
                                <div class="scan-target">${scan.target}</div>
                                <div class="scan-date">${new Date(scan.date).toLocaleString()}</div>
                            </div>
                            <div class="scan-status ${scan.status.toLowerCase()}">${scan.status}</div>
                        </div>
                    `).join('');
                }
            });
    }

    // Scan console
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

    const stopScanBtn = document.getElementById('stopScanBtn');
    if (stopScanBtn) {
        stopScanBtn.addEventListener('click', async function() {
            const response = await fetch('/stopscan', { method: 'POST' });
            const data = await response.json();
            scanConsole.addMessage(data.message);
        });
    }

    const clearConsoleBtn = document.getElementById('clearConsoleBtn');
    if (clearConsoleBtn) {
        clearConsoleBtn.addEventListener('click', function() {
            scanConsole.clear();
        });
    }

    // Function to start a full scan
    async function startFullScan(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        document.getElementById('fullScanTarget').value = '';
        scanConsole.clear();
        scanConsole.addMessage(`[*] Starting full scan for ${formData.get('target')}...`);

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
                // Split the chunk into lines and add each line to the console
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
                if (reports.length === 0) {
                    reportsContainer.innerHTML = '<div class="no-reports">No reports have been generated</div>';
                } else {
                    reportsContainer.innerHTML = reports.map(report => `
                        <div class="report-card">
                            <div class="report-preview-container" onclick="window.open('/report/${report.filename}', '_blank')">
                                <embed src="/report/${report.filename}#page=1" type="application/pdf" class="report-preview">
                            </div>
                            <div class="report-info">
                                <div class="report-title">
                                    ${report.filename.length > 20 ? report.filename.substring(0, 16) + '....pdf' : report.filename}
                                </div>
                                <button class="delete-report" data-filename="${report.filename}">
                                    <span class="material-icons">delete</span>
                                </button>
                            </div>
                        </div>
                    `).join('');
                    const deleteButtons = reportsContainer.querySelectorAll('.delete-report');
                    deleteButtons.forEach(button => {
                        button.addEventListener('click', function() {
                            deleteReport(this.dataset.filename);
                        });
                    });
                }
            })
            .catch(error => console.error(error));
    }

    function deleteReport(filename) {
        if (confirm(`Are you sure you want to delete the report ${filename}?`)) {
            fetch(`/api/reports/${filename}`, { method: 'DELETE' })
                .then(response => {
                    if (response.ok) {
                        loadReports();
                        updateStats();
                    } else {
                        alert('Error deleting the report');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error deleting the report');
                });
        }
    }

    // API Token Management
    function setupTokenForm(tokenName) {
        const formId = `${tokenName}TokenForm`;
        const inputId = `${tokenName}Token`;
        const indicatorId = `${tokenName}TokenSetIndicator`;
        const statusId = `${tokenName}TokenStatus`;

        const tokenForm = document.getElementById(formId);
        const tokenInput = document.getElementById(inputId);
        const tokenSetIndicator = document.getElementById(indicatorId);

        if (tokenForm) {
            // Load saved token on page load
            fetch(`/api/settings/${tokenName}-token`)
                .then(response => response.json())
                .then(data => {
                    if (data.token) {
                        tokenInput.placeholder = data.token;
                        tokenSetIndicator.style.display = 'inline-block';
                    }
                })
                .catch(error => console.error(`Error loading ${tokenName} token:`, error));

            // Handle token form submission
            tokenForm.addEventListener('submit', async function(event) {
                event.preventDefault();
                const tokenStatus = document.getElementById(statusId);

                try {
                    const response = await fetch(`/api/settings/${tokenName}-token`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ token: tokenInput.value }),
                    });

                    const data = await response.json();

                    tokenStatus.textContent = data.message;
                    tokenStatus.className = 'token-status ' + (response.ok ? 'success' : 'error');

                    if (response.ok) {
                        tokenInput.placeholder = tokenInput.value;
                        tokenInput.value = '';
                        tokenSetIndicator.style.display = 'inline-block';
                    }

                    // Clear status message after 3 seconds
                    setTimeout(() => {
                        tokenStatus.style.display = 'none';
                    }, 3000);
                } catch (error) {
                    console.error(`Error saving ${tokenName} token:`, error);
                    tokenStatus.textContent = 'An error occurred while saving the token.';
                    tokenStatus.className = 'token-status error';
                }
            });
        }
    }

    // Call loadReports() when showing the reports page:
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

    // Toggle API Tokens card
    const apiTokensHeader = document.getElementById('apiTokensHeader');
    if (apiTokensHeader) {
        const toggleBtn = apiTokensHeader.querySelector('.toggle-btn');
        const apiTokensContent = document.getElementById('apiTokensContent');

        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() {
                const expanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !expanded);

                if (expanded) {
                    apiTokensContent.classList.remove('expanded');
                    // Esperar a que termine la transición antes de ocultar completamente
                    setTimeout(() => {
                        apiTokensContent.style.display = 'none';
                    }, 300); // Este tiempo debe ser menor que la duración de la transición
                } else {
                    apiTokensContent.style.display = 'block';
                    // Pequeño retraso para asegurar que display:block se aplique primero
                    setTimeout(() => {
                        apiTokensContent.classList.add('expanded');
                    }, 10);
                }
            });
        }
    }

    // Initialization
    showPage('dashboard');
    updateStats();
    updateRecentScans();

    // Initialize all token forms
    setupTokenForm('wpscan');
    setupTokenForm('dnsdumpster');
    setupTokenForm('mxtoolbox');
    setupTokenForm('apininja');

    // Update statistics every 30 seconds
    setInterval(updateStats, 30000);
});
