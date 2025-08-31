
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('transactionModal');
    const addIncomeBtn = document.querySelector('.btn-primary');
    const addExpenseBtn = document.querySelector('.btn-secondary');
    const closeBtn = document.querySelector('.close-btn');
    const modalTitle = document.getElementById('modalTitle');
    const transactionForm = document.getElementById('transactionForm');
    const transactionType = document.getElementById('transactionType');

    // Función para obtener el token CSRF de las cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Mostrar modal al hacer clic en los botones
    if (addIncomeBtn) {
        addIncomeBtn.onclick = function(e) {
            e.preventDefault();
            modalTitle.textContent = 'Agregar Ingreso';
            transactionType.value = 'ingreso';
            modal.style.display = 'block';
        };
    }

    if (addExpenseBtn) {
        addExpenseBtn.onclick = function(e) {
            e.preventDefault();
            modalTitle.textContent = 'Agregar Gasto';
            transactionType.value = 'gasto';
            modal.style.display = 'block';
        };
    }

    // Ocultar modal al hacer clic en el botón de cerrar
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        };
    }

    // Ocultar modal al hacer clic fuera de él
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    // Manejar el envío del formulario con AJAX
    if (transactionForm) {
        transactionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(transactionForm);
            // Convierte FormData a un objeto plano. Esto es lo que necesitas.
            const data = Object.fromEntries(formData.entries());

            // Incluir el token CSRF en la solicitud
            const csrfToken = getCookie('csrftoken');

            fetch('/add_transaction/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken // <-- Envía el token en el header, no en el cuerpo
                },
                body: JSON.stringify(data) // <-- Convierte el objeto a una cadena JSON
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert(result.message || 'Transacción agregada con éxito!');
                    modal.style.display = 'none';
                    // Recargar la página para ver los cambios
                    location.reload(); 
                } else {
                    alert('Error: ' + result.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ocurrió un error al agregar la transacción.');
            });
        });
    }
});