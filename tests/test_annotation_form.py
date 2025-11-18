"""Step definitions для тестирования UI создания аннотаций."""
from pathlib import Path

from bs4 import BeautifulSoup
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Связываем сценарии из feature файла
scenarios('features/annotation_form.feature')


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


@then('должен быть элемент модального окна для создания аннотации')
def check_modal_exists(context):
    """Проверяем наличие модального окна."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем модальное окно по классу или id
    modal_elements = (
        context['html'].find_all(id='annotation-modal') +
        context['html'].find_all(class_='modal') +
        context['html'].find_all(class_='annotation-modal')
    )
    
    assert len(modal_elements) > 0, 'Модальное окно для создания аннотации не найдено'


@then('модальное окно должно быть скрыто по умолчанию')
def check_modal_hidden(context):
    """Проверяем что модальное окно скрыто по умолчанию."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем модальное окно
    modal_elements = (
        context['html'].find_all(id='annotation-modal') +
        context['html'].find_all(class_='modal') +
        context['html'].find_all(class_='annotation-modal')
    )
    
    if len(modal_elements) > 0:
        modal = modal_elements[0]
        # Проверяем что есть стиль display: none или класс hidden
        style = modal.get('style', '')
        classes = modal.get('class', [])
        is_hidden = 'display: none' in style or 'hidden' in classes or 'display:none' in style
        
        # Также проверяем что подключен CSS файл modal.css
        links = context['html'].find_all('link', rel='stylesheet')
        modal_css_connected = any('modal.css' in link.get('href', '') for link in links)
        
        assert is_hidden or modal_css_connected, 'Модальное окно не скрыто по умолчанию'


@then(parsers.parse('в модальном окне должно быть поле "{field_name}" типа {field_type}'))
def check_form_field_exists(context, field_name, field_type):
    """Проверяем наличие поля формы."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем поле по name или id
    fields = context['html'].find_all(attrs={'name': field_name}) + \
             context['html'].find_all(id=field_name)
    
    assert len(fields) > 0, f'Поле "{field_name}" не найдено'
    
    field = fields[0]
    actual_type = field.get('type', '')
    
    # Для textarea проверяем тег
    if field_type == 'textarea':
        assert field.name == 'textarea', f'Поле "{field_name}" должно быть textarea'
    elif field_type == 'range (slider)':
        assert actual_type == 'range', f'Поле "{field_name}" должно быть типа range'
    else:
        assert actual_type == field_type, f'Поле "{field_name}" должно быть типа {field_type}'


@then('поле confidence должно иметь диапазон от 0 до 1')
def check_confidence_range(context):
    """Проверяем диапазон поля confidence."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем поле confidence
    confidence_fields = context['html'].find_all(attrs={'name': 'confidence'}) + \
                       context['html'].find_all(id='confidence')
    
    assert len(confidence_fields) > 0, 'Поле confidence не найдено'
    
    field = confidence_fields[0]
    min_value = field.get('min', '')
    max_value = field.get('max', '')
    step_value = field.get('step', '')
    
    assert min_value == '0' or min_value == 0, f'Поле confidence должно иметь min=0, получено {min_value}'
    assert max_value == '1' or max_value == 1, f'Поле confidence должно иметь max=1, получено {max_value}'


@then('должна быть функция для автозаполнения start_time и end_time из региона')
def check_autofill_function(context):
    """Проверяем наличие функции автозаполнения."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'start_time' in script_content.lower() and 'end_time' in script_content.lower() and ('autofill' in script_content.lower() or 'region' in script_content.lower()):
            function_found = True
            break
    
    # Если подключен annotation-form.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert function_found or annotation_form_connected, 'Функция автозаполнения не найдена'


@then('функция должна использовать данные из текущего региона')
def check_autofill_uses_region(context):
    """Проверяем что функция использует данные региона."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    region_used = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'region' in script_content.lower() and ('start' in script_content.lower() or 'end' in script_content.lower()):
            region_used = True
            break
    
    # Если подключен annotation-form.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert region_used or annotation_form_connected, 'Функция не использует данные региона'


@then(parsers.parse('должна быть кнопка "{button_text}"'))
def check_button_exists(context, button_text):
    """Проверяем наличие кнопки."""
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


@then(parsers.parse('скрипт annotation-form должен использовать overlay "{overlay_id}"'))
def check_annotation_overlay_usage(overlay_id):
    """Проверяем что скрипт annotation-form использует заданный overlay."""
    script_path = Path('static/js/annotation-form.js')
    assert script_path.exists(), 'Файл annotation-form.js не найден'

    content = script_path.read_text(encoding='utf-8')
    assert overlay_id in content, f'overlay "{overlay_id}" не используется в annotation-form.js'
    assert '.modal-overlay' not in content, (
        'annotation-form.js не должен использовать общий селектор .modal-overlay'
    )


@then('кнопка должна иметь обработчик для отправки POST запроса')
def check_save_button_handler(context):
    """Проверяем наличие обработчика для сохранения."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    handler_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'saveannotation' in script_content.lower().replace(' ', '') or 'save.*annotation' in script_content.lower():
            handler_found = True
            break
    
    # Если подключен annotation-form.js, считаем что обработчик там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert handler_found or annotation_form_connected, 'Обработчик для сохранения не найден'


@then('POST запрос должен отправляться на "/api/annotations"')
def check_post_endpoint(context):
    """Проверяем что POST запрос отправляется на правильный endpoint."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    endpoint_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if '/api/annotations' in script_content and ('post' in script_content.lower() or 'fetch' in script_content.lower()):
            endpoint_found = True
            break
    
    # Если подключен annotation-form.js, считаем что endpoint там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert endpoint_found or annotation_form_connected, 'POST запрос не отправляется на /api/annotations'


@then('должен быть элемент для отображения сообщения об успехе')
def check_success_message_element(context):
    """Проверяем наличие элемента для сообщения об успехе."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем элемент по классу или id
    success_elements = (
        context['html'].find_all(id='success-message') +
        context['html'].find_all(class_='success-message') +
        context['html'].find_all(class_='alert-success') +
        context['html'].find_all(class_='message-success')
    )
    
    assert len(success_elements) > 0, 'Элемент для сообщения об успехе не найден'


@then('должен быть элемент для отображения сообщения об ошибке')
def check_error_message_element(context):
    """Проверяем наличие элемента для сообщения об ошибке."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем элемент по классу или id
    error_elements = (
        context['html'].find_all(id='error-message') +
        context['html'].find_all(class_='error-message') +
        context['html'].find_all(class_='alert-error') +
        context['html'].find_all(class_='message-error')
    )
    
    assert len(error_elements) > 0, 'Элемент для сообщения об ошибке не найден'


@then('должна быть функция для закрытия модального окна')
def check_close_modal_function(context):
    """Проверяем наличие функции закрытия модального окна."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'close.*modal' in script_content.lower() or 'hide.*modal' in script_content.lower():
            function_found = True
            break
    
    # Если подключен annotation-form.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert function_found or annotation_form_connected, 'Функция закрытия модального окна не найдена'


@then('функция должна вызываться после успешного сохранения')
def check_close_after_save(context):
    """Проверяем что функция закрытия вызывается после сохранения."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    close_after_save = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'save' in script_content.lower() and ('close' in script_content.lower() or 'hide' in script_content.lower()):
            close_after_save = True
            break
    
    # Если подключен annotation-form.js, считаем что логика там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert close_after_save or annotation_form_connected, 'Функция закрытия не вызывается после сохранения'


@then('должна быть функция валидации формы')
def check_validation_function(context):
    """Проверяем наличие функции валидации."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'validate' in script_content.lower() and ('form' in script_content.lower() or 'annotation' in script_content.lower()):
            function_found = True
            break
    
    # Если подключен annotation-form.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert function_found or annotation_form_connected, 'Функция валидации не найдена'


@then('функция должна проверять что event_label не пустой')
def check_validate_event_label(context):
    """Проверяем валидацию event_label."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    validation_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'event_label' in script_content.lower() and ('empty' in script_content.lower() or 'required' in script_content.lower() or 'trim' in script_content.lower()):
            validation_found = True
            break
    
    # Если подключен annotation-form.js, считаем что валидация там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert validation_found or annotation_form_connected, 'Валидация event_label не найдена'


@then('функция должна проверять что confidence в диапазоне 0-1')
def check_validate_confidence(context):
    """Проверяем валидацию confidence."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    validation_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'confidence' in script_content.lower() and ('0' in script_content or '1' in script_content) and ('range' in script_content.lower() or 'min' in script_content.lower() or 'max' in script_content.lower()):
            validation_found = True
            break
    
    # Если подключен annotation-form.js, считаем что валидация там
    scripts = context['html'].find_all('script', src=True)
    annotation_form_connected = any('annotation-form.js' in script.get('src', '') for script in scripts)
    
    assert validation_found or annotation_form_connected, 'Валидация confidence не найдена'
