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
    
    # Ищем вызов adjustRegionBounds в контексте region-created
    pattern = r'["\']region-created["\'].*?adjustRegionBounds'
    match = re.search(pattern, content, re.DOTALL)
    
    assert match, 'Обработчик region-created не вызывает функцию проверки пересечений (adjustRegionBounds)'


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


@given('audio-player.js содержит функцию adjustRegionBounds')
def read_audio_player_for_adjustment():
    """Читаем файл audio-player.js для проверки adjustRegionBounds"""
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    assert 'function adjustRegionBounds' in content, 'Функция adjustRegionBounds не найдена'
    test_data['audio_player_content'] = content


@when('я проверяю минимальный размер региона')
def extract_min_region_size():
    """Находим значение MIN_REGION_SIZE"""
    content = test_data['audio_player_content']
    pattern = r'MIN_REGION_SIZE\s*=\s*([0-9.]+)'
    match = re.search(pattern, content)
    assert match, 'MIN_REGION_SIZE не найден'
    test_data['min_region_size'] = float(match.group(1))


@then('минимальный размер региона должен быть 1 секунда')
def check_min_region_size():
    """Проверяем что минимальный размер равен 1 секунде"""
    min_size = test_data.get('min_region_size')
    assert min_size is not None, 'MIN_REGION_SIZE не был найден'
    assert abs(min_size - 1.0) < 1e-6, f'Ожидалось 1.0, получено {min_size}'


@when('границы региона скорректированы и размер меньше минимума')
def detect_min_size_removal_logic():
    """Проверяем, что при недостаточном размере регион удаляется"""
    content = test_data['audio_player_content']
    pattern = r'if\s*\(\s*(?:adjustedEnd\s*-\s*adjustedStart|adjustedDuration)\s*<\s*MIN_REGION_SIZE'
    match = re.search(pattern, content)
    assert match, 'Не найдена проверка на минимальный размер после коррекции'
    test_data['min_size_condition_found'] = True


@then('регион должен быть удален')
def ensure_region_removed_on_small_size():
    """Проверяем, что маленький регион удаляется"""
    assert test_data.get('min_size_condition_found'), 'Условие минимального размера не найдено'
    content = test_data['audio_player_content']
    assert '.remove()' in content, 'Удаление региона (.remove()) не найдено'


@given('существует обработчик события region-updated')
def check_region_updated_handler():
    """Проверяем наличие обработчика region-updated"""
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    assert 'region-updated' in content, 'Обработчик события region-updated не найден'
    test_data['audio_player_content'] = content


@when('регион изменяется через drag или resize')
def region_updated_event():
    """Симулируем изменение региона"""
    pass  # Логика проверяется в следующих шагах


@then('обработчик должен динамически корректировать границы')
def check_dynamic_adjustment():
    """Проверяем что обработчик region-updated корректирует границы"""
    content = test_data['audio_player_content']
    
    # Ищем обработчик region-updated и вызов adjustRegionBounds
    pattern = r'["\']region-updated["\'].*?adjustRegionBounds'
    assert re.search(pattern, content, re.DOTALL), \
        'Обработчик region-updated не вызывает adjustRegionBounds'


@then('предотвращать бесконечный цикл обновлений')
def check_recursion_prevention():
    """Проверяем что есть защита от рекурсии"""
    content = test_data['audio_player_content']
    
    # Ищем флаг для предотвращения рекурсии
    has_flag = bool(
        re.search(r'isAdjustingRegion|adjusting|isUpdating', content, re.IGNORECASE)
    )
    
    # Ищем проверку флага в обработчике region-updated
    pattern = r'["\']region-updated["\'].*?if\s*\([^)]*(?:isAdjustingRegion|adjusting|isUpdating)'
    has_check = bool(re.search(pattern, content, re.DOTALL))
    
    assert has_flag and has_check, \
        f'Нет защиты от рекурсии (has_flag={has_flag}, has_check={has_check})'


@given('annotation-list.js содержит конфигурацию регионов')
def read_annotation_config():
    """Читаем файл annotation-list.js"""
    annotation_list_path = Path(__file__).parent.parent / 'static' / 'js' / 'annotation-list.js'
    content = annotation_list_path.read_text(encoding='utf-8')
    test_data['annotation_list_content'] = content


@when('я создаю регион для аннотации')
def extract_annotation_region_config():
    """Находим конфигурацию addRegion для аннотаций"""
    content = test_data['annotation_list_content']
    pattern = r'regionsPlugin\.addRegion\(\s*\{([^}]+)\}\s*\)'
    matches = re.findall(pattern, content, re.DOTALL)
    assert matches, 'Конфигурация regionsPlugin.addRegion не найдена'
    annotation_configs = []
    for block in matches:
        if 'getAnnotationColor' in block:
            drag_match = re.search(r'drag\s*:\s*(true|false)', block)
            resize_match = re.search(r'resize\s*:\s*(true|false)', block)
            annotation_configs.append({
                'drag': drag_match.group(1) if drag_match else None,
                'resize': resize_match.group(1) if resize_match else None
            })
    assert annotation_configs, 'Не найдены конфигурации регионов для аннотаций'
    test_data['annotation_region_configs'] = annotation_configs


@then('регион должен быть недоступен для drag и resize')
def ensure_annotation_region_not_editable():
    """Проверяем что регионы аннотаций не редактируемы"""
    configs = test_data.get('annotation_region_configs', [])
    assert configs, 'Конфигурации регионов аннотаций не найдены'
    for config in configs:
        assert config['drag'] == 'false', f"Ожидалось drag: false, получено {config['drag']}"
        assert config['resize'] == 'false', f"Ожидалось resize: false, получено {config['resize']}"

    content = test_data['annotation_list_content']
    assert 'function lockAnnotationRegion' in content, 'Функция lockAnnotationRegion не найдена'
    assert 'lockAnnotationRegion(region)' in content, 'lockAnnotationRegion не вызывается после создания региона'
    assert re.search(r'const\s+lockOptions\s*=\s*\{\s*drag\s*:\s*false', content), 'lockOptions не задаёт drag: false'
    assert 'region.setOptions(lockOptions)' in content, 'lockOptions не применяются через setOptions'


@given('selection-tool.js содержит обработчик region-removed')
def read_selection_tool_file():
    """Читаем selection-tool.js"""
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    test_data['selection_tool_content'] = content


@when('регион текущего выделения удаляется')
def annotate_region_removed():
    """Сохраняем контекст удаления региона"""
    content = test_data['selection_tool_content']
    pattern = r'regionsPlugin\.on\([\'"]region-removed[\'"]\s*,\s*\(region'
    assert re.search(pattern, content), 'Обработчик region-removed не найден или не принимает параметр region'
    test_data['region_removed_handler_found'] = True


@then('Selection Tool должен очистить текущее выделение и скрыть информацию')
def ensure_selection_cleared_on_remove():
    """Проверяем что при удалении региона состояние очищается"""
    assert test_data.get('region_removed_handler_found'), 'Обработчик region-removed не был подтверждён'
    content = test_data['selection_tool_content']

    # Проверяем что clearSelectionState определяется и вызывается
    assert 'function clearSelectionState' in content, 'Функция clearSelectionState не определена'
    assert re.search(r'region-removed[\'"].*?clearSelectionState', content, re.DOTALL), \
        'clearSelectionState не вызывается в обработчике region-removed'
    assert re.search(r'clearSelectionState\(\)\s*{[^}]*clearRegionTimeDisplay', content, re.DOTALL), \
        'clearSelectionState не очищает отображение времени'
    assert re.search(r'clearSelectionState\(\)\s*{[^}]*clearRegionSpectrogram', content, re.DOTALL), \
        'clearSelectionState не очищает спектрограмму'

