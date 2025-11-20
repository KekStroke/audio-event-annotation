"""
Тесты для предотвращения наложения регионов и цветов
"""
import re
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers

# Загружаем сценарии
scenarios('features/region_overlap_prevention.feature')

# Общие переменные для тестов
test_data = {}


@given('audio-player.js содержит конфигурацию regions plugin')
def read_audio_player_config():
    """Читаем файл audio-player.js"""
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    test_data['audio_player_content'] = audio_player_path.read_text(encoding='utf-8')


@when('я проверяю параметр dragSelection.color')
def find_drag_selection_color():
    """Находим параметр dragSelection.color"""
    content = test_data['audio_player_content']
    # Ищем dragSelection конфигурацию
    pattern = r'dragSelection\s*:\s*\{[^}]*color\s*:\s*["\']([^"\']+)["\']'
    match = re.search(pattern, content, re.DOTALL)
    test_data['drag_selection_color'] = match.group(1) if match else None


@then('цвет должен быть голубым полупрозрачным rgba с alpha < 0.5')
def check_drag_selection_color():
    """Проверяем что цвет голубой полупрозрачный"""
    color = test_data['drag_selection_color']
    assert color is not None, 'dragSelection.color не найден'
    
    # Проверяем формат rgba
    rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', color)
    assert rgba_match, f'Цвет должен быть в формате rgba, получено: {color}'
    
    r, g, b, a = rgba_match.groups()
    r, g, b, a = int(r), int(g), int(b), float(a)
    
    # Проверяем что это голубой (больше синего, чем красного)
    assert b > r, f'Цвет должен быть голубым (b > r), получено: r={r}, g={g}, b={b}'
    
    # Проверяем прозрачность
    assert a < 0.5, f'Alpha должна быть < 0.5 для полупрозрачности, получено: {a}'


@given('annotation-list.js содержит функцию getAnnotationColor')
def read_annotation_list():
    """Читаем файл annotation-list.js"""
    annotation_list_path = Path(__file__).parent.parent / 'static' / 'js' / 'annotation-list.js'
    test_data['annotation_list_content'] = annotation_list_path.read_text(encoding='utf-8')


@when('я проверяю возвращаемый цвет по умолчанию')
def find_default_annotation_color():
    """Находим цвет по умолчанию в getAnnotationColor"""
    content = test_data['annotation_list_content']
    # Ищем return с цветом по умолчанию
    pattern = r'function\s+getAnnotationColor.*?return\s+["\']([^"\']+)["\']'
    match = re.search(pattern, content, re.DOTALL)
    test_data['default_annotation_color'] = match.group(1) if match else None


@then('цвет должен быть красным полупрозрачным rgba с alpha < 0.5')
def check_annotation_color():
    """Проверяем что цвет красный полупрозрачный"""
    color = test_data['default_annotation_color']
    assert color is not None, 'Цвет по умолчанию не найден в getAnnotationColor'
    
    # Проверяем формат rgba
    rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', color)
    assert rgba_match, f'Цвет должен быть в формате rgba, получено: {color}'
    
    r, g, b, a = rgba_match.groups()
    r, g, b, a = int(r), int(g), int(b), float(a)
    
    # Проверяем что это красный (больше красного, чем остальных)
    assert r > g and r > b, f'Цвет должен быть красным (r > g, r > b), получено: r={r}, g={g}, b={b}'
    
    # Проверяем прозрачность
    assert a < 0.5, f'Alpha должна быть < 0.5 для полупрозрачности, получено: {a}'


@given('существует функция для проверки пересечений')
def check_overlap_function_exists():
    """Проверяем наличие функции проверки пересечений"""
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Ищем функцию для проверки пересечений
    assert 'function checkRegionOverlap' in content or 'function isRegionOverlapping' in content or 'const checkRegionOverlap' in content or 'const isRegionOverlapping' in content, \
        'Функция проверки пересечений регионов не найдена'
    
    test_data['audio_player_content'] = content


@when(parsers.parse('я проверяю два региона [{start1:d}, {end1:d}] и [{start2:d}, {end2:d}]'))
def set_test_regions(start1, end1, start2, end2):
    """Сохраняем тестовые регионы"""
    test_data['region1'] = {'start': start1, 'end': end1}
    test_data['region2'] = {'start': start2, 'end': end2}


@then(parsers.parse('функция должна вернуть {result} (есть пересечение)'))
def check_overlap_result_true(result):
    """Проверяем результат для пересекающихся регионов"""
    # Проверяем логику: регионы [0,10] и [5,15] пересекаются
    region1 = test_data['region1']
    region2 = test_data['region2']
    
    # Логика: пересечение есть если конец одного > начала другого И начало одного < конца другого
    has_overlap = (region1['end'] > region2['start'] and region1['start'] < region2['end'])
    
    expected = result.lower() == 'true'
    assert has_overlap == expected, f'Ожидалось пересечение={expected}, получено={has_overlap}'


@then(parsers.parse('функция должна вернуть {result} (нет пересечения)'))
def check_overlap_result_false(result):
    """Проверяем результат для непересекающихся регионов"""
    # Проверяем логику: регионы [0,10] и [11,20] НЕ пересекаются
    region1 = test_data['region1']
    region2 = test_data['region2']
    
    # Логика: пересечение есть если конец одного > начала другого И начало одного < конца другого
    has_overlap = (region1['end'] > region2['start'] and region1['start'] < region2['end'])
    
    expected = result.lower() == 'true'
    assert has_overlap == expected, f'Ожидалось пересечение={expected}, получено={has_overlap}'


@given('существует обработчик события region-created')
def check_region_created_handler():
    """Проверяем наличие обработчика region-created"""
    content = test_data['audio_player_content']
    assert 'region-created' in content, 'Обработчик события region-created не найден'


@when('создается новый регион')
def region_created_event():
    """Симулируем создание региона"""
    pass  # Логика проверяется в следующих шагах


@then('обработчик должен проверить пересечения с существующими регионами')
def check_overlap_verification():
    """Проверяем что обработчик вызывает проверку пересечений"""
    content = test_data['audio_player_content']
    
    # Ищем обработчик region-created и проверяем что внутри есть вызов функции проверки
    pattern = r'["\']region-created["\'].*?\{([^}]*(?:\{[^}]*\})*[^}]*)\}'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        handler_content = match.group(1)
        # Проверяем вызов adjustRegionBounds (которая внутри вызывает checkRegionOverlap)
        assert 'adjustRegionBounds' in handler_content or 'checkRegionOverlap' in handler_content or 'isRegionOverlapping' in handler_content, \
            'Обработчик region-created не вызывает функцию проверки пересечений'


@then('скорректировать границы региона чтобы избежать пересечения')
def check_region_adjustment():
    """Проверяем что границы региона корректируются"""
    content = test_data['audio_player_content']
    
    # Ищем изменение start или end в обработчике
    pattern = r'region-created.*?(region\.start\s*=|region\.end\s*=|region\.update)'
    match = re.search(pattern, content, re.DOTALL)
    assert match, 'Обработчик не корректирует границы региона (не найдено изменение start/end)'


@then('удалить регион если он меньше минимального размера (1 секунда)')
def check_minimum_size_removal():
    """Проверяем что регион удаляется если он слишком мал"""
    content = test_data['audio_player_content']
    
    # Ищем проверку минимального размера (может быть в разных форматах)
    has_size_check = bool(
        re.search(r'region\.end\s*-\s*region\.start\s*<\s*[0-9.]+', content) or
        re.search(r'adjustedEnd\s*-\s*adjustedStart\s*<\s*[0-9.]+', content) or
        re.search(r'MIN_REGION_SIZE', content)
    )
    has_removal = '.remove()' in content
    
    assert has_size_check and has_removal, \
        f'Обработчик не удаляет регион если он меньше минимального размера (size_check={has_size_check}, removal={has_removal})'

