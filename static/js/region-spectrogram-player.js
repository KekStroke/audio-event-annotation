/**
 * Region Spectrogram Player
 * 
 * Модуль для управления отдельным wavesurfer instance с спектрограммой
 * для выделенного региона основного аудио файла.
 * 
 * Функциональность:
 * - Создание второго wavesurfer instance для региона
 * - Извлечение ТОЛЬКО выбранного региона из основного AudioBuffer
 * - Отображение интерактивной спектрограммы (wavesurfer.js spectrogram plugin)
 * - Независимые controls для воспроизведения региона
 * - Синхронизация с изменениями границ региона
 */

class RegionSpectrogramPlayer {
    constructor() {
        this.wavesurfer = null;
        this.spectrogramPlugin = null;
        this.currentAudioFileId = null;
        this.currentRegion = null;
        this.isPlaying = false;

        // DOM elements
        this.container = document.getElementById('region-player-container');
        this.waveformContainer = document.getElementById('region-waveform');
        // this.spectrogramContainer = document.getElementById('region-spectrogram'); // Removed as per user request
        this.playPauseBtn = document.getElementById('region-play-pause');
        this.playIcon = document.getElementById('region-play-icon');
        this.timeDisplay = document.getElementById('region-time-display');
        this.annotationInfo = document.getElementById('region-annotation-info');

        this.initializeEventListeners();
    }

    /**
     * Инициализация event listeners для controls
     */
    initializeEventListeners() {
        if (this.playPauseBtn) {
            this.playPauseBtn.addEventListener('click', () => {
                this.togglePlayPause();
            });
        }
    }

    /**
     * Инициализация wavesurfer instance для региона
     * 
     * @param {string} audioFileId - UUID аудио файла
     * @param {number} start - Начало региона в секундах
     * @param {number} end - Конец региона в секундах
     * @param {number} sampleRate - Sample rate аудио файла
     * @param {Object} region - Объект региона (опционально)
     */
    async init(audioFileId, start, end, sampleRate = 44100, region = null) {
        console.log('RegionSpectrogramPlayer.init called', { audioFileId, start, end, region });
        try {
            // Останавливаем воспроизведение перед инициализацией
            this.stop();

            // Сохраняем ID и регион
            this.currentAudioFileId = audioFileId;
            this.currentRegion = { start, end };

            // Отображаем информацию об аннотации
            this.updateAnnotationInfo(region);

            // Показываем container
            if (this.container) {
                this.container.style.display = 'block';
            }

            // Уничтожаем предыдущий instance если есть
            if (this.wavesurfer) {
                this.wavesurfer.destroy();
                this.wavesurfer = null;
            }

            // Создаём новый wavesurfer instance
            this.wavesurfer = WaveSurfer.create({
                container: this.waveformContainer,
                waveColor: '#4a9eff',
                progressColor: '#1e7ed8',
                cursorColor: '#ffffff',
                height: 128,
                normalize: true,
                backend: 'WebAudio',
                mediaControls: false
            });

            // Инициализируем spectrogram plugin с настройками для биоакустики
            // Используем основной контейнер, так как отдельный div был удален
            this.spectrogramPlugin = this.wavesurfer.registerPlugin(
                WaveSurfer.Spectrogram.create({
                    container: this.container, // Use the main container
                    labels: true,
                    height: 256,
                    colorMap: 'roseus',
                    scale: 'linear',  // Linear scale для биоакустики - показывает ВСЕ частоты
                    frequencyMin: 0,
                    frequencyMax: sampleRate / 2,  // До Nyquist frequency для ультразвука
                    fftSamples: 2048,
                    labelsBackground: 'rgba(0, 0, 0, 0.7)',
                    labelsColor: '#ffffff',
                    labelsHzColor: '#ffffff'
                })
            );

            // Загружаем аудио региона (извлекаем из основного buffer)
            await this.loadRegionAudio(audioFileId, start, end);

            // Подписываемся на события wavesurfer
            this.setupWavesurferEvents();

        } catch (error) {
            console.error('Error initializing region spectrogram player:', error);
        }
    }

    /**
     * Обновление информации об аннотации
     * @param {Object} region - Объект региона
     */
    updateAnnotationInfo(region) {
        console.log('updateAnnotationInfo called with region:', region);
        if (!this.annotationInfo) {
            console.warn('Annotation info container not found');
            return;
        }
        
        this.annotationInfo.innerHTML = '';
        
        // Check both data.annotation (standard) and direct property (fallback)
        const annotation = (region && region.data && region.data.annotation) || (region && region.annotation);

        if (annotation) {
            console.log('Rendering annotation info:', annotation);
            const label = annotation.event_label || 'Unknown Event';
            const confidence = (annotation.confidence !== null && annotation.confidence !== undefined) 
                ? (annotation.confidence * 100).toFixed(0) + '%' 
                : 'N/A';
            const notes = annotation.notes || '';
            
            // Format times
            const formatTime = (t) => {
                const m = Math.floor(t / 60);
                const s = Math.floor(t % 60);
                const ms = Math.floor((t % 1) * 100);
                return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
            };
            const timeRange = `${formatTime(annotation.start_time)} - ${formatTime(annotation.end_time)}`;

            this.annotationInfo.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <strong style="font-size: 1.1em; color: var(--text-primary);">${label}</strong>
                    <span style="font-family: monospace; color: var(--text-secondary); font-size: 0.9em;">${timeRange}</span>
                </div>
                <div style="display: flex; gap: 10px; font-size: 0.9em; color: var(--text-secondary);">
                    <span>Confidence: <span style="color: var(--text-primary); font-weight: bold;">${confidence}</span></span>
                </div>
                ${notes ? `<div style="margin-top: 4px; font-style: italic; color: var(--text-secondary); font-size: 0.9em;">${notes}</div>` : ''}
            `;
            this.annotationInfo.style.display = 'block';
        } else {
            // No annotation data found
            if (region && region.id && region.id.startsWith('annotation-')) {
                 // This IS an annotation but data is missing - show error
                 console.error('Annotation region missing data:', region);
                 this.annotationInfo.innerHTML = `<div style="color: #ff6b6b; font-style: italic;">Error: Annotation data missing</div>`;
                 this.annotationInfo.style.display = 'block';
            } else {
                // Regular selection or manual region - hide info (cleaner UI)
                this.annotationInfo.style.display = 'none';
            }
        }
    }


    /**
     * Загрузка аудио для региона - извлечение из основного wavesurfer AudioBuffer
     * 
     * @param {string} audioFileId - UUID аудио файла
     * @param {number} start - Начало региона в секундах
     * @param {number} end - Конец региона в секундах
     */
    async loadRegionAudio(audioFileId, start, end) {
        const mainWavesurfer = window.wavesurfer;
        if (!mainWavesurfer) {
            throw new Error('Main wavesurfer instance not found');
        }

        const decodedData = mainWavesurfer.getDecodedData();
        if (!decodedData) {
            throw new Error('Audio data not decoded yet');
        }

        const sampleRate = decodedData.sampleRate;
        const startSample = Math.floor(start * sampleRate);
        const endSample = Math.floor(end * sampleRate);
        const length = endSample - startSample;

        if (length <= 0) {
            throw new Error('Invalid region length');
        }

        // Create a new AudioBuffer for the region
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const regionBuffer = audioContext.createBuffer(
            decodedData.numberOfChannels,
            length,
            sampleRate
        );

        // Copy channel data
        for (let i = 0; i < decodedData.numberOfChannels; i++) {
            const channelData = decodedData.getChannelData(i);
            const regionChannelData = regionBuffer.getChannelData(i);
            
            // Copy the segment
            const actualEndSample = Math.min(endSample, channelData.length);
            const actualLength = actualEndSample - startSample;
            
            if (actualLength > 0) {
                const slice = channelData.subarray(startSample, actualEndSample);
                regionChannelData.set(slice);
            }
        }

        // Convert to WAV and load
        const blob = this.audioBufferToWav(regionBuffer);
        const url = URL.createObjectURL(blob);
        
        await this.wavesurfer.load(url);
    }

    /**
     * Конвертация AudioBuffer в WAV Blob
     * 
     * @param {AudioBuffer} buffer - AudioBuffer для конвертации
     * @returns {Blob} WAV Blob
     */
    audioBufferToWav(buffer) {
        const numberOfChannels = buffer.numberOfChannels;
        const sampleRate = buffer.sampleRate;
        const length = buffer.length * numberOfChannels * 2; // 16-bit samples
        const arrayBuffer = new ArrayBuffer(44 + length);
        const view = new DataView(arrayBuffer);

        // Helper function to write string
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };

        // WAV header
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true); // fmt chunk size
        view.setUint16(20, 1, true); // PCM format
        view.setUint16(22, numberOfChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numberOfChannels * 2, true); // byte rate
        view.setUint16(32, numberOfChannels * 2, true); // block align
        view.setUint16(34, 16, true); // bits per sample
        writeString(36, 'data');
        view.setUint32(40, length, true);

        // Write interleaved PCM samples
        const offset = 44;
        let index = 0;
        for (let i = 0; i < buffer.length; i++) {
            for (let channel = 0; channel < numberOfChannels; channel++) {
                const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]));
                view.setInt16(offset + index, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
                index += 2;
            }
        }

        return new Blob([arrayBuffer], { type: 'audio/wav' });
    }

    /**
     * Настройка event listeners для wavesurfer
     */
    setupWavesurferEvents() {
        if (!this.wavesurfer) return;

        // Обновление времени при воспроизведении
        this.wavesurfer.on('audioprocess', () => {
            if (this.isPlaying) {
                const currentTime = this.wavesurfer.getCurrentTime();
                const duration = this.wavesurfer.getDuration();
                this.updateTimeDisplay(currentTime, duration);
            }
        });

        // При окончании воспроизведения
        this.wavesurfer.on('finish', () => {
            this.isPlaying = false;
            this.updatePlayPauseButton();
        });

        // При паузе
        this.wavesurfer.on('pause', () => {
            this.isPlaying = false;
            this.updatePlayPauseButton();
        });

        // При воспроизведении
        this.wavesurfer.on('play', () => {
            this.isPlaying = true;
            this.updatePlayPauseButton();
        });

        // Клик по waveform для перемотки
        this.wavesurfer.on('click', () => {
            const currentTime = this.wavesurfer.getCurrentTime();
            const duration = this.wavesurfer.getDuration();
            this.updateTimeDisplay(currentTime, duration);
        });
    }

    /**
     * Toggle play/pause
     */
    togglePlayPause() {
        if (!this.wavesurfer) return;

        this.wavesurfer.playPause();
    }

    /**
     * Play region
     */
    play() {
        if (!this.wavesurfer) return;

        this.wavesurfer.play();
    }

    /**
     * Pause region
     */
    pause() {
        if (!this.wavesurfer) return;

        this.wavesurfer.pause();
    }

    /**
     * Stop region
     */
    stop() {
        if (!this.wavesurfer) return;

        this.wavesurfer.stop();
        this.isPlaying = false;
        this.updatePlayPauseButton();
    }

    /**
     * Обновление региона при изменении границ
     * 
     * @param {number} start - Новое начало региона
     * @param {number} end - Новый конец региона
     */
    async updateRegion(start, end) {
        if (!this.currentAudioFileId) return;

        // Получаем sample rate из текущего buffer
        let sampleRate = 44100;
        if (this.wavesurfer) {
            const buffer = this.wavesurfer.getDecodedData();
            if (buffer) {
                sampleRate = buffer.sampleRate;
            }
        }

        // Останавливаем воспроизведение
        this.stop();

        // Перезагружаем с новыми границами
        // Важно: передаем текущий регион (если он есть в памяти или можно получить)
        // Но так как updateRegion вызывается обычно извне, где есть доступ к региону,
        // лучше бы передавать регион целиком.
        // Пока оставим null для региона, так как updateRegion используется редко напрямую,
        // обычно вызывается init заново.
        await this.init(this.currentAudioFileId, start, end, sampleRate);
    }

    /**
     * Обновление кнопки play/pause
     */
    updatePlayPauseButton() {
        if (!this.playIcon || !this.playPauseBtn) return;

        if (this.isPlaying) {
            this.playIcon.textContent = '⏸';
            this.playPauseBtn.innerHTML = '<span id="region-play-icon">⏸</span> Pause';
        } else {
            this.playIcon.textContent = '▶';
            this.playPauseBtn.innerHTML = '<span id="region-play-icon">▶</span> Play Region';
        }

        // Обновляем ссылку на icon после изменения innerHTML
        this.playIcon = document.getElementById('region-play-icon');
    }

    /**
     * Обновление отображения времени
     * 
     * @param {number} current - Текущее время в секундах
     * @param {number} total - Общая длительность в секундах
     */
    updateTimeDisplay(current, total) {
        if (!this.timeDisplay) return;

        const formatTime = (seconds) => {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        };

        this.timeDisplay.textContent = `${formatTime(current)} / ${formatTime(total)}`;
    }

    /**
     * Уничтожение wavesurfer instance и освобождение ресурсов
     */
    destroy() {
        // Останавливаем воспроизведение
        if (this.wavesurfer) {
            this.wavesurfer.stop();
        }

        // Уничтожаем wavesurfer
        if (this.wavesurfer) {
            this.wavesurfer.destroy();
            this.wavesurfer = null;
        }

        // Очищаем plugin
        this.spectrogramPlugin = null;

        // Скрываем container
        if (this.container) {
            this.container.style.display = 'none';
        }

        // Сбрасываем состояние
        this.currentAudioFileId = null;
        this.currentRegion = null;
        this.isPlaying = false;

        // Очищаем time display
        if (this.timeDisplay) {
            this.timeDisplay.textContent = '00:00 / 00:00';
        }
    }

    /**
     * Проверка инициализации
     * 
     * @returns {boolean} True если wavesurfer инициализирован
     */
    isInitialized() {
        return this.wavesurfer !== null;
    }
}

// Создаём глобальный instance
window.regionSpectrogramPlayer = new RegionSpectrogramPlayer();
