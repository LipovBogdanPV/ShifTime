let currentOrderItems = [];
let breadcrumbStack = []; // Масив об'єктів: {id: 1, name: "Сковорідка"}
// Функція для додавання товару до замовлення - пов'язана з управлінням замовленнями, можливо залишити
function addToOrder(id, name, price, wholesale) {
// Додаємо товар у масив
    currentOrderItems.push({ id, name, price, wholesale, quantity: 1 });
    
    // Якщо це гравіювання — показуємо форму опису
    if (name.toLowerCase().includes('гравіювання') || name.toLowerCase().includes('друк')) {
        document.getElementById('engraving-section').style.display = 'block';
    }
    
    updateOrderList();
}

// Функція для оновлення списку товарів у замовленні - пов'язана з управлінням замовленнями, можливо залишити
function updateOrderList() {
    const list = document.getElementById('order-items-list');
    list.innerHTML = '';
    let total = 0;

    currentOrderItems.forEach((item, index) => {
        total += item.price * item.quantity;
        list.innerHTML += `
            <div class="d-flex justify-content-between align-items-center mb-2 border-bottom pb-1">
                <span>${item.name} x ${item.quantity}</span>
                <span>${item.price * item.quantity} грн 
                    <button class="btn btn-sm text-danger" onclick="removeItem(${index})">&times;</button>
                </span>
            </div>`;
    });

    document.getElementById('total-price').innerText = total;
    calculateRemaining(total);
}

// Функція для розрахунку залишку після передоплати - пов'язана з управлінням замовленнями, можливо залишити
function calculateRemaining(total) {
    const prepay = parseFloat(document.getElementById('prepayment-input').value) || 0;
    const remaining = total - prepay;
    document.getElementById('remaining-price').innerText = remaining > 0 ? remaining : 0;
}

// Функція для видалення товару з замовлення - пов'язана з управлінням замовленнями, можливо залишити
function removeItem(index) {
    currentOrderItems.splice(index, 1);
    updateOrderList();
}

// Функція для збереження повного замовлення - пов'язана з управлінням замовленнями, можливо залишити
function saveFullOrder() {
    const orderData = {
        client: {
            first_name: document.querySelector('[name="first_name"]').value,
            last_name: document.querySelector('[name="last_name"]').value,
            phone: document.querySelector('[name="phone"]').value,
            // ... інші поля клієнта
        },
        order: {
            platform: document.querySelector('[name="platform"]').value,
            delivery_service: document.getElementById('deliverySelect').value,
            prepayment_amount: document.getElementById('prepayment-input').value,
            total_price: document.getElementById('total-price').innerText,
            engraving: document.querySelector('[name="engraving_text"]')?.value || '',
        },
        items: currentOrderItems
    };

    fetch('/ajax/create-order/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}' },
        body: JSON.stringify(orderData)
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            alert('Замовлення створено!');
            window.location.reload();
        }
    });
}

// Функція для малювання крихт
// Функція для відображення хлібних крихт у каталозі - пов'язана з навігацією в замовленнях, можливо залишити
function renderBreadcrumbs() {
    const container = document.getElementById('breadcrumb-container');
    container.innerHTML = ''; // Очищаємо повністю

    breadcrumbStack.forEach((item) => {
        const btn = document.createElement('button');
        btn.className = "btn btn-sm btn-outline-secondary m-1";
        btn.innerText = item.name;
        
        // Клік просто викликає loadCatalog, а він сам розбереться зі стеком
        btn.onclick = () => loadCatalog(item.id);
        
        container.appendChild(btn);
    });
}

// Функція для розрахунку загальної суми - пов'язана з управлінням замовленнями, можливо залишити
function calculateTotal() {
    // 1. Отримуємо загальну суму (текст з span)
    const totalElement = document.getElementById('total-price');
    const total = parseFloat(totalElement.innerText) || 0;

    // 2. Отримуємо значення передоплати
    const prepayInput = document.getElementById('prepayment-input');
    const prepay = parseFloat(prepayInput.value) || 0;

    // 3. Рахуємо залишок (якщо передоплата > суми, то залишок 0)
    const remaining = total - prepay;
    const finalRemaining = remaining > 0 ? remaining : 0;

    // 4. Оновлюємо span із залишком
    const remainingElement = document.getElementById('remaining-price');
    remainingElement.innerText = finalRemaining.toFixed(2);
}


function initDeliveryForm() {
    const select = document.getElementById('deliverySelect');
    if (select) {
        toggleDeliveryFields(select); // Викликаємо нашу логіку
    }
}
