/**
 * VTS - charts.js v1.0.0
 * Gráficos del dashboard principal.
 * Lee variables inyectadas por el template (window.chartLabels, etc.)
 * Depende de: Chart.js (cargado antes en base.html)
 */

document.addEventListener('DOMContentLoaded', function () {

    // ── GRÁFICO 1: Valor por Sección ─────────────────────────────
    const ctxPerdidas = document.getElementById('perdidasSeccionChart');
    if (ctxPerdidas && window.chartLabels && window.chartData) {
        new Chart(ctxPerdidas, {
            type: 'bar',
            data: {
                labels: window.chartLabels,
                datasets: [{
                    label: 'Valor Invertido ($)',
                    data: window.chartData,
                    backgroundColor: 'rgba(75, 73, 172, 0.7)',
                    borderColor: '#4B49AC',
                    borderWidth: 2,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // ── GRÁFICO 2: ROI Proyectado ─────────────────────────────────
    const ctxRoi = document.getElementById('roiChart');
    if (ctxRoi && window.roiLabels && window.roiData) {
        new Chart(ctxRoi, {
            type: 'bar',
            data: {
                labels: window.roiLabels,
                datasets: [{
                    label: 'ROI (%)',
                    data: window.roiData,
                    backgroundColor: 'rgba(255, 193, 7, 0.7)',
                    borderColor: '#ffc107',
                    borderWidth: 2,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

});