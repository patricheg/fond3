// Главный JavaScript файл

document.addEventListener('DOMContentLoaded', function() {
    // Автоматическое скрытие уведомлений через 5 секунд
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // Подтверждение удаления
    const deleteForms = document.querySelectorAll('form[onsubmit*="confirm"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Вы уверены, что хотите удалить этот элемент?')) {
                e.preventDefault();
            }
        });
    });

    // Плавная прокрутка к якорям
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Анимация появления элементов при прокрутке
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Применяем анимацию к карточкам
    document.querySelectorAll('.card, .news-item, .stat-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });

    // Валидация форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#e74c3c';
                } else {
                    field.style.borderColor = '#e0e0e0';
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Пожалуйста, заполните все обязательные поля');
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

    // Форматирование чисел с разделителями тысяч
    document.querySelectorAll('[data-format-number]').forEach(el => {
        const value = parseFloat(el.textContent);
        if (!isNaN(value)) {
            el.textContent = value.toLocaleString('ru-RU');
        }
    });

    // Копирование ссылки при клике на кнопку "Поделиться"
    const shareButtons = document.querySelectorAll('.share-btn');
    shareButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const url = window.location.href;
            
            if (navigator.share) {
                navigator.share({
                    title: document.title,
                    url: url
                }).catch(err => console.log('Ошибка при попытке поделиться:', err));
            } else if (navigator.clipboard) {
                navigator.clipboard.writeText(url).then(() => {
                    alert('Ссылка скопирована в буфер обмена!');
                });
            }
        });
    });

    // Индикатор прогресса загрузки страницы
    window.addEventListener('load', function() {
        document.body.classList.add('loaded');
    });

    // Lazy loading для изображений
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Активная ссылка в навигации
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-menu a, .admin-nav-item').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = '#3498db';
            link.style.fontWeight = 'bold';
        }
    });

    // Инициализация всех слайдеров на странице
    initSliders();
    
    console.log('✅ Сайт благотворительного фонда загружен успешно!');
});

/**
 * Инициализация слайдеров
 */
function initSliders() {
    document.querySelectorAll('.card-image-slider, .detail-image-slider, .news-image-slider').forEach((slider, index) => {
        slider.setAttribute('data-slider-id', index);
        showSlide(slider, 0);
    });
}

/**
 * Показать конкретный слайд
 */
function showSlide(sliderElement, index) {
    const images = sliderElement.querySelectorAll('.slider-image');
    const dots = sliderElement.querySelectorAll('.slider-dot');
    
    if (images.length === 0) return;
    
    // Нормализуем индекс
    if (index >= images.length) index = 0;
    if (index < 0) index = images.length - 1;
    
    // Сохраняем текущий индекс
    sliderElement.setAttribute('data-current-slide', index);
    
    // Скрываем все изображения
    images.forEach(img => {
        img.style.display = 'none';
    });
    
    // Показываем текущее изображение
    if (images[index]) {
        images[index].style.display = 'block';
    }
    
    // Обновляем точки
    dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
    });
}

/**
 * Переключение слайда
 */
function moveSlide(button, direction) {
    const slider = button.closest('.card-image-slider, .detail-image-slider, .news-image-slider');
    if (!slider) return;
    
    const currentIndex = parseInt(slider.getAttribute('data-current-slide') || '0');
    const newIndex = currentIndex + direction;
    
    showSlide(slider, newIndex);
}

/**
 * Переход к конкретному слайду
 */
function goToSlide(dot, index) {
    const slider = dot.closest('.card-image-slider, .detail-image-slider, .news-image-slider');
    if (!slider) return;
    
    showSlide(slider, index);
}
