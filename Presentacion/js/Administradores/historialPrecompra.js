document.addEventListener("DOMContentLoaded", function() {
    const API_URL = "https://web-production-b7e6.up.railway.app/api";
    
    // Elementos de la tabla principal
    const tableBody = document.getElementById("precompras-table-body");
    const filterInput = document.getElementById("filter-input");
    const filterStatus = document.getElementById("filter-status");
    const loadingSpinner = document.getElementById("loading-spinner");

    // --- NUEVO: Elemento para la tabla de resumen ---
    const pendingItemsBody = document.getElementById("pending-items-summary-body");

    let allPrecompras = [];

    // --- Funciones de formato---
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        return new Date(dateString).toLocaleDateString('es-CO', options);
    }

    function formatCurrency(value) {
        if (value === null || value === undefined) return '$ 0';
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);
    }

    // --- NUEVA FUNCIÓN: Para renderizar la tabla de resumen ---
    /**
     * Calcula y muestra un resumen de todos los items pendientes de entrega.
     * @param {Array} data - La lista completa de todas las precompras.
     */
    function renderPendingItemsSummary(data) {
        const pendingItems = {}; // Usaremos un objeto para agregar las cantidades

        // 1. Filtramos solo las precompras pendientes
        const pendingPrecompras = data.filter(pc => !pc.entregado);
        
        // 2. Iteramos sobre los items de las precompras pendientes para sumar las cantidades
        pendingPrecompras.forEach(pc => {
            if (pc.items && pc.items.length > 0) {
                pc.items.forEach(item => {
                    const itemName = item.nombre ?? 'Producto desconocido';
                    const quantity = item.cantidad;
                    
                    if (pendingItems[itemName]) {
                        pendingItems[itemName] += quantity; // Si ya existe, suma la cantidad
                    } else {
                        pendingItems[itemName] = quantity; // Si no, lo crea
                    }
                });
            }
        });

        // 3. Renderizamos la tabla de resumen
        pendingItemsBody.innerHTML = ""; // Limpiar tabla de resumen
        if (Object.keys(pendingItems).length === 0) {
            pendingItemsBody.innerHTML = `<tr><td colspan="2" style="text-align: center;">No hay productos pendientes de entrega.</td></tr>`;
            return;
        }

        for (const [itemName, totalQuantity] of Object.entries(pendingItems)) {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${itemName}</td>
                <td>${totalQuantity}</td>
            `;
            pendingItemsBody.appendChild(row);
        }
    }


    function toggleDetails(clickedRow, items) {
        const precompraId = clickedRow.dataset.precompraId;
        const existingDetailRow = document.getElementById(`details-for-${precompraId}`);

        if (existingDetailRow) {
            existingDetailRow.remove();
            return;
        }

        const detailRow = document.createElement("tr");
        detailRow.id = `details-for-${precompraId}`;
        detailRow.className = 'details-row';

        let itemsHtml = '<p>No hay productos asociados a esta precompra.</p>';
        if (items && items.length > 0) {
            itemsHtml = '<ul class="details-item-list">';
            items.forEach(item => {
                itemsHtml += `<li><strong>${item.cantidad}x</strong> ${item.nombre ?? 'Producto desconocido'}</li>`;
            });
            itemsHtml += '</ul>';
        }

        detailRow.innerHTML = `<td colspan="6"><div class="details-content"><h4>Productos del Pedido</h4>${itemsHtml}</div></td>`;
        clickedRow.insertAdjacentElement('afterend', detailRow);
    }

    function renderTable(data) {
        tableBody.innerHTML = "";
        if (data.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center;">No se encontraron resultados.</td></tr>`;
            return;
        }

        data.forEach(pc => {
            const row = document.createElement("tr");
            row.className = "clickable-row";
            row.dataset.precompraId = pc.id;

            const statusClass = pc.entregado ? 'status-entregado' : 'status-pendiente';
            const statusText = pc.entregado ? 'Entregado' : 'Pendiente';

            row.innerHTML = `
                <td>#${pc.id}</td>
                <td>${pc.nombre_estudiante}</td>
                <td>${formatDate(pc.fecha_precompra)}</td>
                <td>${formatCurrency(pc.costo_total)}</td>
                <td><span class="status ${statusClass}">${statusText}</span></td>
                <td>${formatDate(pc.fecha_entrega)}</td>
            `;
            
            row.addEventListener('click', () => toggleDetails(row, pc.items));
            tableBody.appendChild(row);
        });
    }

    function applyFilters() {
        const searchTerm = filterInput.value.toLowerCase();
        const status = filterStatus.value;
        const filteredData = allPrecompras.filter(pc => {
            const statusMatch = status === 'todos' || (status === 'entregado' && pc.entregado) || (status === 'pendiente' && !pc.entregado);
            const searchMatch = pc.nombre_estudiante.toLowerCase().includes(searchTerm) || pc.id.toString().includes(searchTerm);
            return statusMatch && searchMatch;
        });
        renderTable(filteredData);
    }

    async function fetchAllPrecompras() {
        loadingSpinner.style.display = 'block';
        tableBody.innerHTML = "";
        try {
            const response = await fetch(`${API_URL}/precompras/todas/detalladas`);
            if (!response.ok) {
                throw new Error("No se pudieron cargar los datos del servidor.");
            }
            allPrecompras = await response.json();
            
            // Llamamos a las dos funciones de renderizado ---
            renderTable(allPrecompras);
            renderPendingItemsSummary(allPrecompras); // <-- Se renderiza el nuevo resumen

        } catch (error) {
            tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: red;">${error.message}</td></tr>`;
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    // --- Inicialización ---
    filterInput.addEventListener("input", applyFilters);
    filterStatus.addEventListener("change", applyFilters);
    
    fetchAllPrecompras();
});