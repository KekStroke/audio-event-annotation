/**
 * Annotation Form для создания аннотаций.
 * 
 * Функционал:
 * - Открытие/закрытие модального окна
 * - Автозаполнение start_time/end_time из региона
 * - Валидация формы на клиенте
 * - Отправка POST запроса на /api/annotations
 * - Визуальная индикация успеха/ошибки
 */

// Глобальные переменные
let annotationFormCurrentAudioFileId = null;
let annotationFormCurrentRegion = null;

// Подписка на выбор аудио файла в списке
document.addEventListener('audioFileSelected', (event) => {
    const audioFileId = event?.detail?.id;
    if (audioFileId) {
        setCurrentAudioFileId(audioFileId);
    }
});

/**
 * Инициализация Annotation Form
 */
function initAnnotationForm() {
    setupAnnotationEventHandlers();
    setupFormValidation();
}

/**
 * Настройка обработчиков событий
 */
function setupAnnotationEventHandlers() {
    // Кнопка открытия модального окна (из selection-tool.js)
    const openAnnotationBtn = document.getElementById('create-annotation');
    if (openAnnotationBtn) {
        openAnnotationBtn.addEventListener('click', openAnnotationModal);
    }

    // Кнопка закрытия модального окна
    const closeBtn = document.querySelector('#annotation-modal .modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeAnnotationModal);
    }

    // Кнопка сохранения аннотации
    const saveBtn = document.getElementById('save-annotation');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveAnnotation);
    }

    // Кнопка отмены
    const cancelBtn = document.getElementById('cancel-annotation');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeAnnotationModal);
    }

    // Закрытие по клику на overlay
    const annotationOverlay = document.getElementById('annotation-modal-overlay');
    if (annotationOverlay) {
        annotationOverlay.addEventListener('click', (e) => {
            if (e.target === annotationOverlay) {
                closeAnnotationModal();
            }
        });
    }

    // Range slider для confidence
    const confidenceSlider = document.getElementById('confidence');
    if (confidenceSlider) {
        confidenceSlider.addEventListener('input', updateConfidenceValue);
    }
}

/**
 * Настройка валидации формы
 */
function setupFormValidation() {
    const form = document.getElementById('annotation-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            if (validateForm()) {
                saveAnnotation();
            }
        });
    }
}

/**
 * Открытие модального окна для создания аннотации
 */
function openAnnotationModal() {
    // Получаем текущий регион из selection-tool.js
    if (typeof selectionToolCurrentRegion !== 'undefined' && selectionToolCurrentRegion) {
        annotationFormCurrentRegion = selectionToolCurrentRegion;
    } else if (typeof wavesurfer !== 'undefined' && wavesurfer) {
        // Пытаемся получить активный регион из wavesurfer
        const regions = wavesurfer.getActivePlugins().regions;
        if (regions && regions.list) {
            const regionList = Object.values(regions.list);
            if (regionList.length > 0) {
                annotationFormCurrentRegion = regionList[0];
            }
        }
    }

    // Автозаполнение start_time и end_time из региона
    autofillRegionTimes();

    // Показываем модальное окно
    const modal = document.getElementById('annotation-modal');
    const overlay = document.getElementById('annotation-modal-overlay');
    if (modal && overlay) {
        modal.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // Фокус на первое поле
    const eventLabelInput = document.getElementById('event-label');
    if (eventLabelInput) {
        eventLabelInput.focus();
    }
}

/**
 * Закрытие модального окна
 */
function closeAnnotationModal() {
    const modal = document.getElementById('annotation-modal');
    const overlay = document.getElementById('annotation-modal-overlay');
    if (modal && overlay) {
        modal.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Очищаем форму
    clearForm();
    hideMessages();
}

/**
 * Автозаполнение start_time и end_time из региона
 */
function autofillRegionTimes() {
    if (!annotationFormCurrentRegion) {
        return;
    }

    // Заполняем скрытые поля start_time и end_time
    const startTimeInput = document.getElementById('start-time');
    const endTimeInput = document.getElementById('end-time');
    
    if (startTimeInput && annotationFormCurrentRegion.start !== undefined) {
        startTimeInput.value = annotationFormCurrentRegion.start;
    }
    if (endTimeInput && annotationFormCurrentRegion.end !== undefined) {
        endTimeInput.value = annotationFormCurrentRegion.end;
    }
}

/**
 * Обновление отображаемого значения confidence
 */
function updateConfidenceValue() {
    const slider = document.getElementById('confidence');
    const valueDisplay = document.getElementById('confidence-value');
    if (slider && valueDisplay) {
        valueDisplay.textContent = parseFloat(slider.value).toFixed(2);
    }
}

/**
 * Валидация формы
 */
function validateForm() {
    const eventLabel = document.getElementById('event-label');
    const confidence = document.getElementById('confidence');
    const startTime = document.getElementById('start-time');
    const endTime = document.getElementById('end-time');

    // Проверка event_label
    if (!eventLabel || !eventLabel.value.trim()) {
        showError('Поле event_label обязательно для заполнения');
        return false;
    }

    // Проверка confidence
    if (confidence) {
        const confidenceValue = parseFloat(confidence.value);
        if (isNaN(confidenceValue) || confidenceValue < 0 || confidenceValue > 1) {
            showError('Confidence должен быть в диапазоне от 0 до 1');
            return false;
        }
    }

    // Проверка start_time и end_time
    if (startTime && endTime) {
        const start = parseFloat(startTime.value);
        const end = parseFloat(endTime.value);
        if (isNaN(start) || isNaN(end) || start >= end) {
            showError('start_time должен быть меньше end_time');
            return false;
        }
    }

    hideMessages();
    return true;
}

/**
 * Сохранение аннотации
 */
function saveAnnotation() {
    if (!validateForm()) {
        return;
    }

    // Получаем данные формы
    const eventLabel = document.getElementById('event-label').value.trim();
    const confidence = document.getElementById('confidence').value;
    const notes = document.getElementById('notes').value.trim();
    const startTime = document.getElementById('start-time').value;
    const endTime = document.getElementById('end-time').value;

    // Получаем audio_file_id (должен быть установлен извне)
    // Fallback на window.currentAudioFileId если локальная переменная не установлена
    const audioFileId = annotationFormCurrentAudioFileId || window.currentAudioFileId;
    if (!audioFileId) {
        showError('Audio file ID не установлен');
        return;
    }

    // Формируем данные для отправки
    const annotationData = {
        audio_file_id: audioFileId,
        start_time: parseFloat(startTime),
        end_time: parseFloat(endTime),
        event_label: eventLabel,
        confidence: confidence ? parseFloat(confidence) : null,
        notes: notes || null
    };

    // Проверяем, редактируем ли мы существующую аннотацию
    const form = document.getElementById('annotation-form');
    const annotationId = form ? form.dataset.annotationId : null;

    // Определяем метод и URL
    const method = annotationId ? 'PUT' : 'POST';
    const url = annotationId ? `/api/annotations/${annotationId}` : '/api/annotations';

    // Отправляем запрос
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(annotationData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Ошибка при сохранении аннотации');
            });
        }
        return response.json();
    })
    .then(data => {
        if (annotationId) {
            showSuccess('Аннотация успешно обновлена');
            // Отправляем событие об обновлении аннотации
            document.dispatchEvent(new CustomEvent('annotationUpdated', { detail: data }));
        } else {
            showSuccess('Аннотация успешно сохранена');
            // Отправляем событие о создании аннотации
            document.dispatchEvent(new CustomEvent('annotationCreated', { detail: data }));
        }
        
        setTimeout(() => {
            closeAnnotationModal();
            // Очищаем ID аннотации из формы
            if (form) {
                delete form.dataset.annotationId;
            }
        }, 1000);
    })
    .catch(error => {
        showError(error.message || 'Ошибка при сохранении аннотации');
    });
}

/**
 * Показ сообщения об успехе
 */
function showSuccess(message) {
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    
    if (errorMessage) {
        errorMessage.classList.remove('active');
    }
    
    if (successMessage) {
        successMessage.textContent = message;
        successMessage.classList.add('active');
    }
}

/**
 * Показ сообщения об ошибке
 */
function showError(message) {
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    
    if (successMessage) {
        successMessage.classList.remove('active');
    }
    
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.classList.add('active');
    }
}

/**
 * Скрытие сообщений
 */
function hideMessages() {
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    
    if (successMessage) {
        successMessage.classList.remove('active');
    }
    if (errorMessage) {
        errorMessage.classList.remove('active');
    }
}

/**
 * Очистка формы
 */
function clearForm() {
    const form = document.getElementById('annotation-form');
    if (form) {
        form.reset();
        // Очищаем ID аннотации
        delete form.dataset.annotationId;
    }
    
    // Сбрасываем значение confidence
    const confidenceValue = document.getElementById('confidence-value');
    if (confidenceValue) {
        confidenceValue.textContent = '0.50';
    }
}

/**
 * Установка текущего Audio File ID
 */
function setCurrentAudioFileId(audioFileId) {
    annotationFormCurrentAudioFileId = audioFileId;
}

/**
 * Установка текущего региона
 */
function setCurrentRegion(region) {
    annotationFormCurrentRegion = region;
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', () => {
    initAnnotationForm();
    
    // Инициализируем значение confidence
    updateConfidenceValue();
});

