/**
 * Selection Tool для работы с выделением фрагментов аудио
 * 
 * Функционал:
 * - Отображение start/end времени выделенного региона
 * - Кнопка Play Selection для воспроизведения региона
 * - Кнопка Clear Selection для очистки выделения
 * - Отображение спектрограммы для выделенного региона
 * - Горячая клавиша Space для play/pause
 * - Zoom на выделенный регион
 */

// Глобальные переменные
let selectionToolCurrentRegion = null;
let selectionToolCurrentAudioFileId = null;
let spectrogramDebounceTimer = null;
let selectionToolRegionHandlersAttached = false;
let selectionToolButtonHandlersAttached = false;
let selectionToolKeyboardHandlersAttached = false;

function getSelectionRegionsPlugin() {
    if (typeof window.getWaveSurferRegionsPlugin === 'function') {
        return window.getWaveSurferRegionsPlugin();
    }
    return window.waveSurferRegionsPlugin || null;
}

// Подписываемся на выбор аудио файла
document.addEventListener('audioFileSelected', (event) => {
    const audioFileId = event?.detail?.id;
    if (audioFileId) {
        setCurrentAudioFileId(audioFileId);
    }
});

// Также берём текущий Audio File ID из глобальной переменной
function ensureAudioFileId() {
    if (!selectionToolCurrentAudioFileId && window.currentAudioFileId) {
        selectionToolCurrentAudioFileId = window.currentAudioFileId;
    }
}

document.addEventListener('wavesurferRegionsReady', () => {
    // Reset flag to allow re-attachment when regions plugin is ready
    selectionToolRegionHandlersAttached = false;
    initSelectionTool();
});

/**
 * Инициализация Selection Tool
 */
function initSelectionTool() {
    if (!wavesurfer) {
        console.warn('wavesurfer не инициализирован');
        return;
    }

    const regionsPlugin = getSelectionRegionsPlugin();
    if (!regionsPlugin) {
        console.warn('Regions plugin не готов, ждём события wavesurferRegionsReady');
        return;
    }

    // Обработчики событий regions
    setupRegionHandlers();

    // Обработчики для кнопок
    setupButtonHandlers();

    // Обработчик горячей клавиши Space
    setupKeyboardHandlers();
}

/**
 * Настройка обработчиков событий регионов
 */
function setupRegionHandlers() {
    if (!wavesurfer || selectionToolRegionHandlersAttached) return;

    const regionsPlugin = getSelectionRegionsPlugin();
    if (!regionsPlugin) {
        console.warn('Regions plugin не найден, обработчики не установлены');
        return;
    }

    selectionToolRegionHandlersAttached = true;

    // WaveSurfer v7: события на плагине regions
    // Событие создания региона
    regionsPlugin.on('region-created', (region) => {
        selectionToolCurrentRegion = region;
        updateRegionTimeDisplay(region);
        loadRegionSpectrogram(region);
    });

    // Событие обновления региона
    regionsPlugin.on('region-updated', (region) => {
        selectionToolCurrentRegion = region;
        updateRegionTimeDisplay(region);
        loadRegionSpectrogram(region);
    });

    // Событие клика по региону
    regionsPlugin.on('region-clicked', (region) => {
        selectionToolCurrentRegion = region;
        updateRegionTimeDisplay(region);
    });

    // Обработчик удаления региона - следим за всеми регионами
    regionsPlugin.on('region-removed', () => {
        // Проверяем, остались ли регионы
        const regions = regionsPlugin.getRegions();
        if (regions.length === 0) {
            selectionToolCurrentRegion = null;
            clearRegionTimeDisplay();
            clearRegionSpectrogram();
        }
    });
}

/**
 * Настройка обработчиков для кнопок
 */
function setupButtonHandlers() {
    if (selectionToolButtonHandlersAttached) return;
    selectionToolButtonHandlersAttached = true;

    // Кнопка Play Selection
    const playSelectionBtn = document.getElementById('play-selection');
    if (playSelectionBtn) {
        playSelectionBtn.addEventListener('click', playSelection);
    }

    // Кнопка Clear Selection
    const clearSelectionBtn = document.getElementById('clear-selection');
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', clearSelection);
    }

    // Кнопка Zoom to Region
    const zoomToRegionBtn = document.getElementById('zoom-to-region');
    if (zoomToRegionBtn) {
        zoomToRegionBtn.addEventListener('click', zoomToRegion);
    }
}

/**
 * Настройка обработчиков клавиатуры
 */
function setupKeyboardHandlers() {
    if (selectionToolKeyboardHandlersAttached) return;
    selectionToolKeyboardHandlersAttached = true;

    document.addEventListener('keydown', (event) => {
        // Space для play/pause (только если не в input/textarea)
        if (event.code === 'Space' || event.key === ' ') {
            const target = event.target;
            if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
                event.preventDefault();
                togglePlayPause();
            }
        }
    });
}

/**
 * Воспроизведение выделенного региона
 */
function playSelection() {
    if (!wavesurfer || !selectionToolCurrentRegion) {
        console.warn('Нет выделенного региона');
        return;
    }

    const regionEnd = selectionToolCurrentRegion.end;
    
    // Обработчик для остановки в конце региона
    const stopAtRegionEnd = () => {
        if (wavesurfer.getCurrentTime() >= regionEnd) {
            wavesurfer.pause();
            wavesurfer.seekTo(regionEnd / wavesurfer.getDuration());
            // Отписываемся от события
            wavesurfer.un('timeupdate', stopAtRegionEnd);
        }
    };

    // Останавливаем текущее воспроизведение
    wavesurfer.pause();

    // Переходим к началу региона
    wavesurfer.seekTo(selectionToolCurrentRegion.start / wavesurfer.getDuration());

    // Подписываемся на событие timeupdate
    wavesurfer.on('timeupdate', stopAtRegionEnd);

    // Воспроизводим
    wavesurfer.play();
}

/**
 * Очистка выделения (удаляет только текущий выделенный регион)
 */
function clearSelection() {
    if (!wavesurfer) return;

    const regionsPlugin = getSelectionRegionsPlugin();
    if (!regionsPlugin) {
        console.warn('Невозможно очистить регионы: плагин regions отсутствует');
        return;
    }

    // Удаляем только текущий выделенный регион
    if (selectionToolCurrentRegion && typeof selectionToolCurrentRegion.remove === 'function') {
        selectionToolCurrentRegion.remove();
        selectionToolCurrentRegion = null;
    }
    
    clearRegionTimeDisplay();
    clearRegionSpectrogram();
}

/**
 * Обновление отображения времени региона
 */
function updateRegionTimeDisplay(region) {
    const timeDisplay = document.getElementById('region-time');
    if (!timeDisplay) return;

    const startFormatted = formatTime(region.start);
    const endFormatted = formatTime(region.end);
    const duration = region.end - region.start;
    const durationFormatted = formatTime(duration);

    timeDisplay.textContent = `${startFormatted} - ${endFormatted} (${durationFormatted})`;
    timeDisplay.style.display = 'block';
}

/**
 * Очистка отображения времени региона
 */
function clearRegionTimeDisplay() {
    const timeDisplay = document.getElementById('region-time');
    if (timeDisplay) {
        timeDisplay.textContent = 'No selection';
        timeDisplay.style.display = 'none';
    }
}

/**
 * Загрузка спектрограммы для региона (с debounce)
 */
function loadRegionSpectrogram(region) {
    ensureAudioFileId();
    if (!selectionToolCurrentAudioFileId) {
        console.warn('Audio file ID не установлен');
        return;
    }

    // Debounce для избежания лишних запросов
    if (spectrogramDebounceTimer) {
        clearTimeout(spectrogramDebounceTimer);
    }

    spectrogramDebounceTimer = setTimeout(() => {
        const startTime = region.start;
        const endTime = region.end;

        // Формируем URL для получения спектрограммы
        const spectrogramUrl = `/api/audio/${selectionToolCurrentAudioFileId}/spectrogram?start_time=${startTime}&end_time=${endTime}&width=800&height=400`;

        // Загружаем спектрограмму
        fetch(spectrogramUrl)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.blob();
            })
            .then((blob) => {
                const imageUrl = URL.createObjectURL(blob);
                displayRegionSpectrogram(imageUrl);
            })
            .catch((error) => {
                console.error('Ошибка загрузки спектрограммы:', error);
            });
    }, 300);  // Debounce 300ms
}

/**
 * Отображение спектрограммы региона
 */
function displayRegionSpectrogram(imageUrl) {
    const spectrogramContainer = document.getElementById('region-spectrogram');
    if (!spectrogramContainer) return;

    // Очищаем предыдущее изображение
    spectrogramContainer.innerHTML = '';

    // Создаём элемент img
    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = 'Region spectrogram';
    img.style.width = '100%';
    img.style.height = 'auto';
    img.style.borderRadius = '4px';

    spectrogramContainer.appendChild(img);
    spectrogramContainer.style.display = 'block';
}

/**
 * Очистка спектрограммы региона
 */
function clearRegionSpectrogram() {
    const spectrogramContainer = document.getElementById('region-spectrogram');
    if (spectrogramContainer) {
        spectrogramContainer.innerHTML = '';
        spectrogramContainer.style.display = 'none';
    }
}

/**
 * Zoom на выделенный регион
 */
function zoomToRegion() {
    if (!wavesurfer || !selectionToolCurrentRegion) {
        console.warn('Нет выделенного региона для zoom');
        return;
    }

    const duration = wavesurfer.getDuration();
    const regionDuration = selectionToolCurrentRegion.end - selectionToolCurrentRegion.start;

    // Вычисляем zoom уровень для отображения региона
    // Целевая ширина региона в пикселях (например, 80% от ширины контейнера)
    const targetWidth = 800;  // Примерная ширина контейнера
    const samplesPerPixel = (regionDuration * wavesurfer.options.sampleRate) / targetWidth;

    // Устанавливаем zoom
    const zoomLevel = Math.max(1, Math.floor(samplesPerPixel));
    wavesurfer.zoom(zoomLevel);

    // Переходим к началу региона
    wavesurfer.seekTo(selectionToolCurrentRegion.start / duration);
}

/**
 * Переключение play/pause
 */
function togglePlayPause() {
    if (!wavesurfer) return;

    if (wavesurfer.isPlaying()) {
        wavesurfer.pause();
    } else {
        wavesurfer.play();
    }
}

/**
 * Форматирование времени в формат MM:SS
 */
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00';

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * Установка текущего Audio File ID
 */
function setCurrentAudioFileId(audioFileId) {
    selectionToolCurrentAudioFileId = audioFileId;
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', () => {
    // Подписываемся на событие wavesurferReady для правильной последовательности инициализации
    // Это избегает race condition с плагинами
    document.addEventListener('wavesurferReady', () => {
        // Пытаемся инициализировать - если regions plugin уже готов
        const regionsPlugin = getSelectionRegionsPlugin();
        if (regionsPlugin) {
            initSelectionTool();
        }
        // Если не готов, ждём события wavesurferRegionsReady (уже подписаны выше)
    }, { once: true });
});




