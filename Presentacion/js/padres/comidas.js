// Lógica del Menú Lateral
const sidebarToggle = document.getElementById('sidebar-toggle');
if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        document.querySelector('.wrapper').classList.toggle('collapse');
    });
}

document.addEventListener("DOMContentLoaded", async function () {
    const apiURL = "https://web-production-b7e6.up.railway.app";

    // -------------------------------------------------------------------
    // --- 1. FUNCIONES DE AUTENTICACIÓN Y API ---------------------------
    // -------------------------------------------------------------------

    function obtenerTokenDeLocalStorage() {
        return localStorage.getItem("jwtToken");
    }

    function obtenerUsuarioDeLocalStorage() {
        const data = localStorage.getItem("usuario");
        try {
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error("Error al parsear datos de usuario:", e);
            limpiarSesionDeLocalStorage();
            return null;
        }
    }

    // <-- CAMBIO: Funciones para manejar la sesión del estudiante.
    function guardarHijoSeleccionado(estudianteId) {
        sessionStorage.setItem('selectedStudent', estudianteId);
    }

    function obtenerHijoSeleccionado() {
        return sessionStorage.getItem('selectedStudent');
    }
    // -- FIN DEL CAMBIO --

    function limpiarSesionDeLocalStorage() {
        localStorage.removeItem("jwtToken");
        localStorage.removeItem("usuario");
        sessionStorage.removeItem("selectedStudent"); // También limpiar la selección de estudiante al cerrar sesión.
    }

    async function hacerPeticionAutenticada(url, options = {}) {
        const token = obtenerTokenDeLocalStorage();
        if (!token) {
            console.error("No hay token, redirigiendo a login.");
            limpiarSesionDeLocalStorage();
            window.location.href = "../login.html";
            throw new Error("No hay token de autenticación");
        }

        const headers = {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
            ...options.headers,
        };

        const response = await fetch(url, { ...options, headers });

        if (response.status === 401 || response.status === 403) {
            console.error("Token inválido/expirado. Redirigiendo a login.");
            limpiarSesionDeLocalStorage();
            window.location.href = "../login.html";
            throw new Error("Sesión expirada o no autorizada");
        }

        return response;
    }

    // -------------------------------------------------------------------
    // --- 2. FUNCIONES DE LA INTERFAZ DE USUARIO (UI) -------------------
    // -------------------------------------------------------------------

    function mostrarError(mensaje) {
        const errorContainer = document.getElementById("error-container");
        const errorMessage = document.getElementById("error-message-text");
        if (errorContainer && errorMessage) {
            errorMessage.textContent = mensaje;
            errorContainer.style.display = "block";
        }
        document.getElementById("loading-container").style.display = "none";
        document.getElementById("alimentos-grid").style.display = "none";
        document.getElementById("no-alimentos").style.display = "none";
        console.error("Error:", mensaje);
    }

    function ocultarError() {
        const errorContainer = document.getElementById("error-container");
        if (errorContainer) {
            errorContainer.style.display = "none";
        }
    }

    function formatearPrecio(precio) {
        const precioNum = parseFloat(precio) || 0;
        return precioNum.toLocaleString("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });
    }

    function obtenerEstudianteSeleccionadoID() { // <-- CAMBIO: Nombre más claro para evitar confusión.
        const selector = document.getElementById("estudiante-selector");
        return selector ? selector.value : null;
    }

    // -------------------------------------------------------------------
    // --- 3. FUNCIONES PRINCIPALES DE LA PÁGINA -------------------------
    // -------------------------------------------------------------------

    async function cargarAlimentos(filtros = {}) {
        try {
            ocultarError();
            document.getElementById("loading-container").style.display = "flex";
            document.getElementById("alimentos-grid").style.display = "none";
            document.getElementById("no-alimentos").style.display = "none";

            let url = `${apiURL}/api/alimentos/`;
            const params = new URLSearchParams();

            if (filtros.nombre) params.append("nombre", filtros.nombre);
            if (filtros.categoria) params.append("categoria", filtros.categoria);

            if (params.toString()) {
                url += `?${params.toString()}`;
            }

            const response = await hacerPeticionAutenticada(url, { method: "GET" });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`Error ${response.status}: ${errorData.detail || response.statusText}`);
            }

            const data = await response.json();
            let alimentos = Array.isArray(data) ? data : (data.results || []);

            const alimentosFiltrados = alimentos.filter(alimento => {
                const precio = parseFloat(alimento.precio);
                if (filtros.precioMin != null && precio < filtros.precioMin) return false;
                if (filtros.precioMax != null && precio > filtros.precioMax) return false;
                return true;
            });

            // Cargar estado de bloqueo para cada alimento
            const estudianteId = obtenerEstudianteSeleccionadoID();
            if (estudianteId) {
                await cargarEstadoBloqueo(alimentosFiltrados, estudianteId);
            }

            mostrarAlimentos(alimentosFiltrados);
            actualizarEstadisticas(alimentos);
            if (document.getElementById("filtro-categoria").options.length <= 1) {
                actualizarCategorias(alimentos);
            }

        } catch (error) {
            console.error("Error cargando alimentos:", error);
            mostrarError(`No se pudieron cargar los alimentos: ${error.message}`);
        } finally {
            document.getElementById("loading-container").style.display = "none";
        }
    }

    async function cargarEstadoBloqueo(alimentos, estudianteId) {
        try {
            const response = await hacerPeticionAutenticada(
                `${apiURL}/estudiantes/${estudianteId}/alimentosBloqueados`, 
                { method: "GET" }
            );

            if (response.ok) {
                const alimentosBloqueados = await response.json();
                const idsAlimentosBloqueados = new Set(
                    alimentosBloqueados.map(ab => ab.id_alimento)
                );

                alimentos.forEach(alimento => {
                    alimento.esta_bloqueado = idsAlimentosBloqueados.has(alimento.id);
                });
            }
        } catch (error) {
            console.error("Error cargando estado de bloqueo:", error);
            alimentos.forEach(alimento => {
                alimento.esta_bloqueado = false;
            });
        }
    }

    function mostrarAlimentos(alimentos) {
        const grid = document.getElementById("alimentos-grid");
        const noAlimentos = document.getElementById("no-alimentos");

        if (!alimentos || alimentos.length === 0) {
            grid.style.display = "none";
            noAlimentos.style.display = "block";
            grid.innerHTML = "";
            return;
        }

        grid.innerHTML = "";
        grid.style.display = "grid";
        noAlimentos.style.display = "none";

        alimentos.forEach(alimento => {
            const card = document.createElement("div");
            card.className = "alimento-card";
            card.setAttribute('data-id', alimento.id);

            const estaBloqueado = alimento.esta_bloqueado || false;
            if (estaBloqueado) {
                card.classList.add('bloqueado');
            }

            const precio = parseFloat(alimento.precio) || 0;
            const calorias = parseInt(alimento.calorias) || 0;
            
            card.innerHTML = `
                <div class="alimento-imagen">
                    ${alimento.imagen ? `<img src="${alimento.imagen}" alt="${alimento.nombre}" style="width:100%;height:100%;object-fit:cover;border-radius:8px;">` : `<i class="fas fa-utensils"></i>`}
                </div>
                <div class="alimento-categoria">${alimento.categoria || 'Sin categoría'}</div>
                <div class="alimento-nombre">${alimento.nombre || 'Sin nombre'}</div>
                
                <div class="alimento-info">
                    <div class="info-item">
                        <div class="info-label">Precio</div>
                        <div class="info-value precio-value">${formatearPrecio(precio)}</div>
                    </div>
                    
                    <div class="info-item">
                        <div class="info-label">Acción</div>
                        <div class="info-value">
                            <label class="switch">
                                <input type="checkbox" ${estaBloqueado ? 'checked' : ''} onchange="cambiarEstadoBloqueo(this, '${alimento.id}')">
                                <span class="slider round"></span>
                            </label>
                        </div>
                    </div>

                    <div class="info-item">
                        <div class="info-label">Calorías</div>
                        <div class="info-value calorias-value">${calorias} Cal</div>
                    </div>

                    <div class="info-item">
                        <div class="info-label">Estado</div>
                        <div class="info-value estado-bloqueo ${estaBloqueado ? 'estado-bloqueado' : 'estado-activo'}">
                            ${estaBloqueado ? 'Bloqueado' : 'Activo'}
                        </div>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    function actualizarEstadisticas(alimentos) {
        document.getElementById("total-alimentos").textContent = alimentos.length;
        document.getElementById("total-categorias").textContent = [...new Set(alimentos.map(a => a.categoria).filter(c => c))].length;
    }

    function actualizarCategorias(alimentos) {
        const select = document.getElementById("filtro-categoria");
        const categorias = [...new Set(alimentos.map(a => a.categoria).filter(c => c))].sort();
        select.innerHTML = '<option value="">Todas las categorías</option>';
        categorias.forEach(categoria => {
            const option = document.createElement("option");
            option.value = categoria;
            option.textContent = categoria;
            select.appendChild(option);
        });
    }

    // <-- CAMBIO: Función `cargarHijos` modificada para aplicar la selección guardada.
    async function cargarHijos() {
        const selectorEstudiante = document.getElementById("estudiante-selector");
        const saldoElemento = document.getElementById("saldo-usuario");
        const usuario = obtenerUsuarioDeLocalStorage();

        if (!selectorEstudiante || !usuario?.nombre) return;

        try {
            const response = await hacerPeticionAutenticada(`${apiURL}/estudiantes/${encodeURIComponent(usuario.nombre)}/hijos`, { method: "GET" });
            if (!response.ok) throw new Error("Error cargando hijos");

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

                // Aplicar la selección guardada desde sessionStorage
                const hijoGuardado = obtenerHijoSeleccionado();
                if (hijoGuardado && selectorEstudiante.querySelector(`option[value="${hijoGuardado}"]`)) {
                    selectorEstudiante.value = hijoGuardado;
                }
                
                // Actualizar el saldo del estudiante actualmente seleccionado
                const opcionSeleccionada = selectorEstudiante.options[selectorEstudiante.selectedIndex];
                if (saldoElemento && opcionSeleccionada) {
                    saldoElemento.textContent = formatearPrecio(opcionSeleccionada.getAttribute("data-saldo") || 0);
                }

            } else {
                selectorEstudiante.innerHTML = "<option value=''>No hay hijos</option>";
                if (saldoElemento) saldoElemento.textContent = formatearPrecio(0);
            }
        } catch (error) {
            console.error("Error cargando hijos:", error);
        }
    }

    // -------------------------------------------------------------------
    // --- 4. FUNCIÓN PARA CONTROL PARENTAL (BLOQUEO) --------------------
    // -------------------------------------------------------------------

    window.cambiarEstadoBloqueo = async function(checkbox, alimentoId) {
        const estudianteId = obtenerEstudianteSeleccionadoID();
        
        if (!estudianteId) {
            alert("Por favor selecciona un estudiante primero.");
            checkbox.checked = !checkbox.checked;
            return;
        }

        const esParaBloquear = checkbox.checked;
        const card = checkbox.closest('.alimento-card');
        checkbox.disabled = true;

        try {
            let response;
            if (esParaBloquear) {
                response = await hacerPeticionAutenticada(
                    `${apiURL}/estudiantes/${estudianteId}/bloquearAlimento`, 
                    {
                        method: 'POST',
                        body: JSON.stringify({ id_alimento: parseInt(alimentoId) })
                    }
                );
            } else {
                response = await hacerPeticionAutenticada(
                    `${apiURL}/estudiantes/${estudianteId}/desbloquearAlimento/${alimentoId}`, 
                    { method: 'DELETE' }
                );
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'La acción no se pudo completar en el servidor.');
            }

            const estadoTexto = card.querySelector('.estado-bloqueo');
            if (esParaBloquear) {
                card.classList.add('bloqueado');
                estadoTexto.textContent = 'Bloqueado';
                estadoTexto.classList.remove('estado-activo');
                estadoTexto.classList.add('estado-bloqueado');
            } else {
                card.classList.remove('bloqueado');
                estadoTexto.textContent = 'Activo';
                estadoTexto.classList.remove('estado-bloqueado');
                estadoTexto.classList.add('estado-activo');
            }
            mostrarMensajeExito(esParaBloquear ? 'Alimento bloqueado exitosamente' : 'Alimento desbloqueado exitosamente');
        } catch (error) {
            console.error("Error al cambiar estado de bloqueo:", error);
            alert(`Error: ${error.message}`);
            checkbox.checked = !esParaBloquear;
        } finally {
            checkbox.disabled = false;
        }
    }

    function mostrarMensajeExito(mensaje) {
        let mensajeContainer = document.getElementById('mensaje-exito');
        if (!mensajeContainer) {
            mensajeContainer = document.createElement('div');
            mensajeContainer.id = 'mensaje-exito';
            mensajeContainer.style.cssText = `
                position: fixed; top: 20px; right: 20px;
                background-color: #4CAF50; color: white;
                padding: 12px 24px; border-radius: 4px;
                z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            `;
            document.body.appendChild(mensajeContainer);
        }
        mensajeContainer.textContent = mensaje;
        mensajeContainer.style.display = 'block';
        setTimeout(() => {
            mensajeContainer.style.display = 'none';
        }, 3000);
    }

    // -------------------------------------------------------------------
    // --- 5. INICIALIZACIÓN Y EVENT LISTENERS ---------------------------
    // -------------------------------------------------------------------

    window.aplicarFiltros = function() {
        const filtros = {
            nombre: document.getElementById("filtro-nombre").value.trim(),
            categoria: document.getElementById("filtro-categoria").value,
            precioMin: document.getElementById("filtro-precio-min").value ? parseFloat(document.getElementById("filtro-precio-min").value) : null,
            precioMax: document.getElementById("filtro-precio-max").value ? parseFloat(document.getElementById("filtro-precio-max").value) : null
        };
        cargarAlimentos(filtros);
    };

    window.limpiarFiltros = function() {
        document.getElementById("filtro-nombre").value = "";
        document.getElementById("filtro-categoria").value = "";
        document.getElementById("filtro-precio-min").value = "";
        document.getElementById("filtro-precio-max").value = "";
        cargarAlimentos();
    };
    
    const usuarioData = obtenerUsuarioDeLocalStorage();
    if (!usuarioData) {
        window.location.href = "../login.html";
        return;
    }
    
    document.getElementById("filtro-nombre").addEventListener("input", function() {
        if (this.value.length >= 2 || this.value.length === 0) {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(aplicarFiltros, 300);
        }
    });

    // <-- CAMBIO: Event listener para el selector de estudiante modificado.
    document.getElementById("estudiante-selector")?.addEventListener("change", function() {
        // 1. Guardar la nueva selección en la sesión.
        guardarHijoSeleccionado(this.value);

        // 2. Actualizar el saldo en la UI.
        const opcion = this.options[this.selectedIndex];
        const saldoElemento = document.getElementById("saldo-usuario");
        if (opcion && saldoElemento) {
            saldoElemento.textContent = formatearPrecio(opcion.getAttribute("data-saldo") || 0);
        }
        
        // 3. Recargar alimentos para actualizar los estados de bloqueo.
        cargarAlimentos();
    });
    
    async function init() {
        await cargarHijos(); // Carga los hijos y aplica la selección guardada.
        await cargarAlimentos(); // Carga los alimentos para el estudiante ya seleccionado.
    }

    init();
});