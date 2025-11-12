// --- CONFIGURACIÓN Y VARIABLES GLOBALES ---
const API_BASE_URL = 'https://web-production-b7e6.up.railway.app';
let allCompras = [];
let allAlimentos = [];
let salesOverTimeChart, categorySalesChart;
let currentReportData = null; // Para almacenar datos del reporte actual

// --- UTILIDADES ---
const formatCurrency = (amount) => `$${amount.toLocaleString('es-CO')}`;
const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    });
};

const formatDateShort = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit'
    });
};

// --- LÓGICA DE DATOS (Mejorada siguiendo el patrón del segundo código) ---
async function fetchInitialData() {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.style.display = 'flex';
    
    try {
        // Hacemos las llamadas en paralelo como en el segundo código
        const [comprasResponse, alimentosResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/compras`),
            fetch(`${API_BASE_URL}/api/alimentos/`)
        ]);

        if (!comprasResponse.ok) throw new Error('Error al obtener las compras');
        if (!alimentosResponse.ok) throw new Error('Error al obtener los alimentos');
        
        allCompras = await comprasResponse.json();
        allAlimentos = await alimentosResponse.json();
        
        console.log('Datos cargados:', { 
            compras: allCompras.length, 
            alimentos: allAlimentos.length 
        });

    } catch (error) {
        console.error('Error crítico al obtener los datos:', error);
        document.getElementById('report-placeholder').innerHTML = 
            `<p style="color: red;">Error al cargar los datos del servidor. Por favor, intente de nuevo.</p>`;
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

// --- LÓGICA DE REPORTES (Corregida) ---
function generateReport() {
    const startDateInput = document.getElementById('start-date').value;
    const endDateInput = document.getElementById('end-date').value;

    if (!startDateInput || !endDateInput) {
        alert('Por favor, seleccione una fecha de inicio y una de fin.');
        return;
    }

    const startDate = new Date(startDateInput);
    startDate.setHours(0, 0, 0, 0);

    const endDate = new Date(endDateInput);
    endDate.setHours(23, 59, 59, 999);
    
    if (startDate > endDate) {
        alert('La fecha de inicio no puede ser posterior a la fecha de fin.');
        return;
    }

    // Filtrar compras por rango de fechas
    const filteredCompras = allCompras.filter(compra => {
        const compraDate = new Date(compra.fecha);
        return compraDate >= startDate && compraDate <= endDate;
    });

    console.log('Compras filtradas:', filteredCompras.length);

    // Guardar datos del reporte actual para impresión
    currentReportData = {
        compras: filteredCompras,
        startDate: startDate,
        endDate: endDate,
        startDateStr: startDateInput,
        endDateStr: endDateInput
    };

    // Mostrar contenido del reporte y botón de impresión
    document.getElementById('report-placeholder').style.display = 'none';
    document.getElementById('report-content').style.display = 'block';
    document.getElementById('print-report-btn').style.display = 'inline-flex';

    // Actualizar todas las secciones del reporte
    updateReportSummary(filteredCompras);
    updateSalesByCategoryChart(filteredCompras, allAlimentos);
    updateTopSellingProductsTable(filteredCompras, allAlimentos);
    updateSalesOverTimeChart(filteredCompras, startDate, endDate);
    updateDetailedTransactionsTable(filteredCompras);
}

function updateReportSummary(compras) {
    try {
        const totalSales = compras.reduce((sum, c) => sum + c.total, 0);
        const totalTransactions = compras.length;
        const avgSaleValue = totalTransactions > 0 ? totalSales / totalTransactions : 0;
        const totalItemsSold = compras.reduce((sum, c) => {
            if (!Array.isArray(c.items)) return sum;
            return sum + c.items.reduce((itemSum, i) => itemSum + i.cantidad, 0);
        }, 0);
        
        document.getElementById('total-sales').textContent = formatCurrency(totalSales);
        document.getElementById('total-transactions').textContent = totalTransactions;
        document.getElementById('avg-sale-value').textContent = formatCurrency(avgSaleValue);
        document.getElementById('total-items-sold').textContent = totalItemsSold;
    } catch (error) {
        console.error('Error al actualizar resumen:', error);
    }
}

function updateSalesByCategoryChart(compras, alimentos) {
    try {
        // Crear mapa de categorías como en el segundo código
        const alimentoCategoryMap = new Map(alimentos.map(a => [a.id, a.categoria]));
        const salesByCategory = {};

        compras.forEach(compra => {
            if (!Array.isArray(compra.items)) return;

            compra.items.forEach(item => {
                const categoria = alimentoCategoryMap.get(item.producto_id) || 'Otros';
                if (!salesByCategory[categoria]) {
                    salesByCategory[categoria] = 0;
                }
                const totalProducto = item.cantidad * item.precio_unitario;
                salesByCategory[categoria] += totalProducto;
            });
        });
        
        const labels = Object.keys(salesByCategory);
        const data = Object.values(salesByCategory);

        // Actualizar gráfica
        categorySalesChart.data.labels = labels;
        categorySalesChart.data.datasets[0].data = data;
        
        // Generar colores dinámicos si es necesario
        if (labels.length > categorySalesChart.data.datasets[0].backgroundColor.length) {
            const colors = labels.map((_, index) => {
                const hue = (index * 137.508) % 360; // Distribución dorada
                return `hsla(${hue}, 70%, 60%, 0.8)`;
            });
            categorySalesChart.data.datasets[0].backgroundColor = colors;
        }
        
        categorySalesChart.update();
        console.log('Gráfica de categorías actualizada:', { labels, data });

    } catch (error) {
        console.error('Error al actualizar gráfica de categorías:', error);
    }
}

function updateTopSellingProductsTable(compras, alimentos) {
    try {
        // Crear mapa de productos
        const productMap = new Map(alimentos.map(a => [a.id, a.nombre]));
        const productSales = {};

        compras.forEach(compra => {
            if (!Array.isArray(compra.items)) return;
            
            compra.items.forEach(item => {
                if (!productSales[item.producto_id]) {
                    productSales[item.producto_id] = 0;
                }
                productSales[item.producto_id] += item.cantidad;
            });
        });

        // Ordenar productos por cantidad vendida
        const sortedProducts = Object.entries(productSales)
            .sort(([, qtyA], [, qtyB]) => qtyB - qtyA)
            .slice(0, 5);
        
        const tbody = document.getElementById('top-products-body');
        tbody.innerHTML = '';
        
        if (sortedProducts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3">No se encontraron productos vendidos en este período.</td></tr>';
            return;
        }

        sortedProducts.forEach(([productId, quantity], index) => {
            const productName = productMap.get(parseInt(productId)) || 'Producto Desconocido';
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${productName}</td>
                <td>${quantity}</td>
            `;
            tbody.appendChild(row);
        });

        console.log('Top productos actualizado:', sortedProducts.length);

    } catch (error) {
        console.error('Error al actualizar top productos:', error);
    }
}

function updateSalesOverTimeChart(compras, startDate, endDate) {
    try {
        // Crear objeto con todas las fechas del rango
        const salesByDay = {};
        let currentDate = new Date(startDate);
        
        while(currentDate <= endDate) {
            const dateKey = currentDate.toISOString().split('T')[0];
            salesByDay[dateKey] = 0;
            currentDate.setDate(currentDate.getDate() + 1);
        }

        // Sumar ventas por día
        compras.forEach(compra => {
            const dateKey = new Date(compra.fecha).toISOString().split('T')[0];
            if (salesByDay.hasOwnProperty(dateKey)) {
                salesByDay[dateKey] += compra.total;
            }
        });

        const labels = Object.keys(salesByDay).sort();
        const data = labels.map(date => salesByDay[date]);

        // Actualizar gráfica
        salesOverTimeChart.data.labels = labels;
        salesOverTimeChart.data.datasets[0].data = data;
        salesOverTimeChart.update();

        console.log('Gráfica temporal actualizada:', { días: labels.length, totalVentas: data.reduce((a, b) => a + b, 0) });

    } catch (error) {
        console.error('Error al actualizar gráfica temporal:', error);
    }
}

function updateDetailedTransactionsTable(compras) {
    try {
        const tbody = document.getElementById('detailed-transactions-body');
        tbody.innerHTML = '';
        
        if (compras.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No se encontraron transacciones en este período.</td></tr>';
            return;
        }

        // Ordenar compras por fecha (más recientes primero)
        const sortedCompras = compras.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));

        sortedCompras.forEach(compra => {
            // Usar nombre_alimento si está disponible, como en el segundo código
            const productosStr = Array.isArray(compra.items) 
                ? compra.items.map(item => `${item.nombre_alimento || 'Producto'} (x${item.cantidad})`).join(', ')
                : 'N/A';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>#${compra.id}</td>
                <td>${formatDate(compra.fecha)}</td>
                <td>Usuario ${compra.usuario_id}</td>
                <td>${productosStr}</td>
                <td>${formatCurrency(compra.total)}</td>
            `;
            tbody.appendChild(row);
        });

        console.log('Tabla de transacciones actualizada:', compras.length, 'transacciones');

    } catch (error) {
        console.error('Error al actualizar tabla de transacciones:', error);
    }
}

// --- FUNCIONES DE IMPRESIÓN ---
function generatePrintContent() {
    if (!currentReportData) {
        alert('No hay datos de reporte para imprimir. Genere un reporte primero.');
        return;
    }

    const { compras, startDateStr, endDateStr } = currentReportData;
    
    // Actualizar fecha de generación
    document.getElementById('print-generated-date').textContent = 
        new Date().toLocaleDateString('es-CO', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

    // Actualizar período del reporte
    document.getElementById('print-date-range').textContent = 
        `${formatDateShort(startDateStr)} - ${formatDateShort(endDateStr)}`;

    // Actualizar KPIs
    updatePrintKPIs(compras);
    
    // Actualizar tablas
    updatePrintCategoryTable(compras);
    updatePrintProductsTable(compras);
    updatePrintDailySalesTable(compras);
    updatePrintAllTransactionsTable(compras);
}

function updatePrintKPIs(compras) {
    const totalSales = compras.reduce((sum, c) => sum + c.total, 0);
    const totalTransactions = compras.length;
    const avgSaleValue = totalTransactions > 0 ? totalSales / totalTransactions : 0;
    const totalItemsSold = compras.reduce((sum, c) => {
        if (!Array.isArray(c.items)) return sum;
        return sum + c.items.reduce((itemSum, i) => itemSum + i.cantidad, 0);
    }, 0);

    document.getElementById('print-total-sales').textContent = formatCurrency(totalSales);
    document.getElementById('print-total-transactions').textContent = totalTransactions;
    document.getElementById('print-avg-sale').textContent = formatCurrency(avgSaleValue);
    document.getElementById('print-total-items').textContent = totalItemsSold;
}

function updatePrintCategoryTable(compras) {
    const alimentoCategoryMap = new Map(allAlimentos.map(a => [a.id, a.categoria]));
    const salesByCategory = {};
    let totalSales = 0;

    compras.forEach(compra => {
        if (!Array.isArray(compra.items)) return;
        compra.items.forEach(item => {
            const categoria = alimentoCategoryMap.get(item.producto_id) || 'Otros';
            const totalProducto = item.cantidad * item.precio_unitario;
            if (!salesByCategory[categoria]) {
                salesByCategory[categoria] = 0;
            }
            salesByCategory[categoria] += totalProducto;
            totalSales += totalProducto;
        });
    });

    const tbody = document.getElementById('print-category-body');
    tbody.innerHTML = '';

    Object.entries(salesByCategory)
        .sort(([, a], [, b]) => b - a)
        .forEach(([categoria, total]) => {
            const porcentaje = totalSales > 0 ? ((total / totalSales) * 100).toFixed(1) : '0.0';
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${categoria}</td>
                <td>${formatCurrency(total)}</td>
                <td>${porcentaje}%</td>
            `;
            tbody.appendChild(row);
        });
}

function updatePrintProductsTable(compras) {
    const productMap = new Map(allAlimentos.map(a => [a.id, a.nombre]));
    const productStats = {};

    compras.forEach(compra => {
        if (!Array.isArray(compra.items)) return;
        compra.items.forEach(item => {
            if (!productStats[item.producto_id]) {
                productStats[item.producto_id] = { cantidad: 0, total: 0 };
            }
            productStats[item.producto_id].cantidad += item.cantidad;
            productStats[item.producto_id].total += item.cantidad * item.precio_unitario;
        });
    });

    const sortedProducts = Object.entries(productStats)
        .sort(([, a], [, b]) => b.cantidad - a.cantidad)
        .slice(0, 10);

    const tbody = document.getElementById('print-products-body');
    tbody.innerHTML = '';

    sortedProducts.forEach(([productId, stats], index) => {
        const productName = productMap.get(parseInt(productId)) || 'Producto Desconocido';
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${productName}</td>
            <td>${stats.cantidad}</td>
            <td>${formatCurrency(stats.total)}</td>
        `;
        tbody.appendChild(row);
    });
}

function updatePrintDailySalesTable(compras) {
    const dailySales = {};

    compras.forEach(compra => {
        const dateKey = new Date(compra.fecha).toISOString().split('T')[0];
        if (!dailySales[dateKey]) {
            dailySales[dateKey] = { transactions: 0, total: 0 };
        }
        dailySales[dateKey].transactions += 1;
        dailySales[dateKey].total += compra.total;
    });

    const tbody = document.getElementById('print-daily-sales-body');
    tbody.innerHTML = '';

    Object.entries(dailySales)
        .sort(([a], [b]) => new Date(b) - new Date(a))
        .forEach(([date, stats]) => {
            const avgPerTransaction = stats.transactions > 0 ? stats.total / stats.transactions : 0;
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${formatDateShort(date)}</td>
                <td>${stats.transactions}</td>
                <td>${formatCurrency(stats.total)}</td>
                <td>${formatCurrency(avgPerTransaction)}</td>
            `;
            tbody.appendChild(row);
        });
}

function updatePrintAllTransactionsTable(compras) {
    const sortedCompras = compras.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
    const tbody = document.getElementById('print-all-transactions-body');
    tbody.innerHTML = '';

    sortedCompras.forEach(compra => {
        const productosStr = Array.isArray(compra.items) 
            ? compra.items.map(item => `${item.nombre_alimento || 'Producto'} (x${item.cantidad})`).join(', ')
            : 'N/A';

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>#${compra.id}</td>
            <td>${formatDate(compra.fecha)}</td>
            <td>Usuario ${compra.usuario_id}</td>
            <td>${productosStr}</td>
            <td>${formatCurrency(compra.total)}</td>
        `;
        tbody.appendChild(row);
    });
}

function printReport() {
    if (!currentReportData) {
        alert('No hay datos de reporte para imprimir. Genere un reporte primero.');
        return;
    }

    // Generar contenido para impresión
    generatePrintContent();
    
    // Mostrar el contenido de impresión
    document.getElementById('print-content').style.display = 'block';
    
    // Imprimir
    window.print();
    
    // Ocultar el contenido de impresión después de un breve delay
    setTimeout(() => {
        document.getElementById('print-content').style.display = 'none';
    }, 100);
}

// --- INICIALIZACIÓN (Mejorada) ---
document.addEventListener('DOMContentLoaded', async () => {
    // Lógica del menú lateral (si existe)
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            document.querySelector('.wrapper').classList.toggle('collapse');
        });
    }

    // Cargar datos principales al inicio
    await fetchInitialData();

    // Configurar fechas por defecto (últimos 30 días)
    const endDateInput = document.getElementById('end-date');
    const startDateInput = document.getElementById('start-date');
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    endDateInput.value = today.toISOString().split('T')[0];
    startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
    
    // Event Listeners
    document.getElementById('generate-report-btn').addEventListener('click', generateReport);
    document.getElementById('print-report-btn').addEventListener('click', printReport);

    // Botón de actualizar (si existe)
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', (e) => {
            e.preventDefault();
            fetchInitialData();
        });
    }

    // Inicializar Gráficos (con configuración mejorada)
    const salesOverTimeCtx = document.getElementById('salesOverTimeChart').getContext('2d');
    salesOverTimeChart = new Chart(salesOverTimeCtx, {
        type: 'line',
        data: { 
            labels: [], 
            datasets: [{ 
                label: 'Ventas Totales', 
                data: [], 
                fill: false, 
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.4,
                pointBackgroundColor: '#3498db',
                pointBorderColor: '#2980b9',
                pointRadius: 4
            }] 
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: { 
                x: { 
                    type: 'category',
                    title: {
                        display: true,
                        text: 'Fecha'
                    }
                }, 
                y: { 
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Ventas ($)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                } 
            }
        }
    });

    const categorySalesCtx = document.getElementById('categorySalesChart').getContext('2d');
    categorySalesChart = new Chart(categorySalesCtx, {
        type: 'doughnut',
        data: { 
            labels: [], 
            datasets: [{ 
                label: 'Ventas por Categoría', 
                data: [], 
                backgroundColor: [
                    'rgba(52, 152, 219, 0.8)',
                    'rgba(231, 76, 60, 0.8)', 
                    'rgba(155, 89, 182, 0.8)', 
                    'rgba(241, 196, 15, 0.8)', 
                    'rgba(46, 204, 113, 0.8)',
                    'rgba(230, 126, 34, 0.8)'
                ],
                borderColor: '#fff',
                borderWidth: 2
            }] 
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            plugins: { 
                legend: { 
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            return `${context.label}: ${formatCurrency(value)}`;
                        }
                    }
                }
            } 
        }
    });

    console.log('Dashboard de reportes inicializado correctamente');
});
