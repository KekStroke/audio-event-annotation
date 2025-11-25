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
let currentlyLoadingAudioId = null;
let lastLoadedAudioId = null;

/**
 * Поиск доступного плагина wavesurfer независимо от пространства имён.
 */
function resolveWaveSurferPlugin(...getters) {
  if (typeof WaveSurfer === "undefined") {
    console.warn("WaveSurfer не загружен");
    return null;
  }

  for (const getter of getters) {
    try {
      const pluginFactory = getter();
      if (pluginFactory && typeof pluginFactory.create === "function") {
        return pluginFactory;
      }
    } catch (error) {
      // Игнорируем ошибку и пробуем следующий кандидат
    }
  }

  return null;
}

/**
 * Создание списка плагинов с учётом их доступности.
 */
function buildWaveSurferPlugins() {
  const plugins = [];

  const timelineFactory = resolveWaveSurferPlugin(
    () => WaveSurfer.timeline,
    () => WaveSurfer.Timeline,
    () => WaveSurfer.plugins && WaveSurfer.plugins.timeline,
    () => WaveSurfer.plugins && WaveSurfer.plugins.Timeline,
    () => window.WaveSurferTimeline
  );
  if (timelineFactory) {
    plugins.push(
      timelineFactory.create({
        container: "#waveform-timeline",
        height: 20,
      })
    );
  } else {
    console.warn("WaveSurfer timeline plugin недоступен, таймлайн отключён.");
  }

  const regionsFactory = resolveWaveSurferPlugin(
    () => WaveSurfer.regions,
    () => WaveSurfer.Regions,
    () => WaveSurfer.plugins && WaveSurfer.plugins.regions,
    () => WaveSurfer.plugins && WaveSurfer.plugins.Regions,
    () => window.WaveSurferRegions
  );
  if (regionsFactory) {
    plugins.push(
      regionsFactory.create({
        // Из документации: dragSelection должен быть объектом, а не boolean
        // https://wavesurfer.xyz/example/regions/
        dragSelection: {
          slop: 5,  // Чувствительность drag selection в пикселях
          color: 'rgba(100, 150, 255, 0.3)'  // Голубой полупрозрачный для новых выделений
        }
      })
    );
  } else {
    console.warn(
      "WaveSurfer regions plugin недоступен, выделение областей отключено."
    );
  }

  const minimapFactory = resolveWaveSurferPlugin(
    () => WaveSurfer.minimap,
    () => WaveSurfer.Minimap,
    () => WaveSurfer.plugins && WaveSurfer.plugins.minimap,
    () => WaveSurfer.plugins && WaveSurfer.plugins.Minimap,
    () => window.WaveSurferMinimap
  );
  if (minimapFactory) {
    plugins.push(
      minimapFactory.create({
        container: "#waveform-minimap",
        height: 50,
      })
    );
  } else {
    console.warn("WaveSurfer minimap plugin недоступен, миникарта отключена.");
  }

  // Spectrogram Plugin (Conditional)
  const showSpectrogram = window.appSettings ? window.appSettings.get('showMainSpectrogram') : false;
  const spectrogramHeight = window.appSettings ? window.appSettings.get('mainSpectrogramHeight') : 256;
  const showLabels = window.appSettings ? window.appSettings.get('showSpectrogramLabels') : true;

  if (showSpectrogram) {
    const spectrogramFactory = resolveWaveSurferPlugin(
      () => WaveSurfer.spectrogram,
      () => WaveSurfer.Spectrogram,
      () => WaveSurfer.plugins && WaveSurfer.plugins.spectrogram,
      () => WaveSurfer.plugins && WaveSurfer.plugins.Spectrogram,
      () => window.WaveSurferSpectrogram
    );
    
    if (spectrogramFactory) {
      plugins.push(
        spectrogramFactory.create({
          container: "#waveform", // Render into the same container
          labels: showLabels,
          height: spectrogramHeight,
          colorMap: 'roseus',
          splitChannels: false,
          scale: 'linear',
          frequencyMin: 0,
          fftSamples: 1024,
          labelsBackground: 'rgba(0, 0, 0, 0.7)',
          labelsColor: '#ffffff',
          labelsHzColor: '#ffffff'
        })
      );
    }
  }

  return plugins;
}

/**
 * Уведомление фронтенда о готовности wavesurfer.
 */
function notifyWavesurferReady() {
  document.dispatchEvent(
    new CustomEvent("wavesurferReady", {
      detail: { wavesurfer: wavesurfer },
    })
  );
}

/**
 * Уведомление фронтенда о готовности плагина regions.
 */
function notifyRegionsPluginReady() {
  const plugin = getWaveSurferRegionsPlugin();
  if (!plugin) {
    return;
  }
  document.dispatchEvent(
    new CustomEvent("wavesurferRegionsReady", { detail: plugin })
  );
}

/**
 * Кэширование активных плагинов WaveSurfer.
 */
/**
 * Получение экземпляра плагина regions.
 */
function getWaveSurferRegionsPlugin() {
  if (!wavesurfer || typeof wavesurfer.getActivePlugins !== "function") {
    return null;
  }

  const active = wavesurfer.getActivePlugins();

  if (Array.isArray(active)) {
    return active.find((plugin) => {
      if (!plugin) return false;
      return (
        plugin.constructor?.name === "RegionsPlugin" ||
        plugin.constructor?.name === "Regions" ||
        typeof plugin.addRegion === "function" ||
        typeof plugin.enableDragSelection === "function"
      );
    }) || null;
  }

  return (active && active.regions) || null;
}

window.getWaveSurferRegionsPlugin = getWaveSurferRegionsPlugin;

function ensureWaveSurferInitialized() {
  if (wavesurfer) {
    return wavesurfer;
  }
  initWaveSurfer(null);
  return wavesurfer;
}

/**
 * Резюм AudioContext (не используется - WaveSurfer v7 по умолчанию использует HTML5 audio)
 * Оставлено для совместимости
 */
function resumeAudioContext() {
  // Не используется в текущей конфигурации
}

// Флаг для предотвращения рекурсии при обновлении регионов
let isAdjustingRegion = false;

/**
 * Инициализация wavesurfer
 */
function initWaveSurfer(audioUrl) {
  // Уничтожаем предыдущий instance если есть
  if (wavesurfer) {
    wavesurfer.destroy();
  }

  currentlyLoadingAudioId = null;
  lastLoadedAudioId = null;
  isAdjustingRegion = false;

  // Создаём новый instance wavesurfer
  // WaveSurfer v7 по умолчанию использует HTML5 audio (не AudioContext)
  // Не передаем собственный media элемент, чтобы события работали правильно
  wavesurfer = WaveSurfer.create({
    container: "#waveform",
    waveColor: "#4a9eff",
    progressColor: "#6bb0ff",
    cursorColor: "#ffffff",
    barWidth: 2,
    barGap: 1,
    barRadius: 3,
    responsive: true,
    height: 200,
    normalize: true,
    interact: true, // Включаем интерактивность для перемотки
    plugins: buildWaveSurferPlugins(),
  });

  // Expose globally for other modules
  window.wavesurfer = wavesurfer;

  notifyWavesurferReady();

  // Загружаем аудио файл
  if (audioUrl) {
    wavesurfer.load(audioUrl);
  }

  // Обработчики событий
  setupAudioEventHandlers();

  return wavesurfer;
}

/**
 * Настройка обработчиков событий для аудио плеера
 */
function setupAudioEventHandlers() {
  if (!wavesurfer) {
    return;
  }

  // Событие play
  wavesurfer.on("play", () => {
    updatePlayPauseButtons(true);
  });

  // Событие pause
  wavesurfer.on("pause", () => {
    updatePlayPauseButtons(false);
  });

  // Событие seek (перемотка)
  wavesurfer.on("seek", (progress) => {
    updateTimeDisplay();
  });

  // Событие timeupdate для обновления времени
  wavesurfer.on("timeupdate", (currentTime) => {
    updateTimeDisplay();
  });

  // Событие ready (аудио загружено)
  wavesurfer.on("ready", () => {
    notifyRegionsPluginReady();
    updateTimeDisplay();
    updateZoomDisplay();
    hideLoadingIndicator();
    setupRegionOverlapPrevention();
  });

  // Событие decode (альтернативное для Web Audio API backend)
  wavesurfer.on("decode", () => {
    notifyRegionsPluginReady();
    setupRegionOverlapPrevention();
  });

  // Обработчики для кнопок Zoom не нужны здесь
  // Они устанавливаются в DOMContentLoaded для ленивой инициализации
}

/**
 * Настройка обработчиков для предотвращения наложения регионов
 */
function setupRegionOverlapPrevention() {
  const regionsPlugin = getWaveSurferRegionsPlugin();
  if (!regionsPlugin) {
    return;
  }

  // Проверяем, не подписывались ли мы уже на эти события
  if (regionsPlugin._overlapPreventionAttached) {
    return;
  }
  regionsPlugin._overlapPreventionAttached = true;

  // Событие region-created (регион создан)
  regionsPlugin.on('region-created', (region) => {
    // Предотвращаем рекурсию
    if (isAdjustingRegion) {
      return;
    }

    // Устанавливаем флаг
    isAdjustingRegion = true;

    try {
      // Проверяем и корректируем границы региона
      const isValid = adjustRegionBounds(region);

      // Если регион слишком мал после коррекции - удаляем его
      if (!isValid && region.remove) {
        region.remove();
      }
    } finally {
      // Сбрасываем флаг
      isAdjustingRegion = false;
    }
  });

  // Событие region-updated (регион изменяется во время drag/resize)
  regionsPlugin.on('region-updated', (region) => {
    // Предотвращаем рекурсию
    if (isAdjustingRegion) {
      return;
    }

    // Устанавливаем флаг
    isAdjustingRegion = true;

    try {
      // Динамически корректируем границы во время изменения
      const isValid = adjustRegionBounds(region);

      // Если регион слишком мал после коррекции - удаляем его
      if (!isValid && region.remove) {
        region.remove();
      }
    } finally {
      // Сбрасываем флаг
      isAdjustingRegion = false;
    }
  });
}

/**
 * Проверка пересечения двух регионов
 * @param {number} start1 - Начало первого региона
 * @param {number} end1 - Конец первого региона
 * @param {number} start2 - Начало второго региона
 * @param {number} end2 - Конец второго региона
 * @returns {boolean} - true если регионы пересекаются
 */
function checkRegionOverlap(start1, end1, start2, end2) {
  return end1 > start2 && start1 < end2;
}

/**
 * Коррекция границ региона чтобы избежать пересечений
 * @param {Object} region - Регион для коррекции
 * @returns {boolean} - true если регион валиден после коррекции
 */
function adjustRegionBounds(region) {
  const MIN_REGION_SIZE = 1.0; // Минимальный размер региона в секундах
  const regionsPlugin = getWaveSurferRegionsPlugin();

  if (!regionsPlugin || !region) {
    return true;
  }

  const audioDuration =
    wavesurfer && typeof wavesurfer.getDuration === 'function'
      ? wavesurfer.getDuration()
      : Number.POSITIVE_INFINITY;

  // Получаем все существующие регионы кроме текущего
  const allRegions = regionsPlugin.getRegions ? regionsPlugin.getRegions() : [];
  const existingRegions = allRegions.filter((r) => r.id !== region.id);
  const sortedRegions = existingRegions.slice().sort((a, b) => a.start - b.start);

  let adjustedStart = region.start;
  let adjustedEnd = region.end;

  // Проверяем пересечения со всеми существующими регионами
  for (const existingRegion of sortedRegions) {
    if (checkRegionOverlap(adjustedStart, adjustedEnd, existingRegion.start, existingRegion.end)) {
      // Есть пересечение - корректируем границы
      if (adjustedStart < existingRegion.start) {
        // Обрезаем конец до начала существующего
        adjustedEnd = Math.min(adjustedEnd, existingRegion.start);
      } else if (adjustedStart < existingRegion.end) {
        // Сдвигаем начало к концу существующего
        adjustedStart = existingRegion.end;
      }
    }
  }

  // Находим ближайшие регионы по соседству после коррекции
  const previousRegion = [...sortedRegions].reverse().find((r) => r.end <= adjustedStart) || null;
  const nextRegion = sortedRegions.find((r) => r.start >= adjustedEnd) || null;
  const minAllowedStart = previousRegion ? previousRegion.end : 0;
  const maxAllowedEnd = nextRegion ? nextRegion.start : audioDuration;

  adjustedStart = Math.max(adjustedStart, minAllowedStart);
  adjustedEnd = Math.min(adjustedEnd, maxAllowedEnd);

  let adjustedDuration = adjustedEnd - adjustedStart;

  if (adjustedDuration < MIN_REGION_SIZE) {
    let remaining = MIN_REGION_SIZE - adjustedDuration;
    const availableBefore = adjustedStart - minAllowedStart;
    const availableAfter = maxAllowedEnd - adjustedEnd;

    // Пытаемся расширить регион вперёд
    const extendAfter = Math.min(availableAfter, remaining);
    if (extendAfter > 0) {
      adjustedEnd += extendAfter;
      remaining -= extendAfter;
    }

    // Если места впереди не хватило - расширяем назад
    if (remaining > 0) {
      const extendBefore = Math.min(availableBefore, remaining);
      if (extendBefore > 0) {
        adjustedStart -= extendBefore;
        remaining -= extendBefore;
      }
    }

    adjustedDuration = adjustedEnd - adjustedStart;

    if (adjustedDuration < MIN_REGION_SIZE - 1e-6) {
      return false; // Регион слишком мал, нужно удалить
    }
  }

  // Обновляем границы если они изменились
  if (adjustedStart !== region.start || adjustedEnd !== region.end) {
    // Используем setOptions для обновления границ (WaveSurfer v7)
    if (typeof region.setOptions === 'function') {
      region.setOptions({ start: adjustedStart, end: adjustedEnd });
    } else {
      // Fallback: напрямую изменяем свойства
      region.start = adjustedStart;
      region.end = adjustedEnd;

      // Попытка вызвать update если метод существует
      if (typeof region.update === 'function') {
        region.update({ start: adjustedStart, end: adjustedEnd });
      }

      // Попытка вызвать render для перерисовки
      if (typeof region.render === 'function') {
        region.render();
      }
    }
  }

  return true; // Регион валиден
}

/**
 * Обновление состояния кнопки Play/Pause
 */
function updatePlayPauseButtons(isPlaying) {
  const playPauseIcon = document.getElementById('play-pause-icon');
  const playPauseText = document.getElementById('play-pause-text');

  if (playPauseIcon) {
    playPauseIcon.textContent = isPlaying ? '⏸' : '▶';
  }

  if (playPauseText) {
    playPauseText.textContent = isPlaying ? 'Pause' : 'Play';
  }
}

/**
 * Обновление отображения времени
 */
function updateTimeDisplay() {
  if (!wavesurfer) return;

  const timeDisplay = document.getElementById("time-display");
  if (!timeDisplay) return;

  const currentTime = wavesurfer.getCurrentTime();
  const duration = wavesurfer.getDuration();

  if (duration) {
    const currentFormatted = formatTime(currentTime);
    const durationFormatted = formatTime(duration);
    timeDisplay.textContent = `${currentFormatted} / ${durationFormatted}`;
  } else {
    timeDisplay.textContent = "00:00 / 00:00";
  }
}

/**
 * Форматирование времени в формат MM:SS
 */
function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return "00:00";

  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

/**
 * Показать индикатор загрузки
 */
function showLoadingIndicator() {
  const loadingEl = document.getElementById('waveform-loading');
  const waveformEl = document.getElementById('waveform');
  const timelineEl = document.getElementById('waveform-timeline');
  const minimapEl = document.getElementById('waveform-minimap');

  if (loadingEl) {
    loadingEl.style.display = 'block';
  }

  // Hide waveform containers during loading to prevent overlap
  if (waveformEl) {
    waveformEl.style.opacity = '0';
    waveformEl.style.visibility = 'hidden';
  }
  if (timelineEl) {
    timelineEl.style.opacity = '0';
    timelineEl.style.visibility = 'hidden';
  }
  if (minimapEl) {
    minimapEl.style.opacity = '0';
    minimapEl.style.visibility = 'hidden';
  }
}

/**
 * Скрыть индикатор загрузки
 */
function hideLoadingIndicator() {
  const loadingEl = document.getElementById('waveform-loading');
  const waveformEl = document.getElementById('waveform');
  const timelineEl = document.getElementById('waveform-timeline');
  const minimapEl = document.getElementById('waveform-minimap');

  if (loadingEl) {
    loadingEl.style.display = 'none';
  }

  // Show waveform containers when loading is complete
  if (waveformEl) {
    waveformEl.style.opacity = '1';
    waveformEl.style.visibility = 'visible';
  }
  if (timelineEl) {
    timelineEl.style.opacity = '1';
    timelineEl.style.visibility = 'visible';
  }
  if (minimapEl) {
    minimapEl.style.opacity = '1';
    minimapEl.style.visibility = 'visible';
  }
}

/**
 * Загрузка аудио файла по ID в wavesurfer
 */
function loadAudioFile(audioFileId) {
  if (!audioFileId || !wavesurfer) {
    return;
  }

  if (currentlyLoadingAudioId === audioFileId || lastLoadedAudioId === audioFileId) {
    return;
  }

  currentlyLoadingAudioId = audioFileId;
  showLoadingIndicator();

  // Очищаем все регионы перед загрузкой нового файла
  clearRegions();

  const audioUrl = `/api/audio/${audioFileId}/stream`;

  const loadPromise = wavesurfer.load(audioUrl);
  if (loadPromise && typeof loadPromise.then === "function") {
    loadPromise
      .then(() => {
        lastLoadedAudioId = audioFileId;
        currentlyLoadingAudioId = null;
        hideLoadingIndicator();

        // Уведомляем слушателей что плагин готов
        notifyRegionsPluginReady();

        // Настраиваем предотвращение наложения регионов
        setupRegionOverlapPrevention();

        // Активируем drag selection
        const regionsPlugin = getWaveSurferRegionsPlugin();
        if (regionsPlugin && typeof regionsPlugin.enableDragSelection === 'function') {
          regionsPlugin.enableDragSelection({
            color: 'rgba(74, 158, 255, 0.2)',
          });
        }
      })
      .catch((error) => {
        console.error('Ошибка загрузки аудио:', error);
        if (currentlyLoadingAudioId === audioFileId) {
          currentlyLoadingAudioId = null;
        }
        hideLoadingIndicator();
      });
  } else {
    lastLoadedAudioId = audioFileId;
    currentlyLoadingAudioId = null;
    hideLoadingIndicator();
  }
}

/**
 * Zoom In x2
 */
function zoomIn() {
  if (!wavesurfer) return;

  if (currentZoom === 0) {
    // Если zoom=0 (весь файл), начинаем с разумного значения
    currentZoom = 50;
  } else {
    // Увеличиваем в 2 раза
    currentZoom = Math.min(currentZoom * 2, 20000);
  }
  wavesurfer.zoom(currentZoom);
  updateZoomDisplay();
}

/**
 * Zoom Out x2
 */
function zoomOut() {
  if (!wavesurfer) return;

  // Уменьшаем в 2 раза
  currentZoom = currentZoom / 2;
  // При малых значениях (<10) сбрасываем в 0
  if (currentZoom < 10) {
    currentZoom = 0;
  }
  wavesurfer.zoom(currentZoom);
  updateZoomDisplay();
}

/**
 * Zoom to Duration - масштабирование чтобы показать заданную длительность
 */
function zoomToDuration(durationSeconds) {
  if (!wavesurfer) return;

  // Валидация
  const duration = parseFloat(durationSeconds);
  if (isNaN(duration) || duration <= 0) {
    showZoomError('Длительность должна быть положительным числом');
    return;
  }

  if (duration > 3600) {
    showZoomError('Длительность не может превышать 3600 секунд (1 час)');
    return;
  }

  // Получаем ширину контейнера waveform
  const waveformContainer = document.getElementById('waveform');
  if (!waveformContainer) return;

  const containerWidth = waveformContainer.offsetWidth;

  // Вычисляем zoom: пиксели/сек = ширина_контейнера / длительность
  currentZoom = containerWidth / duration;

  wavesurfer.zoom(currentZoom);
  updateZoomDisplay();
  clearZoomError();
}

/**
 * Обновление отображения текущего масштаба
 */
function updateZoomDisplay() {
  const displayElement = document.getElementById('current-zoom-display');
  if (!displayElement || !wavesurfer) return;

  const waveformContainer = document.getElementById('waveform');
  if (!waveformContainer) return;

  const containerWidth = waveformContainer.offsetWidth;
  let visibleDuration;

  if (currentZoom === 0) {
    // При zoom=0 видна вся длительность
    visibleDuration = wavesurfer.getDuration();
  } else {
    // При zoom>0: видимая_длительность = ширина_контейнера / zoom
    visibleDuration = containerWidth / currentZoom;
  }

  // Форматируем время
  displayElement.textContent = formatDuration(visibleDuration);
}

/**
 * Форматирование длительности в читаемый вид
 */
function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '0s';

  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
}

/**
 * Показать сообщение об ошибке zoom
 */
function showZoomError(message) {
  // Создаем или обновляем элемент ошибки
  let errorElement = document.querySelector('.zoom-error-message');
  if (!errorElement) {
    errorElement = document.createElement('div');
    errorElement.className = 'error-message zoom-error-message';
    errorElement.style.cssText = 'position: absolute; top: 50px; left: 50%; transform: translateX(-50%); z-index: 1000; padding: 0.75rem 1rem; background-color: #ff4444; color: white; border-radius: 4px;';

    const workspaceHeader = document.querySelector('.workspace-header');
    if (workspaceHeader) {
      workspaceHeader.appendChild(errorElement);
    }
  }

  errorElement.textContent = message;
  errorElement.style.display = 'block';

  // Автоматически скрыть через 3 секунды
  setTimeout(() => {
    if (errorElement) {
      errorElement.style.display = 'none';
    }
  }, 3000);
}

/**
 * Очистить сообщение об ошибке zoom
 */
function clearZoomError() {
  const errorElement = document.querySelector('.zoom-error-message');
  if (errorElement) {
    errorElement.style.display = 'none';
  }
}

/**
 * Создание региона
 */
function createRegion(start, end, color = "#ff6b6b") {
  if (!wavesurfer) return null;

  const regionsPlugin = getWaveSurferRegionsPlugin();
  const regionConfig = {
    start: start,
    end: end,
    color: color,
    drag: true,
    resize: true,
  };

  if (regionsPlugin && typeof regionsPlugin.addRegion === "function") {
    return regionsPlugin.addRegion(regionConfig);
  }

  if (typeof wavesurfer.addRegion === "function") {
    return wavesurfer.addRegion(regionConfig);
  }

  console.warn("Regions plugin недоступен — создать регион невозможно.");
  return null;
}

/**
 * Удаление всех регионов
 */
function clearRegions() {
  if (!wavesurfer) return;

  const regionsPlugin = getWaveSurferRegionsPlugin();
  if (regionsPlugin && typeof regionsPlugin.clearRegions === "function") {
    regionsPlugin.clearRegions();
    return;
  }

  if (typeof wavesurfer.clearRegions === "function") {
    wavesurfer.clearRegions();
    return;
  }

  console.warn("Regions plugin недоступен — очистка регионов пропущена.");
}

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener("DOMContentLoaded", () => {
  // Обработчик выбора аудио файла
  document.addEventListener("audioFileSelected", (event) => {
    const audioFileId = event?.detail?.id;
    if (!audioFileId) {
      return;
    }

    // Если WaveSurfer уже инициализирован, загружаем
    if (wavesurfer) {
      loadAudioFile(audioFileId);
    } else {
      // Если WaveSurfer еще не инициализирован, сохраняем ID
      window.pendingAudioFileId = audioFileId;
    }
  });

  // Обработчик для объединенной кнопки Play/Pause
  const playPauseBtn = document.getElementById('play-pause-btn');
  if (playPauseBtn) {
    playPauseBtn.addEventListener('click', () => {
      // Инициализируем WaveSurfer при первом взаимодействии
      ensureWaveSurferInitialized();

      // Загружаем ожидающий файл, если есть
      if (window.pendingAudioFileId && !lastLoadedAudioId) {
        loadAudioFile(window.pendingAudioFileId);
        window.pendingAudioFileId = null;
      }

      // Переключаем play/pause
      if (wavesurfer) {
        if (wavesurfer.isPlaying()) {
          wavesurfer.pause();
        } else {
          wavesurfer.play();
        }
      }
    });
  }

  const stopBtn = document.querySelector('[data-action="stop"]');
  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      if (wavesurfer) {
        wavesurfer.stop();
      }
    });
  }

  // Обработчик изменения playback speed
  const playbackSpeedInput = document.getElementById('playback-speed');
  const playbackSpeedValue = document.getElementById('playback-speed-value');
  if (playbackSpeedInput) {
    playbackSpeedInput.addEventListener('input', (e) => {
      const speed = parseFloat(e.target.value);
      if (playbackSpeedValue) {
        playbackSpeedValue.textContent = speed.toFixed(1);
      }
      if (wavesurfer && typeof wavesurfer.setPlaybackRate === 'function') {
        wavesurfer.setPlaybackRate(speed);
      }
    });
  }

  // Обработчик изменения volume
  const volumeInput = document.getElementById('volume');
  const volumeValue = document.getElementById('volume-value');
  if (volumeInput) {
    volumeInput.addEventListener('input', (e) => {
      const volume = parseInt(e.target.value);
      if (volumeValue) {
        volumeValue.textContent = volume;
      }
      if (wavesurfer && typeof wavesurfer.setVolume === 'function') {
        wavesurfer.setVolume(volume / 100); // setVolume принимает значения от 0 до 1
      }
    });
  }

  // Обработчики для кнопок Zoom с ленивой инициализацией
  const zoomInBtn = document.getElementById("zoom-in");
  const zoomOutBtn = document.getElementById("zoom-out");

  if (zoomInBtn) {
    zoomInBtn.addEventListener("click", () => {
      ensureWaveSurferInitialized();
      zoomIn();
    });
  }

  if (zoomOutBtn) {
    zoomOutBtn.addEventListener("click", () => {
      ensureWaveSurferInitialized();
      zoomOut();
    });
  }

  // Обработчик для кнопки Zoom to Duration
  const zoomToDurationBtn = document.getElementById("zoom-to-duration-btn");
  const zoomDurationInput = document.getElementById("zoom-duration-input");

  if (zoomToDurationBtn && zoomDurationInput) {
    zoomToDurationBtn.addEventListener("click", () => {
      ensureWaveSurferInitialized();
      const duration = zoomDurationInput.value;
      if (duration) {
        zoomToDuration(duration);
      }
    });

    // Обработчик Enter в поле ввода
    zoomDurationInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        ensureWaveSurferInitialized();
        const duration = zoomDurationInput.value;
        if (duration) {
          zoomToDuration(duration);
        }
      }
    });
  }

  // Listen for settings changes to reload if needed
  document.addEventListener('settingsChanged', (e) => {
    // If showMainSpectrogram changed, we need to re-init wavesurfer
    // But only if we have a loaded file, otherwise next load will pick it up
    if (wavesurfer && lastLoadedAudioId) {
       const currentId = lastLoadedAudioId;
       // Re-init to pick up new plugins (this destroys the old instance)
       initWaveSurfer(null);
       // Load the file again
       loadAudioFile(currentId);
    }
  });
});
