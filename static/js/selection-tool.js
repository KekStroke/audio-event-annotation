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

document.addEventListener('wavesurferRegionsReady', () => {
    setupRegionHandlers();
});

/**
 * Инициализация Selection Tool
 */
function initSelectionTool() {
    if (!wavesurfer) {
        console.warn('wavesurfer не инициализирован');
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

    selectionToolRegionHandlersAttached = true;

    // Событие создания региона
    wavesurfer.on('region-created', (region) => {
        selectionToolCurrentRegion = region;
        updateRegionTimeDisplay(region);
        loadRegionSpectrogram(region);
    });

    // Событие обновления региона
    wavesurfer.on('region-updated', (region) => {
        selectionToolCurrentRegion = region;
        updateRegionTimeDisplay(region);
        loadRegionSpectrogram(region);
    });

    // Событие удаления региона
    wavesurfer.on('region-removed', () => {
        selectionToolCurrentRegion = null;
        clearRegionTimeDisplay();
        clearRegionSpectrogram();
    });

    // Событие клика по региону
    wavesurfer.on('region-clicked', (region) => {
        selectionToolCurrentRegion = region;
        updateRegionTimeDisplay(region);
    });
}

/**
 * Настройка обработчиков для кнопок
 */
function setupButtonHandlers() {
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

    // Останавливаем текущее воспроизведение
    wavesurfer.pause();

    // Переходим к началу региона
    wavesurfer.seekTo(selectionToolCurrentRegion.start / wavesurfer.getDuration());

    // Воспроизводим
    wavesurfer.play();

    // Останавливаем в конце региона
    const regionDuration = selectionToolCurrentRegion.end - selectionToolCurrentRegion.start;
    setTimeout(() => {
        if (wavesurfer.getCurrentTime() >= selectionToolCurrentRegion.end) {
            wavesurfer.pause();
            wavesurfer.seekTo(selectionToolCurrentRegion.end / wavesurfer.getDuration());
        }
    }, regionDuration * 1000);
}

/**
 * Очистка выделения
 */
function clearSelection() {
    if (!wavesurfer) return;

    const regionsPlugin = getSelectionRegionsPlugin();
    if (regionsPlugin && typeof regionsPlugin.clearRegions === 'function') {
        regionsPlugin.clearRegions();
    } else if (typeof wavesurfer.clearRegions === 'function') {
        wavesurfer.clearRegions();
    } else {
        console.warn('Невозможно очистить регионы: плагин regions отсутствует');
    }
    selectionToolCurrentRegion = null;
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
    // Ждём инициализации wavesurfer
    setTimeout(() => {
        if (typeof wavesurfer !== 'undefined' && wavesurfer) {
            initSelectionTool();
        } else {
            // Если wavesurfer ещё не загружен, ждём ещё
            const checkInterval = setInterval(() => {
                if (typeof wavesurfer !== 'undefined' && wavesurfer) {
                    initSelectionTool();
                    clearInterval(checkInterval);
                }
            }, 100);
        }
    }, 500);
});




