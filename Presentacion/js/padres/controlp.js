// Lógica del Menú Lateral
const sidebarToggle = document.getElementById('sidebar-toggle');
if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        document.querySelector('.wrapper').classList.toggle('collapse');
    });
}

document.addEventListener('DOMContentLoaded', async function () { // Hacemos esta función async
    const apiURL = "https://web-production-b7e6.up.railway.app";

    // Mapa para almacenar todos los alimentos y evitar llamadas repetidas
    const alimentosMap = new Map();

    // FUNCIONES PARA MANEJAR LA SESIÓN DEL ESTUDIANTE ---
    /**
     * Guarda el ID del estudiante seleccionado en sessionStorage.
     * @param {string} estudianteId - El ID del estudiante a guardar.
     */
    function guardarHijoSeleccionado(estudianteId) {
        sessionStorage.setItem('selectedStudent', estudianteId);
    }

    /**
     * Obtiene el ID del estudiante guardado desde sessionStorage.
     * @returns {string|null} - El ID del estudiante guardado o null si no hay ninguno.
     */
    function obtenerHijoSeleccionado() {
        return sessionStorage.getItem('selectedStudent');
    }
    // --- FIN DEL CAMBIO ---

    // Carga todos los alimentos en memoria al iniciar
    async function inicializarAlimentos() {
        try {
            const response = await hacerPeticionAutenticada(`${apiURL}/api/alimentos`);
            if (response.ok) {
                const alimentosList = await response.json();
                alimentosList.forEach(alimento => alimentosMap.set(alimento.id, alimento));
                console.log('Lista de alimentos inicializada en memoria.');
            } else {
                throw new Error('No se pudo obtener la lista de alimentos.');
            }
        } catch (error) {
            console.error("Error crítico al inicializar la lista de alimentos:", error);
        }
    }

    // --- LÓGICA DE PESTAÑAS (TABS) ---
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');

            // Cargar datos específicos de la pestaña si es necesario
            const estudianteId = selectorEstudiante.value;
            if (button.dataset.tab === 'bloqueados') {
                renderizarAlimentosBloqueados(estudianteId);
            }
        });
    });

    // --- FUNCIONES DE AUTENTICACIÓN Y API ---
    function obtenerTokenDeLocalStorage() {
        return localStorage.getItem("jwtToken");
    }

    function obtenerUsuarioDeLocalStorage() {
        try {
            return JSON.parse(localStorage.getItem("usuario"));
        } catch (e) {
            return null;
        }
    }

    async function hacerPeticionAutenticada(url, options = {}) {
        const token = obtenerTokenDeLocalStorage();
        if (!token) {
            window.location.href = "../login.html";
            throw new Error("No autenticado");
        }
        const headers = {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
            ...options.headers
        };
        const response = await fetch(url, {
            ...options,
            headers
        });
        if (response.status === 401 || response.status === 403) {
            window.location.href = "../login.html";
            throw new Error("Sesión expirada");
        }
        return response;
    }

    // --- FUNCIONES DE FORMATO ---
    function formatearSaldo(saldo) {
        return (parseFloat(saldo) || 0).toLocaleString("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    function formatearFecha(fecha) {
        if (!fecha) return 'N/A';
        return new Date(fecha).toLocaleString("es-CO", {
            dateStyle: "short",
            timeStyle: "short"
        });
    }

    // --- ELEMENTOS DEL DOM ---
    const selectorEstudiante = document.getElementById("estudiante-selector");
    const saldoElemento = document.getElementById("saldo-usuario");
    const dailyLimitInput = document.getElementById('daily-limit');
    const saveLimitBtn = document.getElementById('guardar-limite-btn');

    // --- FUNCIONES DE RENDERIZADO DE DATOS ---
    // (Todas las funciones renderizarResumen, renderizarHistorial, etc. se mantienen igual)
    function renderizarResumen(compras, saldo, alimentosBloqueados = [], limiteDiario = 0) {
        document.getElementById("resumen-saldo").textContent = formatearSaldo(saldo);
        const hoy = new Date().toDateString();
        const gastoHoy = compras
            .filter(compra => new Date(compra.fecha).toDateString() === hoy)
            .reduce((total, compra) => total + parseFloat(compra.total || 0), 0);
        document.getElementById("resumen-gasto-hoy").innerHTML =
            `${formatearSaldo(gastoHoy)} <span class="limit">/ ${formatearSaldo(limiteDiario)}</span>`;
        document.getElementById("resumen-bloqueados").textContent = alimentosBloqueados.length;
        const tbody = document.getElementById("resumen-compras-body");
        tbody.innerHTML = "";
        if (!compras || compras.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="text-align:center;">No hay compras recientes.</td></tr>`;
            return;
        }
        const comprasRecientes = compras
            .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
            .slice(0, 5);
        comprasRecientes.forEach(compra => {
            const productos = compra.items.map(item => item.nombre_alimento || "Producto").join(', ');
            tbody.innerHTML += `
                <tr>
                    <td>${formatearFecha(compra.fecha)}</td>
                    <td>${productos}</td>
                    <td>${formatearSaldo(compra.total)}</td>
                </tr>`;
        });
    }

    function renderizarHistorial(compras) {
        const tbody = document.getElementById("historial-compras-body");
        tbody.innerHTML = "";
        if (!compras || compras.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;">No hay historial de compras.</td></tr>`;
            return;
        }
        const comprasOrdenadas = compras.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
        comprasOrdenadas.forEach(compra => {
            const productos = compra.items.map(item => item.nombre_alimento || "Producto").join(', ');
            const categorias = [...new Set(compra.items.map(item => item.categoria || "N/A"))].join(', ');
            tbody.innerHTML += `
                <tr>
                    <td>${formatearFecha(compra.fecha)}</td>
                    <td>${productos}</td>
                    <td>${categorias}</td>
                    <td>${formatearSaldo(compra.total)}</td>
                </tr>`;
        });
    }

    async function renderizarAlimentosBloqueados(estudianteId) {
        const tbody = document.getElementById("bloqueados-body");
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">Cargando...</td></tr>`;
        if (!estudianteId) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">Selecciona un estudiante.</td></tr>`;
            return;
        }
        try {
            const response = await hacerPeticionAutenticada(
                `${apiURL}/estudiantes/${estudianteId}/alimentosBloqueados`, { method: "GET" }
            );
            if (!response.ok) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No hay alimentos bloqueados.</td></tr>`;
                return;
            }
            const listaDeBloqueos = await response.json();
            if (!listaDeBloqueos || listaDeBloqueos.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No hay alimentos bloqueados.</td></tr>`;
                return;
            }
            tbody.innerHTML = "";
            listaDeBloqueos.forEach(bloqueo => {
                const alimento = alimentosMap.get(bloqueo.id_alimento);
                const nombre = alimento ? alimento.nombre : "Alimento no encontrado";
                const categoria = alimento ? alimento.categoria : "N/A";
                const precio = alimento ? alimento.precio : 0;
                const imagen = alimento ? alimento.imagen : null;
                const fila = document.createElement('tr');
                fila.innerHTML = `
                    <td>
                        <div class="alimento-info-cell">
                            <div class="alimento-imagen-small">
                                ${imagen ? `<img src="${imagen}" alt="${nombre}">` : `<i class="fas fa-utensils"></i>`}
                            </div>
                            <div class="alimento-detalles">
                                <div class="alimento-nombre-small">${nombre}</div>
                            </div>
                        </div>
                    </td>
                    <td>${categoria}</td>
                    <td>${formatearSaldo(precio)}</td>
                    <td>${formatearFecha(bloqueo.fecha_bloqueo)}</td>
                    <td>
                        <button class="btn-desbloquear" data-alimento-id="${bloqueo.id_alimento}">
                            <i class="fas fa-unlock"></i> Desbloquear
                        </button>
                    </td>`;
                tbody.appendChild(fila);
            });
        } catch (error) {
            console.error("Error cargando alimentos bloqueados:", error);
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">Error al cargar datos.</td></tr>`;
        }
    }


    // --- MANEJO DE EVENTOS Y ACCIONES---
    // (Las funciones para 'bloqueados-body', 'guardar-limite-btn', etc., se mantienen igual)
    document.getElementById('bloqueados-body').addEventListener('click', async (event) => {
        if (event.target && event.target.closest('.btn-desbloquear')) {
            const button = event.target.closest('.btn-desbloquear');
            const alimentoId = button.dataset.alimentoId;
            const estudianteId = selectorEstudiante.value;
            if (confirm('¿Estás seguro de que quieres desbloquear este alimento?')) {
                try {
                    const response = await hacerPeticionAutenticada(
                        `${apiURL}/estudiantes/${estudianteId}/desbloquearAlimento/${alimentoId}`, { method: 'DELETE' }
                    );
                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        throw new Error(errorData.detail || 'No se pudo desbloquear el alimento.');
                    }
                    mostrarMensaje('Alimento desbloqueado exitosamente', 'exito');
                    await renderizarAlimentosBloqueados(estudianteId);
                    actualizarPanelConEstudianteSeleccionado();
                } catch (error) {
                    console.error("Error al desbloquear alimento:", error);
                    mostrarMensaje(`Error: ${error.message}`, 'error');
                }
            }
        }
    });

    saveLimitBtn.addEventListener('click', async () => {
        const estudianteId = selectorEstudiante.value;
        const nuevoLimite = dailyLimitInput.value;
        if (!estudianteId || !nuevoLimite || nuevoLimite < 0) {
            mostrarMensaje('Por favor, introduce un límite válido.', 'error');
            return;
        }
        try {
            const response = await hacerPeticionAutenticada(
                `${apiURL}/estudiantes/${estudianteId}/limiteDiario`, {
                    method: 'PUT',
                    body: JSON.stringify({
                        limite: parseFloat(nuevoLimite)
                    })
                }
            );
            if (!response.ok) {
                throw new Error('No se pudo guardar el límite.');
            }
            mostrarMensaje('Límite diario guardado exitosamente.', 'exito');
            // Recargamos los datos para reflejar el nuevo límite en el resumen
            await cargarHijosYActualizarPanel();
        } catch (error) {
            console.error("Error al guardar el límite:", error);
            mostrarMensaje(error.message, 'error');
        }
    });

    function mostrarMensaje(mensaje, tipo = 'exito') {
        let container = document.getElementById('mensaje-exito');
        if (!container) {
            container = document.createElement('div');
            container.id = 'mensaje-exito';
            document.body.appendChild(container);
        }
        container.textContent = mensaje;
        container.style.backgroundColor = tipo === 'exito' ? '#4CAF50' : '#f44336';
        container.style.display = 'block';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.color = 'white';
        container.style.padding = '12px 24px';
        container.style.borderRadius = '4px';
        container.style.zIndex = '1000';
        container.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
        setTimeout(() => {
            container.style.display = 'none';
        }, 3000);
    }


    // --- LÓGICA PRINCIPAL  ---
    async function cargarDatosDelPanel(estudianteId, saldo, limiteDiario) {
        if (!estudianteId) {
            renderizarResumen([], 0, [], 0);
            renderizarHistorial([]);
            renderizarAlimentosBloqueados(null);
            dailyLimitInput.value = '';
            return;
        }
        dailyLimitInput.value = limiteDiario || '';
        try {
            const [comprasRes, alimentosBloqueados] = await Promise.all([
                hacerPeticionAutenticada(`${apiURL}/compras/usuario/${estudianteId}`).catch(e => null),
                cargarAlimentosBloqueados(estudianteId)
            ]);
            let compras = [];
            if (comprasRes && comprasRes.ok) {
                compras = await comprasRes.json();
            }
            renderizarResumen(compras, saldo, alimentosBloqueados, limiteDiario);
            renderizarHistorial(compras);
        } catch (error) {
            console.error("Error cargando datos del panel:", error);
            renderizarResumen([], saldo, [], limiteDiario);
            renderizarHistorial([]);
            renderizarAlimentosBloqueados(estudianteId);
        }
    }

    async function cargarAlimentosBloqueados(estudianteId) {
        try {
            const response = await hacerPeticionAutenticada(`${apiURL}/estudiantes/${estudianteId}/alimentosBloqueados`);
            if (response.ok) return await response.json();
            return [];
        } catch (error) {
            console.error("Error cargando alimentos bloqueados:", error);
            return [];
        }
    }

    // --- CAMBIO: Lógica para cargar hijos y aplicar selección guardada ---
    async function cargarHijosYActualizarPanel() {
        const usuario = obtenerUsuarioDeLocalStorage();
        if (!usuario) return;

        try {
            const response = await hacerPeticionAutenticada(`${apiURL}/estudiantes/${encodeURIComponent(usuario.nombre)}/hijos`);
            if (!response.ok) throw new Error("No se pudieron cargar los hijos.");

            const hijos = await response.json();
            selectorEstudiante.innerHTML = "";

            if (hijos && hijos.length > 0) {
                hijos.forEach(hijo => {
                    const option = document.createElement("option");
                    option.value = hijo.id;
                    option.setAttribute("data-saldo", hijo.saldo || 0);
                    option.setAttribute("data-limite", hijo.limite_diario || 0);
                    option.textContent = hijo.nombre;
                    selectorEstudiante.appendChild(option);
                });

                // Aplicamos la selección guardada de la sesión
                const hijoGuardado = obtenerHijoSeleccionado();
                if (hijoGuardado && selectorEstudiante.querySelector(`option[value="${hijoGuardado}"]`)) {
                    selectorEstudiante.value = hijoGuardado;
                }
                
                // Actualizamos el panel con la selección correcta (la guardada o la primera por defecto)
                actualizarPanelConEstudianteSeleccionado();

            } else {
                selectorEstudiante.innerHTML = "<option value=''>No hay hijos</option>";
                saldoElemento.textContent = formatearSaldo(0);
                cargarDatosDelPanel(null, 0, 0);
            }
        } catch (error) {
            console.error(error);
            selectorEstudiante.innerHTML = "<option>Error al cargar</option>";
        }
    }

    function actualizarPanelConEstudianteSeleccionado() {
        const opcionSeleccionada = selectorEstudiante.options[selectorEstudiante.selectedIndex];
        if (opcionSeleccionada && opcionSeleccionada.value) {
            const saldo = opcionSeleccionada.getAttribute("data-saldo");
            const estudianteId = opcionSeleccionada.value;
            const limiteDiario = opcionSeleccionada.getAttribute("data-limite");

            saldoElemento.textContent = formatearSaldo(saldo);
            cargarDatosDelPanel(estudianteId, saldo, limiteDiario);

            const activeTab = document.querySelector('.tab-button.active');
            if (activeTab) {
                const tabId = activeTab.dataset.tab;
                if (tabId === 'bloqueados') {
                    renderizarAlimentosBloqueados(estudianteId);
                }
            }
        } else {
            saldoElemento.textContent = formatearSaldo(0);
            cargarDatosDelPanel(null, 0, 0);
        }
    }

    // --- CAMBIO: EVENT LISTENER E INICIALIZACIÓN ---
    selectorEstudiante.addEventListener("change", () => {
        // Primero guardamos el nuevo valor en la sesión
        guardarHijoSeleccionado(selectorEstudiante.value);
        // Luego actualizamos el panel
        actualizarPanelConEstudianteSeleccionado();
    });

    // --- INICIALIZACIÓN ---
    await inicializarAlimentos();
    await cargarHijosYActualizarPanel(); // La lógica de aplicar la selección ya está dentro
});