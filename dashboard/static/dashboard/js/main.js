// dashboard/static/dashboard/js/main.js
console.log("Martillo Vil: Motor de estabilidad iniciado.");

// 1. Obtener CSRF Token para seguridad
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

// 2. Validación visual en tiempo real
function validarStock(input) {
    if (input.value < 0) input.value = 0;
    
    if (input.value == 0) {
        input.style.backgroundColor = "#ffe6e6";
        input.classList.add("border-danger");
    } else {
        input.style.backgroundColor = "";
        input.classList.remove("border-danger");
    }
}

// 3. Aporte Hogar unificado (Tabla y Modal)
function registrarAporteHogar(sku, nombre) {
    const cantidad = prompt(`¿Cuántas unidades de ${nombre || sku} se retiran para Aporte Hogar?`, "1");
    
    if (cantidad && !isNaN(cantidad) && cantidad > 0) {
        fetch('/registrar-aporte-hogar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ 
                sku: sku, 
                cantidad: parseInt(cantidad) 
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                location.reload(); 
            } else {
                alert("❌ Error: " + data.message);
            }
        })
        .catch(error => alert("Error de conexión con Mardum."));
    }
}

// Buscador en tiempo real para La Forja
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('vtsSearch');
    
    if (searchInput) {
        console.log("Martillo Vil: Buscador vinculado.");
        
        searchInput.addEventListener('input', function() { // Cambiado de 'keyup' a 'input' para escáneres
            const filter = this.value.toLowerCase().trim();
            const rows = document.querySelectorAll("tbody tr");

            rows.forEach(row => {
                // Buscamos específicamente en SKU (celda 0) y Producto (celda 1)
                const sku = row.cells[0].textContent.toLowerCase();
                const producto = row.cells[1].textContent.toLowerCase();
                
                if (sku.includes(filter) || producto.includes(filter)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }
});