// admin_calculadora.js — Semáforo de rentabilidad VTS
// Fórmula: todo con IVA incluido (realidad Vacadari)
// costo_real = precio_costo * (1 + sumup_pct + internet_pct + transporte_pct + ...otros)
// margen     = (precio_venta - costo_real) / precio_venta
// Muestra fila de 6 niveles con precio mínimo redondeado hacia arriba

document.addEventListener('DOMContentLoaded', function () {
    const campoCosto = document.getElementById('id_precio_costo');
    const campoVenta = document.getElementById('id_precio_venta');
    if (!campoCosto || !campoVenta) return;

    // ── Niveles del semáforo ─────────────────────────────────────────────────
    // margen_min: margen mínimo (sobre precio_venta) para ENTRAR a ese nivel
    // El precio mínimo para cada nivel = ceil(costo_real / (1 - margen_min))
    const NIVELES = [
        { simbolo: '⚫', label: 'Pérdida',       color: '#212121', margen_min: -Infinity, margen_max: 0.00 },
        { simbolo: '🔴', label: 'Sobrevivencia', color: '#E53935', margen_min: 0.00,      margen_max: 0.10 },
        { simbolo: '🟡', label: 'Neutro',        color: '#F9A825', margen_min: 0.10,      margen_max: 0.18 },
        { simbolo: '🟢', label: 'Saludable',     color: '#43A047', margen_min: 0.18,      margen_max: 0.26 },
        { simbolo: '🔥', label: 'Óptimo',        color: '#FB8C00', margen_min: 0.26,      margen_max: 0.36 },
        { simbolo: '🟣', label: 'Illidari',      color: '#6A1B9A', margen_min: 0.36,      margen_max: Infinity },
    ];

    // ── Panel semáforo ───────────────────────────────────────────────────────
    const panel = document.createElement('div');
    panel.id = 'vts-semaforo';
    panel.style.cssText = `
        margin-top: 10px;
        padding: 10px 14px;
        border-radius: 6px;
        background: #1a1a2e;
        border: 1px solid #2d2d4e;
        font-family: 'Courier New', monospace;
    `;
    panel.innerHTML = '<p style="color:#666; font-size:0.82rem; margin:0;">Ingrese costo para ver semáforo.</p>';

    // Insertar panel después del campo de venta
    const ventaRow = campoVenta.closest('.form-row, .fieldBox, p, div');
    if (ventaRow) ventaRow.after(panel);
    else campoVenta.after(panel);

    let config = null;

    // ── Cargar config desde API ──────────────────────────────────────────────
    fetch('/api/config-costos/')
        .then(r => r.json())
        .then(data => {
            config = data;
            recalcular();
        })
        .catch(() => {
            // Fallback a defaults si la API falla
            config = {
                sumup_pct:      0.03,
                internet_pct:   0.04,
                transporte_pct: 0.05,
            };
            recalcular();
        });

    // ── Calcular factor operativo total (sumando todos los _pct que no sean iva) ──
    function factorOperativo(cfg) {
        let factor = 0;
        for (const [clave, valor] of Object.entries(cfg)) {
            if (clave.endsWith('_pct') && clave !== 'iva') {
                factor += parseFloat(valor) || 0;
            }
        }
        return factor;
    }

    // ── Precio mínimo para alcanzar un margen dado (redondeado hacia arriba) ──
    // precio_minimo = costo_real / (1 - margen_objetivo)
    // Para margen_min = -Infinity (pérdida) → mostrar el precio donde ya estás perdiendo
    function precioMinimo(costoReal, margenObj) {
        if (!isFinite(margenObj) || margenObj <= 0) return 0;          // nivel pérdida → no tiene mínimo
        if (margenObj >= 1) return Infinity;
        return Math.ceil(costoReal / (1 - margenObj));
    }

    // ── Función principal ────────────────────────────────────────────────────
    function recalcular() {
        if (!config) return;

        const costo = parseFloat(campoCosto.value) || 0;
        const venta = parseFloat(campoVenta.value) || 0;

        if (costo <= 0) {
            panel.innerHTML = '<p style="color:#666; font-size:0.82rem; margin:0;">Ingrese costo para ver semáforo.</p>';
            return;
        }

        const factor    = factorOperativo(config);
        const costoReal = costo * (1 + factor);

        // Margen actual (solo si hay precio de venta ingresado)
        const margenActual = venta > 0 ? (venta - costoReal) / venta : null;

        // Determinar nivel actual
        let nivelActual = NIVELES[0];
        if (venta > 0) {
            for (const n of NIVELES) {
                if (margenActual >= n.margen_min) nivelActual = n;
            }
        }

        // ── Construir fila de semáforos ──────────────────────────────────────
        // Para cada nivel mostrar: simbolo $precioMinimo
        // El nivel activo se resalta
        const tarjetas = NIVELES.map((n, i) => {
            const esPerdida = n.margen_min === -Infinity;
            const esIllidari = n.margen_max === Infinity;

            // Precio mínimo para entrar a este nivel
            let pmin;
            if (esPerdida) {
                pmin = '—';  // pérdida no tiene precio mínimo
            } else {
                const val = precioMinimo(costoReal, n.margen_min);
                pmin = isFinite(val) ? '$' + val.toLocaleString('es-CL') : '—';
            }

            const esActivo = venta > 0 && n === nivelActual;
            const opacity  = (!esActivo && venta > 0) ? '0.45' : '1';
            const escala   = esActivo ? 'scale(1.08)' : 'scale(1)';
            const borde    = esActivo ? `2px solid ${n.color}` : '2px solid transparent';
            const bg       = esActivo ? `${n.color}22` : 'transparent';

            return `
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 6px 10px;
                    border-radius: 6px;
                    border: ${borde};
                    background: ${bg};
                    opacity: ${opacity};
                    transform: ${escala};
                    transition: all 0.2s ease;
                    min-width: 80px;
                ">
                    <span style="font-size: 1.4rem; line-height:1;">${n.simbolo}</span>
                    <span style="color: ${n.color}; font-size: 0.68rem; font-weight: bold; margin-top:2px; letter-spacing:0.05em;">${n.label.toUpperCase()}</span>
                    <span style="color: #c8c8d8; font-size: 0.85rem; font-weight: bold; margin-top:3px;">${pmin}</span>
                </div>
            `;
        }).join('');

        // ── Info línea inferior ──────────────────────────────────────────────
        let infoLinea = '';
        if (venta > 0) {
            const ganancia     = venta - costoReal;
            const pct          = (margenActual * 100).toFixed(1);
            const colorPct     = nivelActual.color;
            const signo        = ganancia >= 0 ? '+' : '';
            infoLinea = `
                <div style="
                    margin-top: 8px;
                    padding-top: 7px;
                    border-top: 1px solid #2d2d4e;
                    display: flex;
                    gap: 18px;
                    font-size: 0.78rem;
                    color: #888;
                ">
                    <span>Costo real: <b style="color:#aaa">$${Math.ceil(costoReal).toLocaleString('es-CL')}</b></span>
                    <span>Margen: <b style="color:${colorPct}">${pct}%</b></span>
                    <span>Ganancia unit.: <b style="color:${colorPct}">${signo}$${Math.round(ganancia).toLocaleString('es-CL')}</b></span>
                </div>
            `;
        } else {
            infoLinea = `
                <div style="margin-top:8px; font-size:0.75rem; color:#555;">
                    Costo real estimado: <b style="color:#888">$${Math.ceil(costoReal).toLocaleString('es-CL')}</b>
                    &nbsp;·&nbsp; Ingrese precio de venta para ver nivel activo.
                </div>
            `;
        }

        panel.innerHTML = `
            <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:flex-start;">
                ${tarjetas}
            </div>
            ${infoLinea}
        `;
    }

    campoCosto.addEventListener('input', recalcular);
    campoVenta.addEventListener('input', recalcular);
});