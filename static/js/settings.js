/**
 * Settings Manager
 * Handles application settings, storage, and the settings modal.
 */

const DEFAULT_SETTINGS = {
    spectrogramHeight: 512,
    mainSpectrogramHeight: 256,
    showMainSpectrogram: false,
    showSpectrogramLabels: true
};

class AppSettings {
    constructor() {
        this.settings = { ...DEFAULT_SETTINGS };
        this.modalOverlay = document.getElementById('settings-modal-overlay');
        this.modal = document.getElementById('settings-modal');
        this.form = document.getElementById('settings-form');
        this.heightInput = document.getElementById('setting-spectrogram-height');
        this.mainHeightInput = document.getElementById('setting-main-spectrogram-height');
        this.showMainSpectrogramInput = document.getElementById('setting-show-main-spectrogram');
        this.showLabelsInput = document.getElementById('setting-show-labels');
        
        this.init();
    }

    init() {
        this.loadSettings();
        this.initEventListeners();
    }

    loadSettings() {
        const stored = localStorage.getItem('audioEventAnnotationsSettings');
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                // Remove colorMap if it exists in stored settings
                if (parsed.colorMap) delete parsed.colorMap;
                this.settings = { ...DEFAULT_SETTINGS, ...parsed };
            } catch (e) {
                console.error('Failed to parse settings', e);
            }
        }
    }

    saveSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        localStorage.setItem('audioEventAnnotationsSettings', JSON.stringify(this.settings));
        
        // Dispatch event for other components
        document.dispatchEvent(new CustomEvent('settingsChanged', { detail: this.settings }));
    }

    get(key) {
        return this.settings[key];
    }

    initEventListeners() {
        // Open button
        const openBtn = document.querySelector('[data-action="settings"]');
        if (openBtn) {
            openBtn.addEventListener('click', () => this.openModal());
        }

        // Close buttons
        document.querySelectorAll('[data-close-modal="settings"]').forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        // Overlay click
        if (this.modalOverlay) {
            this.modalOverlay.addEventListener('click', (e) => {
                if (e.target === this.modalOverlay) this.closeModal();
            });
        }

        // Form submit
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSave();
            });
        }
        
        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modalOverlay && this.modalOverlay.classList.contains('active')) {
                this.closeModal();
            }
        });
    }

    openModal() {
        if (!this.modalOverlay || !this.modal) return;
        
        // Populate form
        if (this.heightInput) this.heightInput.value = this.settings.spectrogramHeight;
        if (this.mainHeightInput) this.mainHeightInput.value = this.settings.mainSpectrogramHeight;
        if (this.showMainSpectrogramInput) this.showMainSpectrogramInput.checked = this.settings.showMainSpectrogram;
        if (this.showLabelsInput) this.showLabelsInput.checked = this.settings.showSpectrogramLabels;

        this.modalOverlay.classList.add('active');
        this.modal.classList.add('active');
    }

    closeModal() {
        if (!this.modalOverlay || !this.modal) return;
        this.modalOverlay.classList.remove('active');
        this.modal.classList.remove('active');
    }

    handleSave() {
        const newSettings = {
            spectrogramHeight: parseInt(this.heightInput.value, 10) || 512,
            mainSpectrogramHeight: this.mainHeightInput ? (parseInt(this.mainHeightInput.value, 10) || 256) : 256,
            showMainSpectrogram: this.showMainSpectrogramInput ? this.showMainSpectrogramInput.checked : false,
            showSpectrogramLabels: this.showLabelsInput ? this.showLabelsInput.checked : true
        };
        
        this.saveSettings(newSettings);
        this.closeModal();
    }
}

// Initialize global settings instance
window.appSettings = new AppSettings();
