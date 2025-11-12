// Configuración de la API
const API_BASE_URL = 'https://web-production-b7e6.up.railway.app'; // Asegúrate que esta sea tu URL de API

// Variables globales para las gráficas
let weeklySalesChart;
let categorySalesChart;

// --- Utilidades ---
function isToday(dateString) { const today = new Date(); const date = new Date(dateString); return date.toDateString() === today.toDateString(); }
function isDateInWeek(dateString, targetDate) { const date = new Date(dateString); return date.toDateString() === targetDate.toDateString(); }
function formatCurrency(amount) { return `$${amount.toLocaleString('es-CO')}`; }
function formatDate(dateString) { const date = new Date(dateString); const now = new Date(); const diffMs = now - date; const diffMins = Math.floor(diffMs / (1000 * 60)); if (diffMins < 60) return `hace ${diffMins} min`; if (diffMins < 1440) return `hace ${Math.floor(diffMins / 60)}h`; return date.toLocaleDateString('es-CO'); }
function getWeekDates() { const dates = []; const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']; for (let i = 6; i >= 0; i--) { const date = new Date(); date.setDate(date.getDate() - i); dates.push({ date: date, name: dayNames[date.getDay()] }); } return dates; }

// --- Funciones de Fetching de Datos (Optimizadas) ---

async function fetchAllData() {
    try {
        // Hacemos las dos únicas llamadas necesarias en paralelo
        const [comprasResponse, alimentosResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/compras`),
            fetch(`${API_BASE_URL}/api/alimentos/`)
        ]);

        if (!comprasResponse.ok) throw new Error('Error al obtener las compras');
        if (!alimentosResponse.ok) throw new Error('Error al obtener los alimentos');

        const allCompras = await comprasResponse.json();
        const allAlimentos = await alimentosResponse.json();

        return { allCompras, allAlimentos };

    } catch (error) {
        console.error("Error crítico al obtener los datos:", error);
        // Manejar error global, por ejemplo, mostrando un overlay de error en la página
        document.body.innerHTML = `<div class="error" style="padding: 20px;">Error al cargar los datos del dashboard. Por favor, refresca la página o contacta al administrador.</div>`;
        return null;
    }
}

// --- Funciones de Actualización de UI ---

function updateDashboardStats(allCompras) {
    const dailySalesEl = document.getElementById('daily-sales');
    const dailyTransactionsEl = document.getElementById('daily-transactions');

    try {
        const comprasHoy = allCompras.filter(compra => isToday(compra.fecha));
        const ventasDelDia = comprasHoy.reduce((total, compra) => total + compra.total, 0);

        dailySalesEl.textContent = formatCurrency(ventasDelDia);
        dailyTransactionsEl.textContent = comprasHoy.length;
        [dailySalesEl, dailyTransactionsEl].forEach(el => el.classList.remove('loading', 'error'));

    } catch (error) {
        console.error('Error al actualizar estadísticas diarias:', error);
        dailySalesEl.textContent = 'Error';
        dailyTransactionsEl.textContent = 'Error';
        [dailySalesEl, dailyTransactionsEl].forEach(el => el.classList.add('error'));
    }
}

function updateLowStockItems(allAlimentos) {
    const lowStockEl = document.getElementById('low-stock-items');
    try {
        const stockBajo = allAlimentos.filter(alimento => alimento.cantidad_en_stock < 8);
        lowStockEl.textContent = stockBajo.length;
        lowStockEl.classList.remove('loading', 'error');
    } catch (error) {
        console.error('Error al actualizar stock bajo:', error);
        lowStockEl.textContent = 'Error';
        lowStockEl.classList.add('error');
    }
}

function updateTransactionsTable(allCompras) {
    const tbody = document.getElementById('latest-transactions-body');
    try {
        const comprasRecientes = allCompras
            .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
            .slice(0, 10);

        tbody.innerHTML = '';
        if (comprasRecientes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No hay transacciones recientes.</td></tr>';
            return;
        }

        comprasRecientes.forEach(compra => {
            const row = document.createElement('tr');
            const productosStr = Array.isArray(compra.items)
                ? compra.items.map(item => item.nombre_alimento).join(', ')
                : 'N/A';

            row.innerHTML = `
                <td>#${compra.id}</td>
                <td>Usuario ${compra.usuario_id}</td>
                <td>${formatCurrency(compra.total)}</td>
                <td>${formatDate(compra.fecha)}</td>
                <td>${productosStr}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error al actualizar tabla de transacciones:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="error">Error al cargar transacciones</td></tr>';
    }
}

function updateWeeklySalesChart(allCompras) {
    try {
        const weekDates = getWeekDates();
        const salesByDay = weekDates.map(day => {
            const dayCompras = allCompras.filter(compra => isDateInWeek(compra.fecha, day.date));
            return dayCompras.reduce((total, compra) => total + compra.total, 0);
        });

        weeklySalesChart.data.datasets[0].data = salesByDay;
        weeklySalesChart.update();
    } catch (error) {
        console.error('Error al actualizar gráfico semanal:', error);
    }
}

function updateCategorySalesChart(allCompras, allAlimentos) {
    try {
        const alimentoCategoryMap = new Map(allAlimentos.map(a => [a.id, a.categoria]));
        const salesByCategory = {};

        allCompras.forEach(compra => {
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

        categorySalesChart.data.labels = labels;
        categorySalesChart.data.datasets[0].data = data;
        if (labels.length > categorySalesChart.data.datasets[0].backgroundColor.length) {
            categorySalesChart.data.datasets[0].backgroundColor = labels.map(() => `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 0.8)`);
        }
        categorySalesChart.update();

    } catch (error) {
        console.error('Error al actualizar gráfico de categorías:', error);
    }
}

// --- Función Principal (Ahora mucho más simple) ---
async function loadDashboardData() {
    document.querySelectorAll('.loading').forEach(el => el.textContent = 'Cargando...');

    const data = await fetchAllData();
    if (!data) return; // Detener si hubo un error fatal

    const { allCompras, allAlimentos } = data;

    // Actualizar todos los componentes del dashboard con los datos obtenidos
    updateDashboardStats(allCompras);
    updateLowStockItems(allAlimentos);
    updateTransactionsTable(allCompras);
    updateWeeklySalesChart(allCompras);
    updateCategorySalesChart(allCompras, allAlimentos);
}
document.addEventListener('DOMContentLoaded', function () {
    // --- Validación de sesión y rol ---
    const usuarioData = JSON.parse(localStorage.getItem('usuario'));
    const token = localStorage.getItem('jwtToken');

    if (!usuarioData || !token) {
        window.location.href = "../../login.html";
        return;
    }

    const rol = (usuarioData.rol || "").toLowerCase();

    switch (rol) {
        case "admin":
        case "administrador":
            // Permitir acceso
            break;
        case "padre":
            window.location.href = "../../padres.html";
            return;
        case "usuario":
            window.location.href = "../../padres.html";
            return;
        case "vendedor":
            window.location.href = "../../pages/Vendedor/pos.html";
            return;
        default:
            localStorage.removeItem("jwtToken");
            localStorage.removeItem("usuario");
            window.location.href = "../../login.html";
            return;
    }

    // --- Lógica del Menú Lateral ---
    document.getElementById('sidebar-toggle').addEventListener('click', () => {
        document.querySelector('.wrapper').classList.toggle('collapse');
    });

    // --- Botón de actualizar ---
    document.getElementById('refresh-btn').addEventListener('click', (e) => {
        e.preventDefault();
        loadDashboardData();
    });

    // --- Configuración Gráficos (se inicializan vacíos) ---
    const weeklySalesCtx = document.getElementById('weeklySalesChart').getContext('2d');
    weeklySalesChart = new Chart(weeklySalesCtx, {
        type: 'bar',
        data: {
            labels: getWeekDates().map(d => d.name),
            datasets: [{
                label: 'Ventas ($)',
                data: [],
                backgroundColor: 'rgba(52, 152, 219, 0.7)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => `$${(value / 1000).toLocaleString()}k`
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
                    'rgba(41, 128, 185, 0.8)',
                    'rgba(230, 126, 34, 0.8)',
                    'rgba(142, 68, 173, 0.8)',
                    'rgba(39, 174, 96, 0.8)'
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
                    position: 'bottom'
                }
            }
        }
    });

    // --- Carga Inicial y Auto-actualización ---
    loadDashboardData();
    setInterval(loadDashboardData, 5 * 60 * 1000); // 5 minutos
});
