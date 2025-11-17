"""Step definitions для тестирования API аннотаций."""
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from pytest_bdd import given, parsers, scenarios, then, when

# Связываем сценарии из feature файла
scenarios('features/annotation_api.feature')


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

    file_path = _create_test_audio_file('test_annotation.wav', duration=10.0)
    sample_rate = 44100
    duration = 10.0
    file_size = file_path.stat().st_size

    if 'session' not in context:
        context['session'] = context['db'].get_session()

    audio_file = AudioFile(
        file_path=str(file_path),
        filename='test_annotation.wav',
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


@given(parsers.parse('в БД не существует Annotation с id "{annotation_id}"'))
def annotation_not_in_db(context, annotation_id):
    """Проверяем что Annotation не существует."""
    context['nonexistent_annotation_id'] = annotation_id


@when(parsers.parse('я отправляю POST запрос на "{endpoint}" с телом:\n{body}'))
def send_post_request_with_body(context, endpoint, body, client):
    """Отправляем POST запрос с телом."""
    # Заменяем переменные в endpoint и body
    if 'audio_file_id' in context:
        endpoint = endpoint.replace('{id}', context['audio_file_id'])
    if 'nonexistent_audio_file_id' in context:
        endpoint = endpoint.replace('{id}', context['nonexistent_audio_file_id'])
        body = body.replace('{id}', context['nonexistent_audio_file_id'])

    if 'event_type_id' in context:
        body = body.replace('{event_type_id}', context['event_type_id'])
    if 'audio_file_id' in context:
        body = body.replace('{id}', context['audio_file_id'])

    import json
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = {}

    response = client.post(
        endpoint,
        json=data,
        content_type='application/json'
    )

    context['response'] = response
    context['response_data'] = response.get_json() if response.is_json else None


@when(parsers.parse('я отправляю GET запрос на "{endpoint}"'))
def send_get_request(context, endpoint, client):
    """Отправляем GET запрос."""
    # Заменяем переменные в endpoint
    if 'audio_file_id' in context:
        endpoint = endpoint.replace('{id}', context['audio_file_id'])
    if 'annotation_id' in context:
        endpoint = endpoint.replace('{annotation_id}', context['annotation_id'])
    if 'nonexistent_annotation_id' in context:
        endpoint = endpoint.replace('{annotation_id}', context['nonexistent_annotation_id'])

    response = client.get(endpoint)
    context['response'] = response
    context['response_data'] = response.get_json() if response.is_json else None


@when(parsers.parse('я отправляю PUT запрос на "{endpoint}" с телом:\n{body}'))
def send_put_request_with_body(context, endpoint, body, client):
    """Отправляем PUT запрос с телом."""
    # Заменяем переменные
    if 'annotation_id' in context:
        endpoint = endpoint.replace('{annotation_id}', context['annotation_id'])

    import json
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = {}

    response = client.put(
        endpoint,
        json=data,
        content_type='application/json'
    )

    context['response'] = response
    context['response_data'] = response.get_json() if response.is_json else None


@when(parsers.parse('я отправляю DELETE запрос на "{endpoint}"'))
def send_delete_request(context, endpoint, client):
    """Отправляем DELETE запрос."""
    # Заменяем переменные
    if 'annotation_id' in context:
        endpoint = endpoint.replace('{annotation_id}', context['annotation_id'])

    response = client.delete(endpoint)
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


@then('ответ должен содержать JSON с полем "id"')
def check_response_has_id(context):
    """Проверяем наличие поля id."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'id' in context['response_data'], \
        f"Ответ не содержит поле 'id': {context['response_data']}"


@then('ответ должен содержать JSON с полем "audio_file_id"')
def check_response_has_audio_file_id(context):
    """Проверяем наличие поля audio_file_id."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'audio_file_id' in context['response_data'], \
        f"Ответ не содержит поле 'audio_file_id': {context['response_data']}"


@then(parsers.parse('ответ должен содержать JSON с полем "{field_name}" равным {value:f}'))
def check_response_field_equals_float(context, field_name, value):
    """Проверяем значение поля (float)."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert field_name in context['response_data'], \
        f"Ответ не содержит поле '{field_name}': {context['response_data']}"
    actual_value = context['response_data'][field_name]
    assert abs(actual_value - value) < 0.001, \
        f"Поле '{field_name}' равно {actual_value}, ожидалось {value}"


@then(parsers.parse('ответ должен содержать JSON с полем "{field_name}" равным "{value}"'))
def check_response_field_equals_string(context, field_name, value):
    """Проверяем значение поля (string)."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert field_name in context['response_data'], \
        f"Ответ не содержит поле '{field_name}': {context['response_data']}"
    actual_value = context['response_data'][field_name]
    assert actual_value == value, \
        f"Поле '{field_name}' равно '{actual_value}', ожидалось '{value}'"


@then('ответ должен содержать JSON массив')
def check_response_is_array(context):
    """Проверяем что ответ является массивом."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert isinstance(context['response_data'], list), \
        f"Ответ не является массивом: {type(context['response_data'])}"


@then('массив должен содержать хотя бы один элемент')
def check_array_has_elements(context):
    """Проверяем что массив не пустой."""
    assert len(context['response_data']) > 0, 'Массив пустой'


@then('каждый элемент должен содержать поле "id"')
def check_array_elements_have_id(context):
    """Проверяем что каждый элемент массива имеет поле id."""
    for item in context['response_data']:
        assert 'id' in item, f"Элемент не содержит поле 'id': {item}"


@then('ответ должен содержать JSON с полем "error"')
def check_response_has_error(context):
    """Проверяем наличие поля error."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'error' in context['response_data'], \
        f"Ответ не содержит поле 'error': {context['response_data']}"


@then('при повторном запросе аннотация должна быть удалена')
def check_annotation_deleted(context, client):
    """Проверяем что аннотация удалена."""
    annotation_id = context.get('annotation_id')
    assert annotation_id is not None, 'Annotation ID не найден'

    response = client.get(f'/api/annotations/{annotation_id}')
    assert response.status_code == 404, \
        f'Аннотация не удалена, статус: {response.status_code}'

