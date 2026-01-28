// // dashboard/static/dashboard/js/main.js v2.7.5 (Consolidado)
// console.log("Martillo Vil: Motor de estabilidad v2.7.5 iniciado.");

// // 1. UTILIDADES Y SEGURIDAD
// const getCookie = (name) => {
//     let cookieValue = null;
//     if (document.cookie && document.cookie !== '') {
//         const cookies = document.cookie.split(';');
//         for (let i = 0; i < cookies.length; i++) {
//             const cookie = cookies[i].trim();
//             if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                 break;
//             }
//         }
//     }
//     return cookieValue;
// };

// // 2. UI Y RELOJ (Optimizado para evitar lag en LineageOS)
// const initClock = () => {
//     const clockElement = document.getElementById('live-clock');
//     if (!clockElement) return;
//     const tick = () => {
//         clockElement.textContent = new Date().toLocaleTimeString('es-CL', {
//             hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZone: 'America/Santiago'
//         });
//     };
//     setInterval(tick, 1000); tick();
// };

// // 3. GESTIÓN DE SALIDAS (TRINIDAD)
// function abrirTrinidad(sku, nombre) {
//     const skuInput = document.getElementById('trinidadSku');
//     const nombreText = document.getElementById('trinidadNombre');
//     if(skuInput && nombreText) {
//         skuInput.value = sku;
//         nombreText.innerText = nombre;
//         const modalEl = document.getElementById('modalTrinidadSalida');
//         if (modalEl) {
//             const myModal = bootstrap.Modal.getOrCreateInstance(modalEl);
//             myModal.show();
//         }
//     }
// }

// // 4. INICIALIZACIÓN ÚNICA (DOMContentLoaded)
// document.addEventListener('DOMContentLoaded', function() {
//     initClock();

//     // Buscador La Forja (Legacy support)
//     const searchInput = document.getElementById('vtsSearch');
//     if (searchInput) {
//         searchInput.addEventListener('input', function() {
//             const filter = this.value.toLowerCase().trim();
//             document.querySelectorAll("tbody tr").forEach(row => {
//                 row.style.display = row.innerText.toLowerCase().includes(filter) ? "" : "none";
//             });
//         });
//     }

//     // Gráficos (Protección contra variables null)
//     const ctx = document.getElementById('perdidasSeccionChart');
//     if (ctx && window.chartLabels && window.chartData) {
//         new Chart(ctx, {
//             type: 'bar',
//             data: {
//                 labels: window.chartLabels,
//                 datasets: [{
//                     label: 'Capital', data: window.chartData,
//                     backgroundColor: '#7DA0FA', borderRadius: 12,
//                 }]
//             },
//             options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
//         });
//     }

//     const roiCtx = document.getElementById('roiChart');
//     if (roiCtx && window.roiData) {
//         new Chart(roiCtx, {
//             type: 'line',
//             data: {
//                 labels: window.roiLabels,
//                 datasets: [{
//                     label: 'ROI %', data: window.roiData,
//                     borderColor: '#4B49AC', backgroundColor: 'rgba(75, 73, 172, 0.1)', fill: true, tension: 0.4
//                 }]
//             },
//             options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
//         });
//     }

//     // Manejador de Formulario Trinidad (Versión Única y Real)
//     const formTriada = document.getElementById('formTrinidad');
//     if (formTriada) {
//         formTriada.addEventListener('submit', function(e) {
//             e.preventDefault();
//             const btn = e.submitter;
//             const originalText = btn.innerHTML;
            
//             const payload = {
//                 sku: document.getElementById('trinidadSku').value,
//                 tipo: document.getElementById('tipoSalida').value,
//                 cantidad: parseInt(document.getElementById('trinidadCant').value)
//             };

//             if (!payload.cantidad || payload.cantidad <= 0) {
//                 alert("⚠️ Por Martillo Vil, ingresa una cantidad válida.");
//                 return;
//             }

//             btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
//             btn.disabled = true;

//             fetch('/registrar-movimiento-triada/', {
//                 method: 'POST',
//                 headers: {
//                     'Content-Type': 'application/json',
//                     'X-CSRFToken': getCookie('csrftoken')
//                 },
//                 body: JSON.stringify(payload)
//             })
//             .then(res => res.json())
//             .then(data => {
//                 if (data.status === 'success') location.reload();
//                 else throw new Error(data.message);
//             })
//             .catch(err => {
//                 alert("🚨 Error: " + err.message);
//                 btn.innerHTML = originalText;
//                 btn.disabled = false;
//             });
//         });
//     }

//     // Auto-detección de tarjetas vacías
//     document.querySelectorAll('.metric-card').forEach(card => {
//         const h2 = card.querySelector('h2');
//         if (!h2 || h2.innerText.trim() === "" || h2.innerText.trim() === "$0") {
//             card.classList.add('card-empty-state');
//         }
//     });
// });

// // Escucha el evento disparado por Django/HTMX
// document.body.addEventListener('actualizarTotales', function() {
//     // HTMX recarga solo la sección de métricas [cite: 2026-01-14]
//     htmx.ajax('GET', '{% url "dashboard_home" %}', {target: '#seccion-metricas', select: '#seccion-metricas'});
//     console.log("Zuldazar: Métricas sincronizadas tras movimiento.");
// });

// function abrirTrinidad(sku, nombre) {
//     // 1. Llenamos los datos visuales
//     document.getElementById('trinidadSku').value = sku;
//     document.getElementById('trinidadNombre').innerText = nombre;
    
//     // 2. Actualizamos la URL de HTMX dinámicamente
//     const form = document.getElementById('formTrinidad');
//     const urlBase = "{% url 'registrar_movimiento_htmx' 'PLACEHOLDER' %}";
//     form.setAttribute('hx-post', urlBase.replace('PLACEHOLDER', sku));
    
//     // 3. Procesamos el nuevo atributo para que HTMX lo reconozca
//     htmx.process(form);
    
//     // 4. Mostramos el modal (Bootstrap 5)
//     new bootstrap.Modal(document.getElementById('modalTrinidadSalida')).show();
// }

// // Cerramos el modal automáticamente cuando HTMX termine con éxito
// document.body.addEventListener('htmx:afterOnRequest', function(evt) {
//     if (evt.detail.target.id === 'tabla-productos-body') {
//         const modalEl = document.getElementById('modalTrinidadSalida');
//         const modal = bootstrap.Modal.getInstance(modalEl);
//         if (modal) modal.hide();
//         // Opcional: limpiar el input de cantidad
//         document.getElementById('trinidadCant').value = 1;
//     }
// });

// // --- SECCIÓN FINAL: MONITOREO Y GESTIÓN DE IMÁGENES ---

// function checkProntoQuiebre() {
//     fetch('/api/check-logs/')
//     .then(res => res.json())
//     .then(data => {
//         if (data.alerta) {
//             new Notification("🛡️ Zuldazar: Alerta de Stock", {
//                 body: `¡Pronto Quiebre en ${data.producto}! Solo quedan ${data.stock} un.`,
//                 icon: '/static/img/vts-icon.png'
//             });
//         }
//     })
//     .catch(err => console.log("Zuldazar: Esperando reporte..."));
// }

// // Iniciar monitoreo
// setInterval(checkProntoQuiebre, 60000);

// // 5. INJERTO PARA MANEJO DE IMAGENES (GLOBAL)
// function abrirModalFoto(sku, nombre) {
//     console.log("Martillo Vil: Accediendo a la cámara para SKU:", sku);
    
//     const modalEl = document.getElementById('modalCargaImagen');
//     const titulo = document.getElementById('fotoNombreProd');
//     const form = document.getElementById('formFoto');

//     if (modalEl && titulo && form) {
//         titulo.innerText = nombre;
//         form.action = `/subir-foto/${sku}/`; 
        
//         const myModal = bootstrap.Modal.getOrCreateInstance(modalEl);
//         myModal.show();
//     } else {
//         console.error("Error: Componentes del modal no encontrados en el DOM.");
//     }
// }
// console.log("Lógica de Iridah inyectada correctamente.");

// // --- SECCIÓN DE SEGURIDAD HTMX (Consolidada v2.8) ---
// document.body.addEventListener('htmx:configRequest', (event) => {
//     // 1. Inyectar CSRF Token (¡Indispensable para subir el CSV!)
//     const csrftoken = getCookie('csrftoken');
//     if (csrftoken) {
//         event.detail.headers['X-CSRFToken'] = csrftoken;
//     }

//     // 2. Inyectar Sargerite Token (UUID del Boss)
//     const sargeriteToken = document.querySelector('meta[name="sargerite-token"]')?.content;
    
//     if (sargeriteToken) {
//         event.detail.headers['X-Sargerite-Token'] = sargeriteToken;
//         console.log("🛡️ Sargerite Shield: Token inyectado correctamente.");
//     } else {
//         console.warn("⚠️ Sargerite Shield: No se detectó token en el Meta Tag.");
//     }
// });

// document.body.addEventListener('htmx:afterSwap', function(evt) {
//     initClock(); // Re-vincula el reloj si el contenedor fue reemplazado
// });

/**
 * VTS - Martillo Vil: Motor de Estabilidad v2.8.5
 * REPORTE DE AUDITORÍA: ROI Rescatado, Trinidad Unificada, Reloj Blindado.
 */

console.log("🛡️ Zuldazar: Motor v2.8.5 iniciado. (Triglicéridos bajo control)");

// --- 1. UTILIDADES Y SEGURIDAD ---
const getCookie = (name) => {
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
};

// --- 2. UI: RELOJ Y GRÁFICOS ---
const initClock = () => {
    const clockElement = document.getElementById('live-clock');
    if (!clockElement) return;
    const tick = () => {
        clockElement.textContent = new Date().toLocaleTimeString('es-CL', {
            hour: '2-digit', minute: '2-digit', second: '2-digit', 
            hour12: false, timeZone: 'America/Santiago'
        });
    };
    setInterval(tick, 1000); tick();
};

/**
 * Motor de Gráficos: Rescatado para evitar el "Patapum" visual tras swaps de HTMX
 */
const initCharts = () => {
    // A. Gráfico de Capital por Sección
    const ctx = document.getElementById('perdidasSeccionChart');
    if (ctx && window.chartLabels && window.chartData) {
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

    // B. Gráfico de ROI (¡Aquí está tu tesoro!)
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
};

// --- 3. GESTIÓN DE MODALES (TRINIDAD E IMÁGENES) ---

/**
 * Versión Unificada de Trinidad (HTMX-Ready)
 * Se llama desde el HTML pasando la URL procesada por Django
 */
function abrirTrinidad(sku, nombre, urlAccion) {
    const skuInput = document.getElementById('trinidadSku');
    const nombreText = document.getElementById('trinidadNombre');
    const form = document.getElementById('formTrinidad');

    if (skuInput && nombreText && form) {
        skuInput.value = sku;
        nombreText.innerText = nombre;
        
        // Inyectamos la URL si viene del template para evitar etiquetas Django en el JS
        if (urlAccion) {
            form.setAttribute('hx-post', urlAccion.replace('PLACEHOLDER', sku));
            htmx.process(form);
        }

        const modalEl = document.getElementById('modalTrinidadSalida');
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
}

function abrirModalFoto(sku, nombre) {
    const modalEl = document.getElementById('modalCargaImagen');
    const titulo = document.getElementById('fotoNombreProd');
    const form = document.getElementById('formFoto');

    if (modalEl && titulo && form) {
        titulo.innerText = nombre;
        form.action = `/subir-foto/${sku}/`; 
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
}

// --- 4. CICLO DE VIDA (DOM & HTMX) ---

document.addEventListener('DOMContentLoaded', function() {
    initClock();
    initCharts(); // Carga inicial de gráficos

    // Buscador La Forja (Legacy)
    const searchInput = document.getElementById('vtsSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const filter = this.value.toLowerCase().trim();
            document.querySelectorAll("tbody tr").forEach(row => {
                row.style.display = row.innerText.toLowerCase().includes(filter) ? "" : "none";
            });
        });
    }

    // Auto-detección de tarjetas vacías
    document.querySelectorAll('.metric-card').forEach(card => {
        const h2 = card.querySelector('h2');
        if (!h2 || ["", "$0", "0"].includes(h2.innerText.trim())) {
            card.classList.add('card-empty-state');
        }
    });
});

// Seguridad HTMX: CSRF y Sargerite Shield
document.body.addEventListener('htmx:configRequest', (event) => {
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) event.detail.headers['X-CSRFToken'] = csrftoken;

    const sargeriteToken = document.querySelector('meta[name="sargerite-token"]')?.content;
    if (sargeriteToken) event.detail.headers['X-Sargerite-Token'] = sargeriteToken;
});

// Sincronización Post-Carga: Revive reloj y gráficos tras cambiar de pestaña
document.body.addEventListener('htmx:afterSwap', function(evt) {
    initClock();
    initCharts();
});

// Limpieza de Modales tras éxito
document.body.addEventListener('htmx:afterOnRequest', function(evt) {
    if (evt.detail.target.id === 'tabla-productos-body' && evt.detail.successful) {
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalTrinidadSalida'));
        if (modal) modal.hide();
    }
});

// --- 5. MONITOREO Y NOTIFICACIONES ---

function checkProntoQuiebre() {
    fetch('/api/check-logs/')
    .then(res => res.json())
    .then(data => {
        if (data.alerta) {
            new Notification("🛡️ Zuldazar: Alerta de Stock", {
                body: `¡Pronto Quiebre en ${data.producto}! Solo quedan ${data.stock} un.`,
                icon: '/static/img/vts-icon.png'
            });
        }
    }).catch(() => {});
}
setInterval(checkProntoQuiebre, 60000);

// --- 6. MÓDULO CLIMÁTICO (RECOLETA) ---
const updateWeather = async () => {
    const weatherEl = document.getElementById('vts-weather');
    if (!weatherEl) return;

    try {
        // Usamos una API abierta (ej. wttr.in) o tu propia endpoint de Django
        const response = await fetch('https://wttr.in/Recoleta,Chile?format=%c+%t');
        if (response.ok) {
            const data = await response.text();
            weatherEl.innerHTML = `<i class="fas fa-cloud-sun text-warning"></i> ${data}`;
        }
    } catch (err) {
        weatherEl.innerHTML = `<i class="fas fa-sun text-warning"></i> Nublado con posibilidades de Sazantos`;
        console.warn("Error de conexión con el Gran Cielo.");
    }
};

// --- EL "PEGAMENTO" HTMX ---
document.body.addEventListener('htmx:afterSwap', function(evt) {
    initClock();      // Revive el reloj
    updateWeather();  // Revive el clima
    console.log("♻️ Zuldazar: Ciclo de vida UI restaurado.");
});

// Carga inicial
document.addEventListener('DOMContentLoaded', updateWeather);

// Ejecutar al cargar y cada 30 min
updateWeather();
setInterval(updateWeather, 1800000);