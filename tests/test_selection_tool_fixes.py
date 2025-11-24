"""
Тесты для исправлений Selection Tool
"""
from pathlib import Path
import re
from pytest_bdd import scenarios, given, when, then, parsers

# Загружаем сценарии из feature-файла
scenarios('features/selection_tool_fixes.feature')

test_context = {}

@given('selection-tool.js contains clearSelection function')
def selection_tool_has_clear_selection():
    """Проверяем что файл существует и содержит функцию"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    assert selection_tool_path.exists()
    content = selection_tool_path.read_text(encoding='utf-8')
    assert 'function clearSelection()' in content

@when('I check clearSelection code')
def check_clear_selection_code():
    """Сохраняем содержимое для проверки"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    return selection_tool_path.read_text(encoding='utf-8')

@then('function should call selectionToolCurrentRegion.remove()')
def check_uses_region_remove():
    """
    FAILING TEST: Проверяем что используется удаление конкретного региона
    """
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    # Ищем функцию clearSelection
    func_match = re.search(
        r'function clearSelection\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match, "Функция clearSelection не найдена"
    func_body = func_match.group(0)
    
    # FAILING TEST: должен вызывать remove() на текущем регионе
    assert 'selectionToolCurrentRegion.remove()' in func_body, \
        'clearSelection должна удалять только текущий регион через .remove()'

@then('function should NOT call clearRegions() to delete all regions')
def check_not_uses_clear_regions():
    """Проверяем что НЕ используется clearRegions"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function clearSelection\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match
    func_body = func_match.group(0)
    
    # НЕ должно быть clearRegions()
    assert 'clearRegions()' not in func_body, \
        'clearSelection НЕ должна использовать clearRegions()'

@then('function should NOT delete all regions in a loop')
def check_not_uses_foreach():
    """Проверяем что НЕ используется forEach для удаления всех регионов"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function clearSelection\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match
    func_body = func_match.group(0)
    
    # НЕ должно быть getRegions() с forEach
    assert not (('getRegions()' in func_body or 'getRegions(' in func_body) and 'forEach' in func_body), \
        'clearSelection НЕ должна удалять все регионы в цикле'


@given('selection-tool.js contains zoomToRegion function')
def selection_tool_has_zoom():
    """Проверяем что файл содержит функцию zoomToRegion"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    assert 'function zoomToRegion()' in content

@when('I check zoomToRegion code')
def check_zoom_to_region_code():
    """Сохраняем содержимое для проверки"""
    pass

@then('function should call wavesurfer.zoom()')
def check_uses_zoom():
    """
    FAILING TEST: Проверяем что используется wavesurfer.zoom()
    """
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function zoomToRegion\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match, "Функция zoomToRegion не найдена"
    func_body = func_match.group(0)
    
    # Должен вызывать zoom()
    assert 'wavesurfer.zoom(' in func_body, \
        'zoomToRegion должна вызывать wavesurfer.zoom()'

@then('function should call wavesurfer.seekTo()')
def check_uses_seekto():
    """Проверяем что используется wavesurfer.seekTo()"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function zoomToRegion\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match
    func_body = func_match.group(0)
    
    assert 'wavesurfer.seekTo(' in func_body, \
        'zoomToRegion должна вызывать wavesurfer.seekTo()'

@then('function should use parameters from selectionToolCurrentRegion')
def check_uses_current_region():
    """Проверяем что используются параметры текущего региона"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function zoomToRegion\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match
    func_body = func_match.group(0)
    
    assert 'selectionToolCurrentRegion.start' in func_body or 'selectionToolCurrentRegion.end' in func_body, \
        'zoomToRegion должна использовать параметры из selectionToolCurrentRegion'


@given('selection-tool.js contains playSelection function')
def selection_tool_has_play_selection():
    """Проверяем что файл содержит функцию playSelection"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    assert 'function playSelection()' in content

@when('I check playSelection code')
def check_play_selection_code():
    """Сохраняем содержимое для проверки"""
    pass

@then('function should use timeupdate event handler')
def check_uses_timeupdate():
    """
    FAILING TEST: Проверяем что используется событие timeupdate
    """
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function playSelection\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match, "Функция playSelection не найдена"
    func_body = func_match.group(0)
    
    # FAILING TEST: должна подписываться на 'timeupdate'
    assert "'timeupdate'" in func_body or '"timeupdate"' in func_body, \
        'playSelection должна использовать событие timeupdate для отслеживания позиции'

@then('handler should check currentTime >= region.end')
def check_compares_time():
    """
    FAILING TEST: Проверяем что сравнивается текущее время с концом региона
    """
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function playSelection\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match
    func_body = func_match.group(0)
    
    # FAILING TEST: должна проверять currentTime >= end
    assert '>=' in func_body and 'getCurrentTime()' in func_body and '.end' in func_body, \
        'playSelection должна проверять currentTime >= region.end'

@then('handler should call pause() when reaching end')
def check_calls_pause():
    """Проверяем что вызывается pause() в обработчике"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function playSelection\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match
    func_body = func_match.group(0)
    
    # Должна вызывать pause()
    assert 'pause()' in func_body, \
        'playSelection должна вызывать pause() при достижении конца региона'


@given('selection-tool.js contains ensureAudioFileId function')
def selection_tool_has_ensure():
    """
    FAILING TEST: Проверяем что файл содержит функцию ensureAudioFileId
    """
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    assert 'function ensureAudioFileId()' in content, \
        'selection-tool.js должен содержать функцию ensureAudioFileId()'

@when('function is called')
def call_function():
    """Подготовка к проверке"""
    pass

@then('it should check window.currentAudioFileId')
def check_uses_window_current():
    """Проверяем что используется window.currentAudioFileId"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function ensureAudioFileId\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match
    func_body = func_match.group(0)
    
    assert 'window.currentAudioFileId' in func_body, \
        'ensureAudioFileId должна проверять window.currentAudioFileId'

@then('set selectionToolCurrentAudioFileId from global variable')
def check_sets_selection_tool_id():
    """Проверяем что устанавливается selectionToolCurrentAudioFileId"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    func_match = re.search(
        r'function ensureAudioFileId\(\).*?\n\}',
        content,
        re.DOTALL
    )
    assert func_match
    func_body = func_match.group(0)
    
    assert 'selectionToolCurrentAudioFileId' in func_body and '=' in func_body, \
        'ensureAudioFileId должна устанавливать selectionToolCurrentAudioFileId'


@given('audio-player.js не содержит функций кэширования')
def audio_player_has_no_cache():
    """Проверяем что файл не содержит кэширующей логики."""
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    test_context.clear()
    test_context['audio_player_content'] = content
    assert 'cacheWaveSurferPlugins' not in content, 'cacheWaveSurferPlugins должна быть удалена'
    assert 'window.waveSurferRegionsPlugin' not in content, 'Не должно быть window.waveSurferRegionsPlugin'


@when('я проверяю реализацию getWaveSurferRegionsPlugin')
def inspect_get_regions():
    """Сохраняем тело функции getWaveSurferRegionsPlugin."""
    content = test_context.get('audio_player_content')
    if content is None:
        audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
        content = audio_player_path.read_text(encoding='utf-8')
        test_context['audio_player_content'] = content
    marker = 'function getWaveSurferRegionsPlugin()'
    assert marker in content, 'Функция getWaveSurferRegionsPlugin должна существовать'
    start = content.index(marker)
    brace_count = 0
    body_chars = []
    started = False
    for char in content[start:]:
        body_chars.append(char)
        if char == '{':
            brace_count += 1
            started = True
        elif char == '}':
            if started:
                brace_count -= 1
                if brace_count == 0:
                    break
    body = ''.join(body_chars)
    test_context['get_regions_body'] = body


@then('функция должна использовать wavesurfer.getActivePlugins()')
def ensure_uses_get_active():
    """Проверяем что функция обращается к wavesurfer.getActivePlugins()."""
    body = test_context.get('get_regions_body', '')
    assert 'getActivePlugins' in body, 'Должен быть вызов wavesurfer.getActivePlugins()'


@then('код не должен обращаться к window.waveSurferRegionsPlugin')
def ensure_no_window_reference():
    """Проверяем отсутствие ссылок на window.waveSurferRegionsPlugin."""
    content = test_context.get('audio_player_content', '')
    assert 'window.waveSurferRegionsPlugin' not in content, \
        'Не должно быть обращений к window.waveSurferRegionsPlugin'

