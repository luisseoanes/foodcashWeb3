document.addEventListener("DOMContentLoaded", async () => {
    // ===============================
    //      CONFIGURACIÓN CENTRAL
    // ===============================
    const API_BASE_URL = "https://web-production-b7e6.up.railway.app"; // URL centralizada para la API

    // ===============================
    // Verificar sesión y variables globales
    // ===============================
    const usuarioData = JSON.parse(localStorage.getItem("usuario"));
    if (!usuarioData) {
        window.location.href = "../../login.html";
        return;
    }
    document.getElementById("nombre-usuario").textContent = usuarioData.nombre;

    const cart = [];
    let total = 0;
    let studentData = null;
    let alimentosList = [];
    let blockedFoodIds = new Set(); 

    // ===============================
    // Elementos de la interfaz
    // ===============================
    const productsGrid = document.querySelector(".products-grid");
    const categoryButtons = document.querySelectorAll(".filter-btn");
    const productSearchInput = document.getElementById("product-search");
    const notificationContainer = document.getElementById("notification-container");

    // ===============================
    // Sidebar Toggle
    // ===============================
    document.getElementById("sidebar-toggle").addEventListener("click", () => {
        document.querySelector(".wrapper").classList.toggle("collapse");
    });

    // ===============================
    // Buscar estudiante
    // ===============================
    document.getElementById("student-search-form").addEventListener("submit", async function (e) {
        e.preventDefault();
        const cedula = document.getElementById("student-id").value.trim();
        if (!cedula) {
            showNotification("Por favor, ingrese la cédula del estudiante", "error");
            return;
        }
        
        studentData = null;
        blockedFoodIds.clear();

        try {
            // Se usa la variable API_BASE_URL
            const studentResponse = await fetch(`${API_BASE_URL}/estudiantes/cedula/${encodeURIComponent(cedula)}`);
            if (!studentResponse.ok) {
                throw new Error("No se encontró un estudiante con esa cédula");
            }
            studentData = await studentResponse.json();
            
            await fetchBlockedFoods(studentData.id);
            displayStudentInfo(studentData);
            renderProducts(alimentosList);
            showNotification("Estudiante encontrado. Restricciones aplicadas.", "success");

        } catch (error) {
            console.error("Error al buscar estudiante:", error);
            showNotification("Error: " + error.message, "error");
            renderProducts(alimentosList);
        }
    });

    async function fetchBlockedFoods(studentId) {
        try {
            // Se usa la variable API_BASE_URL
            const response = await fetch(`${API_BASE_URL}/estudiantes/${studentId}/alimentosBloqueados`);
            if (!response.ok) {
                console.warn(`No se encontraron alimentos bloqueados para el estudiante ${studentId}.`);
                blockedFoodIds.clear();
                return;
            }
            const blockedList = await response.json();
            blockedFoodIds = new Set(blockedList.map(item => item.id_alimento));
        } catch (error) {
            console.error("Error al obtener alimentos bloqueados:", error);
            showNotification("No se pudieron cargar las restricciones del estudiante", "warning");
            blockedFoodIds.clear();
        }
    }

    function displayStudentInfo(student) {
        document.getElementById("student-name").textContent = student.nombre;
        document.getElementById("display-student-id").textContent = student.cedula;
        document.getElementById("student-balance").textContent = formatCurrency(student.saldo);
        document.getElementById("student-details").style.display = "flex";
    }

    function updateCart() {
        const cartItems = document.querySelector(".cart-items");
        cartItems.innerHTML = "";
        if (cart.length === 0) {
            cartItems.innerHTML = `
                <div class="empty-cart-message">
                    <i class="fas fa-shopping-basket"></i>
                    <p>Carrito vacío</p>
                </div>
            `;
            document.querySelector(".checkout-btn").disabled = true;
            updateTotals(0, 0);
            return;
        }
        let subtotal = 0;
        cart.forEach((item, index) => {
            subtotal += item.total;
            const li = document.createElement("li");
            li.className = "cart-item";
            li.innerHTML = `
                <div class="item-details">
                    <span class="item-name">${item.name}</span>
                    <div class="item-price">
                        <span class="quantity">${item.quantity}x</span>
                        <span class="price">${formatCurrency(item.price)}</span>
                    </div>
                </div>
                <div class="item-total">
                    ${formatCurrency(item.total)}
                    <button class="remove-item" data-index="${index}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            cartItems.appendChild(li);
        });
        total = subtotal; // Asumiendo que no hay impuestos
        updateTotals(subtotal, total);
        document.querySelectorAll(".remove-item").forEach(button => {
            button.addEventListener("click", function () {
                const index = parseInt(this.dataset.index);
                cart.splice(index, 1);
                updateCart();
            });
        });
    }

    function updateTotals(subtotal, total) {
        document.querySelector(".subtotal").textContent = formatCurrency(subtotal);
        document.querySelector(".total-amount").textContent = formatCurrency(total);
    }
    
    function addToCart(productEl) {
        if (!studentData) {
            showNotification("Primero debe buscar y seleccionar un estudiante", "error");
            return;
        }
        
        const productId = parseInt(productEl.getAttribute("data-id"));

        if (blockedFoodIds.has(productId)) {
            showNotification("Este producto está bloqueado para el estudiante y no se puede comprar.", "error");
            return;
        }

        const productName = productEl.querySelector("h3").textContent;
        const productPrice = parseInt(productEl.querySelector(".price").textContent.replace(/\D/g, ''));
        const quantity = parseInt(productEl.querySelector(".quantity").value);
        const productStock = parseInt(productEl.getAttribute("data-stock"));

        if (quantity > productStock) {
            showNotification(`Solo hay ${productStock} unidades disponibles`, "error");
            return;
        }

        const newStock = productStock - quantity;
        productEl.setAttribute("data-stock", newStock);
        productEl.querySelector(".stock-badge").textContent = newStock;
        
        const itemTotal = productPrice * quantity;
        cart.push({ id: productId, name: productName, price: productPrice, quantity: quantity, total: itemTotal });
        
        updateCart();
        showNotification(`${quantity} ${productName} agregado al carrito`, "success");
        document.querySelector(".checkout-btn").disabled = false;
    }

    // ===============================
    // Finalizar Venta y Modales
    // ===============================
    document.querySelector(".checkout-btn").addEventListener("click", function () {
        if (!studentData) {
            showNotification("Debe seleccionar un estudiante", "error");
            return;
        }
        if (cart.length === 0) {
            showNotification("El carrito está vacío", "error");
            return;
        }
        if (total > studentData.saldo) {
            showNotification("El estudiante no tiene saldo suficiente", "error");
            return;
        }
        document.getElementById("confirm-student-name").textContent = studentData.nombre;
        document.getElementById("confirm-total").textContent = formatCurrency(total);
        document.getElementById("confirm-balance").textContent = formatCurrency(studentData.saldo);
        document.getElementById("confirm-new-balance").textContent = formatCurrency(studentData.saldo - total);
        document.getElementById("confirm-modal").style.display = "flex";
    });

    document.getElementById("confirm-sale").addEventListener("click", async function () {
        if (!studentData || !studentData.id) {
            showNotification("Error: No se encontró el ID del estudiante", "error");
            return;
        }
      
        try {
            const saldoEndpoint = `${API_BASE_URL}/estudiantes/${encodeURIComponent(studentData.id)}/descargaSaldo`;
            const saldoResponse = await fetch(saldoEndpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ monto: total })
            });
      
            if (!saldoResponse.ok) throw new Error("Error al actualizar el saldo del estudiante");
      
            const updatedStudent = await saldoResponse.json();
            studentData.saldo = updatedStudent.saldo;
            document.getElementById("student-balance").textContent = formatCurrency(updatedStudent.saldo);
      
            const compraPayload = {
                usuario_id: parseInt(studentData.id),
                fecha: new Date().toISOString(),
                total: parseFloat(total.toFixed(2)),
                items: cart.map(item => ({
                    producto_id: parseInt(item.id),
                    cantidad: parseInt(item.quantity),
                    precio_unitario: parseFloat(item.price.toFixed(2))
                }))
            };

            const compraResponse = await fetch(`${API_BASE_URL}/guardarCompra`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(compraPayload)
            });
      
            if (!compraResponse.ok) {
                const errorText = await compraResponse.text();
                throw new Error(`Error al guardar la compra: ${compraResponse.status} - ${errorText}`);
            }

            const compraResult = await compraResponse.json();
            console.log('Compra guardada exitosamente:', compraResult);
      
            document.getElementById("confirm-modal").style.display = "none";
      
            document.getElementById("receipt-student").textContent = studentData.nombre;
            document.getElementById("receipt-total").textContent = formatCurrency(total);
            document.getElementById("receipt-balance").textContent = formatCurrency(updatedStudent.saldo);
            const now = new Date();
            document.getElementById("receipt-date").textContent = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
            document.getElementById("success-modal").style.display = "flex";
      
            addToRecentSales(studentData.nombre, total);
      
            cart.length = 0;
            updateCart();
        } catch (error) {
            console.error("Error al confirmar la venta:", error);
            showNotification("Error al confirmar la venta: " + error.message, "error");
        }
    });

    document.getElementById("cancel-sale").addEventListener("click", () => {
        document.getElementById("confirm-modal").style.display = "none";
    });

    document.getElementById("new-sale").addEventListener("click", () => {
        document.getElementById("success-modal").style.display = "none";
        document.getElementById("student-search-form").reset();
        document.getElementById("student-details").style.display = "none";
        studentData = null;
        blockedFoodIds.clear();
        renderProducts(alimentosList);
    });

    document.querySelectorAll(".close-modal").forEach(closeBtn => {
        closeBtn.addEventListener("click", function () {
            this.closest(".modal").style.display = "none";
        });
    });

    function addToRecentSales(studentName, saleTotal) {
        const salesList = document.querySelector(".sales-list");
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const li = document.createElement("li");
        li.innerHTML = `
            <div class="sale-info">
                <span class="sale-student">${studentName}</span>
                <span class="sale-time">${timeStr}</span>
            </div>
            <span class="sale-amount">${formatCurrency(saleTotal)}</span>
        `;
        salesList.prepend(li);
        if (salesList.children.length > 5) {
            salesList.removeChild(salesList.lastChild);
        }
    }

    // ===============================
    // Funciones para Productos (API)
    // ===============================
    async function fetchAlimentos() {
        try {
            // Se usa la variable API_BASE_URL
            const response = await fetch(`${API_BASE_URL}/api/alimentos/`);
            if (!response.ok) {
                throw new Error("Error al obtener los alimentos");
            }
            alimentosList = await response.json();
            renderProducts(alimentosList);
        } catch (error) {
            console.error("Error cargando alimentos:", error);
            showNotification("Error al cargar los alimentos", "error");
        }
    }

    function renderProducts(data) {
        productsGrid.innerHTML = "";
        data.forEach(alimento => {
            const isBlocked = blockedFoodIds.has(alimento.id);
            const productEl = document.createElement("div");
            productEl.classList.add("product");
            if (isBlocked) {
                productEl.classList.add("product-blocked");
            }
            productEl.setAttribute("data-id", alimento.id);
            productEl.setAttribute("data-category", alimento.categoria || "otros");
            productEl.setAttribute("data-stock", alimento.cantidad_en_stock);

            const disabledAttribute = isBlocked ? 'disabled' : '';

            productEl.innerHTML = `
                <div class="product-image">
                    <img src="${alimento.imagen}" alt="${alimento.nombre}" style="width:100px; height:100px; object-fit:cover;">
                    <span class="stock-badge">${alimento.cantidad_en_stock}</span>
                </div>
                <div class="product-info">
                    <h3>${alimento.nombre}</h3>
                    <p class="price">${formatCurrency(alimento.precio)}</p>
                    <div class="nutritional-info">
                        <span class="calories">${alimento.calorias} cal</span>
                        <i class="fas fa-info-circle info-icon" title="Información nutricional"></i>
                    </div>
                </div>
                <div class="product-actions">
                    <div class="quantity-control">
                        <button class="quantity-btn minus" ${disabledAttribute}>-</button>
                        <input type="number" min="1" max="${alimento.cantidad_en_stock}" value="1" class="quantity" ${disabledAttribute}>
                        <button class="quantity-btn plus" ${disabledAttribute}>+</button>
                    </div>
                    <button class="add-to-cart" ${disabledAttribute}><i class="fas fa-cart-plus"></i> Agregar</button>
                </div>
            `;
            productsGrid.appendChild(productEl);
        });
        addProductEventListeners();
    }
  
    function addProductEventListeners() {
        document.querySelectorAll(".quantity-btn").forEach(button => {
            button.addEventListener("click", function () {
                const quantityInput = this.parentElement.querySelector(".quantity");
                let currentValue = parseInt(quantityInput.value);
                const max = parseInt(quantityInput.getAttribute("max"));
                if (this.classList.contains("plus") && currentValue < max) {
                    quantityInput.value = currentValue + 1;
                } else if (this.classList.contains("minus") && currentValue > 1) {
                    quantityInput.value = currentValue - 1;
                }
            });
        });
        document.querySelectorAll(".add-to-cart").forEach(button => {
            button.addEventListener("click", () => {
                addToCart(button.closest(".product"));
            });
        });
    }

    // ===============================
    // Notificaciones y Formateo
    // ===============================
    function showNotification(message, type = "info") {
        const notification = document.createElement("div");
        notification.classList.add("notification", type);
        let icon = "info-circle";
        if (type === "success") icon = "check-circle";
        if (type === "error") icon = "times-circle";
        if (type === "warning") icon = "exclamation-triangle";
        notification.innerHTML = `<i class="fas fa-${icon}"></i> <span>${message}</span>`;
        notificationContainer.appendChild(notification);
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    function formatCurrency(value) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }

    // ===============================
    // Filtros y Búsqueda de Productos
    // ===============================
    categoryButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            categoryButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const category = btn.dataset.category;
            let filteredList = alimentosList;
            if (category !== "all") {
                filteredList = alimentosList.filter(item => (item.categoria || 'otros').toLowerCase() === category.toLowerCase());
            }
            productSearchInput.value = "";
            renderProducts(filteredList);
        });
    });

    productSearchInput.addEventListener("input", () => {
        const query = productSearchInput.value.toLowerCase();
        const activeCategory = document.querySelector(".filter-btn.active").dataset.category;
        
        let baseList = alimentosList;
        if(activeCategory !== 'all') {
            baseList = alimentosList.filter(item => (item.categoria || 'otros').toLowerCase() === activeCategory.toLowerCase());
        }

        const filtered = baseList.filter(item => item.nombre.toLowerCase().includes(query));
        renderProducts(filtered);
    });

    // ===============================
    // Iniciar: Obtener productos desde el API
    // ===============================
    fetchAlimentos();
});