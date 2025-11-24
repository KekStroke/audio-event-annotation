/**
 * Annotation List для отображения и управления списком аннотаций.
 * 
 * Функционал:
 * - Загрузка списка аннотаций с сервера
 * - Отображение аннотаций в sidebar
 * - Клик по аннотации выделяет регион
 * - Кнопки Edit и Delete для каждой аннотации
 * - Цветовая кодировка по типу события
 * - Счетчик аннотаций
 * - Динамическое обновление после CRUD операций
 */

// Глобальные переменные
let annotationListCurrentAudioFileId = null;
let annotations = [];
let annotationRegions = {}; // Маппинг annotation_id -> region

function getAnnotationRegionsPlugin() {
    if (typeof window.getWaveSurferRegionsPlugin === 'function') {
        return window.getWaveSurferRegionsPlugin();
    }
    return null;
}

/**
 * Блокирует редактирование региона аннотации (drag/resize)
 */
function lockAnnotationRegion(region) {
    if (!region) return;

    const lockOptions = { drag: false, resize: false };

    if (typeof region.setOptions === 'function') {
        region.setOptions(lockOptions);
    } else {
        region.drag = false;
        region.resize = false;
        if (typeof region.update === 'function') {
            region.update(lockOptions);
        }
    }

    if (region.element) {
        region.element.classList.add('annotation-region-locked');
        region.element.setAttribute('data-annotation-locked', 'true');
    }
}

// Подписка на выбор аудио файла
document.addEventListener('audioFileSelected', (event) => {
    const audioFileId = event?.detail?.id;
    if (audioFileId) {
        setCurrentAudioFileId(audioFileId);
        loadAnnotations();
    }
});

document.addEventListener('wavesurferRegionsReady', () => {
    syncWithWavesurferRegions();
});

/**
 * Инициализация Annotation List
 */
function initAnnotationList() {
    setupEventListeners();
}

/**
 * Настройка обработчиков событий
 */
function setupEventListeners() {
    // Слушаем события обновления аннотаций
    document.addEventListener('annotationCreated', loadAnnotations);
    document.addEventListener('annotationUpdated', loadAnnotations);
    document.addEventListener('annotationDeleted', loadAnnotations);
}

/**
 * Установка текущего Audio File ID
 */
function setCurrentAudioFileId(audioFileId) {
    annotationListCurrentAudioFileId = audioFileId;
    if (audioFileId) {
        loadAnnotations();
    }
}

/**
 * Загрузка списка аннотаций с сервера
 */
function loadAnnotations() {
    if (!annotationListCurrentAudioFileId) {
        console.warn('Audio file ID не установлен');
        return;
    }

    fetch(`/api/annotations?audio_file_id=${annotationListCurrentAudioFileId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            annotations = data;
            renderAnnotationsList();
            syncWithWavesurferRegions();
            updateAnnotationsCount();
        })
        .catch(error => {
            console.error('Ошибка загрузки аннотаций:', error);
        });
}

/**
 * Отображение списка аннотаций
 */
function renderAnnotationsList() {
    const annotationsList = document.getElementById('annotations-list');
    if (!annotationsList) {
        console.warn('Элемент annotations-list не найден');
        return;
    }

    // Очищаем список
    annotationsList.innerHTML = '';

    if (annotations.length === 0) {
        annotationsList.innerHTML = '<div class="annotation-item-empty">No annotations</div>';
        return;
    }

    // Создаем элементы для каждой аннотации
    annotations.forEach(annotation => {
        const annotationItem = createAnnotationItem(annotation);
        annotationsList.appendChild(annotationItem);
    });
}

/**
 * Создание элемента аннотации
 */
function createAnnotationItem(annotation) {
    const item = document.createElement('div');
    item.className = 'annotation-item';
    item.dataset.annotationId = annotation.id;

    // Цветовая кодировка (по умолчанию используем цвет из event_type или случайный)
    const color = getAnnotationColor(annotation);
    item.style.borderLeft = `4px solid ${color}`;

    // Time range
    const timeRange = formatTimeRange(annotation.start_time, annotation.end_time);
    
    // Event label
    const eventLabel = annotation.event_label || 'Unknown';
    
    // Confidence
    const confidence = annotation.confidence !== null && annotation.confidence !== undefined
        ? (annotation.confidence * 100).toFixed(0) + '%'
        : 'N/A';

    // HTML структура
    item.innerHTML = `
        <div class="annotation-item-header">
            <div class="annotation-time-range">${timeRange}</div>
            <div class="annotation-actions">
                <button class="annotation-btn annotation-btn-edit" data-annotation-id="${annotation.id}" title="Edit">✎</button>
                <button class="annotation-btn annotation-btn-delete" data-annotation-id="${annotation.id}" title="Delete">✕</button>
            </div>
        </div>
        <div class="annotation-item-body">
            <div class="annotation-event-label">${escapeHtml(eventLabel)}</div>
            <div class="annotation-confidence">Confidence: ${confidence}</div>
        </div>
    `;

    // Обработчик клика по аннотации
    item.addEventListener('click', (e) => {
        // Не выделяем регион, если кликнули на кнопку
        if (e.target.classList.contains('annotation-btn')) {
            return;
        }
        selectAnnotationRegion(annotation);
    });

    // Обработчики кнопок
    const editBtn = item.querySelector('.annotation-btn-edit');
    if (editBtn) {
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            editAnnotation(annotation);
        });
    }

    const deleteBtn = item.querySelector('.annotation-btn-delete');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteAnnotation(annotation.id);
        });
    }

    return item;
}

/**
 * Форматирование временного диапазона
 */
function formatTimeRange(startTime, endTime) {
    const start = formatTime(startTime);
    const end = formatTime(endTime);
    return `${start} - ${end}`;
}

/**
 * Форматирование времени
 */
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00';

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(2, '0')}`;
}

/**
 * Получение цвета для аннотации
 */
function getAnnotationColor(annotation) {
    // Если есть event_type с цветом, используем его
    if (annotation.event_type && annotation.event_type.color) {
        return annotation.event_type.color;
    }
    
    // Иначе используем красный полупрозрачный для аннотаций
    return 'rgba(255, 100, 100, 0.3)'; // Красный полупрозрачный
}

/**
 * Выделение региона при клике на аннотацию
 */
function selectAnnotationRegion(annotation) {
    if (!wavesurfer) {
        console.warn('wavesurfer не инициализирован');
        return;
    }

    // Создаем или выделяем регион в wavesurfer
    const regionId = `annotation-${annotation.id}`;
    
    // Удаляем предыдущий регион для этой аннотации, если есть
    if (annotationRegions[annotation.id]) {
        try {
            annotationRegions[annotation.id].remove();
        } catch (e) {
            // Регион уже удален
        }
    }

    // Создаем новый регион
    const regionsPlugin = getAnnotationRegionsPlugin();
    if (!regionsPlugin || typeof regionsPlugin.addRegion !== 'function') {
        console.warn('Плагин regions недоступен — нельзя выделить аннотацию на waveform');
        return;
    }

    const region = regionsPlugin.addRegion({
        id: regionId,
        start: annotation.start_time,
        end: annotation.end_time,
        color: getAnnotationColor(annotation),
        drag: false,
        resize: false,
    });

    lockAnnotationRegion(region);

    annotationRegions[annotation.id] = region;

    // Прокручиваем к региону
    wavesurfer.seekTo(annotation.start_time / wavesurfer.getDuration());

    // Выделяем элемент аннотации в списке
    highlightAnnotationItem(annotation.id);
}

/**
 * Выделение элемента аннотации в списке
 */
function highlightAnnotationItem(annotationId) {
    // Убираем выделение со всех элементов
    const items = document.querySelectorAll('.annotation-item');
    items.forEach(item => {
        item.classList.remove('annotation-item-active');
    });

    // Выделяем текущий элемент
    const item = document.querySelector(`[data-annotation-id="${annotationId}"]`);
    if (item) {
        item.classList.add('annotation-item-active');
    }
}

/**
 * Редактирование аннотации
 */
function editAnnotation(annotation) {
    // Открываем модальное окно редактирования
    if (typeof openAnnotationModal === 'function') {
        // Заполняем форму данными аннотации
        const eventLabelInput = document.getElementById('event-label');
        const confidenceInput = document.getElementById('confidence');
        const notesInput = document.getElementById('notes');
        const startTimeInput = document.getElementById('start-time');
        const endTimeInput = document.getElementById('end-time');

        if (eventLabelInput) eventLabelInput.value = annotation.event_label || '';
        if (confidenceInput) confidenceInput.value = annotation.confidence || 0.5;
        if (notesInput) notesInput.value = annotation.notes || '';
        if (startTimeInput) startTimeInput.value = annotation.start_time || 0;
        if (endTimeInput) endTimeInput.value = annotation.end_time || 0;

        // Сохраняем ID аннотации для обновления
        document.getElementById('annotation-form').dataset.annotationId = annotation.id;

        // Открываем модальное окно
        openAnnotationModal();
    } else {
        console.warn('Функция openAnnotationModal не найдена');
    }
}

/**
 * Удаление аннотации
 */
function deleteAnnotation(annotationId) {
    // Запрашиваем подтверждение
    if (!confirm('Are you sure you want to delete this annotation?')) {
        return;
    }

    // Отправляем DELETE запрос
    fetch(`/api/annotations/${annotationId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Удаляем регион из wavesurfer
        if (annotationRegions[annotationId]) {
            try {
                annotationRegions[annotationId].remove();
            } catch (e) {
                // Регион уже удален
            }
            delete annotationRegions[annotationId];
        }

        // Обновляем список
        loadAnnotations();

        // Отправляем событие об удалении
        document.dispatchEvent(new CustomEvent('annotationDeleted', { detail: { id: annotationId } }));
    })
    .catch(error => {
        console.error('Ошибка удаления аннотации:', error);
        alert('Ошибка при удалении аннотации: ' + error.message);
    });
}

/**
 * Синхронизация с wavesurfer regions
 */
function syncWithWavesurferRegions() {
    if (!wavesurfer) {
        return;
    }

    // Очищаем старые регионы аннотаций
    Object.keys(annotationRegions).forEach(annotationId => {
        try {
            annotationRegions[annotationId].remove();
        } catch (e) {
            // Регион уже удален
        }
    });
    annotationRegions = {};

    // Создаем регионы для всех аннотаций
    const regionsPlugin = getAnnotationRegionsPlugin();
    if (!regionsPlugin || typeof regionsPlugin.addRegion !== 'function') {
        return;
    }

    annotations.forEach(annotation => {
        const regionId = `annotation-${annotation.id}`;
        const region = regionsPlugin.addRegion({
            id: regionId,
            start: annotation.start_time,
            end: annotation.end_time,
            color: getAnnotationColor(annotation),
            drag: false,
            resize: false,
        });

        lockAnnotationRegion(region);

        annotationRegions[annotation.id] = region;
    });
}

/**
 * Обновление счетчика аннотаций
 */
function updateAnnotationsCount() {
    const countElement = document.getElementById('annotations-count');
    if (countElement) {
        const count = annotations.length;
        countElement.textContent = `${count} annotation${count !== 1 ? 's' : ''}`;
    }
}

/**
 * Экранирование HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Экспорт аннотаций в JSON
 */
function exportAnnotations() {
    if (!annotationListCurrentAudioFileId) {
        console.warn('Audio file ID не установлен');
        alert('No audio file selected');
        return;
    }

    // Формируем URL для экспорта
    const exportUrl = `/api/audio/${annotationListCurrentAudioFileId}/export?format=json`;

    // Создаем временную ссылку для скачивания
    const link = document.createElement('a');
    link.href = exportUrl;
    link.download = 'annotations.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', () => {
    initAnnotationList();

    // Обработчик кнопки Export
    const exportBtn = document.getElementById('export-annotations');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportAnnotations);
    }
});

