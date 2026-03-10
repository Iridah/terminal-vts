// admin_calculadora.js — Semáforo de rentabilidad en admin AuditoriaVTS
document.addEventListener('DOMContentLoaded', function () {
    const campoCosto = document.getElementById('id_precio_costo');
    const campoVenta = document.getElementById('id_precio_venta');
    if (!campoCosto || !campoVenta) return;

    // Crear panel semáforo
    const panel = document.createElement('div');
    panel.id = 'vts-semaforo';
    panel.style.cssText = 'margin-top:15px; padding:12px; border-radius:8px; background:#f8f9fa; border:1px solid #dee2e6;';
    panel.innerHTML = '<p style="color:#888; font-size:0.85rem;">Ingrese costo y precio para ver el semáforo.</p>';
    campoVenta.closest('.form-row, .fieldBox, p').after(panel);

    let config = null;

    fetch('/api/config-costos/')
        .then(r => r.json())
        .then(data => { config = data; recalcular(); });

    function recalcular() {
        if (!config) return;
        const costo = parseFloat(campoCosto.value) || 0;
        const venta = parseFloat(campoVenta.value) || 0;
        if (costo <= 0 || venta <= 0) return;

        const costoOp = costo * (1 + config.sumup_pct + config.internet_pct + config.transporte_pct);
        const ventaNeta = venta / (1 + config.iva);
        const margen = (ventaNeta - costoOp) / ventaNeta;

        let color, texto, simbolo;
        if      (margen < 0.05) { color = '#714B23'; simbolo = '🟤'; texto = 'PÉRDIDA'; }
        else if (margen < 0.14) { color = '#ff4d4d'; simbolo = '🔴'; texto = 'SOBREVIVENCIA'; }
        else if (margen < 0.22) { color = '#ffc107'; simbolo = '🟡'; texto = 'NEUTRO'; }
        else if (margen < 0.28) { color = '#71c016'; simbolo = '🟢'; texto = 'SALUDABLE'; }
        else                    { color = '#38004F'; simbolo = '🟣'; texto = 'ILLIDARI'; }

        const pct = (margen * 100).toFixed(1);
        const ganancia = ventaNeta - costoOp;

        panel.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="font-size:2rem;">${simbolo}</span>
                <div>
                    <strong style="color:${color}; font-size:1.1rem;">${texto}</strong>
                    <div style="font-size:0.85rem; color:#555;">
                        Margen: <b>${pct}%</b> &nbsp;|&nbsp; Ganancia unitaria: <b>$${Math.round(ganancia).toLocaleString('es-CL')}</b>
                    </div>
                </div>
            </div>
        `;
    }

    campoCosto.addEventListener('input', recalcular);
    campoVenta.addEventListener('input', recalcular);
});