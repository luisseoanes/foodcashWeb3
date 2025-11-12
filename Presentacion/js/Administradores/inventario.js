class InventarioManager {
    constructor() {
        this.baseURL = 'https://web-production-b7e6.up.railway.app/api/alimentos/';
        this.productos = [];
        this.filteredProducts = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInventory();
    }

    setupEventListeners() {
        // Búsqueda en tiempo real
        document.getElementById('inventory-search').addEventListener('input', (e) => {
            this.filterProducts(e.target.value);
        });

        // Botón añadir nuevo producto
        document.getElementById('add-new-product').addEventListener('click', () => {
            this.showAddProductModal();
        });

        // Botón actualizar
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadInventory();
        });
    }

    async loadInventory() {
        try {
            this.showLoading();
            const response = await fetch(this.baseURL);
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            
            this.productos = await response.json();
            this.filteredProducts = [...this.productos];
            this.renderInventoryTable();
            this.showNotification('Inventario cargado correctamente', 'success');
        } catch (error) {
            console.error('Error al cargar inventario:', error);
            this.showNotification('Error al cargar el inventario', 'error');
        }
    }

    filterProducts(searchTerm) {
        if (!searchTerm.trim()) {
            this.filteredProducts = [...this.productos];
        } else {
            const term = searchTerm.toLowerCase();
            this.filteredProducts = this.productos.filter(producto => 
                producto.nombre.toLowerCase().includes(term) ||
                producto.categoria.toLowerCase().includes(term)
            );
        }
        this.renderInventoryTable();
    }

    renderInventoryTable() {
        const tbody = document.getElementById('inventory-table-body');
        
        if (this.filteredProducts.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="no-data">
                        <i class="fas fa-box-open"></i>
                        <p>No se encontraron productos</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.filteredProducts.map(producto => `
            <tr class="${producto.cantidad_en_stock <= 5 ? 'low-stock' : ''}">
                <td>${producto.id}</td>
                <td>
                    <div class="product-info">
                        ${producto.imagen ? `<img src="${producto.imagen}" alt="${producto.nombre}" class="product-image">` : ''}
                        <div>
                            <strong>${producto.nombre}</strong>
                            <small>${producto.calorias} cal</small>
                        </div>
                    </div>
                </td>
                <td><span class="category-badge">${producto.categoria}</span></td>
                <td class="price">$${producto.precio.toLocaleString()}</td>
                <td>
                    <div class="stock-info">
                        <span class="stock-number ${producto.cantidad_en_stock <= 5 ? 'low-stock' : ''}">${producto.cantidad_en_stock}</span>
                        ${producto.cantidad_en_stock <= 5 ? '<i class="fas fa-exclamation-triangle low-stock-warning" title="Stock bajo"></i>' : ''}
                    </div>
                </td>
                <td class="actions">
                    <button class="btn-action btn-edit" onclick="inventarioManager.editProduct(${producto.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-stock" onclick="inventarioManager.showStockModal(${producto.id})" title="Ajustar Stock">
                        <i class="fas fa-boxes"></i>
                    </button>
                    <button class="btn-action btn-delete" onclick="inventarioManager.deleteProduct(${producto.id})" title="Eliminar">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    showStockModal(productId) {
        const producto = this.productos.find(p => p.id === productId);
        if (!producto) return;

        const modal = this.createModal(`
            <div class="modal-header">
                <h3><i class="fas fa-boxes"></i> Ajustar Stock - ${producto.nombre}</h3>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="current-stock">
                    <p><strong>Stock actual:</strong> <span class="stock-highlight">${producto.cantidad_en_stock}</span> unidades</p>
                </div>
                
                <div class="stock-actions">
                    <div class="action-group">
                        <h4><i class="fas fa-plus-circle text-success"></i> Aumentar Stock</h4>
                        <div class="input-group">
                            <input type="number" id="increase-amount" min="1" placeholder="Cantidad a añadir">
                            <button class="btn-success" onclick="inventarioManager.adjustStock(${productId}, 'increase')">
                                <i class="fas fa-plus"></i> Añadir
                            </button>
                        </div>
                    </div>
                    
                    <div class="action-group">
                        <h4><i class="fas fa-minus-circle text-danger"></i> Disminuir Stock</h4>
                        <div class="input-group">
                            <input type="number" id="decrease-amount" min="1" max="${producto.cantidad_en_stock}" placeholder="Cantidad a restar">
                            <button class="btn-danger" onclick="inventarioManager.adjustStock(${productId}, 'decrease')">
                                <i class="fas fa-minus"></i> Restar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `);

        document.body.appendChild(modal);
    }

    async adjustStock(productId, action) {
        const amountInput = document.getElementById(action === 'increase' ? 'increase-amount' : 'decrease-amount');
        const amount = parseInt(amountInput.value);

        if (!amount || amount <= 0) {
            this.showNotification('Ingrese una cantidad válida', 'error');
            return;
        }

        try {
            if (action === 'increase') {
                await this.increaseStock(productId, amount);
            } else {
                await this.decreaseStock(productId, amount);
            }
            
            this.closeModal();
            this.loadInventory();
        } catch (error) {
            console.error('Error al ajustar stock:', error);
            this.showNotification('Error al ajustar el stock', 'error');
        }
    }

    async increaseStock(productId, amount) {
        const producto = this.productos.find(p => p.id === productId);
        const newStock = producto.cantidad_en_stock + amount;
        
        const response = await fetch(`${this.baseURL}${productId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ...producto,
                cantidad_en_stock: newStock
            })
        });

        if (!response.ok) {
            throw new Error('Error al aumentar stock');
        }

        this.showNotification(`Stock aumentado en ${amount} unidades`, 'success');
    }

    async decreaseStock(productId, amount) {
        const response = await fetch(`${this.baseURL}${productId}/disminuir_inventario`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cantidad: amount
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al disminuir stock');
        }

        this.showNotification(`Stock disminuido en ${amount} unidades`, 'success');
    }

    showAddProductModal() {
        const modal = this.createModal(`
            <div class="modal-header">
                <h3><i class="fas fa-plus"></i> Añadir Nuevo Producto</h3>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <form id="add-product-form">
                    <div class="form-group">
                        <label>Nombre del Producto *</label>
                        <input type="text" id="product-name" required>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Categoría *</label>
                            <select id="product-category" required>
                                <option value="">Seleccionar categoría</option>
                                <option value="Bebidas">Bebidas</option>
                                <option value="Comida Rápida">Comida Rápida</option>
                                <option value="Postres">Postres</option>
                                <option value="Ensaladas">Ensaladas</option>
                                <option value="Snacks">Snacks</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Precio *</label>
                            <input type="number" id="product-price" min="0" step="0.01" required>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Stock Inicial *</label>
                            <input type="number" id="product-stock" min="0" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Calorías</label>
                            <input type="number" id="product-calories" min="0">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>URL de Imagen</label>
                        <input type="url" id="product-image" placeholder="https://ejemplo.com/imagen.jpg">
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn-secondary" onclick="inventarioManager.closeModal()">Cancelar</button>
                        <button type="submit" class="btn-primary">
                            <i class="fas fa-save"></i> Guardar Producto
                        </button>
                    </div>
                </form>
            </div>
        `);

        document.body.appendChild(modal);

        // Manejar envío del formulario
        document.getElementById('add-product-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveNewProduct();
        });
    }

    async saveNewProduct() {
        const formData = {
            nombre: document.getElementById('product-name').value,
            categoria: document.getElementById('product-category').value,
            precio: parseFloat(document.getElementById('product-price').value),
            cantidad_en_stock: parseInt(document.getElementById('product-stock').value),
            calorias: parseInt(document.getElementById('product-calories').value) || 0,
            imagen: document.getElementById('product-image').value || null
        };

        try {
            const response = await fetch(this.baseURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al crear producto');
            }

            this.closeModal();
            this.loadInventory();
            this.showNotification('Producto creado exitosamente', 'success');
        } catch (error) {
            console.error('Error al crear producto:', error);
            this.showNotification(error.message, 'error');
        }
    }

    async deleteProduct(productId) {
        const producto = this.productos.find(p => p.id === productId);
        
        if (!confirm(`¿Está seguro que desea eliminar "${producto.nombre}"?`)) {
            return;
        }

        try {
            const response = await fetch(`${this.baseURL}${productId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Error al eliminar producto');
            }

            this.loadInventory();
            this.showNotification('Producto eliminado exitosamente', 'success');
        } catch (error) {
            console.error('Error al eliminar producto:', error);
            this.showNotification('Error al eliminar el producto', 'error');
        }
    }

    editProduct(productId) {
        const producto = this.productos.find(p => p.id === productId);
        if (!producto) return;

        const modal = this.createModal(`
            <div class="modal-header">
                <h3><i class="fas fa-edit"></i> Editar Producto</h3>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <form id="edit-product-form">
                    <div class="form-group">
                        <label>Nombre del Producto *</label>
                        <input type="text" id="edit-product-name" value="${producto.nombre}" required>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Categoría *</label>
                            <select id="edit-product-category" required>
                                <option value="Bebidas" ${producto.categoria === 'Bebidas' ? 'selected' : ''}>Bebidas</option>
                                <option value="Comida Rápida" ${producto.categoria === 'Comida Rápida' ? 'selected' : ''}>Comida Rápida</option>
                                <option value="Postres" ${producto.categoria === 'Postres' ? 'selected' : ''}>Postres</option>
                                <option value="Ensaladas" ${producto.categoria === 'Ensaladas' ? 'selected' : ''}>Ensaladas</option>
                                <option value="Snacks" ${producto.categoria === 'Snacks' ? 'selected' : ''}>Snacks</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Precio *</label>
                            <input type="number" id="edit-product-price" value="${producto.precio}" min="0" step="0.01" required>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Stock *</label>
                            <input type="number" id="edit-product-stock" value="${producto.cantidad_en_stock}" min="0" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Calorías</label>
                            <input type="number" id="edit-product-calories" value="${producto.calorias}" min="0">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>URL de Imagen</label>
                        <input type="url" id="edit-product-image" value="${producto.imagen || ''}">
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn-secondary" onclick="inventarioManager.closeModal()">Cancelar</button>
                        <button type="submit" class="btn-primary">
                            <i class="fas fa-save"></i> Actualizar Producto
                        </button>
                    </div>
                </form>
            </div>
        `);

        document.body.appendChild(modal);

        document.getElementById('edit-product-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateProduct(productId);
        });
    }

    async updateProduct(productId) {
        const formData = {
            nombre: document.getElementById('edit-product-name').value,
            categoria: document.getElementById('edit-product-category').value,
            precio: parseFloat(document.getElementById('edit-product-price').value),
            cantidad_en_stock: parseInt(document.getElementById('edit-product-stock').value),
            calorias: parseInt(document.getElementById('edit-product-calories').value) || 0,
            imagen: document.getElementById('edit-product-image').value || null
        };

        try {
            const response = await fetch(`${this.baseURL}${productId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al actualizar producto');
            }

            this.closeModal();
            this.loadInventory();
            this.showNotification('Producto actualizado exitosamente', 'success');
        } catch (error) {
            console.error('Error al actualizar producto:', error);
            this.showNotification(error.message, 'error');
        }
    }

    // Utilidades
    createModal(content) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                ${content}
            </div>
        `;

        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.classList.contains('close-modal')) {
                this.closeModal();
            }
        });

        return modal;
    }

    closeModal() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.remove();
        }
    }

    showLoading() {
        const tbody = document.getElementById('inventory-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Cargando inventario...</p>
                </td>
            </tr>
        `;
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icon = type === 'success' ? 'fa-check-circle' : 
                    type === 'error' ? 'fa-exclamation-circle' : 
                    'fa-info-circle';
        
        notification.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
            <button class="close-notification">&times;</button>
        `;

        container.appendChild(notification);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);

        // Botón cerrar
        notification.querySelector('.close-notification').addEventListener('click', () => {
            notification.remove();
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.inventarioManager = new InventarioManager();
});

// Toggle sidebar
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const wrapper = document.querySelector('.wrapper');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            wrapper.classList.toggle('collapse');
        });
    }
});