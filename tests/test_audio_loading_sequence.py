"""
Тесты для проверки последовательности загрузки аудио.

Проблема: WaveSurfer создан, но аудио не загружается.
"""

import pytest
from pathlib import Path


def test_audio_file_selected_triggers_load():
    """
    FAILING TEST: При выборе файла должна вызываться loadAudioFile.
    
    Проблема из консоли:
    - [WaveSurfer] 🔧 WaveSurfer создан, ожидаем загрузки аудио...
    - (Нет сообщения о загрузке аудио!)
    - Regions не работают
    
    Ожидаемая последовательность:
    1. Клик на файл -> ensureWaveSurferInitialized()
    2. Создается WaveSurfer
    3. Диспатчится событие audioFileSelected
    4. Обработчик audioFileSelected вызывает loadAudioFile()
    5. loadAudioFile() вызывает wavesurfer.load()
    
    Проверяем что эта последовательность настроена в коде.
    """
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем что есть обработчик audioFileSelected
    assert 'audioFileSelected' in content, 'Обработчик audioFileSelected не найден'
    
    # Ищем обработчик и проверяем что он вызывает loadAudioFile
    lines = content.split('\n')
    found_handler = False
    calls_load_audio = False
    
    in_handler = False
    for i, line in enumerate(lines):
        if 'addEventListener' in line and 'audioFileSelected' in line:
            found_handler = True
            in_handler = True
        
        if in_handler:
            if 'loadAudioFile' in line:
                calls_load_audio = True
                break
            # Конец обработчика
            if '});' in line and i > 0:
                break
    
    assert found_handler, 'Обработчик addEventListener("audioFileSelected") не найден'
    
    # FAILING TEST
    assert calls_load_audio, \
        'FAILING: Обработчик audioFileSelected НЕ вызывает loadAudioFile()! ' \
        'Поэтому аудио не загружается и regions plugin не становится доступным. ' \
        'В коде есть проверка if (wavesurfer), но она должна ВСЕГДА быть true, ' \
        'потому что ensureWaveSurferInitialized() вызывается при клике на файл.'


def test_ensure_wavesurfer_loads_no_audio():
    """
    Проверяем что ensureWaveSurferInitialized создает WaveSurfer БЕЗ аудио.
    
    Это правильное поведение - аудио загружается отдельно через loadAudioFile.
    """
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем что ensureWaveSurferInitialized вызывает initWaveSurfer с null
    lines = content.split('\n')
    found_ensure = False
    calls_init_with_null = False
    
    for i, line in enumerate(lines):
        if 'function ensureWaveSurferInitialized' in line:
            found_ensure = True
        
        if found_ensure and 'initWaveSurfer(null)' in line:
            calls_init_with_null = True
            break
    
    assert found_ensure, 'Функция ensureWaveSurferInitialized не найдена'
    assert calls_init_with_null, \
        'ensureWaveSurferInitialized должна вызывать initWaveSurfer(null), ' \
        'потому что аудио загружается отдельно через loadAudioFile'


def test_load_audio_file_checks_wavesurfer_exists():
    """
    Проверяем что loadAudioFile проверяет наличие wavesurfer.
    """
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Ищем функцию loadAudioFile
    lines = content.split('\n')
    in_function = False
    has_wavesurfer_check = False
    
    for i, line in enumerate(lines):
        if 'function loadAudioFile' in line:
            in_function = True
        
        if in_function and ('if (!wavesurfer)' in line or 'if (!audioFileId || !wavesurfer)' in line):
            has_wavesurfer_check = True
            break
    
    assert has_wavesurfer_check, \
        'loadAudioFile должна проверять наличие wavesurfer перед загрузкой'

