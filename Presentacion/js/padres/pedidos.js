document.addEventListener("DOMContentLoaded", function () {
    const apiURL = "https://web-production-b7e6.up.railway.app";
    let carrito = {};
    let saldoEstudiante = 0;
    let todosLosProductos = [];
    let idsBloqueados = new Set();

    // --- ELEMENTOS DEL DOM ---
    const selectorEstudiante = document.getElementById("estudiante-selector");
    // ... (otros elementos que ya tenías)
    // --- NUEVOS ELEMENTOS PARA EL HISTORIAL ---
    const historialTableBody = document.getElementById("historial-table-body");
    const historialLoadingSpinner = document.getElementById("historial-loading-spinner");

    /**
     * Formatea una fecha a un formato legible para Colombia.
     * @param {string} dateString - La fecha en formato ISO (ej: "2025-06-13T15:30:00Z")
     * @returns {string} - La fecha formateada o 'N/A' si la entrada es inválida.
     */
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        };
        return new Date(dateString).toLocaleDateString('es-CO', options);
    }

    // --- 1. FUNCIONES DE AUTENTICACIÓN Y API ---
    function obtenerTokenDeLocalStorage() { return localStorage.getItem("jwtToken"); }
    function obtenerUsuarioDeLocalStorage() {
        try { return localStorage.getItem("usuario") ? JSON.parse(localStorage.getItem("usuario")) : null; }
        catch (e) { console.error("Error al parsear datos de usuario:", e); limpiarSesion(); return null; }
    }
    function guardarHijoSeleccionado(id) { sessionStorage.setItem('selectedStudent', id); }
    function obtenerHijoSeleccionado() { return sessionStorage.getItem('selectedStudent'); }
    function limpiarSesion() {
        localStorage.clear(); sessionStorage.clear(); window.location.href = "../login.html";
    }
    async function hacerPeticionAutenticada(url, options = {}) {
        const token = obtenerTokenDeLocalStorage();
        if (!token) { limpiarSesion(); throw new Error("No hay token"); }
        const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', ...options.headers };
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401 || response.status === 403) { limpiarSesion(); throw new Error("Sesión expirada"); }
        return response;
    }

    // --- 2. FUNCIONES DE UI ---
    function formatearPrecio(p) { return (parseFloat(p) || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0, maximumFractionDigits: 0 }); }
    function obtenerEstudianteSeleccionadoID() { return selectorEstudiante?.value; }
    function actualizarNombreEstudianteEnUI(n) { document.querySelectorAll('.nombre-estudiante-header, .nombre-estudiante-modal').forEach(el => el.textContent = n || '[Estudiante]'); }
    function mostrarError(m) { alert(`Error: ${m}`); console.error("Error:", m); }

    
    // --- NUEVAS FUNCIONES PARA EL HISTORIAL ---
    
    /**
     * Carga el historial de pedidos para un estudiante específico.
     */
    async function cargarHistorial(studentId) {
        if (!studentId) {
            historialTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center;">Seleccione un estudiante para ver su historial.</td></tr>`;
            return;
        }
        historialLoadingSpinner.style.display = 'block';
        historialTableBody.innerHTML = "";

        try {
            // Llama al nuevo endpoint que creaste en el backend
            const response = await hacerPeticionAutenticada(`${apiURL}/api/precompras/estudiante/${studentId}/historial`);
            if (!response.ok) throw new Error('No se pudo cargar el historial.');
            const historial = await response.json();
            renderHistorialTable(historial);
        } catch (error) {
            historialTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: red;">${error.message}</td></tr>`;
        } finally {
            historialLoadingSpinner.style.display = 'none';
        }
    }

    /**
     * Renderiza la tabla de historial con filas expandibles.
     */
    function renderHistorialTable(data) {
        historialTableBody.innerHTML = "";
        if (data.length === 0) {
            // Se actualiza el colspan a 5 para abarcar la nueva columna
            historialTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center;">Este estudiante no tiene pedidos en su historial.</td></tr>`;
            return;
        }

        data.forEach(pc => {
            const row = document.createElement("tr");
            row.className = "clickable-row";
            row.dataset.precompraId = pc.id;

            const statusClass = pc.entregado ? 'status-entregado' : 'status-pendiente';
            const statusText = pc.entregado ? 'Entregado' : 'Pendiente';

            // AÑADIMOS LA NUEVA CELDA (<td>) PARA LA FECHA DE ENTREGA
            row.innerHTML = `
                <td>#${pc.id}</td>
                <td>${formatDate(pc.fecha_precompra)}</td>
                <td>${formatearPrecio(pc.costo_total)}</td>
                <td><span class="status ${statusClass}">${statusText}</span></td>
                <td>${formatDate(pc.fecha_entrega)}</td> 
            `;
            
            row.addEventListener('click', () => toggleHistorialDetails(row, pc.items));
            historialTableBody.appendChild(row);
        });
    }
    
    /**
     * Muestra u oculta los detalles de un pedido en el historial.
     */
    function toggleHistorialDetails(clickedRow, items) {
        const precompraId = clickedRow.dataset.precompraId;
        const existingDetailRow = document.getElementById(`historial-details-for-${precompraId}`);

        if (existingDetailRow) {
            existingDetailRow.remove();
            return;
        }

        const detailRow = document.createElement("tr");
        detailRow.id = `historial-details-for-${precompraId}`;
        detailRow.className = 'details-row';

        let itemsHtml = '<p>No hay productos asociados a este pedido.</p>';
        if (items && items.length > 0) {
            itemsHtml = '<ul class="details-item-list">';
            items.forEach(item => {
                itemsHtml += `<li><strong>${item.cantidad}x</strong> ${item.nombre ?? 'Producto desconocido'}</li>`;
            });
            itemsHtml += '</ul>';
        }
        
        // Se actualiza el colspan a 5 para abarcar la nueva columna
        detailRow.innerHTML = `<td colspan="5"><div class="details-content"><h5>Productos del Pedido</h5>${itemsHtml}</div></td>`;
        clickedRow.insertAdjacentElement('afterend', detailRow);
    }
    

    // --- 3. LÓGICA DE CARGA DE DATOS (Modificada) ---
    async function cargarHijos() {
        const usuario = obtenerUsuarioDeLocalStorage();
        if (!selectorEstudiante || !usuario?.nombre) return;
        try {
            const res = await hacerPeticionAutenticada(`${apiURL}/estudiantes/${encodeURIComponent(usuario.nombre)}/hijos`);
            if (!res.ok) throw new Error("No se pudieron cargar los estudiantes.");
            const hijos = await res.json();
            selectorEstudiante.innerHTML = "";
            if (hijos?.length > 0) {
                hijos.forEach(h => {
                    const opt = document.createElement("option");
                    opt.value = h.id;
                    opt.dataset.saldo = h.saldo || 0;
                    opt.dataset.nombre = h.nombre || 'Hijo';
                    opt.textContent = h.nombre;
                    selectorEstudiante.appendChild(opt);
                });
                const guardado = obtenerHijoSeleccionado();
                if (guardado && selectorEstudiante.querySelector(`option[value="${guardado}"]`)) {
                    selectorEstudiante.value = guardado;
                }
            } else {
                selectorEstudiante.innerHTML = "<option value=''>No hay estudiantes</option>";
            }
            actualizarInfoEstudianteSeleccionado();
        } catch (e) { mostrarError(e.message); }
    }

    function actualizarInfoEstudianteSeleccionado() {
        const opt = selectorEstudiante.options[selectorEstudiante.selectedIndex];
        const studentId = opt?.value;

        if (studentId) {
            saldoEstudiante = parseFloat(opt.dataset.saldo) || 0;
            actualizarNombreEstudianteEnUI(opt.dataset.nombre);
            cargarYMostrarProductos();
            // --- ¡AQUÍ SE LLAMA A LA NUEVA FUNCIÓN! ---
            cargarHistorial(studentId); 
        } else {
            saldoEstudiante = 0;
            actualizarNombreEstudianteEnUI('');
            document.getElementById("alimentos-grid").innerHTML = '<p>Selecciona un estudiante para ver los productos.</p>';
            historialTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center;">Seleccione un estudiante para ver su historial.</td></tr>`;
        }
        document.getElementById("saldo-usuario").textContent = formatearPrecio(saldoEstudiante);
        carrito = {};
        renderizarCarrito();
    }

    // ... (El resto de tus funciones: cargarYMostrarProductos, renderizarCarrito, realizarPedido, etc. se quedan exactamente igual)
    // Se omiten por brevedad, pero deben estar en tu archivo.
    // Pega este código y reemplaza las funciones que se repiten. Las que no están aquí, se conservan.

    async function cargarYMostrarProductos() {
        const grid = document.getElementById("alimentos-grid");
        const id = obtenerEstudianteSeleccionadoID();
        if (!id) { grid.innerHTML = '<p>Selecciona un estudiante para ver los productos.</p>'; return; }
        grid.innerHTML = '<p>Cargando productos...</p>';
        try {
            const res = await hacerPeticionAutenticada(`${apiURL}/api/alimentos/`);
            if (!res.ok) throw new Error(`No se pudieron cargar los productos (${res.status})`);
            const data = await res.json();
            todosLosProductos = data.results || (Array.isArray(data) ? data : []);
            
            const resBloqueo = await hacerPeticionAutenticada(`${apiURL}/estudiantes/${id}/alimentosBloqueados`);
            idsBloqueados = resBloqueo.ok ? new Set((await resBloqueo.json()).map(b => b.id_alimento)) : new Set();
            
            aplicarFiltrosYRenderizar();
        } catch (e) { grid.innerHTML = `<p style="color: red;">${e.message}</p>`; }
    }

    function aplicarFiltrosYRenderizar() {
        const nombre = document.getElementById("filtro-nombre").value.toLowerCase();
        const categoria = document.getElementById("filtro-categoria").value;
        const filtrados = todosLosProductos.filter(p => (!nombre || p.nombre.toLowerCase().includes(nombre)) && (!categoria || p.categoria === categoria));
        mostrarProductos(filtrados, idsBloqueados);
    }

    function mostrarProductos(productos, idsBloqueados) {
        const grid = document.getElementById("alimentos-grid");
        grid.innerHTML = "";
        if (productos?.length === 0) { grid.innerHTML = '<p>No hay productos que coincidan.</p>'; return; }
        productos.forEach(p => {
            const card = document.createElement("div");
            card.className = "alimento-card";
            card.dataset.id = p.id;
            const bloqueado = idsBloqueados.has(p.id);
            if (bloqueado) card.classList.add('bloqueado');
            card.innerHTML = `${bloqueado ? `<div class="bloqueado-overlay"><i class="fas fa-lock"></i><span>Bloqueado</span></div>` : ''}<img class="alimento-imagen" src="${p.imagen || 'https://via.placeholder.com/150'}" alt="${p.nombre}"><div class="alimento-body"><span class="alimento-categoria">${p.categoria || ''}</span><h3 class="alimento-nombre">${p.nombre}</h3><div class="alimento-info"><div class="info-item"><span>Precio</span><span class="precio-value">${formatearPrecio(p.precio)}</span></div><div class="info-item"><span>Calorías</span><span>${p.calorias || 0} Cal</span></div></div><div class="alimento-actions"><div class="quantity-selector"><button class="btn-quantity minus" ${bloqueado ? 'disabled' : ''}>-</button><input type="number" value="1" min="1" readonly ${bloqueado ? 'disabled' : ''}><button class="btn-quantity plus" ${bloqueado ? 'disabled' : ''}>+</button></div><button class="btn-agregar" ${bloqueado ? 'disabled' : ''}><i class="fas fa-cart-plus"></i> Agregar</button></div></div>`;
            card.dataset.producto = JSON.stringify(p);
            grid.appendChild(card);
        });
    }

    function agregarAlCarrito(id) {
        const card = document.querySelector(`.alimento-card[data-id='${id}']`);
        if (!card || card.classList.contains('bloqueado')) return;
        const p = JSON.parse(card.dataset.producto);
        const cant = parseInt(card.querySelector('input[type="number"]').value, 10);
        if (carrito[id]) carrito[id].cantidad += cant; else carrito[id] = { ...p, cantidad: cant };
        card.querySelector('input[type="number"]').value = 1;
        renderizarCarrito();
    }

    function renderizarCarrito() {
        const lista = document.getElementById("carrito-items");
        lista.innerHTML = "";
        if (Object.keys(carrito).length === 0) {
            lista.innerHTML = `<div class="carrito-vacio"><i class="fas fa-cart-arrow-down"></i><p>Tu carrito está vacío</p><span>Agrega productos para comenzar.</span></div>`;
        } else {
            for (const id in carrito) {
                const i = carrito[id];
                const itemEl = document.createElement("div");
                itemEl.className = "carrito-item";
                itemEl.innerHTML = `<div class="item-info"><p class="item-nombre">${i.nombre}</p><p class="item-precio">${formatearPrecio(i.precio)} x ${i.cantidad} = ${formatearPrecio(i.precio * i.cantidad)}</p></div><div class="item-actions"><button class="btn-remover-item" data-id="${id}" aria-label="Remover ${i.nombre}"><i class="fas fa-trash-alt" aria-hidden="true"></i></button></div>`;
                lista.appendChild(itemEl);
            }
        }
        actualizarTotales();
    }
    
    function actualizarTotales() {
        const subtotal = Object.values(carrito).reduce((acc, i) => acc + ((i.precio || 0) * i.cantidad), 0);
        document.getElementById("carrito-subtotal").textContent = formatearPrecio(subtotal);
        document.getElementById("carrito-total").textContent = formatearPrecio(subtotal);
        document.getElementById("carrito-saldo-actual").textContent = formatearPrecio(saldoEstudiante);
        const restante = saldoEstudiante - subtotal;
        document.getElementById("carrito-saldo-restante").textContent = formatearPrecio(restante);
        document.getElementById("btn-realizar-pedido").disabled = !(subtotal > 0 && restante >= 0);
        document.getElementById("saldo-insuficiente-warning").style.display = subtotal > saldoEstudiante ? 'block' : 'none';
    }
    
    async function realizarPedido() {
    const idEstudiante = obtenerEstudianteSeleccionadoID();
    if (!idEstudiante || Object.keys(carrito).length === 0) {
        return mostrarError("Selecciona un estudiante y agrega productos al carrito.");
    }

    // Calculamos subtotal local
    const subtotalLocal = Object.values(carrito).reduce((acc, i) => acc + ((parseFloat(i.precio) || 0) * (parseInt(i.cantidad, 10) || 0)), 0);
    const costoAdicional = parseFloat("100.00") || 0; // mismo valor que envías en la precompra
    const totalAPagar = subtotalLocal + costoAdicional;

    // Validación DEL SALDO en el cliente - si no alcanza, no dejamos seguir
    if ((saldoEstudiante || 0) < totalAPagar) {
        // Puedes usar mostrarError que ya tienes definido
        mostrarError(`Saldo insuficiente. Total a pagar: ${formatearPrecio(totalAPagar)} — Saldo disponible: ${formatearPrecio(saldoEstudiante)}`);
        // Aseguramos que el botón de confirmar quede deshabilitado
        document.getElementById('btn-modal-confirmar').disabled = true;
        return;
    }

    const btn = document.getElementById('btn-modal-confirmar');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

    const datosPrecompra = {
        estudiante_id: parseInt(idEstudiante, 10),
        items: Object.values(carrito).map(item => ({ producto_id: item.id, cantidad: item.cantidad })),
        costo_adicional: "100.00"
    };

    try {
        // 1) Creación de la precompra
        const response = await hacerPeticionAutenticada(`${apiURL}/api/precompras/nueva`, {
            method: 'POST',
            body: JSON.stringify(datosPrecompra)
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "Ocurrió un error al crear la precompra.");
        }
        const createdPrecompra = await response.json();

        // Determinamos el monto a descargar: preferimos el valor devuelto por el backend
        const montoDescarga = parseFloat(createdPrecompra.costo_total ?? totalAPagar) || 0;
        if (montoDescarga <= 0) {
            console.warn("Monto a descargar es 0 — no se realizará descarga de saldo.");
        } else {
            // 2) Llamada al endpoint que descuenta saldo del estudiante
            const descargaResp = await hacerPeticionAutenticada(`${apiURL}/estudiantes/${encodeURIComponent(idEstudiante)}/descargaSaldo`, {
                method: 'POST',
                body: JSON.stringify({ monto: montoDescarga })
            });

            if (!descargaResp.ok) {
                let errText = "Error al actualizar el saldo del estudiante.";
                try {
                    const errJson = await descargaResp.json();
                    errText = errJson.detail || errJson.message || errText;
                } catch (e) { /* noop */ }
                throw new Error(`${errText} (precompra creada: ${createdPrecompra.id})`);
            }

            const updatedStudent = await descargaResp.json();

            // 3) Actualizamos el saldo en la UI y variable local
            saldoEstudiante = parseFloat(updatedStudent.saldo) || (saldoEstudiante - montoDescarga);
            document.getElementById("saldo-usuario").textContent = formatearPrecio(saldoEstudiante);
            // Actualizamos dataset del option para que futuros cambios reflejen el nuevo saldo
            const opt = selectorEstudiante.querySelector(`option[value="${idEstudiante}"]`);
            if (opt) opt.dataset.saldo = saldoEstudiante;
        }

        alert("¡Pedido realizado con éxito!");
        cerrarModal();
        carrito = {};
        renderizarCarrito();
        await cargarHijos(); // recarga info/historial

    } catch (error) {
        console.error("Error detallado al procesar la precompra:", error);
        mostrarError(`Error al realizar el pedido: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Confirmar y Pagar';
    }
}

    
    function abrirModal() {
        const boton = document.getElementById('btn-realizar-pedido');
        if (boton.disabled) return;
        document.getElementById('modal-total-pedido').textContent = document.getElementById('carrito-total').textContent;
        document.getElementById('modal-confirmacion').classList.add('visible');
    }

    function cerrarModal() {
        document.getElementById('modal-confirmacion').classList.remove('visible');
    }
    
    function manejarClicksGlobales(e) {
        const target = e.target;
        const card = target.closest('.alimento-card');
        if (card && !card.classList.contains('bloqueado')) {
            const input = card.querySelector('input[type="number"]');
            if (target.closest('.plus')) {
                input.value = parseInt(input.value) + 1;
            } else if (target.closest('.minus') && input.value > 1) {
                input.value = parseInt(input.value) - 1;
            } else if (target.closest('.btn-agregar')) {
                agregarAlCarrito(card.dataset.id);
            }
            return;
        }
        const btnRemover = target.closest('.btn-remover-item');
        if (btnRemover) {
            delete carrito[btnRemover.dataset.id];
            renderizarCarrito();
            return;
        }
        if (target.closest('#btn-realizar-pedido')) {
            abrirModal();
            return;
        }
        if (target.closest('#btn-modal-confirmar')) {
            realizarPedido();
            return;
        }
        if (target.closest('#btn-modal-cancelar') || target.closest('#modal-close-btn')) {
            cerrarModal();
            return;
        }
    }

    // --- 7. INICIALIZACIÓN ---
    async function init() {
        if (!obtenerUsuarioDeLocalStorage()) return limpiarSesion();
        await cargarHijos();
        selectorEstudiante?.addEventListener("change", () => {
            guardarHijoSeleccionado(selectorEstudiante.value);
            actualizarInfoEstudianteSeleccionado();
        });
        document.getElementById('filtro-nombre').addEventListener('input', aplicarFiltrosYRenderizar);
        document.getElementById('filtro-categoria').addEventListener('change', aplicarFiltrosYRenderizar);
        document.querySelector('.btn-filtrar')?.addEventListener('click', aplicarFiltrosYRenderizar);
        document.body.addEventListener('click', manejarClicksGlobales);
    }
    init();
});

