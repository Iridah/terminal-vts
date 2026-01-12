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