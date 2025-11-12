// Lógica del Menú Lateral
const sidebarToggle = document.getElementById('sidebar-toggle');
if(sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        document.querySelector('.wrapper').classList.toggle('collapse');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const apiURL = "https://web-production-b7e6.up.railway.app";
    let todasLasComprasEstudiante = []; // Almacenamos las compras del estudiante actual
    let todosLosAlimentos = []; // Almacenamos todos los alimentos para el mapa de categorías
    let miGraficoDeCategorias = null;

    // --- AUTENTICACIÓN Y HELPERS---
    function obtenerTokenDeLocalStorage() { return localStorage.getItem("jwtToken"); }
    async function hacerPeticionAutenticada(url, options = {}) {
        const token = obtenerTokenDeLocalStorage();
        if (!token) { window.location.href = "../login.html"; throw new Error("No autenticado"); }
        const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...options.headers };
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401 || response.status === 403) { window.location.href = "../login.html"; throw new Error("Sesión expirada"); }
        return response;
    }
    function formatearSaldo(saldo) { return (parseFloat(saldo) || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0, maximumFractionDigits: 0 }); }
    
    // --- ELEMENTOS DEL DOM ---
    const selectorEstudiante = document.getElementById("estudiante-selector");
    const saldoElemento = document.getElementById("saldo-usuario");
    const dateFilterButtons = document.querySelectorAll('.date-button');

    // --- LÓGICA DE PROCESAMIENTO DE DATOS ---

    // --- ADAPTADO DEL DASHBOARD: Lógica de procesamiento mejorada ---
    function procesarDatosDeCompra(compras, alimentos, diasAtras) {
        const ahora = new Date();
        const fechaLimite = new Date();
        fechaLimite.setDate(ahora.getDate() - diasAtras);

        const comprasFiltradas = compras.filter(c => new Date(c.fecha) >= fechaLimite);

        if (comprasFiltradas.length === 0) {
            return { avgCalories: 0, topFood: 'N/A', topCategory: 'N/A', totalSpent: 0, top5Foods: [], categoryChartData: { labels: [], data: [] } };
        }

        // 1. Crear el mapa de categorías para búsqueda rápida
        const mapaCategorias = new Map(alimentos.map(a => [a.id, a.categoria || 'Sin Categoría']));
        
        const contadorAlimentos = {};
        const gastosPorCategoria = {};
        const caloriasPorDia = {};
        let gastoTotal = 0;

        comprasFiltradas.forEach(compra => {
            gastoTotal += parseFloat(compra.total) || 0;
            const fechaCompra = new Date(compra.fecha).toISOString().split('T')[0];
            caloriasPorDia[fechaCompra] = caloriasPorDia[fechaCompra] || 0;

            if (!Array.isArray(compra.items)) return;

            compra.items.forEach(item => {
                // Sumar calorías
                caloriasPorDia[fechaCompra] += parseFloat(item.calorias) || 0;
                
                // Contar alimentos para el Top 5
                const nombreAlimento = item.nombre_alimento || 'Desconocido';
                contadorAlimentos[nombreAlimento] = (contadorAlimentos[nombreAlimento] || 0) + 1;

                // 2. Usar el mapa para agregar gastos por categoría
                const categoria = mapaCategorias.get(item.producto_id) || item.categoria || 'Varios';
                const valorItem = (parseFloat(item.precio_unitario) || 0) * (parseInt(item.cantidad) || 1);
                gastosPorCategoria[categoria] = (gastosPorCategoria[categoria] || 0) + valorItem;
            });
        });
        
        // Calcular KPIs
        const numDias = Object.keys(caloriasPorDia).length;
        const totalCalorias = Object.values(caloriasPorDia).reduce((a, b) => a + b, 0);
        const avgCalories = numDias > 0 ? Math.round(totalCalorias / numDias) : 0;
        
        const top5Foods = Object.entries(contadorAlimentos).sort(([,a],[,b]) => b-a).slice(0, 5);
        const topFood = top5Foods.length > 0 ? top5Foods[0][0] : 'N/A';
        
        const topCategoryEntry = Object.entries(gastosPorCategoria).sort(([,a],[,b]) => b-a)[0];
        const topCategory = topCategoryEntry ? topCategoryEntry[0] : 'N/A';

        return {
            avgCalories,
            topFood,
            topCategory,
            totalSpent: gastoTotal,
            top5Foods,
            categoryChartData: {
                labels: Object.keys(gastosPorCategoria),
                data: Object.values(gastosPorCategoria)
            }
        };
    }

    // --- FUNCIONES DE RENDERIZADO ---
    function renderizarAnalisis(datos) {
        document.getElementById('avg-calories').textContent = `${datos.avgCalories} kcal`;
        document.getElementById('top-food').textContent = datos.topFood;
        document.getElementById('top-category').textContent = datos.topCategory;
        document.getElementById('total-spent').textContent = formatearSaldo(datos.totalSpent);
        
        const top5List = document.getElementById('top-5-list');
        top5List.innerHTML = "";
        if (datos.top5Foods.length > 0) {
            datos.top5Foods.forEach(([nombre, count]) => {
                top5List.innerHTML += `<li><span class="item-name">${nombre}</span> <span class="item-count">${count} ${count > 1 ? 'veces' : 'vez'}</span></li>`;
            });
        } else {
            top5List.innerHTML = '<li>No hay datos en este período.</li>';
        }
        
        renderizarGrafico(datos.categoryChartData);
    }

    function renderizarGrafico({ labels, data }) {
        const ctx = document.getElementById('category-chart').getContext('2d');
        if (miGraficoDeCategorias) {
            miGraficoDeCategorias.destroy();
        }
        
        if (labels.length === 0) {
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            ctx.textAlign = 'center';
            ctx.font = '14px sans-serif';
            ctx.fillStyle = '#6c757d';
            ctx.fillText('No hay gastos por categoría para mostrar.', ctx.canvas.width / 2, ctx.canvas.height / 2);
            return;
        }

        miGraficoDeCategorias = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Gasto por Categoría',
                    data: data,
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#E7E9ED', '#808080'],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'right' } }
            }
        });
    }

    // --- LÓGICA PRINCIPAL Y CARGA DE DATOS ---
    
    // --- NUEVO: Carga los datos iniciales (todos los alimentos) una sola vez ---
    async function cargarDatosGlobales() {
        try {
            const response = await hacerPeticionAutenticada(`${apiURL}/api/alimentos/`);
            if (!response.ok) throw new Error('No se pudo cargar la lista de alimentos');
            todosLosAlimentos = await response.json();
        } catch (error) {
            console.error(error);
            // Manejar error, quizás mostrar un mensaje al usuario
        }
    }

    async function cargarDatosEstudiante(estudianteId) {
        try {
            const response = await hacerPeticionAutenticada(`${apiURL}/compras/usuario/${estudianteId}`);
            if (!response.ok) {
                todasLasComprasEstudiante = [];
            } else {
                todasLasComprasEstudiante = await response.json();
            }
            // Activar el filtro de fecha por defecto (7 días)
            document.querySelector('.date-button[data-days="7"]').click();
        } catch (error) {
            console.error("Error al cargar compras:", error);
            todasLasComprasEstudiante = [];
            document.querySelector('.date-button[data-days="7"]').click();
        }
    }
    
    async function cargarHijosYActualizarPanel() {
        const usuario = JSON.parse(localStorage.getItem("usuario"));
        if (!usuario) return;
        
        try {
            const response = await hacerPeticionAutenticada(`${apiURL}/estudiantes/${encodeURIComponent(usuario.nombre)}/hijos`);
            const hijos = await response.json();
            selectorEstudiante.innerHTML = "";
            
            if (hijos && hijos.length > 0) {
                hijos.forEach(hijo => {
                    selectorEstudiante.innerHTML += `<option value="${hijo.id}" data-saldo="${hijo.saldo || 0}">${hijo.nombre}</option>`;
                });
                
                // AQUÍ ESTÁ LA PARTE CLAVE: Recuperar el estudiante seleccionado de sessionStorage
                const savedStudent = sessionStorage.getItem("selectedStudent");
                if (savedStudent && Array.from(selectorEstudiante.options).some(opt => opt.value === savedStudent)) {
                    selectorEstudiante.value = savedStudent;
                } else if (selectorEstudiante.options.length > 0) {
                    selectorEstudiante.selectedIndex = 0;
                }
                
                actualizarPanelConEstudianteSeleccionado();
            } else {
                selectorEstudiante.innerHTML = "<option value=''>No hay hijos</option>";
            }
        } catch (error) {
            console.error("Error al cargar hijos:", error);
        }
    }
    
    function actualizarPanelConEstudianteSeleccionado() {
        const opt = selectorEstudiante.options[selectorEstudiante.selectedIndex];
        if (opt && opt.value) {
            saldoElemento.textContent = formatearSaldo(opt.getAttribute("data-saldo"));
            cargarDatosEstudiante(opt.value);
        }
    }

    // --- EVENT LISTENERS E INICIALIZACIÓN ---
    
    // AGREGAR: Event listener para guardar la selección en sessionStorage cuando cambie
    selectorEstudiante.addEventListener("change", function() {
        actualizarPanelConEstudianteSeleccionado();
        // Guardar la selección en sessionStorage
        sessionStorage.setItem("selectedStudent", selectorEstudiante.value);
    });
    
    dateFilterButtons.forEach(button => {
        button.addEventListener('click', () => {
            dateFilterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const dias = parseInt(button.dataset.days, 10);
            // Ahora pasamos la lista completa de alimentos a la función de procesamiento
            const datosProcesados = procesarDatosDeCompra(todasLasComprasEstudiante, todosLosAlimentos, dias);
            renderizarAnalisis(datosProcesados);
        });
    });

    async function init() {
        await cargarDatosGlobales(); // Cargar primero los datos que no cambian
        await cargarHijosYActualizarPanel(); // Luego cargar los hijos y el panel inicial
    }

    init();
});