// Asegúrate de que este script se cargue después de jQuery
$(document).ready(function(){
    var wrapper = $(".wrapper");

    $(".hamburger").on("click", function(){
        // Si la pantalla es más ancha que 768px (tableta/escritorio)
        if (window.innerWidth > 768) {
            // Usa la lógica original de 'collapse'
            wrapper.toggleClass("collapse");
        } 
        // Si la pantalla es de 768px o menos (móvil)
        else {
            // Usa la nueva clase para mostrar/ocultar la barra lateral
            wrapper.toggleClass("sidebar-open");
        }
    });
});

