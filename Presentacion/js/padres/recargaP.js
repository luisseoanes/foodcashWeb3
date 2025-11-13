// js/padres/recargaP.js

document.addEventListener("DOMContentLoaded", () => {
    // ----- Config -----
    const API_URL = "https://web-production-b7e6.up.railway.app";
    const RECARGAS_BASE = `${API_URL}/api/recargas`;
    const MINIMO_RECARGA = 10000;
    const WIDGET_SCRIPT_URL = "https://checkout.wompi.co/widget.js";

    // ----- Autenticación / Sesión -----
    function obtenerTokenDeLocalStorage() {
        return localStorage.getItem("jwtToken");
    }

    function obtenerUsuarioDeLocalStorage() {
        const data = localStorage.getItem("usuario");
        try {
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error("Error parseando usuario en localStorage:", e);
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
            console.error("No hay token de autenticación. Redirigiendo a login.");
            limpiarSesionDeLocalStorage();
            window.location.href = "login.html";
            throw new Error("No hay token de autenticación");
        }

        const headers = {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
            ...(options.headers || {}),
        };

        const controller = new AbortController();
        const timeout = options.timeout || 20000;
        const id = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, { ...options, headers, signal: controller.signal });
            clearTimeout(id);

            if (response.status === 401 || response.status === 403) {
                console.error("Token inválido/expirado o sin permiso (401/403). Redirigiendo a login.");
                limpiarSesionDeLocalStorage();
                window.location.href = "login.html";
                throw new Error("Sesión expirada o no autorizada");
            }

            return response;
        } catch (err) {
            clearTimeout(id);
            if (err.name === 'AbortError') {
                throw new Error('La petición tardó demasiado (timeout)');
            }
            throw err;
        }
    }

    // ----- Helpers UI -----
        // ----- Helpers UI -----
    function mostrarMensaje(mensaje, tipo = "info", duracion = 6000) {
        // Remover notificación anterior si existe
        const alertAnterior = document.getElementById("alert-messages");
        if (alertAnterior) {
            alertAnterior.remove();
        }

        // Crear contenedor de notificación
        const alertElement = document.createElement("div");
        alertElement.id = "alert-messages";
        
        // Estilos base
        alertElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 350px;
            max-width: 450px;
            padding: 20px 24px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 15px;
            font-weight: 500;
            line-height: 1.5;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            backdrop-filter: blur(10px);
        `;

        // Iconos y colores según el tipo
        let icono, colorFondo, colorTexto, colorBorde;
        
        switch(tipo) {
            case 'success':
                icono = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" fill="#10b981" opacity="0.2"/>
                        <path d="M7 12.5l3.5 3.5L17 8.5" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                `;
                colorFondo = 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)';
                colorTexto = '#065f46';
                colorBorde = '#10b981';
                break;
            case 'danger':
                icono = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" fill="#ef4444" opacity="0.2"/>
                        <path d="M15 9l-6 6M9 9l6 6" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                `;
                colorFondo = 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)';
                colorTexto = '#991b1b';
                colorBorde = '#ef4444';
                break;
            case 'warning':
                icono = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" fill="#f59e0b" opacity="0.2"/>
                        <path d="M12 7v6M12 16h.01" stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                `;
                colorFondo = 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)';
                colorTexto = '#92400e';
                colorBorde = '#f59e0b';
                break;
            default: // info
                icono = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" fill="#3b82f6" opacity="0.2"/>
                        <path d="M12 16v-4M12 8h.01" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>
                `;
                colorFondo = 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)';
                colorTexto = '#1e40af';
                colorBorde = '#3b82f6';
        }

        alertElement.style.background = colorFondo;
        alertElement.style.color = colorTexto;
        alertElement.style.borderLeft = `4px solid ${colorBorde}`;

        // Estructura HTML
        alertElement.innerHTML = `
            <div style="flex-shrink: 0;">${icono}</div>
            <div style="flex: 1;">${mensaje}</div>
            <button id="close-alert" style="
                background: transparent;
                border: none;
                color: ${colorTexto};
                opacity: 0.6;
                cursor: pointer;
                padding: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: all 0.2s;
                flex-shrink: 0;
            " onmouseover="this.style.opacity='1'; this.style.background='rgba(0,0,0,0.1)'" 
               onmouseout="this.style.opacity='0.6'; this.style.background='transparent'">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </button>
        `;

        // Añadir animación CSS
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(alertElement);

        // Función para cerrar
        const cerrarNotificacion = () => {
            alertElement.style.animation = 'slideOut 0.3s ease-in-out';
            setTimeout(() => {
                if (alertElement && alertElement.parentNode) {
                    alertElement.remove();
                }
            }, 300);
        };

        // Botón de cerrar
        const closeButton = alertElement.querySelector('#close-alert');
        if (closeButton) {
            closeButton.addEventListener('click', cerrarNotificacion);
        }

        // Auto-cerrar después de la duración especificada
        if (duracion > 0) {
            setTimeout(cerrarNotificacion, duracion);
        }
    }

    function formatearSaldo(saldo) {
        const saldoNumerico = parseFloat(saldo);
        const n = isNaN(saldoNumerico) ? 0 : saldoNumerico;
        return n.toLocaleString("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });
    }

    // ----- Elementos del DOM -----
    const selectorEstudiante = document.getElementById("estudiante-selector");
    const saldoElemento = document.getElementById("saldo-usuario");
    const cardPreviewId = document.getElementById("card-preview-id");
    const cardPreviewName = document.getElementById("card-preview-name");

    const amountInput = document.getElementById("amount");
    const quickAmountButtons = document.querySelectorAll(".btn-quick-amount") || [];
    const breakdownSubtotal = document.getElementById("breakdown-subtotal");
    const breakdownServiceFee = document.getElementById("breakdown-service-fee");
    const breakdownIva = document.getElementById("breakdown-iva");
    const breakdownTotal = document.getElementById("breakdown-total");
    const recargaForm = document.getElementById("recargaForm");
    const submitButton = recargaForm ? recargaForm.querySelector('[type="submit"]') : null;

    // Estado actual
    let peticionEnCurso = false;

    // ----- VERIFICAR RESULTADO DE RECARGA AL CARGAR -----
    function verificarResultadoRecarga() {
        const urlParams = new URLSearchParams(window.location.search);
        const status = urlParams.get('status');
        const monto = urlParams.get('monto');

        if (status) {
            const montoFormateado = monto ? formatearSaldo(parseFloat(monto)) : '';
            switch(status) {
                case 'success':
                    mostrarMensaje(`✓ Recarga de ${montoFormateado} realizada satisfactoriamente`, 'success', 8000);
                    break;
                case 'declined':
                    mostrarMensaje(`✗ Recarga de ${montoFormateado} no aprobada. Por favor, intente nuevamente.`, 'danger', 8000);
                    break;
                case 'pending':
                    mostrarMensaje(`⏳ Recarga de ${montoFormateado} pendiente de confirmación`, 'warning', 8000);
                    break;
                case 'error':
                    mostrarMensaje(`✗ Error en la recarga. Por favor, contacte con soporte.`, 'danger', 8000);
                    break;
            }

            const cleanUrl = window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);

            if (status === 'success') {
                setTimeout(() => { cargarHijos(); }, 1000);
            }
        }
    }

    // ----- Cálculo de desglose -----
    function calcularDesglose(monto) {
        const comision = Math.round(monto * 0.08);
        const iva = Math.round(comision * 0.19);
        const total = monto + comision + iva;
        return { monto, comision, iva, total };
    }

    function actualizarDesgloseEnUI(monto) {
        const { monto: m, comision, iva, total } = calcularDesglose(monto);
        if (breakdownSubtotal) breakdownSubtotal.textContent = `$${m.toLocaleString()}`;
        if (breakdownServiceFee) breakdownServiceFee.textContent = `$${comision.toLocaleString()}`;
        if (breakdownIva) breakdownIva.textContent = `$${iva.toLocaleString()}`;
        if (breakdownTotal) breakdownTotal.textContent = `$${total.toLocaleString()}`;
    }

    // Manejo de botones de monto rápido
    quickAmountButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const amt = parseInt(btn.getAttribute("data-amount"), 10) || 0;
            if (amountInput) {
                amountInput.value = amt;
                amountInput.dispatchEvent(new Event("input"));
            }
        });
    });

    if (amountInput) {
        amountInput.addEventListener("input", (e) => {
            const monto = Math.max(0, Math.round(Number(e.target.value) || 0));
            actualizarDesgloseEnUI(monto);
        });
    }

    // ----- Funciones para tabla de compras -----
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

    function actualizarTablaCompras(compras) {
        const tbody = document.querySelector(".table100-body tbody");
        if (!tbody) return;
        tbody.innerHTML = "";

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

        const comprasOrdenadas = compras
            .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
            .slice(0, 5);

        comprasOrdenadas.forEach(compra => {
            try {
                const fila = document.createElement("tr");
                fila.className = "row100 body";

                const fechaFormateada = formatearFecha(compra.fecha);
                const totalFormateado = formatearSaldo(compra.total || 0);

                let productosListado = "Detalle no disponible";
                let caloriasTotales = 0;
                if (compra.items && Array.isArray(compra.items) && compra.items.length > 0) {
                    productosListado = compra.items.map(item => item.nombre_alimento || "Producto").join(" - ");
                    caloriasTotales = compra.items.reduce((sum, item) => {
                        const caloriasUnitarias = parseFloat(item.calorias) || 0;
                        return sum + (caloriasUnitarias * (item.cantidad || 1));
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
                console.error("Error procesando compra:", error, compra);
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

    async function cargarComprasEstudiante(estudianteId) {
        if (!estudianteId) {
            limpiarTablaCompras();
            return;
        }
        try {
            const encodedId = encodeURIComponent(String(estudianteId));
            const resp = await hacerPeticionAutenticada(`${API_URL}/compras/usuario/${encodedId}`, { method: "GET" });
            if (!resp.ok) {
                if (resp.status === 404) {
                    limpiarTablaCompras();
                    return;
                }
                throw new Error(`Error ${resp.status}: ${resp.statusText}`);
            }

            const compras = await resp.json();
            if (!Array.isArray(compras)) throw new Error("Formato de compras inesperado");
            actualizarTablaCompras(compras);
        } catch (e) {
            console.error("Error cargando compras:", e);
            limpiarTablaCompras();
        }
    }

    // ----- Actualizar saldo y preview (NO MODIFICAR) -----
    function actualizarSaldoYPreview() {
        if (!selectorEstudiante || selectorEstudiante.options.length === 0) return;
        
        const opcion = selectorEstudiante.options[selectorEstudiante.selectedIndex];
        if (opcion && opcion.value) {
            const saldo = opcion.getAttribute("data-saldo") || 0;
            const cedula = opcion.getAttribute("data-cedula") || "---";
            const nombre = opcion.textContent;
            
            if (saldoElemento) {
                saldoElemento.textContent = formatearSaldo(saldo);
            }
            
            if (cardPreviewId) {
                cardPreviewId.textContent = cedula;
            }
            if (cardPreviewName) {
                cardPreviewName.textContent = nombre;
            }
            
            cargarComprasEstudiante(opcion.value);
        } else {
            if (saldoElemento) saldoElemento.textContent = formatearSaldo(0);
            if (cardPreviewId) cardPreviewId.textContent = "---";
            if (cardPreviewName) cardPreviewName.textContent = "Seleccione un estudiante";
            limpiarTablaCompras();
        }
    }

    // ----- ADICIÓN: función que actualiza solo la cédula en la tarjeta -----
    function actualizarCedulaEnTarjeta() {
        if (!selectorEstudiante || !cardPreviewId) return;
        const opcion = selectorEstudiante.options[selectorEstudiante.selectedIndex];
        if (!opcion) {
            cardPreviewId.textContent = '---';
            return;
        }

        const cedulaRaw = opcion.getAttribute("data-cedula") || '';
        const cedulaFormateada = (cedulaRaw !== '' && !isNaN(Number(cedulaRaw)))
            ? Number(cedulaRaw).toLocaleString('es-CO')
            : (cedulaRaw || '---');

        cardPreviewId.textContent = cedulaFormateada;
    }

    // ----- Cargar hijos -----
    async function cargarHijos() {
        if (!selectorEstudiante) {
            console.error("El elemento #estudiante-selector no existe.");
            mostrarMensaje("Error de interfaz: falta selector de estudiantes.", "danger");
            return;
        }

        const usuarioData = obtenerUsuarioDeLocalStorage();
        if (!usuarioData || !usuarioData.nombre) {
            console.error("No hay datos de usuario para cargar hijos.");
            mostrarMensaje("Error: No se pudo identificar al responsable.", "danger");
            return;
        }

        try {
            const response = await hacerPeticionAutenticada(
                `${API_URL}/estudiantes/${encodeURIComponent(usuarioData.nombre)}/hijos`,
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
                    option.value = hijo.id; // mantener id para peticiones
                    option.setAttribute("data-saldo", hijo.saldo || 0);

                    // === ADICIÓN: guardar cédula en data-cedula (fallbacks)
                    const cedulaValor = hijo.cedula || hijo.documento || hijo.identificacion || '';
                    option.setAttribute("data-cedula", cedulaValor);

                    option.textContent = hijo.nombre;
                    selectorEstudiante.appendChild(option);
                });

                const savedStudent = sessionStorage.getItem("selectedStudent");
                if (savedStudent && Array.from(selectorEstudiante.options).some(opt => opt.value === savedStudent)) {
                    selectorEstudiante.value = savedStudent;
                } else if (selectorEstudiante.options.length > 0) {
                    selectorEstudiante.selectedIndex = 0;
                }

                // NO se modifica actualizarSaldoYPreview() (como pediste)
                actualizarSaldoYPreview();

                // === ADICIÓN: actualizar sólo la cédula en la tarjeta
                actualizarCedulaEnTarjeta();
            } else {
                selectorEstudiante.innerHTML = "<option value=''>No se encontraron hijos</option>";
                if (saldoElemento) saldoElemento.textContent = formatearSaldo(0);
                if (cardPreviewId) cardPreviewId.textContent = "---";
                if (cardPreviewName) cardPreviewName.textContent = "Sin estudiantes";
                limpiarTablaCompras();
                mostrarMensaje("No tiene estudiantes asociados.", "warning");
            }
        } catch (error) {
            console.error("Error cargando hijos:", error);
            if (error.message.toLowerCase().includes("sesión expirada")) return;
            mostrarMensaje(`No se pudo cargar la lista de hijos: ${error.message}`, "danger");
            selectorEstudiante.innerHTML = "<option>Error al cargar</option>";
            if (saldoElemento) saldoElemento.textContent = formatearSaldo(0);
            if (cardPreviewId) cardPreviewId.textContent = "---";
            if (cardPreviewName) cardPreviewName.textContent = "Error";
            limpiarTablaCompras();
        }
    }

    // ----- Event listener para cambio de estudiante -----
    if (selectorEstudiante) {
        // Mantengo tu listener actual (no lo modifico)
        selectorEstudiante.addEventListener("change", function () {
            actualizarSaldoYPreview();
            sessionStorage.setItem("selectedStudent", selectorEstudiante.value);
        });

        // === ADICIÓN: listener adicional que actualiza solo la cédula en la tarjeta ===
        selectorEstudiante.addEventListener("change", function () {
            actualizarCedulaEnTarjeta();
        });
    }

    // ----- Función para cargar script del widget -----
    function cargarScript(src, options = {}) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            
            const timeout = options.timeout || 10000;
            const retry = options.retry || 0;
            
            const timer = setTimeout(() => {
                script.remove();
                if (retry > 0) {
                    cargarScript(src, { ...options, retry: retry - 1 })
                        .then(resolve)
                        .catch(reject);
                } else {
                    reject(new Error('Timeout cargando script'));
                }
            }, timeout);
            
            script.onload = () => {
                clearTimeout(timer);
                resolve();
            };
            
            script.onerror = () => {
                clearTimeout(timer);
                script.remove();
                if (retry > 0) {
                    cargarScript(src, { ...options, retry: retry - 1 })
                        .then(resolve)
                        .catch(reject);
                } else {
                    reject(new Error('Error cargando script'));
                }
            };
            
            document.head.appendChild(script);
        });
    }

    // ----- Iniciar pago con backend -----
    async function iniciarPagoConBackend() {
        console.clear();
        console.log("=== INICIANDO PROCESO DE RECARGA ===");
        console.log("Timestamp:", new Date().toISOString());

        const estudianteId = selectorEstudiante?.value;
        const montoBase = parseFloat(amountInput?.value) || 0;

        if (!estudianteId) {
            mostrarMensaje('Por favor, selecciona un estudiante para recargar.', 'warning');
            return;
        }

        if (montoBase < MINIMO_RECARGA) {
            mostrarMensaje(`El monto mínimo de recarga es de $${MINIMO_RECARGA.toLocaleString()} COP.`, 'warning');
            return;
        }

        if (peticionEnCurso) {
            mostrarMensaje('Ya hay una recarga en proceso. Espere.', 'warning');
            return;
        }

        peticionEnCurso = true;
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Procesando...';
        }

        try {
            const payload = {
                usuario_id: estudianteId,
                monto: montoBase
            };

            const response = await hacerPeticionAutenticada(`${RECARGAS_BASE}/iniciar`, {
                method: 'POST',
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                let errorData = { detail: 'Error al iniciar la recarga.' };
                try {
                    errorData = await response.json();
                } catch (e) {}
                throw new Error(errorData.detail || 'Error desconocido.');
            }

            const recargaData = await response.json();
            console.log("Respuesta del backend:", recargaData);

            if (!recargaData.widget_config) {
                throw new Error('No se recibió configuración del widget');
            }

            if (!window.WidgetCheckout) {
                await cargarScript(WIDGET_SCRIPT_URL, { timeout: 15000, retry: 2 });
            }

            const widgetConfig = recargaData.widget_config;

            // Construir URL de retorno con el monto
            const currentUrl = new URL(window.location.href);
            const baseUrl = `${currentUrl.origin}${currentUrl.pathname}`;
            const redirectBase = `${baseUrl}?recarga_id=${recargaData.recarga_id}&monto=${montoBase}`;

            const wompiConfig = {
                publicKey: widgetConfig.publicKey,
                currency: widgetConfig.currency,
                amountInCents: widgetConfig.amountInCents,
                reference: widgetConfig.reference,
                signature: {
                    integrity: widgetConfig.signature
                },
                redirectUrl: redirectBase
            };

            if (widgetConfig.customerEmail) wompiConfig.customerEmail = widgetConfig.customerEmail;
            if (widgetConfig.customerData) wompiConfig.customerData = widgetConfig.customerData;
            if (widgetConfig.paymentDescription) wompiConfig.paymentDescription = widgetConfig.paymentDescription;

            console.log("=== CONFIG FINAL ===");
            console.log("Config completo:", wompiConfig);

            const checkout = new window.WidgetCheckout(wompiConfig);

            checkout.open(function(result) {
                console.log("Resultado del widget:", result);

                const recargaId = recargaData.recarga_id;
                const urlBase = `${window.location.origin}${window.location.pathname}`;

                if (result.transaction) {
                    const status = result.transaction.status;

                    if (status === 'APPROVED') {
                        window.location.href = `${urlBase}?recarga_id=${recargaId}&monto=${montoBase}&status=success`;
                    } else if (status === 'DECLINED') {
                        window.location.href = `${urlBase}?recarga_id=${recargaId}&monto=${montoBase}&status=declined`;
                    } else if (status === 'PENDING') {
                        window.location.href = `${urlBase}?recarga_id=${recargaId}&monto=${montoBase}&status=pending`;
                    } else {
                        window.location.href = `${urlBase}?recarga_id=${recargaId}&monto=${montoBase}&status=error`;
                    }
                } else {
                    mostrarMensaje('Transacción cancelada', 'info');
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.textContent = 'Pagar y Recargar';
                    }
                    peticionEnCurso = false;
                }
            });

        } catch (error) {
            console.error("Error:", error);
            mostrarMensaje(`Error: ${error.message}`, 'danger');

            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Pagar y Recargar';
            }
            peticionEnCurso = false;
        }
    }

    // ----- Manejo del formulario de recarga -----
    if (recargaForm) {
        recargaForm.addEventListener("submit", async (evt) => {
            evt.preventDefault();
            await iniciarPagoConBackend();
        });
    } else {
        console.warn("Formulario #recargaForm no encontrado en la página.");
    }

    // ----- Inicialización -----
    function inicializar() {
        const initialAmount = Math.max(0, Math.round(Number(amountInput?.value || 0)));
        actualizarDesgloseEnUI(initialAmount);
        
        // Verificar si hay un resultado de recarga en la URL
        verificarResultadoRecarga();
        
        // Cargar los hijos
        cargarHijos();

        // Llamada adicional por si ya hay selección
        actualizarCedulaEnTarjeta();
    }

    inicializar();
});
