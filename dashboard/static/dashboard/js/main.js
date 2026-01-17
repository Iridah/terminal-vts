// dashboard/static/dashboard/js/main.js v2.7.5 (Consolidado)
console.log("Martillo Vil: Motor de estabilidad v2.7.5 iniciado.");

// 1. UTILIDADES Y SEGURIDAD
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 2. VALIDACIÓN Y UI
function validarStock(input) {
    if (input.value < 0) input.value = 0;
    input.style.backgroundColor = (input.value == 0) ? "#ffe6e6" : "";
    if (input.value == 0) input.classList.add("border-danger");
    else input.classList.remove("border-danger");
}

const initClock = () => {
    const clockElement = document.getElementById('live-clock');
    if (!clockElement) return;
    const tick = () => {
        clockElement.textContent = new Date().toLocaleTimeString('es-CL', {
            hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZone: 'America/Santiago'
        });
    };
    setInterval(tick, 1000); tick();
};

// 3. GESTIÓN DE SALIDAS (TRINIDAD)
function abrirTrinidad(sku, nombre) {
    const skuInput = document.getElementById('trinidadSku');
    const nombreText = document.getElementById('trinidadNombre');
    if(skuInput && nombreText) {
        skuInput.value = sku;
        nombreText.innerText = nombre;
        const myModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modalTrinidadSalida'));
        myModal.show();
    }
}

// 4. INICIALIZACIÓN DE EVENTOS (Unificado)
document.addEventListener('DOMContentLoaded', function() {
    initClock();

    // Buscador La Forja
    const searchInput = document.getElementById('vtsSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const filter = this.value.toLowerCase().trim();
            document.querySelectorAll("tbody tr").forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(filter) ? "" : "none";
            });
        });
    }

    // Gráfico de Capital por Sección
    const ctx = document.getElementById('perdidasSeccionChart');
    if (ctx && window.chartLabels) {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: window.chartLabels,
                datasets: [{
                    label: 'Capital', data: window.chartData,
                    backgroundColor: '#7DA0FA', borderRadius: 12,
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    // Gráfico de ROI
    const roiCtx = document.getElementById('roiChart');
    if (roiCtx && window.roiData) {
        new Chart(roiCtx, {
            type: 'line',
            data: {
                labels: window.roiLabels,
                datasets: [{
                    label: 'ROI %', data: window.roiData,
                    borderColor: '#4B49AC', backgroundColor: 'rgba(75, 73, 172, 0.1)', fill: true, tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    // Manejador de Formulario Trinidad
    const formTriada = document.getElementById('formTrinidad');
    if (formTriada) {
        formTriada.addEventListener('submit', function(e) {
            e.preventDefault();
            const payload = {
                sku: document.getElementById('trinidadSku').value,
                tipo: document.getElementById('tipoSalida').value,
                cantidad: parseInt(document.getElementById('trinidadCant').value)
            };
            const btn = e.submitter;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            btn.disabled = true;
            
            console.log("🚀 Enviando a Mardum:", payload);
            setTimeout(() => { location.reload(); }, 600);
        });
    }
});

// Añade esto al final de tu DOMContentLoaded para asegurar que las tarjetas tengan altura
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.metric-card');
    cards.forEach(card => {
        // Si la tarjeta no tiene un h2 con datos, le ponemos un estado de espera
        const dataValue = card.querySelector('h2');
        if (!dataValue || dataValue.innerText.trim() === "" || dataValue.innerText === "$0") {
            card.classList.add('card-empty-state');
        }
    });
});

// dashboard/static/dashboard/js/main.js

document.getElementById('formTrinidad')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const btn = e.submitter;
    const originalText = btn.innerHTML;
    
    const payload = {
        sku: document.getElementById('trinidadSku').value,
        tipo: document.getElementById('tipoSalida').value,
        cantidad: parseInt(document.getElementById('trinidadCant').value)
    };

    // Validación básica de seguridad
    if (!payload.cantidad || payload.cantidad <= 0) {
        alert("⚠️ Por Martillo Vil, ingresa una cantidad válida.");
        return;
    }

    // Feedback visual inmediato
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Procesando...';
    btn.disabled = true;

    // Conexión real con Mardum (Django)
    fetch('/registrar-movimiento-triada/', { // Asegúrate que esta URL coincida con tu urls.py
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Éxito: recargamos para ver el historial actualizado
            location.reload();
        } else {
            alert("❌ Error en Mardum: " + data.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("🚨 Error crítico de conexión.");
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
});
