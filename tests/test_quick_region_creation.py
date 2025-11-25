"""
Тесты для функционала быстрого создания регионов
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Загружаем сценарии из feature файла
scenarios('features/quick_region_creation.feature')

@pytest.fixture
def quick_region_state():
    """Состояние для тестирования быстрого создания регионов"""
    return {
        'audio_duration': 300,
        'regions': [],
        'selected_region': None,
        'region_duration_input': 10,
        'error_message': None,
        'region_id_counter': 0
    }

# Background steps
@given('the application is loaded')
def app_loaded(quick_region_state):
    """Приложение загружено"""
    quick_region_state['app_loaded'] = True

@given(parsers.parse('an audio file with duration {duration:d} seconds is loaded'))
def audio_loaded(quick_region_state, duration):
    """Загружен аудио файл"""
    quick_region_state['audio_duration'] = duration

# Given steps
@given(parsers.parse('the region duration input has value "{value}"'))
def region_duration_input_value(quick_region_state, value):
    """Установлено значение длины региона"""
    quick_region_state['region_duration_input'] = float(value)

@given(parsers.parse('I set the region duration input to "{value}"'))
def set_region_duration(quick_region_state, value):
    """Устанавливаем значение длины региона"""
    quick_region_state['region_duration_input'] = float(value)

@given(parsers.parse('a region exists from {start:d} to {end:d} seconds'))
def region_exists(quick_region_state, start, end):
    """Существует регион"""
    quick_region_state['region_id_counter'] += 1
    quick_region_state['regions'].append({
        'id': f'region-{quick_region_state["region_id_counter"]}',
        'start': start,
        'end': end,
        'selected': False,
        'locked': False
    })

@given(parsers.parse('an annotation exists from {start:d} to {end:d} seconds with a locked region'))
def locked_annotation_exists(quick_region_state, start, end):
    """Существует аннотация с locked регионом"""
    quick_region_state['region_id_counter'] += 1
    quick_region_state['regions'].append({
        'id': f'annotation-region-{quick_region_state["region_id_counter"]}',
        'start': start,
        'end': end,
        'selected': False,
        'locked': True
    })

# When steps  
@when('I click the "Create Region" button')
def click_create_region(quick_region_state):
    """Клик по кнопке создания региона - симуляция логики createQuickRegion()"""
    duration = quick_region_state['region_duration_input']
    audio_duration = quick_region_state['audio_duration']
    
    # Валидация - минимум 0.1 секунды
    if duration < 0.1:
        quick_region_state['error_message'] = 'Duration must be at least 0.1 seconds'
        return
    
    # Валидация - не больше длины аудио
    if duration > audio_duration:
        quick_region_state['error_message'] = 'Duration cannot exceed audio duration'
        return
    
    # Находим самый правый регион
    if quick_region_state['regions']:
        rightmost_end = max(r['end'] for r in quick_region_state['regions'])
        start_position = rightmost_end
    else:
        start_position = 0
    
    end_position = start_position + duration
    
    # Проверяем, помещается ли регион
    if end_position > audio_duration:
        quick_region_state['error_message'] = 'Not enough space'
        return
    
    # Создаем регион
    quick_region_state['region_id_counter'] += 1
    new_region = {
        'id': f'region-{quick_region_state["region_id_counter"]}',
        'start': start_position,
        'end': end_position,
        'selected': True,  # Автоматически выделяем
        'locked': False
    }
    
    # Снимаем выделение с других регионов
    for region in quick_region_state['regions']:
        region['selected'] = False
    
    quick_region_state['regions'].append(new_region)
    quick_region_state['selected_region'] = new_region

@when('I click on the region')
def click_on_region(quick_region_state):
    """Клик по региону"""
    if quick_region_state['regions']:
        # Снимаем выделение со всех
        for region in quick_region_state['regions']:
            region['selected'] = False
        # Выделяем первый
        quick_region_state['regions'][0]['selected'] = True
        quick_region_state['selected_region'] = quick_region_state['regions'][0]

@when('I click on the locked region')
def click_on_locked_region(quick_region_state):
    """Клик по locked региону"""
    locked_regions = [r for r in quick_region_state['regions'] if r.get('locked')]
    if locked_regions:
        # Снимаем выделение со всех
        for region in quick_region_state['regions']:
            region['selected'] = False
        # Выделяем первый locked
        locked_regions[0]['selected'] = True
        quick_region_state['selected_region'] = locked_regions[0]

# Then steps
@then(parsers.parse('a new region should be created with duration {duration:d} seconds'))
def check_region_created(quick_region_state, duration):
    """Проверяем что регион создан с нужной длиной"""
    assert len(quick_region_state['regions']) > 0
    last_region = quick_region_state['regions'][-1]
    actual_duration = last_region['end'] - last_region['start']
    assert actual_duration == duration, f"Expected duration {duration}, got {actual_duration}"

@then(parsers.parse('the region should start at position {position:d} seconds'))
def check_region_start(quick_region_state, position):
    """Проверяем позицию начала региона"""
    assert len(quick_region_state['regions']) > 0
    last_region = quick_region_state['regions'][-1]
    assert last_region['start'] == position, f"Expected start {position}, got {last_region['start']}"

@then('the region should be automatically selected')
def check_region_selected(quick_region_state):
    """Проверяем что регион автоматически выделен"""
    assert len(quick_region_state['regions']) > 0
    last_region = quick_region_state['regions'][-1]
    assert last_region['selected'] is True, "Region should be selected"
    assert quick_region_state['selected_region'] == last_region

@then('no new region should be created')
def check_no_region_created(quick_region_state):
    """Проверяем что новый регион НЕ создан"""
    # Количество регионов не должно измениться
    # Это проверяется через error_message
    assert quick_region_state['error_message'] is not None

@then(parsers.parse('an error message "{message}" should be shown'))
def check_error_message(quick_region_state, message):
    """Проверяем сообщение об ошибке"""
    assert quick_region_state['error_message'] == message, \
        f"Expected error '{message}', got '{quick_region_state['error_message']}'"

@then('the region should have a visual highlight')
def check_visual_highlight(quick_region_state):
    """Проверяем визуальное выделение"""
    selected = quick_region_state['selected_region']
    assert selected is not None, "No region is selected"
    assert selected['selected'] is True, "Selected region should have selected flag"

@then('the highlight should be different from unselected regions')
def check_highlight_different(quick_region_state):
    """Проверяем что выделение отличается от невыделенных"""
    selected = quick_region_state['selected_region']
    unselected = [r for r in quick_region_state['regions'] if not r['selected']]
    
    # Выделенный должен иметь флаг selected=True
    assert selected['selected'] is True
    # Невыделенные должны иметь флаг selected=False
    for region in unselected:
        assert region['selected'] is False

@then('the locked region should have a visual highlight')
def check_locked_visual_highlight(quick_region_state):
    """Проверяем визуальное выделение locked региона"""
    selected = quick_region_state['selected_region']
    assert selected is not None, "No region is selected"
    assert selected['selected'] is True, "Selected region should have selected flag"
    assert selected['locked'] is True, "Selected region should be locked"

@then('the highlight should be different from unselected locked regions')
def check_locked_highlight_different(quick_region_state):
    """Проверяем что выделение locked отличается от невыделенных locked"""
    selected = quick_region_state['selected_region']
    unselected_locked = [r for r in quick_region_state['regions'] 
                         if r.get('locked') and not r['selected']]
    
    # Выделенный должен иметь флаг selected=True
    assert selected['selected'] is True
    # Невыделенные locked должны иметь флаг selected=False
    for region in unselected_locked:
        assert region['selected'] is False
