
        document.addEventListener('DOMContentLoaded', function() {
            // --- Lógica del Menú Lateral ---
            const sidebarToggle = document.getElementById('sidebar-toggle');
            const wrapper = document.querySelector('.wrapper');
            sidebarToggle.addEventListener('click', () => {
                wrapper.classList.toggle('collapse');
            });

            // --- Lógica para el Acordeón de FAQ ---
            const faqItems = document.querySelectorAll('.faq-item');
            faqItems.forEach(item => {
                const question = item.querySelector('.faq-question');
                question.addEventListener('click', () => {
                    // Cierra otros items abiertos para que solo uno esté abierto a la vez
                    faqItems.forEach(otherItem => {
                        if (otherItem !== item && otherItem.classList.contains('active')) {
                            otherItem.classList.remove('active');
                        }
                    });
                    // Abre o cierra el item actual
                    item.classList.toggle('active');
                });
            });

            // --- Lógica para el Formulario de Contacto ---
            const contactForm = document.getElementById('contact-support-form');
            contactForm.addEventListener('submit', function(event) {
                event.preventDefault(); // Previene el envío real del formulario
                
                // Simula el envío y muestra una notificación
                showNotification('Mensaje enviado correctamente. Nos pondremos en contacto pronto.', 'success');
                
                // Limpia el formulario
                contactForm.reset();
            });

            // --- Función para mostrar Notificaciones ---
            function showNotification(message, type) {
                const container = document.getElementById('notification-container');
                const notification = document.createElement('div');
                notification.className = `notification ${type}`; // 'success' o 'error'
                notification.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-times-circle'}"></i> ${message}`;
                
                container.appendChild(notification);

                // CSS para la notificación (se inyecta aquí para no crear más archivos)
                const style = document.createElement('style');
                style.innerHTML = `
                    #notification-container {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        z-index: 1000;
                    }
                    .notification {
                        padding: 15px 20px;
                        margin-bottom: 10px;
                        border-radius: 5px;
                        color: #fff;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                        opacity: 0;
                        transform: translateX(100%);
                        animation: slideIn 0.5s forwards;
                    }
                    .notification.success { background-color: #27ae60; }
                    .notification.error { background-color: #c0392b; }
                    .notification .fas { margin-right: 10px; }

                    @keyframes slideIn {
                        to {
                            opacity: 1;
                            transform: translateX(0);
                        }
                    }
                    
                    @keyframes slideOut {
                        to {
                            opacity: 0;
                            transform: translateX(120%);
                        }
                    }
                `;
                document.head.appendChild(style);

                // La notificación desaparece después de 4 segundos
                setTimeout(() => {
                    notification.style.animation = 'slideOut 0.5s forwards';
                    setTimeout(() => notification.remove(), 500);
                }, 4000);
            }
        });