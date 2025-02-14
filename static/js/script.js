document.addEventListener('DOMContentLoaded', function() {
    const scanForm = document.getElementById('scanForm');
    const resultsDiv = document.getElementById('results');

    scanForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        // Mostrar estado de carga
        resultsDiv.innerHTML = `
            <div class="scanning">
                <div class="spinner"></div>
                <p>Escaneando objetivo: ${formData.get('target')}</p>
                <div class="log"></div>
            </div>
        `;

        fetch('/scan', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            let resultHtml = '<div class="scan-results">';

            for (const [module, result] of Object.entries(data)) {
                resultHtml += `
                    <div class="result-module">
                        <div class="module-header">
                            <span class="material-icons">assignment</span>
                            <h3>${module}</h3>
                        </div>
                        <pre>${JSON.stringify(result, null, 2)}</pre>
                    </div>
                `;
            }

            resultHtml += '</div>';
            resultsDiv.innerHTML = resultHtml;
        })
        .catch(error => {
            resultsDiv.innerHTML = `
                <div class="error">
                    <span class="material-icons">error</span>
                    <p>Error: ${error}</p>
                </div>
            `;
        });
    });
});

// Añadir animación al botón "Nuevo Escaneo"
document.querySelector('.new-scan-btn').addEventListener('click', function() {
    document.querySelector('#target').focus();
});