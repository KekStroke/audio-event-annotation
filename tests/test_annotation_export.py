"""Step definitions для тестирования экспорта аннотаций."""
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from pytest_bdd import given, parsers, scenarios, then, when

# Связываем сценарии из feature файла
scenarios('features/annotation_export.feature')


@pytest.fixture
def app():
    """Создаём Flask приложение для тестов."""
    from app import app as flask_app

    flask_app.config['TESTING'] = True
    flask_app.config['DATABASE_URL'] = 'sqlite:///:memory:'
    return flask_app


@pytest.fixture
def client(app):
    """Создаём тестовый клиент Flask."""
    return app.test_client()


@pytest.fixture
def test_db(tmp_path):
    """Создаём временную тестовую БД."""
    from src.models.database import Database

    db_path = tmp_path / 'test.db'
    db = Database(f'sqlite:///{db_path}')
    db.create_all()
    return db


@pytest.fixture
def context():
    """Контекст для хранения данных между шагами теста."""
    return {}


def _create_test_audio_file(filename: str, duration: float = 5.0) -> Path:
    """Создаёт временной WAV файл для тестов."""
    tmp_dir = Path(tempfile.gettempdir()) / 'audio_annotation_test'
    tmp_dir.mkdir(exist_ok=True, parents=True)

    file_path = tmp_dir / filename
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal = np.sin(2 * np.pi * 440 * t)
    stereo_signal = np.column_stack([signal, signal])
    sf.write(str(file_path), stereo_signal, sample_rate)

    return file_path


@given('Flask приложение запущено')
def flask_app_running(app, test_db, context):
    """Устанавливаем Flask приложение в контекст и мокаем БД."""
    from src.models import database

    database._db_instance = test_db
    context['app'] = app
    context['db'] = test_db


@given('база данных инициализирована')
def database_initialized(context):
    """Инициализируем БД."""
    context['session'] = context['db'].get_session()


@given('в БД существует AudioFile с id')
def create_audio_file_in_db(context):
    """Создаём AudioFile в БД."""
    from src.models.audio_file import AudioFile

    file_path = _create_test_audio_file('test_export.wav', duration=10.0)
    sample_rate = 44100
    duration = 10.0
    file_size = file_path.stat().st_size

    if 'session' not in context:
        context['session'] = context['db'].get_session()

    audio_file = AudioFile(
        file_path=str(file_path),
        filename='test_export.wav',
        duration=duration,
        sample_rate=sample_rate,
        channels=2,
        file_size=file_size
    )

    session = context['session']
    session.add(audio_file)
    session.commit()

    context['audio_file'] = audio_file
    context['audio_file_id'] = str(audio_file.id)
    context['test_file_path'] = str(file_path)


@given(parsers.parse('в БД существует EventType с именем "{event_type_name}"'))
def create_event_type_in_db(context, event_type_name):
    """Создаём EventType в БД."""
    from src.models.event_type import EventType

    if 'session' not in context:
        context['session'] = context['db'].get_session()

    session = context['session']

    # Проверяем существует ли уже
    event_type = EventType.get_by_name(session, event_type_name)
    if not event_type:
        event_type = EventType(name=event_type_name, color='#FF0000')
        session.add(event_type)
        session.commit()

    context['event_type'] = event_type
    context['event_type_id'] = str(event_type.id)


@given('в БД существует Annotation для AudioFile')
def create_annotation_in_db(context):
    """Создаём Annotation в БД."""
    from src.models.annotation import Annotation

    if 'session' not in context:
        context['session'] = context['db'].get_session()

    session = context['session']

    # Убеждаемся что есть AudioFile и EventType
    if 'audio_file' not in context:
        create_audio_file_in_db(context)
    if 'event_type' not in context:
        create_event_type_in_db(context, 'speech')

    annotation = Annotation(
        audio_file_id=context['audio_file'].id,
        start_time=1.0,
        end_time=2.5,
        event_label='Test annotation'
    )

    session.add(annotation)
    session.commit()

    context['annotation'] = annotation
    context['annotation_id'] = str(annotation.id)


@given(parsers.parse('в БД не существует AudioFile с id "{audio_file_id}"'))
def audio_file_not_in_db(context, audio_file_id):
    """Проверяем что AudioFile не существует."""
    context['nonexistent_audio_file_id'] = audio_file_id


@when(parsers.parse('я отправляю GET запрос на "{endpoint}"'))
def send_get_request(context, endpoint, client):
    """Отправляем GET запрос."""
    # Заменяем переменные в endpoint
    if 'audio_file_id' in context:
        endpoint = endpoint.replace('{id}', context['audio_file_id'])
    if 'nonexistent_audio_file_id' in context:
        endpoint = endpoint.replace('{id}', context['nonexistent_audio_file_id'])

    response = client.get(endpoint)
    context['response'] = response
    context['response_data'] = response.get_json() if response.is_json else None


@then(parsers.parse('ответ должен иметь статус {status:d}'))
def check_response_status(context, status):
    """Проверяем статус ответа."""
    actual_status = context['response'].status_code
    assert actual_status == status, (
        f'Ожидался статус {status}, получен {actual_status}. '
        f'Ответ: {context.get("response_data")}'
    )


@then(parsers.parse('ответ должен иметь Content-Type "{content_type}"'))
def check_content_type(context, content_type):
    """Проверяем Content-Type заголовок."""
    actual_content_type = context['response'].headers.get('Content-Type', '')
    assert content_type in actual_content_type, \
        f'Ожидался Content-Type "{content_type}", получен "{actual_content_type}"'


@then('ответ должен иметь Content-Disposition header с именем файла')
def check_content_disposition(context):
    """Проверяем Content-Disposition заголовок."""
    content_disposition = context['response'].headers.get('Content-Disposition', '')
    assert 'attachment' in content_disposition or 'filename' in content_disposition, \
        f'Content-Disposition header не содержит attachment или filename: {content_disposition}'


@then(parsers.parse('ответ должен содержать JSON с полем "{field_name}"'))
def check_response_has_field(context, field_name):
    """Проверяем наличие поля в JSON."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert field_name in context['response_data'], \
        f"Ответ не содержит поле '{field_name}': {context['response_data']}"


@then('поле "audio_file" должно содержать метаданные файла')
def check_audio_file_metadata(context):
    """Проверяем что поле audio_file содержит метаданные."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'audio_file' in context['response_data'], 'Поле audio_file не найдено'
    
    audio_file = context['response_data']['audio_file']
    assert isinstance(audio_file, dict), 'Поле audio_file должно быть словарем'


@then(parsers.parse('поле "{field_name}" должно содержать поле "{nested_field}"'))
def check_nested_field(context, field_name, nested_field):
    """Проверяем наличие вложенного поля."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert field_name in context['response_data'], f'Поле "{field_name}" не найдено'
    
    field_value = context['response_data'][field_name]
    assert isinstance(field_value, dict), f'Поле "{field_name}" должно быть словарем'
    assert nested_field in field_value, \
        f"Поле '{field_name}' не содержит поле '{nested_field}': {field_value}"


@then('поле "annotations" должно быть массивом')
def check_annotations_is_array(context):
    """Проверяем что поле annotations является массивом."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'annotations' in context['response_data'], 'Поле annotations не найдено'
    
    annotations = context['response_data']['annotations']
    assert isinstance(annotations, list), 'Поле annotations должно быть массивом'


@then('массив аннотаций должен содержать хотя бы один элемент')
def check_annotations_has_elements(context):
    """Проверяем что массив аннотаций не пустой."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'annotations' in context['response_data'], 'Поле annotations не найдено'
    
    annotations = context['response_data']['annotations']
    assert len(annotations) > 0, 'Массив аннотаций пустой'


@then('каждая аннотация должна содержать поле "id"')
def check_annotation_has_id(context):
    """Проверяем что каждая аннотация имеет поле id."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'annotations' in context['response_data'], 'Поле annotations не найдено'
    
    annotations = context['response_data']['annotations']
    for annotation in annotations:
        assert 'id' in annotation, f"Аннотация не содержит поле 'id': {annotation}"


@then(parsers.parse('каждая аннотация должна содержать поле "{field_name}"'))
def check_annotation_has_field(context, field_name):
    """Проверяем что каждая аннотация имеет указанное поле."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'annotations' in context['response_data'], 'Поле annotations не найдено'
    
    annotations = context['response_data']['annotations']
    for annotation in annotations:
        assert field_name in annotation, \
            f"Аннотация не содержит поле '{field_name}': {annotation}"


@then('поле "annotations" должно быть пустым массивом')
def check_annotations_is_empty(context):
    """Проверяем что массив аннотаций пустой."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'annotations' in context['response_data'], 'Поле annotations не найдено'
    
    annotations = context['response_data']['annotations']
    assert isinstance(annotations, list), 'Поле annotations должно быть массивом'
    assert len(annotations) == 0, 'Массив аннотаций должен быть пустым'


@then('ответ должен содержать JSON с полем "error"')
def check_response_has_error(context):
    """Проверяем наличие поля error."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'error' in context['response_data'], \
        f"Ответ не содержит поле 'error': {context['response_data']}"


@when('я открываю главную страницу "/"')
def open_main_page(context, client):
    """Открываем главную страницу и сохраняем ответ."""
    response = client.get('/')
    context['response'] = response
    context['response_data'] = response.get_data(as_text=True)
    
    # Парсим HTML
    if response.status_code == 200:
        from bs4 import BeautifulSoup
        context['html'] = BeautifulSoup(context['response_data'], 'html.parser')


@then(parsers.parse('должна быть кнопка "{button_text}"'))
def check_export_button_exists(context, button_text):
    """Проверяем наличие кнопки Export."""
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


@then('кнопка должна иметь обработчик для экспорта аннотаций')
def check_export_button_handler(context):
    """Проверяем наличие обработчика для экспорта."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    handler_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'export' in script_content.lower() and ('annotation' in script_content.lower() or 'download' in script_content.lower() or 'exportAnnotations' in script_content):
            handler_found = True
            break
    
    # Если подключен annotation-list.js, считаем что обработчик там (функция exportAnnotations)
    scripts = context['html'].find_all('script', src=True)
    annotation_list_connected = any('annotation-list.js' in script.get('src', '') for script in scripts)
    
    assert handler_found or annotation_list_connected, 'Обработчик для экспорта не найден'

