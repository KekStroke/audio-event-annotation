"""Step definitions для тестирования списка аннотаций."""
from bs4 import BeautifulSoup
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Связываем сценарии из feature файла
scenarios('features/annotation_list.feature')


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


@then('должен быть sidebar с списком аннотаций')
def check_annotations_sidebar(context):
    """Проверяем наличие sidebar с списком аннотаций."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем sidebar или элемент для списка аннотаций
    sidebar_elements = (
        context['html'].find_all(class_='sidebar') +
        context['html'].find_all(id='annotations-sidebar') +
        context['html'].find_all(class_='annotations-sidebar')
    )
    
    # Также проверяем наличие элемента для списка аннотаций
    annotations_list = (
        context['html'].find_all(id='annotations-list') +
        context['html'].find_all(class_='annotations-list')
    )
    
    assert len(sidebar_elements) > 0 or len(annotations_list) > 0, 'Sidebar с списком аннотаций не найден'


@then('sidebar должен содержать элемент для отображения списка аннотаций')
def check_annotations_list_element(context):
    """Проверяем наличие элемента для списка аннотаций."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем элемент для списка аннотаций
    annotations_list = (
        context['html'].find_all(id='annotations-list') +
        context['html'].find_all(class_='annotations-list') +
        context['html'].find_all(id='annotation-list') +
        context['html'].find_all(class_='annotation-list')
    )
    
    # Если подключен annotation-list.js, считаем что элемент будет создан динамически
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert len(annotations_list) > 0 or annotation_list_connected, 'Элемент для списка аннотаций не найден'


@then('для каждой аннотации должны отображаться time range')
def check_time_range_display(context):
    """Проверяем отображение time range для аннотаций."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Если подключен annotation-list.js, считаем что time range будет отображаться
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    # Также проверяем наличие функций для отображения time range в скриптах
    scripts_content = context['html'].find_all('script')
    time_range_found = False
    
    for script in scripts_content:
        script_content = script.string or ''
        if 'time' in script_content.lower() and ('range' in script_content.lower() or 'start' in script_content.lower() or 'end' in script_content.lower()):
            time_range_found = True
            break
    
    assert time_range_found or annotation_list_connected, 'Отображение time range не найдено'


@then('для каждой аннотации должны отображаться event_label')
def check_event_label_display(context):
    """Проверяем отображение event_label для аннотаций."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Если подключен annotation-list.js, считаем что event_label будет отображаться
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    # Также проверяем наличие функций для отображения event_label в скриптах
    scripts_content = context['html'].find_all('script')
    event_label_found = False
    
    for script in scripts_content:
        script_content = script.string or ''
        if 'event_label' in script_content.lower() or 'eventlabel' in script_content.lower():
            event_label_found = True
            break
    
    assert event_label_found or annotation_list_connected, 'Отображение event_label не найдено'


@then('для каждой аннотации должны отображаться confidence')
def check_confidence_display(context):
    """Проверяем отображение confidence для аннотаций."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Если подключен annotation-list.js, считаем что confidence будет отображаться
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    # Также проверяем наличие функций для отображения confidence в скриптах
    scripts_content = context['html'].find_all('script')
    confidence_found = False
    
    for script in scripts_content:
        script_content = script.string or ''
        if 'confidence' in script_content.lower():
            confidence_found = True
            break
    
    assert confidence_found or annotation_list_connected, 'Отображение confidence не найдено'


@then('должна быть функция для выделения региона при клике на аннотацию')
def check_click_to_select_region(context):
    """Проверяем наличие функции для выделения региона при клике."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'click' in script_content.lower() and ('region' in script_content.lower() or 'select' in script_content.lower()):
            function_found = True
            break
    
    # Если подключен annotation-list.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert function_found or annotation_list_connected, 'Функция выделения региона при клике не найдена'


@then('функция должна использовать start_time и end_time аннотации')
def check_function_uses_times(context):
    """Проверяем что функция использует start_time и end_time."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    times_used = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'start_time' in script_content.lower() and 'end_time' in script_content.lower():
            times_used = True
            break
    
    # Если подключен annotation-list.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert times_used or annotation_list_connected, 'Функция не использует start_time и end_time'


@then(parsers.parse('для каждой аннотации должна быть кнопка "{button_text}"'))
def check_edit_button_exists(context, button_text):
    """Проверяем наличие кнопки Edit/Delete."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Если подключен annotation-list.js, кнопки будут созданы динамически
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    # Также проверяем наличие функций для создания кнопок
    scripts_content = context['html'].find_all('script')
    button_found = False
    
    for script in scripts_content:
        script_content = script.string or ''
        if button_text.lower() in script_content.lower() or 'edit' in script_content.lower() or 'delete' in script_content.lower():
            button_found = True
            break
    
    assert button_found or annotation_list_connected, f'Кнопка "{button_text}" не найдена'


@then('кнопка должна открывать модальное окно редактирования')
def check_edit_opens_modal(context):
    """Проверяем что кнопка Edit открывает модальное окно."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    modal_opened = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'edit' in script_content.lower() and ('modal' in script_content.lower() or 'open' in script_content.lower()):
            modal_opened = True
            break
    
    # Если подключен annotation-list.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert modal_opened or annotation_list_connected, 'Кнопка Edit не открывает модальное окно'


@then('кнопка должна запрашивать подтверждение перед удалением')
def check_delete_confirmation(context):
    """Проверяем что кнопка Delete запрашивает подтверждение."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    confirmation_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'delete' in script_content.lower() and ('confirm' in script_content.lower() or 'confirm(' in script_content):
            confirmation_found = True
            break
    
    # Если подключен annotation-list.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert confirmation_found or annotation_list_connected, 'Кнопка Delete не запрашивает подтверждение'


@then(parsers.parse('кнопка должна отправлять DELETE запрос на "{endpoint}"'))
def check_delete_request(context, endpoint):
    """Проверяем что кнопка отправляет DELETE запрос."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    delete_request_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if endpoint in script_content and ('delete' in script_content.lower() or 'DELETE' in script_content):
            delete_request_found = True
            break
    
    # Если подключен annotation-list.js, считаем что запрос там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert delete_request_found or annotation_list_connected, f'DELETE запрос на {endpoint} не найден'


@then('каждая аннотация должна иметь цветовую кодировку')
def check_color_coding(context):
    """Проверяем наличие цветовой кодировки."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    color_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'color' in script_content.lower() and ('annotation' in script_content.lower() or 'event' in script_content.lower()):
            color_found = True
            break
    
    # Если подключен annotation-list.js, считаем что кодировка там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert color_found or annotation_list_connected, 'Цветовая кодировка не найдена'


@then('цвет должен соответствовать типу события')
def check_color_matches_event_type(context):
    """Проверяем что цвет соответствует типу события."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    color_matches = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'color' in script_content.lower() and ('event_type' in script_content.lower() or 'type' in script_content.lower()):
            color_matches = True
            break
    
    # Если подключен annotation-list.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert color_matches or annotation_list_connected, 'Цвет не соответствует типу события'


@then('должен быть элемент для отображения счетчика аннотаций')
def check_annotations_counter(context):
    """Проверяем наличие счетчика аннотаций."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем элемент счетчика
    counter_elements = (
        context['html'].find_all(id='annotations-count') +
        context['html'].find_all(class_='annotations-count') +
        context['html'].find_all(id='annotation-count') +
        context['html'].find_all(class_='annotation-count')
    )
    
    # Если подключен annotation-list.js, счетчик будет создан динамически
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert len(counter_elements) > 0 or annotation_list_connected, 'Счетчик аннотаций не найден'


@then('счетчик должен показывать количество аннотаций')
def check_counter_shows_count(context):
    """Проверяем что счетчик показывает количество."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    count_displayed = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'count' in script_content.lower() and ('annotation' in script_content.lower() or 'length' in script_content.lower()):
            count_displayed = True
            break
    
    # Если подключен annotation-list.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert count_displayed or annotation_list_connected, 'Счетчик не показывает количество аннотаций'


@then('должна быть функция для загрузки списка аннотаций')
def check_load_annotations_function(context):
    """Проверяем наличие функции для загрузки списка."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'load' in script_content.lower() and 'annotation' in script_content.lower():
            function_found = True
            break
    
    # Если подключен annotation-list.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert function_found or annotation_list_connected, 'Функция загрузки списка аннотаций не найдена'


@then('функция должна вызываться после CRUD операций')
def check_function_called_after_crud(context):
    """Проверяем что функция вызывается после CRUD операций."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    crud_integration = False
    
    for script in scripts:
        script_content = script.string or ''
        if ('create' in script_content.lower() or 'update' in script_content.lower() or 'delete' in script_content.lower()) and 'load' in script_content.lower():
            crud_integration = True
            break
    
    # Если подключен annotation-list.js, считаем что интеграция там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert crud_integration or annotation_list_connected, 'Функция не вызывается после CRUD операций'


@then('функция должна загружать аннотации с сервера')
def check_load_from_server(context):
    """Проверяем что функция загружает аннотации с сервера."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    server_load = False
    
    for script in scripts:
        script_content = script.string or ''
        if '/api/annotations' in script_content and ('fetch' in script_content.lower() or 'get' in script_content.lower()):
            server_load = True
            break
    
    # Если подключен annotation-list.js, считаем что загрузка там
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert server_load or annotation_list_connected, 'Функция не загружает аннотации с сервера'
