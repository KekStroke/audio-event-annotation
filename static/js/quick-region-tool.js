/**
 * Quick Region Tool - инструмент для быстрого создания регионов заданной длины
 * 
 * Функционал:
 * - Создание регионов заданной длины
 * - Автоматическое позиционирование после последнего региона
 * - Автоматическое выделение созданного региона
 * - Валидация длины региона
 * - Визуальное выделение активных регионов
 */

// Глобальные переменные
let quickRegionCurrentRegion = null;
let quickRegionButtonHandlersAttached = false;

/**
 * Получение плагина regions
 */
function getQuickRegionPlugin() {
    if (typeof window.getWaveSurferRegionsPlugin === 'function') {
        return window.getWaveSurferRegionsPlugin();
    }
    return null;
}

/**
 * Инициализация Quick Region Tool
 */
function initQuickRegionTool() {
    if (!wavesurfer) {
        console.warn('wavesurfer не инициализирован');
        return;
    }

    const regionsPlugin = getQuickRegionPlugin();
    if (!regionsPlugin) {
        console.warn('Regions plugin не готов');
        return;
    }

    setupQuickRegionHandlers();
    setupRegionSelectionHandlers();
}

/**
 * Настройка обработчиков кнопок
 */
function setupQuickRegionHandlers() {
    if (quickRegionButtonHandlersAttached) return;
    quickRegionButtonHandlersAttached = true;

    const createBtn = document.getElementById('create-quick-region-btn');
    const durationInput = document.getElementById('quick-region-duration');

    if (createBtn && durationInput) {
        createBtn.addEventListener('click', () => createQuickRegion());
        
        // Enter в поле ввода тоже создает регион
        durationInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                createQuickRegion();
            }
        });
    }
}

/**
 * Настройка обработчиков выделения регионов
 */
function setupRegionSelectionHandlers() {
    const regionsPlugin = getQuickRegionPlugin();
    if (!regionsPlugin) return;

    // При клике на регион - выделяем его
    regionsPlugin.on('region-clicked', (region) => {
        selectRegion(region);
    });

    // При создании региона через drag - выделяем его
    regionsPlugin.on('region-created', (region) => {
        selectRegion(region);
    });
}

/**
 * Создание быстрого региона
 */
function createQuickRegion() {
    const regionsPlugin = getQuickRegionPlugin();
    if (!regionsPlugin || !wavesurfer) {
        showQuickRegionError('WaveSurfer не готов');
        return;
    }

    const durationInput = document.getElementById('quick-region-duration');
    if (!durationInput) return;

    const duration = parseFloat(durationInput.value);
    const audioDuration = wavesurfer.getDuration();

    // Валидация
    if (isNaN(duration) || duration < 0.1) {
        showQuickRegionError('Duration must be at least 0.1 seconds');
        return;
    }

    if (duration > audioDuration) {
        showQuickRegionError('Duration cannot exceed audio duration');
        return;
    }

    // Находим позицию для нового региона (после самого правого)
    const regions = regionsPlugin.getRegions();
    let startPosition = 0;

    if (regions && regions.length > 0) {
        const rightmostEnd = Math.max(...regions.map(r => r.end));
        startPosition = rightmostEnd;
    }

    const endPosition = startPosition + duration;

    // Проверяем что регион помещается
    if (endPosition > audioDuration) {
        showQuickRegionError('Not enough space');
        return;
    }

    // Создаем регион
    const newRegion = regionsPlugin.addRegion({
        start: startPosition,
        end: endPosition,
        color: 'rgba(100, 150, 255, 0.3)',
        drag: true,
        resize: true
    });

    // Автоматически выделяем созданный регион
    selectRegion(newRegion);

    // Прокручиваем к региону
    wavesurfer.seekTo(startPosition / audioDuration);

    // Очищаем ошибку
    hideQuickRegionError();
}

/**
 * Выделение региона
 */
function selectRegion(region) {
    if (!region) return;

    // Снимаем выделение со всех регионов
    const regionsPlugin = getQuickRegionPlugin();
    if (regionsPlugin) {
        const allRegions = regionsPlugin.getRegions();
        if (allRegions) {
            allRegions.forEach(r => {
                if (r.element) {
                    r.element.classList.remove('region-selected');
                }
            });
        }
    }

    // Выделяем текущий регион
    if (region.element) {
        region.element.classList.add('region-selected');
    }

    quickRegionCurrentRegion = region;
}

/**
 * Показ сообщения об ошибке
 */
function showQuickRegionError(message) {
    const errorElement = document.getElementById('quick-region-error');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

/**
 * Скрытие сообщения об ошибке
 */
function hideQuickRegionError() {
    const errorElement = document.getElementById('quick-region-error');
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('wavesurferReady', () => {
        const regionsPlugin = getQuickRegionPlugin();
        if (regionsPlugin) {
            initQuickRegionTool();
        }
    }, { once: true });

    // Также слушаем событие готовности regions plugin
    document.addEventListener('wavesurferRegionsReady', () => {
        quickRegionButtonHandlersAttached = false;
        initQuickRegionTool();
    });
});
