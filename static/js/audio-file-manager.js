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

// Import Folder Modal Elements
let importFolderModalOverlay = null;
let importFolderModal = null;
let importFolderForm = null;
let importFolderPathInput = null;
let importFolderSuccessMessage = null;
let importFolderErrorMessage = null;
let importFolderSubmitButton = null;

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
    initImportFolderModal();
    loadAudioFiles();
}

/**
 * Инициализация модального окна импорта папки
 */
function initImportFolderModal() {
    importFolderModalOverlay = document.getElementById('import-folder-modal-overlay');
    importFolderModal = document.getElementById('import-folder-modal');
    importFolderForm = document.getElementById('import-folder-form');
    importFolderPathInput = document.getElementById('import-folder-path');
    importFolderSuccessMessage = document.getElementById('import-folder-success');
    importFolderErrorMessage = document.getElementById('import-folder-error');
    importFolderSubmitButton = document.getElementById('import-folder-submit');

    const importFolderButton = document.querySelector('[data-action="import-folder"]');
    if (importFolderButton) {
        importFolderButton.addEventListener('click', () => {
            resetImportFolderForm();
            openImportFolderModal();
        });
    }

    if (importFolderForm) {
        importFolderForm.addEventListener('submit', handleImportFolderSubmit);
    }

    document.querySelectorAll('[data-close-modal="import-folder"]').forEach((button) => {
        button.addEventListener('click', closeImportFolderModal);
    });

    if (importFolderModalOverlay) {
        importFolderModalOverlay.addEventListener('click', (event) => {
            if (event.target === importFolderModalOverlay) {
                closeImportFolderModal();
            }
        });
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && importFolderModalOverlay?.classList.contains('active')) {
            closeImportFolderModal();
        }
    });
}

/**
 * Обработчик отправки формы импорта папки
 */
async function handleImportFolderSubmit(event) {
    event.preventDefault();
    if (!importFolderPathInput) {
        return;
    }

    const folderPath = importFolderPathInput.value.trim();
    if (!folderPath) {
        showImportFolderError('Please enter a folder path');
        return;
    }

    if (importFolderSubmitButton) {
        importFolderSubmitButton.disabled = true;
        importFolderSubmitButton.textContent = 'Importing...';
    }

    try {
        const response = await fetch('/api/audio/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: folderPath }),
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || 'Failed to import folder');
        }

        showImportFolderSuccess(`Successfully imported ${data.imported_count} files.`);
        await loadAudioFiles();

        setTimeout(() => {
            closeImportFolderModal();
            resetImportFolderForm();
        }, 1500);

    } catch (error) {
        console.error('Error importing folder:', error);
        showImportFolderError(error.message || 'Error importing folder');
    } finally {
        if (importFolderSubmitButton) {
            importFolderSubmitButton.disabled = false;
            importFolderSubmitButton.textContent = 'Import Folder';
        }
    }
}

/**
 * Показ сообщения об успехе импорта
 */
function showImportFolderSuccess(message) {
    if (!importFolderSuccessMessage) return;
    importFolderSuccessMessage.textContent = message;
    if (message) {
        importFolderSuccessMessage.classList.add('active');
    } else {
        importFolderSuccessMessage.classList.remove('active');
    }
    if (importFolderErrorMessage) {
        importFolderErrorMessage.classList.remove('active');
    }
}

/**
 * Показ сообщения об ошибке импорта
 */
function showImportFolderError(message) {
    if (!importFolderErrorMessage) return;
    importFolderErrorMessage.textContent = message;
    if (message) {
        importFolderErrorMessage.classList.add('active');
    } else {
        importFolderErrorMessage.classList.remove('active');
    }
    if (importFolderSuccessMessage) {
        importFolderSuccessMessage.classList.remove('active');
    }
}

/**
 * Сброс формы импорта
 */
function resetImportFolderForm() {
    if (importFolderForm) {
        importFolderForm.reset();
    }
    showImportFolderSuccess('');
    showImportFolderError('');
}

/**
 * Открытие модального окна импорта
 */
function openImportFolderModal() {
    if (!importFolderModalOverlay || !importFolderModal) {
        return;
    }
    importFolderModalOverlay.classList.add('active');
    importFolderModal.classList.add('active');
    importFolderPathInput?.focus();
}

/**
 * Закрытие модального окна импорта
 */
function closeImportFolderModal() {
    if (!importFolderModalOverlay || !importFolderModal) {
        return;
    }
    importFolderModalOverlay.classList.remove('active');
    importFolderModal.classList.remove('active');
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
        const item = document.createElement('div');
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
            <div class="file-info" style="flex: 1; display: flex; justify-content: space-between; align-items: center; overflow: hidden; cursor: pointer;">
                <span class="file-name" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-right: 8px;">${title}</span>
                <span class="file-duration" style="flex-shrink: 0;">${duration}</span>
            </div>
            <button type="button" class="delete-file-btn" title="Delete file" style="background: none; border: none; color: var(--text-secondary); cursor: pointer; margin-left: 0.5rem; padding: 0.2rem; font-size: 1.1em; opacity: 0.7;">✕</button>
        `;

        // Click on file info selects the file
        const fileInfo = item.querySelector('.file-info');
        fileInfo.addEventListener('click', () => {
            // Initialize WaveSurfer on file click (user gesture!)
            // This must be synchronous within the click handler
            if (typeof ensureWaveSurferInitialized === 'function') {
                ensureWaveSurferInitialized();
            }
            selectAudioFile(file.id);
        });

        // Click on delete button
        const deleteBtn = item.querySelector('.delete-file-btn');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent selection
            deleteAudioFile(file.id, file.filename);
        });
        
        // Hover effect for delete button
        deleteBtn.addEventListener('mouseenter', () => { deleteBtn.style.opacity = '1'; deleteBtn.style.color = '#ff6b6b'; });
        deleteBtn.addEventListener('mouseleave', () => { deleteBtn.style.opacity = '0.7'; deleteBtn.style.color = 'var(--text-secondary)'; });

        fileListElement.appendChild(item);
    });
}

/**
 * Удаление аудио файла
 */
async function deleteAudioFile(audioFileId, filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/audio/${audioFileId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.error || 'Failed to delete file');
        }

        // Если удален текущий файл, сбрасываем выбор
        if (window.currentAudioFileId === audioFileId) {
            window.currentAudioFileId = null;
            // Очищаем плеер если нужно (можно добавить событие)
            if (window.wavesurfer) {
                window.wavesurfer.empty();
            }
        }

        // Перезагружаем список
        await loadAudioFiles();

    } catch (error) {
        console.error('Error deleting file:', error);
        alert('Error deleting file: ' + error.message);
    }
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

