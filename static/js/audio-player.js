/**
 * Audio Player с использованием wavesurfer.js
 * 
 * Функционал:
 * - Инициализация wavesurfer с waveform визуализацией
 * - Воспроизведение и пауза
 * - Отображение текущего времени
 * - Перемотка кликом по waveform
 * - Регионы для выделения интервалов
 * - Zoom in/out для waveform
 */

// Глобальная переменная для wavesurfer instance
let wavesurfer = null;
let currentZoom = 0;

/**
 * Инициализация wavesurfer
 */
function initWaveSurfer(audioUrl) {
    // Уничтожаем предыдущий instance если есть
    if (wavesurfer) {
        wavesurfer.destroy();
    }

    // Создаём новый instance wavesurfer
    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: '#4a9eff',
        progressColor: '#6bb0ff',
        cursorColor: '#ffffff',
        barWidth: 2,
        barRadius: 3,
        responsive: true,
        height: 200,
        normalize: true,
        interact: true,  // Включаем интерактивность для перемотки
        plugins: [
            WaveSurfer.timeline.create({
                container: '#waveform-timeline',
                height: 20,
            }),
            WaveSurfer.regions.create({
                dragSelection: true,
            }),
            WaveSurfer.minimap.create({
                container: '#waveform-minimap',
                height: 50,
            }),
        ],
    });

    // Загружаем аудио файл
    if (audioUrl) {
        wavesurfer.load(audioUrl);
    }

    // Обработчики событий
    setupEventHandlers();

    return wavesurfer;
}

/**
 * Настройка обработчиков событий
 */
function setupEventHandlers() {
    if (!wavesurfer) return;

    // Событие play
    wavesurfer.on('play', () => {
        updatePlayPauseButtons(true);
    });

    // Событие pause
    wavesurfer.on('pause', () => {
        updatePlayPauseButtons(false);
    });

    // Событие seek (перемотка)
    wavesurfer.on('seek', (progress) => {
        updateTimeDisplay();
    });

    // Событие timeupdate для обновления времени
    wavesurfer.on('timeupdate', (currentTime) => {
        updateTimeDisplay();
    });

    // Событие ready (аудио загружено)
    wavesurfer.on('ready', () => {
        updateTimeDisplay();
    });

    // Событие region-created (регион создан)
    wavesurfer.on('region-created', (region) => {
        console.log('Region created:', region);
    });

    // Обработчики для кнопок Play/Pause
    const playBtn = document.querySelector('[data-action="play"]');
    const pauseBtn = document.querySelector('[data-action="pause"]');

    if (playBtn) {
        playBtn.addEventListener('click', () => {
            if (wavesurfer) {
                wavesurfer.play();
            }
        });
    }

    if (pauseBtn) {
        pauseBtn.addEventListener('click', () => {
            if (wavesurfer) {
                wavesurfer.pause();
            }
        });
    }

    // Обработчики для кнопок Zoom
    const zoomInBtn = document.getElementById('zoom-in');
    const zoomOutBtn = document.getElementById('zoom-out');

    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', () => {
            zoomIn();
        });
    }

    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', () => {
            zoomOut();
        });
    }
}

/**
 * Обновление состояния кнопок Play/Pause
 */
function updatePlayPauseButtons(isPlaying) {
    const playBtn = document.querySelector('[data-action="play"]');
    const pauseBtn = document.querySelector('[data-action="pause"]');

    if (playBtn) {
        playBtn.disabled = isPlaying;
    }
    if (pauseBtn) {
        pauseBtn.disabled = !isPlaying;
    }
}

/**
 * Обновление отображения времени
 */
function updateTimeDisplay() {
    if (!wavesurfer) return;

    const timeDisplay = document.getElementById('time-display');
    if (!timeDisplay) return;

    const currentTime = wavesurfer.getCurrentTime();
    const duration = wavesurfer.getDuration();

    if (duration) {
        const currentFormatted = formatTime(currentTime);
        const durationFormatted = formatTime(duration);
        timeDisplay.textContent = `${currentFormatted} / ${durationFormatted}`;
    } else {
        timeDisplay.textContent = '00:00 / 00:00';
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
 * Zoom In
 */
function zoomIn() {
    if (!wavesurfer) return;

    currentZoom = Math.min(currentZoom + 50, 2000);
    wavesurfer.zoom(currentZoom);
}

/**
 * Zoom Out
 */
function zoomOut() {
    if (!wavesurfer) return;

    currentZoom = Math.max(currentZoom - 50, 0);
    wavesurfer.zoom(currentZoom);
}

/**
 * Создание региона
 */
function createRegion(start, end, color = '#ff6b6b') {
    if (!wavesurfer) return null;

    const region = wavesurfer.addRegion({
        start: start,
        end: end,
        color: color,
        drag: true,
        resize: true,
    });

    return region;
}

/**
 * Удаление всех регионов
 */
function clearRegions() {
    if (!wavesurfer) return;

    wavesurfer.clearRegions();
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', () => {
    // Инициализируем wavesurfer с пустым контейнером
    // Аудио будет загружено позже при выборе файла
    initWaveSurfer(null);

    // Здесь можно добавить логику загрузки аудио файла
    // когда пользователь выберет файл из списка
});

