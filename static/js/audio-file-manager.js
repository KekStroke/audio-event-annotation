/**
 * Управление списком аудио файлов и кнопкой Add File.
 */

let audioFiles = [];
let fileListElement = null;
let addFileModalOverlay = null;
let addFileModal = null;
let addFileForm = null;
let addFilePathInput = null;
let addFileSuccessMessage = null;
let addFileErrorMessage = null;
let addFileSubmitButton = null;

document.addEventListener('DOMContentLoaded', () => {
    initAudioFileManager();
});

/**
 * Инициализация модуля управления аудио файлами
 */
function initAudioFileManager() {
    fileListElement = document.querySelector('.file-list');
    if (!fileListElement) {
        return;
    }

    if (typeof window.currentAudioFileId === 'undefined') {
        window.currentAudioFileId = null;
    }

    initAddFileModal();
    loadAudioFiles();
}

/**
 * Настройка модального окна добавления файла
 */
function initAddFileModal() {
    addFileModalOverlay = document.getElementById('add-file-modal-overlay');
    addFileModal = document.getElementById('add-file-modal');
    addFileForm = document.getElementById('add-file-form');
    addFilePathInput = document.getElementById('add-file-path');
    addFileSuccessMessage = document.getElementById('add-file-success');
    addFileErrorMessage = document.getElementById('add-file-error');
    addFileSubmitButton = document.getElementById('add-file-submit');

    const addFileButton = document.querySelector('[data-action="add-file"]');
    if (addFileButton) {
        addFileButton.addEventListener('click', () => {
            resetAddFileForm();
            openAddFileModal();
        });
    }

    if (addFileForm) {
        addFileForm.addEventListener('submit', handleAddFileSubmit);
    }

    document.querySelectorAll('[data-close-modal="add-file"]').forEach((button) => {
        button.addEventListener('click', closeAddFileModal);
    });

    if (addFileModalOverlay) {
        addFileModalOverlay.addEventListener('click', (event) => {
            if (event.target === addFileModalOverlay) {
                closeAddFileModal();
            }
        });
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && addFileModalOverlay?.classList.contains('active')) {
            closeAddFileModal();
        }
    });
}

/**
 * Обработчик отправки формы добавления
 */
async function handleAddFileSubmit(event) {
    event.preventDefault();
    if (!addFilePathInput) {
        return;
    }

    const filePath = addFilePathInput.value.trim();
    if (!filePath) {
        showAddFileError('Укажите путь к аудио файлу');
        return;
    }

    setSubmitState(true);

    try {
        const response = await fetch('/api/audio/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ file_path: filePath }),
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            const message = data?.error || 'Не удалось добавить файл';
            throw new Error(message);
        }

        showAddFileSuccess('Файл успешно добавлен');
        await loadAudioFiles(data.id);

        setTimeout(() => {
            closeAddFileModal();
            resetAddFileForm();
        }, 600);
    } catch (error) {
        console.error('Ошибка добавления аудио файла:', error);
        showAddFileError(error.message || 'Произошла ошибка при добавлении файла');
    } finally {
        setSubmitState(false);
    }
}

/**
 * Загрузка списка аудио файлов с сервера
 */
async function loadAudioFiles(selectedAudioFileId = null) {
    if (!fileListElement) {
        return;
    }

    try {
        const response = await fetch('/api/audio');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        audioFiles = await response.json();
    } catch (error) {
        console.error('Ошибка загрузки списка аудио файлов:', error);
        audioFiles = [];
    }

    renderFileList();

    if (selectedAudioFileId && audioFiles.some((file) => file.id === selectedAudioFileId)) {
        selectAudioFile(selectedAudioFileId);
        return;
    }

    // Auto-select first file if none is selected
    if (!window.currentAudioFileId && audioFiles.length > 0) {
        // Initialize WaveSurfer before auto-selecting first file
        if (typeof ensureWaveSurferInitialized === 'function') {
            ensureWaveSurferInitialized();
        }
        selectAudioFile(audioFiles[0].id, { force: true });
    }
}

/**
 * Рендер списка аудио файлов
 */
function renderFileList() {
    if (!fileListElement) {
        return;
    }

    fileListElement.innerHTML = '';

    if (!audioFiles.length) {
        const emptyItem = document.createElement('div');
        emptyItem.className = 'file-item';
        emptyItem.setAttribute('role', 'listitem');
        emptyItem.setAttribute('tabindex', '3');
        emptyItem.innerHTML = '<span class="file-name">No files loaded</span>';
        fileListElement.appendChild(emptyItem);
        return;
    }

    audioFiles.forEach((file, index) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'file-item';
        item.dataset.audioFileId = file.id;
        item.setAttribute('role', 'listitem');
        item.setAttribute('tabindex', String(index + 3));

        if (file.id === window.currentAudioFileId) {
            item.classList.add('file-item-active');
        }

        const title = escapeHtml(file.filename || 'Unnamed file');
        const duration = formatDurationLabel(file.duration);

        item.innerHTML = `
            <span class="file-name">${title}</span>
            <span class="file-duration">${duration}</span>
        `;

        item.addEventListener('click', () => {
            // Initialize WaveSurfer on file click (user gesture!)
            // This must be synchronous within the click handler
            if (typeof ensureWaveSurferInitialized === 'function') {
                ensureWaveSurferInitialized();
            }
            selectAudioFile(file.id);
        });

        fileListElement.appendChild(item);
    });
}

/**
 * Выбор аудио файла пользователем
 */
function selectAudioFile(audioFileId, options = {}) {
    const selectedFile = audioFiles.find((file) => file.id === audioFileId);
    if (!selectedFile) {
        return;
    }

    const forceSelection = options.force === true;
    if (!forceSelection && window.currentAudioFileId === audioFileId) {
        return;
    }

    window.currentAudioFileId = audioFileId;
    dispatchAudioFileSelected(selectedFile);
    renderFileList();
}

/**
 * Диспетчер события выбора аудио файла
 */
function dispatchAudioFileSelected(audioFile) {
    const event = new CustomEvent('audioFileSelected', { detail: audioFile });
    document.dispatchEvent(event);
}

/**
 * Управление состоянием кнопки отправки
 */
function setSubmitState(isSubmitting) {
    if (addFileSubmitButton) {
        addFileSubmitButton.disabled = isSubmitting;
    }
}

/**
 * Показ сообщения об успешном добавлении
 */
function showAddFileSuccess(message) {
    if (!addFileSuccessMessage) return;
    addFileSuccessMessage.textContent = message;
    if (message) {
        addFileSuccessMessage.classList.add('active');
    } else {
        addFileSuccessMessage.classList.remove('active');
    }
    if (addFileErrorMessage) {
        addFileErrorMessage.classList.remove('active');
    }
}

/**
 * Показ сообщения об ошибке
 */
function showAddFileError(message) {
    if (!addFileErrorMessage) return;
    addFileErrorMessage.textContent = message;
    if (message) {
        addFileErrorMessage.classList.add('active');
    } else {
        addFileErrorMessage.classList.remove('active');
    }
    if (addFileSuccessMessage) {
        addFileSuccessMessage.classList.remove('active');
    }
}

/**
 * Сброс формы и сообщений
 */
function resetAddFileForm() {
    if (addFileForm) {
        addFileForm.reset();
    }
    showAddFileSuccess('');
    showAddFileError('');
}

/**
 * Открытие модального окна
 */
function openAddFileModal() {
    if (!addFileModalOverlay || !addFileModal) {
        return;
    }
    addFileModalOverlay.classList.add('active');
    addFileModal.classList.add('active');
    addFilePathInput?.focus();
}

/**
 * Закрытие модального окна
 */
function closeAddFileModal() {
    if (!addFileModalOverlay || !addFileModal) {
        return;
    }
    addFileModalOverlay.classList.remove('active');
    addFileModal.classList.remove('active');
}

/**
 * Форматирование длительности для списка файлов
 */
function formatDurationLabel(duration) {
    if (typeof duration !== 'number' || Number.isNaN(duration)) {
        return '00:00';
    }
    const mins = Math.floor(duration / 60);
    const secs = Math.floor(duration % 60);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * Экранирование HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

