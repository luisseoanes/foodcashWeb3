// Lógica del Menú Lateral
const sidebarToggle = document.getElementById('sidebar-toggle');
if(sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        document.querySelector('.wrapper').classList.toggle('collapse');
    });
}

document.addEventListener("DOMContentLoaded", async function () {
    const apiURL = "https://web-production-b7e6.up.railway.app";

    // --- FUNCIONES DE AUTENTICACIÓN (USANDO localStorage) ---
    function obtenerTokenDeLocalStorage() {
        return localStorage.getItem("jwtToken");
    }
    function obtenerUsuarioDeLocalStorage() {
        const data = localStorage.getItem("usuario");
        try {
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error("Error al parsear datos de usuario de localStorage:", e);
            limpiarSesionDeLocalStorage();
            return null;
        }
    }
    function limpiarSesionDeLocalStorage() {
        localStorage.removeItem("jwtToken");
        localStorage.removeItem("usuario");
        sessionStorage.removeItem("selectedStudent");
    }
    async function hacerPeticionAutenticada(url, options = {}) {
        const token = obtenerTokenDeLocalStorage();
        if (!token) {
            console.error("No hay token, redirigiendo a login.");
            limpiarSesionDeLocalStorage();
            window.location.href = "login.html";
            throw new Error("No hay token de autenticación");
        }
        const headers = {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
            ...options.headers,
        };
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401 || response.status === 403) {
            console.error("Token inválido/expirado o sin permiso (401/403). Redirigiendo a login.");
            limpiarSesionDeLocalStorage();
            window.location.href = "login.html";
            throw new Error("Sesión expirada o no autorizada");
        }
        return response;
    }

    // --- FUNCIONES DE UI ---
    function mostrarMensaje(mensaje, tipo = "info") {
        let alertElement = document.getElementById("alert-messages");
        if (!alertElement) {
            alertElement = document.createElement("div");
            alertElement.id = "alert-messages";
            alertElement.style.cssText =
                "position:fixed; top:60px; right:20px; z-index:1050; padding:10px; border-radius:5px;";
            document.body.appendChild(alertElement);
        }

        alertElement.textContent = mensaje;
        alertElement.className = `alert alert-${tipo}`;
        alertElement.style.display = "block";

        if (tipo !== "success") {
            setTimeout(() => {
                if (alertElement) alertElement.style.display = "none";
            }, 7000);
        }
    }

    function formatearSaldo(saldo) {
        const saldoNumerico = parseFloat(saldo);
        if (isNaN(saldoNumerico)) {
            return (0).toLocaleString("es-CO", {
                style: "currency",
                currency: "COP",
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            });
        }
        return saldoNumerico.toLocaleString("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });
    }

    function formatearFecha(fecha) {
        try {
            const fechaObj = new Date(fecha);
            return fechaObj.toLocaleDateString("es-CO", {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch (error) {
            console.error("Error formateando fecha:", error);
            return "Fecha inválida";
        }
    }

    function limpiarTablaCompras() {
        const tbody = document.querySelector(".table100-body tbody");
        if (tbody) {
            tbody.innerHTML = `
                <tr class="row100 body">
                    <td class="cell100 column1" colspan="4" style="text-align: center;">
                        Seleccione un estudiante para ver sus compras.
                    </td>
                </tr>
            `;
        }
    }

    // --- INICIO DE LÓGICA DE PÁGINA ---
    const usuarioData = obtenerUsuarioDeLocalStorage();
    const jwtToken = obtenerTokenDeLocalStorage();

    if (!usuarioData || !jwtToken) {
        console.error("No se encontró usuarioData o jwtToken. Redirigiendo a login.");
        window.location.href = "login.html";
        return;
    }

    const rolesPermitidos = ["padre", "usuario"];
    const rol = (usuarioData.rol || "").toLowerCase();

switch (rol) {
    case "padre":
    case "usuario":
        // Rol permitido, continúa
        break;

    case "admin":
    case "administrador":
        window.location.href = "pages/administrador/admin.html";
        return;

    case "vendedor":
        window.location.href = "pages/Vendedor/pos.html";
        return;

    case "profesor":
        window.location.href = "pages/profesores/profesores.html";
        return;

    default:
        console.error(`Rol no reconocido ('${usuarioData.rol}'). Redirigiendo a login.`);
        limpiarSesionDeLocalStorage();
        window.location.href = "login.html";
        return;
}


    // --- ELEMENTOS DEL DOM ---
    const nombreUsuarioElement = document.getElementById("nombre-usuario");
    const selectorEstudiante = document.getElementById("estudiante-selector");
    const saldoElemento = document.getElementById("saldo-usuario");
    const logoutLink = document.querySelector('a[href="logout.html"]');

    // Mostrar nombre de usuario
    if (nombreUsuarioElement) {
        nombreUsuarioElement.textContent = usuarioData.nombre || "Padre/Madre";
    } else {
        console.warn("Elemento #nombre-usuario no encontrado.");
    }

    // --- FUNCIÓN PARA ACTUALIZAR LA TABLA ---
    function actualizarTablaCompras(compras) {
        const tbody = document.querySelector(".table100-body tbody");
        if (!tbody) {
            console.error("No se encontró el tbody de la tabla de compras.");
            return;
        }

        tbody.innerHTML = ""; // Limpiar contenido

        if (!compras || compras.length === 0) {
            tbody.innerHTML = `
                <tr class="row100 body">
                    <td class="cell100 column1" colspan="4" style="text-align: center;">
                        No hay compras registradas para este estudiante.
                    </td>
                </tr>
            `;
            return;
        }

        // Ordenar por fecha descendente y tomar las primeras 5
        const comprasOrdenadas = compras
            .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
            .slice(0, 5);

        comprasOrdenadas.forEach((compra, index) => {
            try {
                const fila = document.createElement("tr");
                fila.className = "row100 body";

                // Formatear fecha y total
                const fechaFormateada = formatearFecha(compra.fecha);
                const totalFormateado = formatearSaldo(compra.total || 0);

                // Construir lista de productos con nombre y cantidad
                let productosListado = "Detalle no disponible";
                let caloriasTotales = 0;
                if (compra.items && Array.isArray(compra.items) && compra.items.length > 0) {
                    productosListado = compra.items
                        .map(item => `${item.nombre_alimento || "Producto"}`)
                        .join(" - ");
                    caloriasTotales = compra.items.reduce((sum, item) => {
                        // Se asume que item.calorias es calorías por 100 unidades
                        const caloriasUnitarias = parseFloat(item.calorias) || 0;
                        return sum + (caloriasUnitarias * item.cantidad);
                    }, 0);
                }

                fila.innerHTML = `
                    <td class="cell100 column1">${fechaFormateada}</td>
                    <td class="cell100 column2">${productosListado}</td>
                    <td class="cell100 column4">${Math.round(caloriasTotales)} Cal</td>
                    <td class="cell100 column5">${totalFormateado}</td>
                `;
                tbody.appendChild(fila);
            } catch (error) {
                console.error(`Error procesando compra índice ${index}:`, error, compra);
            }
        });

        if (compras.length > 5) {
            const filaInfo = document.createElement("tr");
            filaInfo.className = "row100 body";
            filaInfo.innerHTML = `
                <td class="cell100 column1" colspan="4" style="text-align: center; font-style: italic; color: #666;">
                    Mostrando las últimas 5 compras de ${compras.length} totales
                </td>
            `;
            tbody.appendChild(filaInfo);
        }
    }

    // --- FUNCIÓN PARA CARGAR COMPRAS DE UN ESTUDIANTE ---
    async function cargarComprasEstudiante(estudianteId) {
        if (!estudianteId) {
            console.warn("No se ha seleccionado un estudiante.");
            limpiarTablaCompras();
            return;
        }

        try {
            const idNumerico = parseInt(estudianteId);
            if (isNaN(idNumerico)) {
                throw new Error("ID de estudiante no válido");
            }

            const response = await hacerPeticionAutenticada(
                `${apiURL}/compras/usuario/${idNumerico}`,
                { method: "GET" }
            );

            if (!response.ok) {
                let errorData;
                try {
                    const text = await response.text();
                    errorData = text.trim() ? JSON.parse(text) : { detail: response.statusText };
                } catch {
                    errorData = { detail: response.statusText };
                }

                if (response.status === 404) {
                    console.warn("Usuario no encontrado para ID:", idNumerico);
                    limpiarTablaCompras();
                    mostrarMensaje("No se encontraron registros para este estudiante.", "warning");
                    return;
                }
                if (response.status === 500) {
                    console.error("Error interno del servidor para usuario ID:", idNumerico);
                    limpiarTablaCompras();
                    mostrarMensaje("Error interno del servidor. Contacte al administrador.", "danger");
                    return;
                }
                throw new Error(`Error ${response.status}: ${errorData.detail || response.statusText}`);
            }

            const compras = await response.json();
            if (!Array.isArray(compras)) {
                console.error("Formato de respuesta inesperado:", compras);
                throw new Error("Respuesta del servidor no es un array");
            }

            actualizarTablaCompras(compras);
        } catch (error) {
            console.error("Error cargando compras:", error);
            if (error.message.toLowerCase().includes("sesión expirada")) return;
            mostrarMensaje(`No se pudieron cargar las compras: ${error.message}`, "danger");
            limpiarTablaCompras();
        }
    }

    function actualizarSaldoYCompras() {
        if (
            !selectorEstudiante ||
            selectorEstudiante.options.length === 0 ||
            !saldoElemento
        )
            return;
        const opcion = selectorEstudiante.options[selectorEstudiante.selectedIndex];
        if (opcion && opcion.value && opcion.getAttribute("data-saldo")) {
            saldoElemento.textContent = formatearSaldo(opcion.getAttribute("data-saldo"));
            cargarComprasEstudiante(opcion.value);
        } else {
            saldoElemento.textContent = formatearSaldo(0);
            limpiarTablaCompras();
        }
    }

    // --- FUNCIÓN PARA CARGAR “HIJOS” (ESTUDIANTES) ---
    async function cargarHijos() {
        if (!selectorEstudiante) {
            console.error("El elemento #estudiante-selector no existe.");
            mostrarMensaje("Error de interfaz: falta selector de estudiantes.", "danger");
            return;
        }
        if (!usuarioData || !usuarioData.nombre) {
            console.error("No hay datos de usuario para cargar hijos.");
            mostrarMensaje("Error: No se pudo identificar al responsable.", "danger");
            return;
        }

        try {
            const response = await hacerPeticionAutenticada(
                `${apiURL}/estudiantes/${encodeURIComponent(usuarioData.nombre)}/hijos`,
                { method: "GET" }
            );
            if (!response.ok) {
                const errorData = await response
                    .json()
                    .catch(() => ({ detail: response.statusText }));
                throw new Error(`Error ${response.status}: ${errorData.detail || response.statusText}`);
            }

            const hijos = await response.json();
            selectorEstudiante.innerHTML = "";

            if (Array.isArray(hijos) && hijos.length > 0) {
                hijos.forEach((hijo) => {
                    const option = document.createElement("option");
                    option.value = hijo.id;
                    option.setAttribute("data-saldo", hijo.saldo || 0);
                    option.textContent = hijo.nombre;
                    selectorEstudiante.appendChild(option);
                });

                const savedStudent = sessionStorage.getItem("selectedStudent");
                if (
                    savedStudent &&
                    Array.from(selectorEstudiante.options).some(
                        (opt) => opt.value === savedStudent
                    )
                ) {
                    selectorEstudiante.value = savedStudent;
                } else if (selectorEstudiante.options.length > 0) {
                    selectorEstudiante.selectedIndex = 0;
                }

                actualizarSaldoYCompras();
            } else {
                selectorEstudiante.innerHTML = "<option value=''>No se encontraron hijos</option>";
                saldoElemento.textContent = formatearSaldo(0);
                limpiarTablaCompras();
                mostrarMensaje("No tiene estudiantes asociados.", "warning");
            }
        } catch (error) {
            console.error("Error cargando hijos:", error);
            if (error.message.toLowerCase().includes("sesión expirada")) return;
            mostrarMensaje(`No se pudo cargar la lista de hijos: ${error.message}`, "danger");
            selectorEstudiante.innerHTML = "<option>Error al cargar</option>";
            saldoElemento.textContent = formatearSaldo(0);
            limpiarTablaCompras();
        }
    }

    // --- EVENT LISTENERS ---
    if (selectorEstudiante) {
        selectorEstudiante.addEventListener("change", function () {
            actualizarSaldoYCompras();
            sessionStorage.setItem("selectedStudent", selectorEstudiante.value);
        });
    } else {
        console.warn("El elemento #estudiante-selector no se encontró.");
    }

   

    // Carga inicial de hijos (luego se cargarán las compras del primero seleccionado)
    cargarHijos();
});
