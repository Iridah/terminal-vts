/**
 * VTS - MARTILLO VIL: Motor de Estabilidad v2.8.5
 */
console.log("🛡️ Zuldazar: Motor v2.8.5 iniciado. (Triglicéridos bajo control)");

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

// --- CICLO DE VIDA ---
document.addEventListener('DOMContentLoaded', function() {
    // Reloj
    const clock = document.getElementById('live-clock');
    if (clock) {
        setInterval(() => {
            clock.textContent = new Date().toLocaleTimeString('es-CL', { hour12: false });
        }, 1000);
    }
    // Signo peso del sueldo
    const sueldoInput = document.getElementsByName('sueldo')[0];
    if (sueldoInput && sueldoInput.value) {
        let val = sueldoInput.value.replace(/\D/g, '');
        if (val) {
            sueldoInput.value = '$ ' + new Intl.NumberFormat('es-CL').format(parseInt(val));
        }
    }
});

// --- SEGURIDAD HTMX ---
document.body.addEventListener('htmx:configRequest', (event) => {
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) event.detail.headers['X-CSRFToken'] = csrftoken;

    const sargeriteToken = document.querySelector('meta[name="sargerite-token"]')?.content;
    if (sargeriteToken) {
        event.detail.headers['X-Sargerite-Token'] = sargeriteToken;
    }
});
// --- LISTENERS DE ENTRADA (MÁSCARAS) ---
document.body.addEventListener('input', function(e) {
    // 1. Formateador de RUT (Buscador)
    if (e.target.id === 'rut_search' || e.target.name === 'rut') {
        let val = e.target.value.replace(/[.-]/g, '').toUpperCase();
        if (val.length > 9) val = val.slice(0, 9);
        if (val.length > 1) {
            e.target.value = val.slice(0, -1) + '-' + val.slice(-1);
        } else {
            e.target.value = val;
        }
    }

    // 2. Formateador de Sueldo (Tesorería)
    if (e.target.name === 'sueldo') {
        let value = e.target.value.replace(/\D/g, '');
        if (value === "") return;
        let num = parseInt(value, 10);
        let formatted = new Intl.NumberFormat('es-CL').format(num);
        e.target.value = '$ ' + formatted;
    }
});

// --- TRINIDAD: Movimientos de Stock ---
function abrirTrinidad(sku, nombre, stockActual) {
    // Inyectar datos en el modal
    document.getElementById('trinidadSku').value = sku;
    document.getElementById('trinidadNombre').textContent = nombre;
    document.getElementById('trinidadStock').textContent = stockActual + ' unidades';
    document.getElementById('trinidadCant').value = 1;

    // Actualizar el hx-post con el SKU real
    const form = document.getElementById('formTrinidad');
    form.setAttribute('hx-post', `/registrar-movimiento/${sku}/`);
    htmx.process(form); // Re-procesar HTMX con el nuevo atributo

    // Abrir modal
    const modal = new bootstrap.Modal(document.getElementById('modalTrinidadSalida'));
    modal.show();
}

// --- MODAL FOTO ---
function abrirModalFoto(sku, nombre) {
    document.getElementById('fotoNombreProd').textContent = nombre;
    const form = document.getElementById('formFoto');
    form.setAttribute('action', `/inventario/${sku}/subir-foto/`);

    const modal = new bootstrap.Modal(document.getElementById('modalCargaImagen'));
    modal.show();
}

function toggleVariantes(sku) {
    const filas = document.querySelectorAll('.variante-row-' + sku);
    const chevron = document.getElementById('chevron-' + sku);
    filas.forEach(f => {
        f.style.display = f.style.display === 'none' ? 'table-row' : 'none';
    });
    chevron.style.transform = chevron.style.transform === 'rotate(180deg)' ? '' : 'rotate(180deg)';
}