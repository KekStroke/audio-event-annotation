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
let waveSurferRegionsPlugin = null;

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
          slop: 5  // Чувствительность drag selection в пикселях
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
function cacheWaveSurferPlugins() {
  if (!wavesurfer || typeof wavesurfer.getActivePlugins !== "function") {
    waveSurferRegionsPlugin = null;
    window.waveSurferRegionsPlugin = null;
    return;
  }

  const active = wavesurfer.getActivePlugins();
  
  // Если это массив, ищем regions plugin по характерным методам
  if (Array.isArray(active)) {
    const regionsPlugin = active.find(p => 
      p && (
        p.constructor?.name === 'RegionsPlugin' ||
        p.constructor?.name === 'Regions' ||
        typeof p.addRegion === 'function' ||
        typeof p.enableDragSelection === 'function'
      )
    );
    
    waveSurferRegionsPlugin = regionsPlugin || null;
  } else {
    // Если это объект (старый формат)
    waveSurferRegionsPlugin = (active && active.regions) || null;
  }
  
  window.waveSurferRegionsPlugin = waveSurferRegionsPlugin;
  notifyRegionsPluginReady();
}

/**
 * Получение экземпляра плагина regions.
 */
function getWaveSurferRegionsPlugin() {
  if (waveSurferRegionsPlugin) {
    return waveSurferRegionsPlugin;
  }

  if (wavesurfer && typeof wavesurfer.getActivePlugins === "function") {
    const active = wavesurfer.getActivePlugins();
    waveSurferRegionsPlugin = (active && active.regions) || null;
    window.waveSurferRegionsPlugin = waveSurferRegionsPlugin;
    return waveSurferRegionsPlugin;
  }

  return null;
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
  waveSurferRegionsPlugin = null;
  window.waveSurferRegionsPlugin = null;

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

  // НЕ вызываем cacheWaveSurferPlugins() здесь!
  // Плагины еще не готовы после WaveSurfer.create()
  // Они станут доступны только в обработчике 'ready'
  
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
    cacheWaveSurferPlugins();
    updateTimeDisplay();
    hideLoadingIndicator();
  });
  
  // Событие decode (альтернативное для Web Audio API backend)
  wavesurfer.on("decode", () => {
    cacheWaveSurferPlugins();
  });

  // Событие region-created (регион создан)
  wavesurfer.on("region-created", (region) => {
    // Регион создан
  });

  // Обработчики для кнопок Zoom не нужны здесь
  // Они устанавливаются в DOMContentLoaded для ленивой инициализации
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

  const audioUrl = `/api/audio/${audioFileId}/stream`;
  
  const loadPromise = wavesurfer.load(audioUrl);
  if (loadPromise && typeof loadPromise.then === "function") {
    loadPromise
      .then(() => {
        lastLoadedAudioId = audioFileId;
        currentlyLoadingAudioId = null;
        hideLoadingIndicator();
        
        // Кэшируем плагины после загрузки
        cacheWaveSurferPlugins();
        
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
});
