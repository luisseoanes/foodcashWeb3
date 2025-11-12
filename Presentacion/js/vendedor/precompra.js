document.addEventListener("DOMContentLoaded", function() {
    
    const API_URL = "https://web-production-b7e6.up.railway.app"; 
    const cedulaInput = document.getElementById("cedula-input");
    const searchBtn = document.getElementById("search-btn");
    const studentInfoDisplay = document.getElementById("student-info-display");
    const resultsContainer = document.getElementById("results-container");
    const detailsContainer = document.getElementById("details-container");

    searchBtn.addEventListener("click", iniciarBusqueda);
    cedulaInput.addEventListener("keyup", (event) => {
        if (event.key === "Enter") {
            iniciarBusqueda();
        }
    });

    async function iniciarBusqueda() {
        const cedula = cedulaInput.value.trim();
        if (!cedula) {
            alert("Por favor, ingrese la cédula del estudiante.");
            return;
        }

        studentInfoDisplay.textContent = "";
        studentInfoDisplay.style.display = "none";
        resultsContainer.innerHTML = `<p class="placeholder-text">Buscando estudiante...</p>`;
        detailsContainer.classList.add("hidden");

        try {
            // PASO 1: Buscar al estudiante por cédula
            const studentResponse = await fetch(`${API_URL}/estudiantes/cedula/${cedula}`);
            
            if (!studentResponse.ok) {
                if (studentResponse.status === 404) throw new Error("Estudiante con esa cédula no encontrado.");
                throw new Error("Error del servidor al buscar al estudiante.");
            }
            
            const student = await studentResponse.json();
            const studentId = student.id;
            const studentName = student.nombre;

            studentInfoDisplay.innerHTML = `Mostrando pedidos para: <strong>${studentName}</strong>`;
            studentInfoDisplay.style.display = "block";
            resultsContainer.innerHTML = `<p class="placeholder-text">Buscando precompras para ${studentName}...</p>`;

            // PASO 2: Con el ID interno, buscar sus precompras pendientes
            const precomprasResponse = await fetch(`${API_URL}/api/precompras/estudiante/${studentId}/pendientes`);
            if (!precomprasResponse.ok) throw new Error("Error al buscar las precompras del estudiante.");

            const precompras = await precomprasResponse.json();
            renderPrecompras(precompras, studentName);

        } catch (error) {
            resultsContainer.innerHTML = `<p class="placeholder-text" style="color: red;">${error.message}</p>`;
        }
    }

    function renderPrecompras(precompras, studentName) {
        resultsContainer.innerHTML = "";
        if (precompras.length === 0) {
            resultsContainer.innerHTML = `<p class="placeholder-text">No se encontraron precompras pendientes para ${studentName}.</p>`;
            return;
        }

        precompras.forEach(pc => {
            const card = document.createElement("div");
            card.className = "precompra-card";
            card.dataset.id = pc.id;
            card.dataset.studentName = studentName;

            const formattedDate = new Date(pc.fecha_precompra).toLocaleString('es-CO');
            const formattedTotal = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(pc.costo_total);

            card.innerHTML = `
                <div class="id">Pedido #${pc.id}</div>
                <div class="date"><i class="fas fa-calendar-alt"></i> ${formattedDate}</div>
                <div class="total"><i class="fas fa-dollar-sign"></i> ${formattedTotal}</div>
            `;
            
            card.addEventListener("click", (event) => mostrarDetalles(event.currentTarget));
            resultsContainer.appendChild(card);
        });
    }

    async function mostrarDetalles(cardElement) {
        const precompraId = cardElement.dataset.id;
        const studentName = cardElement.dataset.studentName;

        detailsContainer.classList.remove("hidden");
        detailsContainer.innerHTML = `<p>Cargando detalles del pedido #${precompraId}...</p>`;

        try {
            const response = await fetch(`${API_URL}/api/precompras/${precompraId}/detalles`);
            if (!response.ok) throw new Error("No se pudieron cargar los detalles del pedido.");

            const data = await response.json();
            const { precompra, compra } = data;

            let itemsHtml = '';
            compra.items.forEach(item => {
                const precio = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(item.precio_unitario);
                itemsHtml += `<li><span class="item-name">${item.cantidad}x ${item.nombre_alimento}</span><span class="item-details">${precio} c/u</span></li>`;
            });
            
            const total = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(precompra.costo_total);
            
            detailsContainer.innerHTML = `
                <h3>Detalles del Pedido #${precompra.id}</h3>
                <div class="details-header">
                    <span>Para: <strong>${studentName}</strong></span><br>
                    <span>Total: <strong>${total}</strong></span>
                </div>
                <h4>Productos a entregar:</h4>
                <ul class="items-list">${itemsHtml}</ul>
                <button class="deliver-btn" id="confirm-delivery-btn" data-id="${precompra.id}">
                    <i class="fas fa-check-circle"></i> Confirmar Entrega
                </button>
            `;

            document.getElementById("confirm-delivery-btn").addEventListener("click", entregarPedido);
        } catch (error) {
            detailsContainer.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    }
    
    async function entregarPedido(event) {
        const precompraId = event.currentTarget.dataset.id;
        const btn = event.currentTarget;

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        
        try {
            const response = await fetch(`${API_URL}/api/precompras/${precompraId}/entregar`, { method: 'PATCH' });
            if (!response.ok) throw new Error("El servidor no pudo procesar la entrega.");
            
            alert(`¡Pedido #${precompraId} entregado con éxito!`);
            
            detailsContainer.classList.add("hidden");
            iniciarBusqueda();
        } catch(error) {
            alert(`Error: ${error.message}`);
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check-circle"></i> Confirmar Entrega';
        }
    }
});