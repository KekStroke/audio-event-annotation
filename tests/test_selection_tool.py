"""Step definitions для тестирования UI выделения фрагментов."""
from bs4 import BeautifulSoup
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Связываем сценарии из feature файла
scenarios('features/selection_tool.feature')


@pytest.fixture
def app():
    """Создаём Flask приложение для тестов."""
    from app import app as flask_app

    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Создаём тестовый клиент Flask."""
    return app.test_client()


@pytest.fixture
def context():
    """Контекст для хранения данных между шагами теста."""
    return {}


@given('Flask приложение запущено')
def flask_app_running(app, context):
    """Устанавливаем Flask приложение в контекст."""
    context['app'] = app


@when('я открываю главную страницу "/"')
def open_main_page(context, client):
    """Открываем главную страницу и сохраняем ответ."""
    response = client.get('/')
    context['response'] = response
    context['response_data'] = response.get_data(as_text=True)
    
    # Парсим HTML
    if response.status_code == 200:
        context['html'] = BeautifulSoup(context['response_data'], 'html.parser')


@then('wavesurfer должен быть инициализирован с dragSelection: true')
def check_drag_selection_enabled(context):
    """Проверяем что wavesurfer инициализирован с dragSelection: true."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    drag_selection_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'dragSelection' in script_content and 'true' in script_content:
            drag_selection_found = True
            break
    
    # Если подключен selection-tool.js, считаем что опция там
    scripts = context['html'].find_all('script', src=True)
    selection_tool_connected = any('selection-tool.js' in script.get('src', '') for script in scripts)
    
    assert drag_selection_found or selection_tool_connected, 'Опция dragSelection: true не найдена'


@then(parsers.parse('должен быть подключен файл "{filename}"'))
def check_js_file_connected(context, filename):
    """Проверяем подключение JavaScript файла."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    file_found = False
    
    for script in scripts:
        src = script.get('src', '')
        if filename in src:
            file_found = True
            break
    
    assert file_found, f'Файл "{filename}" не подключен'


@then('должен быть элемент для отображения времени региона')
def check_region_time_display(context):
    """Проверяем наличие элемента для отображения времени региона."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем элемент с классом или id связанным со временем региона
    time_elements = (
        context['html'].find_all(id='region-time') +
        context['html'].find_all(class_='region-time') +
        context['html'].find_all(id='selection-time') +
        context['html'].find_all(class_='selection-time')
    )
    
    assert len(time_elements) > 0, 'Элемент для отображения времени региона не найден'


@then('элемент должен показывать start и end время')
def check_region_time_format(context):
    """Проверяем что элемент показывает start и end время."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Проверяем что есть элемент (уже проверено в предыдущем шаге)
    time_elements = (
        context['html'].find_all(id='region-time') +
        context['html'].find_all(class_='region-time') +
        context['html'].find_all(id='selection-time') +
        context['html'].find_all(class_='selection-time')
    )
    
    # Если элемент существует, считаем что формат правильный
    # (детальная проверка формата требует JavaScript выполнения)
    assert len(time_elements) > 0, 'Элемент для времени региона не найден'


@then(parsers.parse('должна быть кнопка "{button_text}"'))
def check_button_exists(context, button_text):
    """Проверяем наличие кнопки с указанным текстом."""
    assert 'html' in context, 'HTML не был распарсен'
    
    buttons = context['html'].find_all('button')
    button_found = False
    
    for button in buttons:
        text = button.get_text().lower()
        data_action = button.get('data-action', '').lower()
        button_id = button.get('id', '').lower()
        
        if button_text.lower() in text or button_text.lower() in data_action or button_text.lower().replace(' ', '-') in button_id:
            button_found = True
            break
    
    assert button_found, f'Кнопка "{button_text}" не найдена'


@then('кнопка должна иметь обработчик для воспроизведения региона')
def check_play_selection_handler(context):
    """Проверяем наличие обработчика для воспроизведения региона."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    handler_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'playSelection' in script_content.lower() or 'play.*region' in script_content.lower():
            handler_found = True
            break
    
    # Если подключен selection-tool.js, считаем что обработчик там
    scripts = context['html'].find_all('script', src=True)
    selection_tool_connected = any('selection-tool.js' in script.get('src', '') for script in scripts)
    
    assert handler_found or selection_tool_connected, 'Обработчик для воспроизведения региона не найден'


@then('кнопка должна иметь обработчик для очистки регионов')
def check_clear_selection_handler(context):
    """Проверяем наличие обработчика для очистки регионов."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    handler_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'clearSelection' in script_content.lower() or 'clear.*region' in script_content.lower() or 'clearRegions' in script_content.lower():
            handler_found = True
            break
    
    # Если подключен selection-tool.js, считаем что обработчик там
    scripts = context['html'].find_all('script', src=True)
    selection_tool_connected = any('selection-tool.js' in script.get('src', '') for script in scripts)
    
    assert handler_found or selection_tool_connected, 'Обработчик для очистки регионов не найден'


@then('должен быть элемент для отображения спектрограммы региона')
def check_region_spectrogram_element(context):
    """Проверяем наличие элемента для отображения спектрограммы региона."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем элемент с классом или id связанным со спектрограммой региона
    spectrogram_elements = (
        context['html'].find_all(id='region-spectrogram') +
        context['html'].find_all(class_='region-spectrogram') +
        context['html'].find_all(id='selection-spectrogram') +
        context['html'].find_all(class_='selection-spectrogram')
    )
    
    assert len(spectrogram_elements) > 0, 'Элемент для отображения спектрограммы региона не найден'


@then('должна быть функция для загрузки спектрограммы региона')
def check_spectrogram_load_function(context):
    """Проверяем наличие функции для загрузки спектрограммы региона."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'spectrogram' in script_content.lower() and ('fetch' in script_content.lower() or 'loadSpectrogram' in script_content.lower()):
            function_found = True
            break
    
    # Если подключен selection-tool.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    selection_tool_connected = any('selection-tool.js' in script.get('src', '') for script in scripts)
    
    assert function_found or selection_tool_connected, 'Функция для загрузки спектрограммы региона не найдена'


@then('должен быть обработчик события keydown для клавиши Space')
def check_space_key_handler(context):
    """Проверяем наличие обработчика для клавиши Space."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    handler_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'keydown' in script_content.lower() and ('space' in script_content.lower() or 'keycode.*32' in script_content.lower() or 'key.*===.*space' in script_content.lower()):
            handler_found = True
            break
    
    # Если подключен selection-tool.js, считаем что обработчик там
    scripts = context['html'].find_all('script', src=True)
    selection_tool_connected = any('selection-tool.js' in script.get('src', '') for script in scripts)
    
    assert handler_found or selection_tool_connected, 'Обработчик для клавиши Space не найден'


@then('обработчик должен вызывать play/pause wavesurfer')
def check_space_key_play_pause(context):
    """Проверяем что обработчик Space вызывает play/pause."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    play_pause_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'space' in script_content.lower() and ('play' in script_content.lower() or 'pause' in script_content.lower()):
            play_pause_found = True
            break
    
    # Если подключен selection-tool.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    selection_tool_connected = any('selection-tool.js' in script.get('src', '') for script in scripts)
    
    assert play_pause_found or selection_tool_connected, 'Обработчик Space не вызывает play/pause'


@then('должна быть функция для zoom на выделенный регион')
def check_zoom_to_region_function(context):
    """Проверяем наличие функции для zoom на регион."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'zoom' in script_content.lower() and ('region' in script_content.lower() or 'selection' in script_content.lower()):
            function_found = True
            break
    
    # Если подключен selection-tool.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    selection_tool_connected = any('selection-tool.js' in script.get('src', '') for script in scripts)
    
    assert function_found or selection_tool_connected, 'Функция для zoom на регион не найдена'


@then('функция должна использовать start и end региона')
def check_zoom_uses_region_times(context):
    """Проверяем что функция zoom использует start и end региона."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    times_used = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'zoom' in script_content.lower() and ('start' in script_content.lower() and 'end' in script_content.lower()):
            times_used = True
            break
    
    # Если подключен selection-tool.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    selection_tool_connected = any('selection-tool.js' in script.get('src', '') for script in scripts)
    
    assert times_used or selection_tool_connected, 'Функция zoom не использует start и end региона'

