// JavaScript для админ-панели

/**
 * Предпросмотр одного изображения перед загрузкой (старая функция для совместимости)
 */
function previewImage(event, previewId) {
    const file = event.target.files[0];
    const preview = document.getElementById(previewId);
    const container = preview ? preview.closest('.current-image') : null;
    
    if (file) {
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Пожалуйста, выберите изображение формата PNG, JPG, GIF или WEBP');
            event.target.value = '';
            return;
        }
        
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            alert('Размер файла не должен превышать 5 МБ');
            event.target.value = '';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            if (preview) {
                preview.src = e.target.result;
                if (container) container.style.display = 'block';
            }
        };
        reader.readAsDataURL(file);
    }
}

/**
 * Предпросмотр нескольких изображений перед загрузкой
 */
function previewMultipleImages(event, containerId) {
    const files = event.target.files;
    const container = document.getElementById(containerId);
    
    if (!container) return;
    
    // Очищаем предыдущий предпросмотр
    container.innerHTML = '';
    
    if (files.length === 0) return;
    
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    const maxSize = 5 * 1024 * 1024;
    
    Array.from(files).forEach((file, index) => {
        // Проверка типа файла
        if (!validTypes.includes(file.type)) {
            alert(`Файл "${file.name}" имеет недопустимый формат. Используйте PNG, JPG, GIF или WEBP`);
            return;
        }
        
        // Проверка размера файла
        if (file.size > maxSize) {
            alert(`Файл "${file.name}" превышает максимальный размер 5 МБ`);
            return;
        }
        
        // Создаем элемент для предпросмотра
        const reader = new FileReader();
        reader.onload = function(e) {
            const imageItem = document.createElement('div');
            imageItem.className = 'image-item';
            imageItem.innerHTML = `
                <img src="${e.target.result}" alt="Preview ${index + 1}" class="image-preview-thumb">
                <span class="image-name">${file.name}</span>
            `;
            container.appendChild(imageItem);
        };
        reader.readAsDataURL(file);
    });
    
    // Показываем информацию о количестве выбранных файлов
    const infoText = document.createElement('p');
    infoText.className = 'form-text';
    infoText.style.marginTop = '0.5rem';
    infoText.textContent = `Выбрано файлов: ${files.length}`;
    container.appendChild(infoText);
}

/**
 * Подтверждение удаления с дополнительной информацией
 */
document.addEventListener('DOMContentLoaded', function() {
    // Улучшенное подтверждение удаления
    const deleteForms = document.querySelectorAll('form[onsubmit*="confirm"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const itemName = this.closest('tr')?.querySelector('td:nth-child(2)')?.textContent || 'этот элемент';
            if (!confirm(`Вы уверены, что хотите удалить "${itemName}"?\n\nЭто действие необратимо.`)) {
                e.preventDefault();
            }
        });
    });
    
    // Автосохранение формы в localStorage (на случай случайного закрытия)
    const forms = document.querySelectorAll('.admin-form');
    forms.forEach(form => {
        const formId = window.location.pathname;
        
        // Загружаем сохраненные данные
        const savedData = localStorage.getItem(formId);
        if (savedData && !form.querySelector('[value]')?.value) {
            const data = JSON.parse(savedData);
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input && input.type !== 'file') {
                    input.value = data[key];
                }
            });
        }
        
        // Сохраняем данные при изменении
        form.addEventListener('input', function(e) {
            if (e.target.type !== 'file' && e.target.type !== 'checkbox') {
                const formData = {};
                new FormData(form).forEach((value, key) => {
                    if (key !== 'image_file') {
                        formData[key] = value;
                    }
                });
                localStorage.setItem(formId, JSON.stringify(formData));
            }
        });
        
        // Очищаем при успешной отправке
        form.addEventListener('submit', function() {
            localStorage.removeItem(formId);
        });
    });
    
    // Показываем количество символов в textarea
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        const counter = document.createElement('small');
        counter.className = 'form-text char-counter';
        counter.style.float = 'right';
        textarea.parentNode.appendChild(counter);
        
        function updateCounter() {
            const length = textarea.value.length;
            counter.textContent = `${length} символов`;
        }
        
        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });
    
    // Подсветка активной страницы в боковом меню
    const currentPath = window.location.pathname;
    document.querySelectorAll('.admin-nav-item').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = '#34495e';
            link.style.color = '#fff';
            link.style.paddingLeft = '2rem';
        }
    });
    
    // Анимация для статистических карточек
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Валидация форм
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            let firstInvalid = null;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#e74c3c';
                    if (!firstInvalid) firstInvalid = field;
                } else {
                    field.style.borderColor = '#e0e0e0';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Пожалуйста, заполните все обязательные поля');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
        
        // Сброс подсветки при вводе
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                this.style.borderColor = '#e0e0e0';
            });
        });
    });
    
    console.log('✅ Админ-панель инициализирована');
});
