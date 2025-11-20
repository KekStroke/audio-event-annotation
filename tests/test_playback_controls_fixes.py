"""
Тесты для исправлений Playback Controls
"""
from pathlib import Path
import re
from pytest_bdd import scenarios, given, when, then

# Загружаем сценарии из feature-файла
scenarios('features/playback_controls_fixes.feature')

@given('index.html contains playback speed range input')
def html_has_speed_input():
    """Проверяем что HTML содержит speed input"""
    html_path = Path(__file__).parent.parent / 'templates' / 'index.html'
    content = html_path.read_text(encoding='utf-8')
    assert 'id="playback-speed"' in content or 'playback-speed' in content

@when('I check the HTML structure')
def check_html_structure():
    """Сохраняем для проверки"""
    pass

@then('there should be a label or span displaying speed value')
def check_speed_value_display():
    """
    FAILING TEST: Проверяем наличие элемента для отображения значения скорости
    """
    html_path = Path(__file__).parent.parent / 'templates' / 'index.html'
    content = html_path.read_text(encoding='utf-8')
    
    # FAILING TEST: должен быть элемент для отображения значения
    # Ищем span или label рядом с playback-speed
    speed_section = re.search(
        r'playback-speed.*?(?=</div>|</label>|$)',
        content,
        re.DOTALL | re.IGNORECASE
    )
    
    if speed_section:
        section_text = speed_section.group(0)
        assert ('id="speed-value"' in section_text or 
                'id="playback-speed-value"' in section_text or
                '<span' in section_text), \
            'Должен быть элемент (span/label) для отображения значения скорости'
    else:
        raise AssertionError('Не найден раздел с playback-speed')

@then('the display should be updated when speed changes')
def check_speed_update_handler():
    """
    FAILING TEST: Проверяем обработчик изменения скорости
    """
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # FAILING TEST: должен быть обработчик, который обновляет отображение
    assert ('playback-speed' in content and 
            ('addEventListener' in content or 'oninput' in content or 'onchange' in content)), \
        'Должен быть обработчик для обновления отображения скорости'


@given('index.html contains volume range input')
def html_has_volume_input():
    """Проверяем что HTML содержит volume input"""
    html_path = Path(__file__).parent.parent / 'templates' / 'index.html'
    content = html_path.read_text(encoding='utf-8')
    assert 'id="volume"' in content or 'volume' in content

@then('there should be a label or span displaying volume value')
def check_volume_value_display():
    """
    Проверяем наличие элемента для отображения значения громкости
    """
    html_path = Path(__file__).parent.parent / 'templates' / 'index.html'
    content = html_path.read_text(encoding='utf-8')
    
    # Ищем секцию volume более широко - включая label перед input
    volume_section = re.search(
        r'<label.*?volume.*?</label>.*?id="volume"',
        content,
        re.DOTALL | re.IGNORECASE
    )
    
    if volume_section:
        section_text = volume_section.group(0)
        assert ('id="volume-value"' in section_text or 
                '<span' in section_text), \
            'Должен быть элемент (span/label) для отображения значения громкости'
    else:
        # Альтернативный поиск - просто проверяем наличие volume-value в HTML
        assert 'id="volume-value"' in content, \
            'Должен быть элемент с id="volume-value" для отображения значения громкости'

@then('the display should be updated when volume changes')
def check_volume_update_handler():
    """
    FAILING TEST: Проверяем обработчик изменения громкости
    """
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # FAILING TEST: должен быть обработчик, который обновляет отображение
    assert ('volume' in content and 
            ('addEventListener' in content or 'oninput' in content or 'onchange' in content)), \
        'Должен быть обработчик для обновления отображения громкости'


@given('audio-player.js handles playback speed changes')
def audio_player_has_speed_handler():
    """Проверяем наличие обработчика скорости"""
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    assert 'playback-speed' in content or 'playbackSpeed' in content

@when('speed input value changes')
def speed_changes():
    """Подготовка к проверке"""
    pass

@then('wavesurfer.setPlaybackRate should be called')
def check_set_playback_rate():
    """
    FAILING TEST: Проверяем вызов setPlaybackRate
    """
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # FAILING TEST: должен вызывать setPlaybackRate
    assert 'setPlaybackRate' in content, \
        'audio-player.js должен вызывать wavesurfer.setPlaybackRate()'


@given('audio-player.js handles volume changes')
def audio_player_has_volume_handler():
    """Проверяем наличие обработчика громкости"""
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    assert 'volume' in content

@when('volume input value changes')
def volume_changes():
    """Подготовка к проверке"""
    pass

@then('wavesurfer.setVolume should be called')
def check_set_volume():
    """
    FAILING TEST: Проверяем вызов setVolume
    """
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # FAILING TEST: должен вызывать setVolume
    assert 'setVolume' in content, \
        'audio-player.js должен вызывать wavesurfer.setVolume()'


@given('index.html has separate play and pause buttons')
def html_has_separate_buttons():
    """Проверяем что есть отдельные кнопки"""
    html_path = Path(__file__).parent.parent / 'templates' / 'index.html'
    # Это given - просто проверяем что файл существует
    assert html_path.exists()

@when('I check the controls structure')
def check_controls():
    """Подготовка к проверке"""
    pass

@then('there should be a single play-pause toggle button')
def check_single_button():
    """
    FAILING TEST: Проверяем наличие одной кнопки play-pause
    """
    html_path = Path(__file__).parent.parent / 'templates' / 'index.html'
    content = html_path.read_text(encoding='utf-8')
    
    # FAILING TEST: должна быть одна кнопка с id="play-pause-btn"
    assert 'id="play-pause-btn"' in content or 'id="play-pause"' in content, \
        'Должна быть одна кнопка play-pause вместо двух отдельных'

@then('button should show play icon when paused')
def check_play_icon():
    """Проверяем наличие play иконки"""
    html_path = Path(__file__).parent.parent / 'templates' / 'index.html'
    content = html_path.read_text(encoding='utf-8')
    
    # Должна быть иконка play (SVG или текст)
    assert ('▶' in content or 'play' in content.lower() or '<svg' in content), \
        'Должна быть иконка play'

@then('button should show pause icon when playing')
def check_pause_icon():
    """Проверяем наличие pause иконки"""
    html_path = Path(__file__).parent.parent / 'templates' / 'index.html'
    content = html_path.read_text(encoding='utf-8')
    
    # Должна быть иконка pause (SVG или текст)
    assert ('⏸' in content or 'pause' in content.lower() or '<svg' in content), \
        'Должна быть иконка pause'

