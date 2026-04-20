// Dashboard utilities JavaScript
// Functions not directly related to orders management

const DASHBOARD_LAST_CONTENT_KEY = 'saleshub_last_content_url';

function saveLastContentUrl(url) {
    if (!url || typeof url !== 'string') return;
    if (!url.startsWith('/ajax/')) return;
    localStorage.setItem(DASHBOARD_LAST_CONTENT_KEY, url);
}

function getLastContentUrl() {
    const url = localStorage.getItem(DASHBOARD_LAST_CONTENT_KEY);
    if (!url || !url.startsWith('/ajax/')) {
        return '/ajax/contentdashboard/';
    }
    return url;
}

function loadContent(element) {
    let url;
    let clickedElement = null;

    // Перевіряємо: якщо це рядок (текст), то це вже URL.
    // Якщо це об'єкт, то ми шукаємо в ньому атрибут data-url.
    if (typeof element === 'string') {
        url = element;
        clickedElement = document.querySelector(`.sidebar a[data-url="${url}"]`);
    } else {
        clickedElement = element; // Зберігаємо посилання на кнопку
        url = element.getAttribute('data-url');
    }

    if (!url) {
        return;
    }

    // 2. Оновлюємо візуальний стан (Активна кнопка)
    if (clickedElement) {
        // Прибираємо 'active' у всіх кнопок меню
        document.querySelectorAll('.sidebar a').forEach(btn => btn.classList.remove('active'));
        // Додаємо 'active' тільки тій, що натиснули
        clickedElement.classList.add('active');
    }

    saveLastContentUrl(url);

    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = '<p>Завантаження...</p>';

    fetch(url)
        .then(response => response.text())
        .then(html => {
            contentArea.innerHTML = html;
            initDeliveryForm();
            initOrderDraftPersistence();
        })
        .catch(error => {
            contentArea.innerHTML = '<p style="color:red">Помилка завантаження даних.</p>';
        });
}

function editUser(userId) {
    const url = userId ? `/ajax/user-form/${userId}/` : '/ajax/user-form/';
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const modalBody = document.getElementById('modal-body');
            if (modalBody) modalBody.innerHTML = data.html;
            const modal = document.getElementById('modalOverlay');
            if (modal) modal.style.display = 'flex';
            // Тут більше не потрібно навішувати onsubmit
        });
}

function saveUser(userId) {
    const form = document.getElementById('crmUserRegForm');
    
    // 1. ПЕРЕВІРКА: чи ми взагалі знайшли форму?
    if (!form) {
        alert("Помилка: Форму не знайдено в DOM!");
        return;
    }

    const formData = new FormData(form);

    // 2. ДЕБАГ: виводимо в консоль все, що збирається
    console.log("Дані форми, що відправляються:");
    for (let [key, value] of formData.entries()) {
        console.log(key, ":", value);
    }

    const url = userId ? `/ajax/user-save/${userId}/` : '/ajax/user-save/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal();
            loadContent('/ajax/admins/');
        } else {
            console.error("Помилки з сервера:", data.errors);
            // Виводимо помилки, щоб розуміти, що не так
            alert(JSON.stringify(data.errors));
        }
    });
}

function closeModal() {
    console.log("Спроба закрити модальне вікно...");
    const modal = document.getElementById('modalOverlay');
    const modalBox = document.querySelector('#modalOverlay .modal-box');
    
    // ДЕБАГ: дивимось, що реально знайдено
    console.log("Знайдено елемент:", modal);

    if (modal) {
        modal.style.display = 'none';
        if (modalBox) {
            modalBox.style.width = '';
        }
        const modalBody = document.getElementById('modal-body');
        if (modalBody) modalBody.innerHTML = '';
    } else {
        console.error("ПОМИЛКА: Елемент 'modalOverlay' не знайдено в DOM!");
    }
}

function deleteUser(userId, userName) {
    // Вікно підтвердження
    if (confirm(`Ви впевнені, що хочете видалити користувача ${userName}?`)) {
        
        fetch(`/ajax/user-delete/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                // Оновлюємо список користувачів
                loadContent('/ajax/admins/');
            } else {
                alert('Помилка: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Сталася помилка при видаленні.');
        });
    }
}

function editRole(roleId) {
    const url = roleId ? `/ajax/role-form/${roleId}/` : '/ajax/role-form/';
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const modalBody = document.getElementById('modal-body');
            if (modalBody) modalBody.innerHTML = data.html;
            const modal = document.getElementById('modalOverlay');
            if (modal) modal.style.display = 'flex';
            
            const roleForm = document.getElementById('crmRoleForm');
            if (roleForm) roleForm.onsubmit = function(e) {
                e.preventDefault();
                saveRole(roleId);
            };
        });
}

function saveRole(roleId) {
    const form = document.getElementById('crmRoleForm');
    const formData = new FormData(form);
    const url = roleId ? `/ajax/role-save/${roleId}/` : '/ajax/role-save/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal();
            loadContent('/ajax/admins/');
        } else {
            alert('Помилка при збереженні ролі');
        }
    });
}

function deleteRole(roleId, roleName) {
    if (confirm(`Ви впевнені, що хочете видалити роль "${roleName}"? Всі користувачі цієї ролі втратять свої права.`)) {
        
        fetch(`/ajax/role-delete/${roleId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                loadContent('/ajax/admins/'); // Перезавантажуємо сторінку адмінки
            } else {
                alert('Помилка: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Сталася помилка при видаленні ролі.');
        });
    }
}

let currentOrderItems = [];
let breadcrumbStack = []; // Масив об'єктів: {id: 1, name: "Сковорідка"}
const ORDER_DRAFT_STORAGE_KEY = 'saleshub_order_draft_v1';
const NOVA_POSHTA_API_KEY = 'a0102a00f2f88e7c84d935843d290edd';
const NOVA_POSHTA_API_URL = 'https://api.novaposhta.ua/v2.0/json/';
const CITY_SUGGESTION_DELAY = 250;
let citySuggestionsTimer = null;
let novaPoshtaOutsideClickBound = false;
let draftHandlersBound = false;
let isRestoringOrderDraft = false;
const deliveryState = {
    city: '',
    cityRef: '',
    region: '',
    district: ''
};

function showTab(tabName, element) {
    const scoreTab = document.getElementById('tab-score');
    const contactsTab = document.getElementById('tab-contacts');
    const container = document.getElementById('content-container');

    // 1. Скидаємо активний клас для всіх кнопок (залишаємо твою логіку)
    document.querySelectorAll('.nav-link').forEach(btn => {
        btn.classList.remove('active');
    });
    if (element) {
        element.classList.add('active');
    }

    // 2. ОСОБЛИВИЙ РЕЖИМ: Обидві вкладки разом
    if (tabName === 'both') {
        container.style.display = 'flex'; // Робимо контейнер гнучким (пліч-о-пліч)
        container.style.gap = '20px';

        [scoreTab, contactsTab].forEach(tab => {
            if (tab) {
                tab.style.display = 'block';
                tab.style.flex = '1'; // Кожна вкладка займає 50% ширини
            }
        });
        return; // Виходимо з функції, далі стандартна логіка не потрібна
    }
    const targetId = 'tab-' + tabName;
    const targetTab = document.getElementById(targetId);

    // 1. ПЕРЕВІРКА: чи існує взагалі цей елемент?
    if (!targetTab) {
        console.error("Помилка: елемент з ID '" + targetId + "' не знайдено!");
        return; // Зупиняємо функцію, якщо ID неправильний
    }

    // 2. Скидаємо всі таби
    document.querySelectorAll('.custom-tab-content').forEach(tab => {
        tab.style.display = 'none';
    });

    // 3. Увімкнення потрібного
    targetTab.style.display = 'block';

    // 4. Активний клас для кнопок
    document.querySelectorAll('.nav-link').forEach(btn => {
        btn.classList.remove('active');
    });
    if (element) {
        element.classList.add('active');
    }
    initDeliveryForm();
}

// Відкрити модалку та завантажити форму
function openModal(url) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            const modalBody = document.getElementById('modal-body');
            if (!modalBody) {
                console.error("Помилка: елемент 'modal-body' не знайдено в DOM");
                return;
            }
            modalBody.innerHTML = html;
            const modal = document.getElementById('modalOverlay');
            if (modal) modal.style.display = 'flex';
        })
        .catch(error => {
            console.error('Error loading modal:', error);
        });
}

// Збереження категорії
function saveCategory(categoryId) {
    const form = document.getElementById('categoryForm');
    const formData = new FormData(form);
    const url = categoryId ? `/ajax/category-save/${categoryId}/` : '/ajax/category-save/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal();
            loadContent('/ajax/manage_products/'); // Перезавантажуємо вкладку каталогу
        } else {
            alert('Помилка при збереженні категорії');
            console.log(data.errors);
        }
    });
}

// Збереження товару
function saveProduct(productId) {
    const form = document.getElementById('productForm');
    const formData = new FormData(form);
    const url = productId ? `/ajax/product-save/${productId}/` : '/ajax/product-save/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal();
            loadContent('/ajax/manage_products/'); // Перезавантажуємо вкладку товарів
        } else {
            alert('Помилка при збереженні товару');
            console.log(data.errors);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const lastContentUrl = getLastContentUrl();
    loadContent(lastContentUrl);
});

function deleteItem(url) {
    if (confirm('Ви впевнені, що хочете видалити цей елемент?')) {
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value, // Важливо для безпеки Django
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                // Оновлюємо поточну вкладку (наприклад, перезавантажуємо контент)
                // Можна просто перезавантажити сторінку або викликати функцію оновлення:
                location.reload(); 
            } else {
                alert('Помилка при видаленні');
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

// Показує/ховає Email
function toggleEmail() {
    const checkBox = document.getElementById("foreignDelivery");
    const emailGroup = document.getElementById("email-group");
    emailGroup.style.display = checkBox.checked ? "block" : "none";
}

// Використовуємо делегування: слухаємо кліки/зміни на всій сторінці
document.addEventListener('change', function(event) {
    // Перевіряємо, чи зміна відбулася саме в нашому селекті
    if (event.target && event.target.id === 'deliverySelect') {
        toggleDeliveryFields(event.target);
    }
});

// Показує поля адреси залежно від доставки
function toggleDeliveryFields(selectElement) {
    // 1. Безпечна перевірка: якщо елемента немає, нічого не робимо
    if (!selectElement) {
        console.warn("Елемент доставки не знайдено");
        return;
    }

    const npFields = document.getElementById('np-fields');
    const manualFields = document.getElementById('manual-address');
    
    // Перевіряємо, чи існують ці блоки перед тим, як міняти стиль
    if (!npFields || !manualFields) return;

    const val = selectElement.value;

    if (val === 'nova_poshta') {
        npFields.style.display = 'block';
        manualFields.style.display = 'none';
    } else if (val === 'ukr_poshta' || val === 'self_pickup') {
        npFields.style.display = 'none';
        manualFields.style.display = 'block';
        clearCitySuggestions();
    } else {
        npFields.style.display = 'none';
        manualFields.style.display = 'none';
        clearCitySuggestions();
    }
}

// Функція завантаження каталогу з оновленням кнопок у хедері
function loadCatalog(categoryId, categoryName, addToStack = true) {
    fetch(`/ajax/get-catalog/${categoryId}/`)
        .then(res => res.json())
        .then(data => {
            // 2. Розумна обробка стеку
            const existingIndex = breadcrumbStack.findIndex(item => item.id === categoryId);

            if (existingIndex !== -1) {
                // Якщо категорія ВЖЕ є в списку, обрізаємо стек до неї
                breadcrumbStack = breadcrumbStack.slice(0, existingIndex + 1);
            } else {
                // Якщо категорії немає - додаємо в кінець
                breadcrumbStack.push({ id: categoryId, name: data.category_name });
            }

            // 3. Перемальовуємо все
            renderBreadcrumbs();
            renderCatalogContent(data); // Винесемо рендер товарів в окрему функцію для чистоти
        });
}

function renderCatalogContent(data) {
    const container = document.getElementById('catalog-container');
    container.innerHTML = ''; 

    // Малюємо підкатегорії
    data.categories.forEach(cat => {
        container.innerHTML += `<button class="btn btn-primary m-1" onclick="loadCatalog(${cat.id})">${cat.name}</button>`;
    });

    // Малюємо товари
    data.products.forEach(prod => {
        container.innerHTML += `
            <div class="card m-1 p-2 border" style="width: 150px;">
                <small>${prod.name}</small>
                <p><strong>${prod.selling_price} грн</strong></p>
                <button class="btn btn-sm btn-success" 
                        onclick="addToOrder(${prod.id}, '${prod.name}', ${prod.selling_price}, ${prod.drop_price})">
                    Додати
                </button>
            </div>`;
    });
}

// --- Новий блок: керування замовленням і кошиком ---
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function addToOrder(productId, productName, sellingPrice, dropPrice = 0) {
    const existing = currentOrderItems.find(item => item.id === productId);
    if (existing) {
        existing.quantity += 1;
    } else {
        currentOrderItems.push({
            id: productId,
            name: productName,
            sellingPrice: Number(sellingPrice),
            dropPrice: Number(dropPrice),
            quantity: 1
        });
    }
    renderOrderItems();
    calculateTotal();
    saveOrderDraft();
}

function changeOrderQuantity(productId, delta) {
    const item = currentOrderItems.find(item => item.id === productId);
    if (!item) return;
    item.quantity = Math.max(1, item.quantity + delta);
    renderOrderItems();
    calculateTotal();
    saveOrderDraft();
}

function removeOrderItem(productId) {
    currentOrderItems = currentOrderItems.filter(item => item.id !== productId);
    renderOrderItems();
    calculateTotal();
    saveOrderDraft();
}

function renderOrderItems() {
    const container = document.getElementById('order-items-list');
    if (!container) return;

    if (currentOrderItems.length === 0) {
        container.innerHTML = '<div class="text-muted">Тут буде список товарів замовлення.</div>';
        return;
    }

    container.innerHTML = currentOrderItems.map(item => `
        <div class="order-item d-flex justify-content-between align-items-center mb-2 p-2 bg-white border rounded">
            <div>
                <strong>${item.name}</strong>
                <div><small>Ціна: ${item.sellingPrice.toFixed(2)} грн × ${item.quantity}</small></div>
            </div>
            <div class="d-flex gap-2 align-items-center">
                <button class="btn btn-sm btn-light" type="button" onclick="changeOrderQuantity(${item.id}, -1)">-</button>
                <span>${item.quantity}</span>
                <button class="btn btn-sm btn-light" type="button" onclick="changeOrderQuantity(${item.id}, 1)">+</button>
                <button class="btn btn-sm btn-danger" type="button" onclick="removeOrderItem(${item.id})">✕</button>
            </div>
        </div>`).join('');
}

function calculateTotal() {
    const total = currentOrderItems.reduce((sum, item) => sum + item.sellingPrice * item.quantity, 0);
    const prepaymentInput = document.getElementById('prepayment-input');
    const prepayment = prepaymentInput ? Number(prepaymentInput.value) || 0 : 0;
    const remaining = Math.max(total - prepayment, 0);
    const totalPriceNode = document.getElementById('total-price');
    const remainingPriceNode = document.getElementById('remaining-price');
    if (totalPriceNode) totalPriceNode.textContent = total.toFixed(2);
    if (remainingPriceNode) remainingPriceNode.textContent = remaining.toFixed(2);
    return { total, remaining, prepayment };
}

function collectOrderPayload() {
    const deliveryService = document.querySelector('[name="delivery_service"]')?.value || 'nova_poshta';

    const npCity = document.getElementById('city-input')?.value?.trim() || '';
    const npRegion = document.getElementById('region-input')?.value?.trim() || '';
    const npPostDepartment = document.getElementById('warehouse-select')?.value?.trim() || '';

    const manualCity = document.getElementById('manual-city-input')?.value?.trim() || '';
    const manualRegion = document.getElementById('manual-region-input')?.value?.trim() || '';
    const manualPostDepartment = document.getElementById('manual-post-department-input')?.value?.trim() || '';

    const city = deliveryService === 'nova_poshta' ? npCity : manualCity;
    const region = deliveryService === 'nova_poshta' ? npRegion : manualRegion;
    const postDepartment = deliveryService === 'nova_poshta' ? npPostDepartment : manualPostDepartment;

    const client = {
        last_name: document.querySelector('[name="last_name"]')?.value || '',
        first_name: document.querySelector('[name="first_name"]')?.value || '',
        middle_name: document.querySelector('[name="middle_name"]')?.value || '',
        phone: document.querySelector('[name="phone"]')?.value || '',
        email: document.querySelector('[name="email"]')?.value || '',
        region: region,
        city: city,
        post_department: postDepartment
    };

    const order = {
        platform: document.querySelector('[name="platform"]')?.value || 'instagram',
        delivery_service: deliveryService,
        prepayment_amount: Number(document.querySelector('[name="prepayment_amount"]')?.value || document.getElementById('prepayment-input')?.value || 0),
        total_price: calculateTotal().total,
        engraving_description: document.querySelector('[name="engraving_description"]')?.value || '',
        customer_request: document.querySelector('[name="customer_request"]')?.value || ''
    };

    const items = currentOrderItems.map(item => ({
        id: item.id,
        quantity: item.quantity
    }));

    return { client, order, items };
}

function submitOrder() {
    if (!currentOrderItems.length) {
        alert('Додайте хоча б один товар до замовлення.');
        return;
    }

    const payload = collectOrderPayload();
    if (!payload.client.phone) {
        alert('Вкажіть телефон клієнта.');
        return;
    }
    if (!payload.client.city || !payload.client.region || !payload.client.post_department) {
        alert('Заповніть адресу доставки: місто, область і відділення/адресу.');
        return;
    }

    fetch('/ajax/create-order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`Замовлення створено. ID: ${data.order_id}`);
            clearOrderDraftStorage();
            resetOrderFormUI();
            currentOrderItems = [];
            renderOrderItems();
            calculateTotal();
        } else {
            alert(data.message || 'Помилка при створенні замовлення');
        }
    })
    .catch(error => {
        console.error('Order error:', error);
        alert('Сталася помилка при відправці замовлення.');
    });
}

function getOrderDraftSnapshot() {
    return {
        items: currentOrderItems,
        fields: {
            last_name: document.querySelector('[name="last_name"]')?.value || '',
            first_name: document.querySelector('[name="first_name"]')?.value || '',
            middle_name: document.querySelector('[name="middle_name"]')?.value || '',
            phone: document.querySelector('[name="phone"]')?.value || '',
            email: document.querySelector('[name="email"]')?.value || '',
            platform: document.querySelector('[name="platform"]')?.value || 'instagram',
            delivery_service: document.querySelector('[name="delivery_service"]')?.value || 'nova_poshta',
            prepayment_amount: document.querySelector('[name="prepayment_amount"]')?.value || '0',
            engraving_description: document.querySelector('[name="engraving_description"]')?.value || '',
            customer_request: document.querySelector('[name="customer_request"]')?.value || '',
            city_input: document.getElementById('city-input')?.value || '',
            region_input: document.getElementById('region-input')?.value || '',
            district_input: document.getElementById('district-input')?.value || '',
            warehouse_select: document.getElementById('warehouse-select')?.value || '',
            manual_city: document.getElementById('manual-city-input')?.value || '',
            manual_region: document.getElementById('manual-region-input')?.value || '',
            manual_district: document.getElementById('manual-district-input')?.value || '',
            manual_post_department: document.getElementById('manual-post-department-input')?.value || ''
        }
    };
}

function saveOrderDraft() {
    if (isRestoringOrderDraft) return;
    if (!document.getElementById('order-items-list') || !document.getElementById('deliverySelect')) return;

    try {
        const snapshot = getOrderDraftSnapshot();
        localStorage.setItem(ORDER_DRAFT_STORAGE_KEY, JSON.stringify(snapshot));
    } catch (error) {
        console.error('Не вдалося зберегти чернетку замовлення:', error);
    }
}

function clearOrderDraftStorage() {
    try {
        localStorage.removeItem(ORDER_DRAFT_STORAGE_KEY);
    } catch (error) {
        console.error('Не вдалося очистити чернетку замовлення:', error);
    }
}

function bindOrderDraftHandlers() {
    if (draftHandlersBound) return;

    document.addEventListener('input', event => {
        if (!event.target) return;
        const target = event.target;
        if (target.matches('[name="last_name"], [name="first_name"], [name="middle_name"], [name="phone"], [name="email"], [name="prepayment_amount"], [name="engraving_description"], [name="customer_request"], #city-input, #region-input, #district-input, #manual-city-input, #manual-region-input, #manual-district-input, #manual-post-department-input')) {
            saveOrderDraft();
        }
    });

    document.addEventListener('change', event => {
        if (!event.target) return;
        const target = event.target;
        if (target.matches('[name="platform"], [name="delivery_service"], #warehouse-select')) {
            saveOrderDraft();
        }
    });

    draftHandlersBound = true;
}

function resetOrderFormUI() {
    const fieldsToClear = [
        '[name="last_name"]',
        '[name="first_name"]',
        '[name="middle_name"]',
        '[name="phone"]',
        '[name="email"]',
        '[name="engraving_description"]',
        '[name="customer_request"]',
        '#city-input',
        '#region-input',
        '#district-input',
        '#manual-city-input',
        '#manual-region-input',
        '#manual-district-input',
        '#manual-post-department-input'
    ];

    fieldsToClear.forEach(selector => {
        const el = document.querySelector(selector);
        if (el) {
            el.value = '';
        }
    });

    const platform = document.querySelector('[name="platform"]');
    if (platform) platform.value = 'instagram';

    const delivery = document.querySelector('[name="delivery_service"]');
    if (delivery) {
        delivery.value = 'nova_poshta';
        toggleDeliveryFields(delivery);
    }

    const prepayment = document.querySelector('[name="prepayment_amount"]');
    if (prepayment) prepayment.value = '0';

    const warehouse = document.getElementById('warehouse-select');
    if (warehouse) {
        warehouse.innerHTML = '<option value="">Спочатку оберіть місто...</option>';
    }
}

function clearOrderDraftData() {
    clearOrderDraftStorage();
    currentOrderItems = [];
    resetOrderFormUI();
    renderOrderItems();
    calculateTotal();
    alert('Чернетку замовлення очищено.');
}

async function restoreOrderDraft() {
    if (!document.getElementById('order-items-list') || !document.getElementById('deliverySelect')) return;

    let draft;
    try {
        draft = JSON.parse(localStorage.getItem(ORDER_DRAFT_STORAGE_KEY) || 'null');
    } catch (error) {
        console.error('Не вдалося прочитати чернетку замовлення:', error);
        return;
    }

    if (!draft || typeof draft !== 'object') return;

    isRestoringOrderDraft = true;
    const fields = draft.fields || {};

    const setValue = (selector, value) => {
        const el = document.querySelector(selector);
        if (el && value !== undefined && value !== null) {
            el.value = value;
        }
    };

    setValue('[name="last_name"]', fields.last_name || '');
    setValue('[name="first_name"]', fields.first_name || '');
    setValue('[name="middle_name"]', fields.middle_name || '');
    setValue('[name="phone"]', fields.phone || '');
    setValue('[name="email"]', fields.email || '');
    setValue('[name="platform"]', fields.platform || 'instagram');
    setValue('[name="prepayment_amount"]', fields.prepayment_amount || '0');
    setValue('[name="engraving_description"]', fields.engraving_description || '');
    setValue('[name="customer_request"]', fields.customer_request || '');

    setValue('#city-input', fields.city_input || '');
    setValue('#region-input', fields.region_input || '');
    setValue('#district-input', fields.district_input || '');
    setValue('#manual-city-input', fields.manual_city || '');
    setValue('#manual-region-input', fields.manual_region || '');
    setValue('#manual-district-input', fields.manual_district || '');
    setValue('#manual-post-department-input', fields.manual_post_department || '');

    const deliverySelect = document.querySelector('[name="delivery_service"]');
    if (deliverySelect) {
        deliverySelect.value = fields.delivery_service || 'nova_poshta';
        toggleDeliveryFields(deliverySelect);
    }

    currentOrderItems = Array.isArray(draft.items)
        ? draft.items.map(item => ({
            id: Number(item.id),
            name: item.name,
            sellingPrice: Number(item.sellingPrice),
            dropPrice: Number(item.dropPrice || 0),
            quantity: Number(item.quantity || 1)
        })).filter(item => item.id && item.name && item.quantity > 0)
        : [];

    renderOrderItems();
    calculateTotal();

    if ((fields.delivery_service || 'nova_poshta') === 'nova_poshta' && (fields.city_input || '').trim().length >= 2) {
        await loadDeliveryData(fields.city_input || '');
        const warehouseSelect = document.getElementById('warehouse-select');
        if (warehouseSelect && fields.warehouse_select) {
            warehouseSelect.value = fields.warehouse_select;
        }
    }

    isRestoringOrderDraft = false;
}

function initOrderDraftPersistence() {
    bindOrderDraftHandlers();
    restoreOrderDraft();
}

function renderBreadcrumbs() {
    const container = document.getElementById('breadcrumb-container');
    if (!container) return;
    if (breadcrumbStack.length === 0) {
        container.innerHTML = '<button class="btn btn-sm btn-light" onclick="resetCatalog()">🏠 Початок</button>';
        return;
    }
    container.innerHTML = breadcrumbStack.map(item => `
        <button class="btn btn-sm btn-light" onclick="loadCatalog(${item.id})">${item.name}</button>`).join('');
}

function resetCatalog() {
    document.getElementById('breadcrumb-container').innerHTML = '<button class="btn btn-sm btn-light" onclick="resetCatalog()">🏠 Початок</button>';
    // Тут виклик початкових категорій
    location.reload(); // Спрощений варіант, або викликати функцію завантаження root
}

// 1. Додаємо ці функції, щоб усунути помилки в консолі
function getSelectedDeliveryService() {
    return document.getElementById('deliverySelect')?.value || '';
}

function setRegionDistrict(region, district) {
    const regionInput = document.getElementById('region-input');
    const districtInput = document.getElementById('district-input');

    if (regionInput) {
        regionInput.value = region || '';
    }
    if (districtInput) {
        districtInput.value = district || '';
    }
}

async function novaPoshtaApi(modelName, calledMethod, methodProperties = {}) {
    const response = await fetch(NOVA_POSHTA_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            apiKey: NOVA_POSHTA_API_KEY,
            modelName,
            calledMethod,
            methodProperties
        })
    });

    if (!response.ok) {
        throw new Error(`Nova Poshta API error ${response.status}`);
    }

    const json = await response.json();
    if (!json.success) {
        throw new Error((json.errors && json.errors.join(', ')) || 'Nova Poshta API error');
    }

    return json.data || [];
}

async function fetchNovaPoshtaCities(query) {
    if (!query) {
        return [];
    }

    const cities = await novaPoshtaApi('Address', 'getCities', {
        FindByString: query,
        Limit: 20
    });

    return cities
        .map(item => ({
            name: item.Description || '',
            ref: item.Ref || '',
            area: item.AreaDescription || '',
            district: item.RegionDescription || item.SettlementTypeDescription || ''
        }))
        .filter(item => item.name)
        .slice(0, 20);
}

function renderCitySuggestions(suggestions) {
    const suggestionsBox = document.getElementById('citySuggestions');
    if (!suggestionsBox) return;

    if (!suggestions.length) {
        suggestionsBox.innerHTML = '';
        suggestionsBox.classList.remove('visible');
        return;
    }

    suggestionsBox.innerHTML = suggestions
        .map(option => `<div class="city-suggestion-item" data-city="${option.name}" data-ref="${option.ref}" data-area="${option.area}" data-district="${option.district}">${option.name}</div>`)
        .join('');

    suggestionsBox.classList.add('visible');

    suggestionsBox.querySelectorAll('.city-suggestion-item').forEach(item => {
        item.addEventListener('mousedown', async event => {
            event.preventDefault();
            const cityValue = item.getAttribute('data-city') || '';
            const cityRef = item.getAttribute('data-ref') || '';
            const area = item.getAttribute('data-area') || '';
            const district = item.getAttribute('data-district') || '';

            const input = document.getElementById('city-input');
            if (input) {
                input.value = cityValue;
            }

            deliveryState.city = cityValue;
            deliveryState.cityRef = cityRef;
            deliveryState.region = area;
            deliveryState.district = district;

            setRegionDistrict(area, district);
            clearCitySuggestions();
            await loadDeliveryData(cityValue, cityRef);
        });
    });
}

function clearCitySuggestions() {
    const suggestionsBox = document.getElementById('citySuggestions');
    if (!suggestionsBox) return;
    suggestionsBox.innerHTML = '';
    suggestionsBox.classList.remove('visible');
}

async function updateCitySuggestions() {
    const input = document.getElementById('city-input');
    const city = input ? input.value.trim() : '';
    const service = getSelectedDeliveryService();

    if (!city || service !== 'nova_poshta') {
        clearCitySuggestions();
        return;
    }

    if (citySuggestionsTimer) {
        clearTimeout(citySuggestionsTimer);
    }

    citySuggestionsTimer = setTimeout(async () => {
        try {
            const suggestions = await fetchNovaPoshtaCities(city);
            renderCitySuggestions(suggestions);
        } catch (error) {
            console.error('City suggestions error:', error);
            clearCitySuggestions();
        }
    }, CITY_SUGGESTION_DELAY);
}

async function fetchNovaPoshtaBranches(city, cityRef = '') {
    let resolvedCityRef = cityRef;
    let resolvedCityName = city;

    if (!resolvedCityRef) {
        const cities = await novaPoshtaApi('Address', 'getCities', {
            FindByString: city,
            Limit: 20
        });

        if (!cities.length) {
            return [];
        }

        const cityData = cities[0];
        resolvedCityRef = cityData.Ref || '';
        resolvedCityName = cityData.Description || city;
        deliveryState.region = cityData.AreaDescription || '';
        deliveryState.district = cityData.RegionDescription || cityData.SettlementTypeDescription || '';
        setRegionDistrict(deliveryState.region, deliveryState.district);
    }

    deliveryState.city = resolvedCityName;
    deliveryState.cityRef = resolvedCityRef;

    const warehouses = await novaPoshtaApi('AddressGeneral', 'getWarehouses', {
        CityRef: resolvedCityRef,
        Language: 'UA'
    });

    return warehouses.map(warehouse => warehouse.Description || '').filter(Boolean);
}

async function loadDeliveryData(cityOverride = '', cityRef = '') {
    const cityInput = document.getElementById('city-input');
    const warehouseSelect = document.getElementById('warehouse-select');

    if (!cityInput || !warehouseSelect) return;

    const service = getSelectedDeliveryService();
    if (service !== 'nova_poshta') {
        warehouseSelect.innerHTML = '<option value="">Оберіть спосіб доставки</option>';
        return;
    }

    const city = (cityOverride || cityInput.value || '').trim();
    if (city.length < 2) {
        warehouseSelect.innerHTML = '<option value="">Спочатку оберіть місто</option>';
        return;
    }

    try {
        const warehouses = await fetchNovaPoshtaBranches(city, cityRef);

        if (!warehouses.length) {
            warehouseSelect.innerHTML = '<option value="">Відділення не знайдено</option>';
            return;
        }

        warehouseSelect.innerHTML = '<option value="">Оберіть відділення</option>';
        warehouses.forEach(warehouseText => {
            const option = document.createElement('option');
            option.value = warehouseText;
            option.textContent = warehouseText;
            warehouseSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading delivery data:', error);
        warehouseSelect.innerHTML = '<option value="">Помилка завантаження відділень</option>';
    }
}

function bindNovaPoshtaHandlers() {
    const cityInput = document.getElementById('city-input');
    const warehouseSelect = document.getElementById('warehouse-select');

    if (cityInput) {
        cityInput.oninput = () => {
            updateCitySuggestions();
        };

        cityInput.onchange = () => {
            loadDeliveryData();
        };

        cityInput.onblur = () => {
            setTimeout(() => {
                clearCitySuggestions();
            }, 120);
        };
    }

    if (warehouseSelect) {
        warehouseSelect.onchange = () => {
            const manualAddressField = document.querySelector('[name="post_department"]');
            if (manualAddressField) {
                manualAddressField.value = warehouseSelect.value;
            }
        };
    }

    if (!novaPoshtaOutsideClickBound) {
        document.addEventListener('click', event => {
            const box = document.getElementById('citySuggestions');
            const input = document.getElementById('city-input');
            if (!box || !input) return;
            if (event.target !== input && !box.contains(event.target)) {
                clearCitySuggestions();
            }
        });
        novaPoshtaOutsideClickBound = true;
    }
}

function initDeliveryForm() {
    const select = document.getElementById('deliverySelect');
    if (select) {
        toggleDeliveryFields(select); // Викликаємо нашу логіку
        bindNovaPoshtaHandlers();
        bindOrderDraftHandlers();
    }
}

// --- Дані замовлень: фільтри, редагування, ТТН, Telegram ---
function applyOrderFilters() {
    const q = document.getElementById('ordersSearch')?.value?.trim() || '';
    const startDate = document.getElementById('ordersStartDate')?.value || '';
    const endDate = document.getElementById('ordersEndDate')?.value || '';
    const managerId = document.getElementById('ordersManager')?.value || '';
    const status = document.getElementById('ordersStatus')?.value || '';

    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    if (managerId) params.set('manager_id', managerId);
    if (status) params.set('status', status);

    const query = params.toString();
    const url = query ? `/ajax/content_order_details/?${query}` : '/ajax/content_order_details/';
    loadContent(url);
}

function toggleOrderDetails(orderId) {
    const row = document.getElementById(`order-details-${orderId}`);
    if (!row) return;
    row.style.display = row.style.display === 'table-row' ? 'none' : 'table-row';
}

function openOrderEditForm(orderId) {
    fetch(`/ajax/order-edit-form/${orderId}/`)
        .then(response => response.json())
        .then(data => {
            const modalBody = document.getElementById('modal-body');
            const modal = document.getElementById('modalOverlay');
            if (modalBody) modalBody.innerHTML = data.html;
            if (modal) modal.style.display = 'flex';
        })
        .catch(error => {
            console.error(error);
            alert('Не вдалося відкрити форму редагування замовлення.');
        });
}

function addOrderItemRow() {
    const template = document.getElementById('order-item-row-template');
    const editor = document.getElementById('order-items-editor');
    if (!template || !editor) return;
    editor.insertAdjacentHTML('beforeend', template.innerHTML);
}

function saveOrderEditForm(orderId) {
    const form = document.getElementById('orderEditForm');
    if (!form) return;

    const formData = new FormData(form);

    fetch(`/ajax/order-save/${orderId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal();
            applyOrderFilters();
        } else {
            alert(data.message || 'Помилка збереження замовлення');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Сталася помилка при збереженні замовлення.');
    });
}

function deleteOrder(orderId) {
    if (!confirm('Видалити це замовлення? Дію неможливо скасувати.')) {
        return;
    }

    fetch(`/ajax/order-delete/${orderId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            applyOrderFilters();
        } else {
            alert(data.message || 'Не вдалося видалити замовлення.');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Сталася помилка при видаленні замовлення.');
    });
}

function trackOrderByTtn(orderId) {
    const ttn = prompt('Введіть ТТН для оновлення статусу:');
    if (!ttn) return;

    const formData = new FormData();
    formData.append('ttn', ttn.trim());

    fetch(`/ajax/order-track/${orderId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.status !== 'ok') {
            alert(data.message || 'Не вдалося оновити статус доставки');
            return;
        }

        const deliveryNode = document.getElementById(`delivery-status-${orderId}`);
        if (deliveryNode) {
            deliveryNode.textContent = data.delivery_status_text || '-';
        }
        applyOrderFilters();
    })
    .catch(error => {
        console.error(error);
        alert('Помилка при зверненні до API Нової Пошти.');
    });
}

function openOrderTelegramForm(orderId) {
    fetch(`/ajax/order-telegram-form/${orderId}/`)
        .then(response => response.json())
        .then(data => {
            const modalBody = document.getElementById('modal-body');
            const modal = document.getElementById('modalOverlay');
            if (modalBody) modalBody.innerHTML = data.html;
            if (modal) modal.style.display = 'flex';
        })
        .catch(error => {
            console.error(error);
            alert('Не вдалося відкрити форму відправки в Telegram.');
        });
}

function sendOrderToTelegram(orderId) {
    const form = document.getElementById('orderTelegramForm');
    if (!form) return;

    const formData = new FormData(form);

    fetch(`/ajax/order-telegram-send/${orderId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal();
            applyOrderFilters();
        } else {
            alert(data.message || 'Не вдалося надіслати повідомлення.');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Помилка відправки в Telegram.');
    });
}

function refreshOrderTemplatePreview(orderId) {
    const templateId = document.getElementById('orderTemplateSelect')?.value || '';
    const query = templateId ? `?template_id=${encodeURIComponent(templateId)}` : '';

    fetch(`/ajax/order-template-preview/${orderId}/${query}`)
        .then(response => response.json())
        .then(data => {
            const textarea = document.querySelector('#orderTelegramForm textarea[name="message_text"]');
            if (textarea && typeof data.text === 'string') {
                textarea.value = data.text;
            }
        })
        .catch(error => {
            console.error(error);
            alert('Не вдалося оновити текст шаблону.');
        });
}

function openMessageTemplateForm(templateId = null) {
    const url = templateId ? `/ajax/template-form/${templateId}/` : '/ajax/template-form/';

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const modalBody = document.getElementById('modal-body');
            const modal = document.getElementById('modalOverlay');
            const modalBox = document.querySelector('#modalOverlay .modal-box');
            if (modalBody) modalBody.innerHTML = data.html;
            if (modalBox) modalBox.style.width = '600px';
            if (modal) modal.style.display = 'flex';
            initTemplateFormPreview();
        })
        .catch(error => {
            console.error(error);
            alert('Не вдалося відкрити форму шаблону.');
        });
}

function initTemplateFormPreview() {
    const textarea = document.getElementById('id_body');
    const previewBox = document.getElementById('templatePreviewBox');
    if (!textarea || !previewBox) return;

    const sampleData = {
        manager_order_no: '307',
        order_number_global: '307',
        separator: '* * * * * * * * * * * * * * * * * * * *',
        items_block: '• Сковорода 4 мм (60)\n• Кришка (60)\n• Чохол (60)\n• Підставка Садж .Розбірні ніжки. для (60)',
        customer_total_block: '----------------------------------------\nВартість для клієнта: 3360 грн\n(Наложка)\n',
        drop_price: '2520',
        region: 'Дніпропетровська обл.',
        city: "Кам\'янське (Дніпропетровська обл)",
        post_department: '№12 (до 30 кг) бульв. Будівельників, 42А',
        recipient: 'Толкушнік Олександра',
        phone: '0677460466',
        ttn_block: 'ТТН - Створіть самі',
        customer_request: '-',
    };

    const renderPreview = () => {
        let text = textarea.value || '';
        Object.entries(sampleData).forEach(([key, value]) => {
            text = text.replaceAll(`{${key}}`, String(value));
        });
        previewBox.textContent = text;
    };

    textarea.removeEventListener('input', textarea.__templatePreviewHandler || (() => {}));
    textarea.__templatePreviewHandler = renderPreview;
    textarea.addEventListener('input', renderPreview);
    renderPreview();
}

function saveMessageTemplateForm(templateId = null) {
    const form = document.getElementById('messageTemplateForm');
    if (!form) return;

    const formData = new FormData(form);
    const url = templateId ? `/ajax/template-save/${templateId}/` : '/ajax/template-save/';

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal();
            loadContent('/ajax/templates/');
        } else {
            alert(data.message || 'Не вдалося зберегти шаблон.');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Помилка при збереженні шаблону.');
    });
}

function deleteMessageTemplate(templateId) {
    if (!confirm('Ви впевнені, що хочете видалити цей шаблон?')) {
        return;
    }

    fetch(`/ajax/template-delete/${templateId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            loadContent('/ajax/templates/');
        } else {
            alert(data.message || 'Не вдалося видалити шаблон.');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Помилка при видаленні шаблону.');
    });
}

function getFinanceContentUrl() {
    const period = document.getElementById('financePeriod')?.value || 'month';
    const dateValue = document.getElementById('financeDate')?.value || '';
    const statusNodes = document.querySelectorAll('input[name="finance-status"]:checked');
    const params = new URLSearchParams();
    params.set('period', period);
    if (dateValue) {
        params.set('date', dateValue);
    }
    statusNodes.forEach(node => {
        if (node.value) {
            params.append('status', node.value);
        }
    });
    return `/ajax/finance/?${params.toString()}`;
}

function applyFinanceFilters() {
    loadContent(getFinanceContentUrl());
}

function saveFinanceConfig() {
    const form = document.getElementById('financeConfigForm');
    if (!form) return;

    fetch('/ajax/finance/config-save/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: new FormData(form),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            applyFinanceFilters();
        } else {
            alert(data.message || 'Не вдалося зберегти фінансові параметри.');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Сталася помилка при збереженні фінансових параметрів.');
    });
}

function saveUserPayrollSettings(userId, formElement) {
    if (!formElement) return;

    fetch(`/ajax/finance/user-payroll-save/${userId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: new FormData(formElement),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            applyFinanceFilters();
        } else {
            alert(data.message || 'Не вдалося зберегти параметри користувача.');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Сталася помилка при збереженні параметрів користувача.');
    });
}

function addAdExpense() {
    const form = document.getElementById('adExpenseForm');
    if (!form) return;

    fetch('/ajax/finance/ad-expense-add/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: new FormData(form),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            form.reset();
            const financeDate = document.getElementById('financeDate');
            if (financeDate) {
                const dateInput = form.querySelector('[name="spend_date"]');
                if (dateInput) {
                    dateInput.value = financeDate.value;
                }
            }
            applyFinanceFilters();
        } else {
            alert(data.message || 'Не вдалося додати витрати на рекламу.');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Сталася помилка при додаванні витрат на рекламу.');
    });
}

function deleteAdExpense(expenseId) {
    if (!confirm('Видалити цей запис витрат?')) {
        return;
    }

    fetch(`/ajax/finance/ad-expense-delete/${expenseId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            applyFinanceFilters();
        } else {
            alert(data.message || 'Не вдалося видалити витрати.');
        }
    })
    .catch(error => {
        console.error(error);
        alert('Сталася помилка при видаленні витрат.');
    });
}
// Функція для додавання товару в замовлення та розрахунку суми і збереження в базі та оновлення інтерфейсу
