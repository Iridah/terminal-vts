$(document).ready(function() {
    console.log("Martillo Vil: JS Cargado y listo.");

    // Asegurar que los modales se inicialicen correctamente
    $('.modal').modal({
        show: false,
        backdrop: 'static'
    });

    // Limpieza automática de restos de modales al cerrar
    $('.modal').on('hidden.bs.modal', function () {
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();
    });
});

// Función esencial para que Django acepte el POST
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

function registrarAporteHogar(event) {
    // 1. Prevenir que la página se recargue (F5)
    if (event) event.preventDefault();

    // 2. Capturar el SKU desde el título del modal
    // Buscamos el modal que está actualmente visible (el que clickeaste)
    const modalActivo = event.target.closest('.modal');
    // Buscamos la referencia del SKU dentro de ESE modal específico
    const skuElement = modalActivo.querySelector('.modal-sku-reference');
    if (!skuElement) {
        alert("Error: No se encontró el SKU en el modal.");
        return;
    }

    // Usamos el atributo data-sku que es mucho más limpio que limpiar texto
    const sku = skuElement.getAttribute('data-sku');
    // 3. Pedir la cantidad
    const cantidad = prompt(`¿Cuántas unidades de ${sku} se retiran para Aporte Hogar?`, "1");
    
    // 4. Validar y enviar
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
                alert(`✅ Retiro exitoso de ${sku}. Stock actual: ${data.nuevo_stock}`);
                location.reload(); 
            } else {
                alert("❌ Error: " + data.message);
            }
        })
        .catch(error => {
            console.error('Error en fetch:', error);
            alert("Error de conexión con Mardum.");
        });
    }
}