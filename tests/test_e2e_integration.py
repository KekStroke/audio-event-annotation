"""Step definitions для E2E интеграционного тестирования."""
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from pytest_bdd import given, parsers, scenarios, then, when

# Связываем сценарии из feature файла
scenarios('features/e2e_integration.feature')


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

    file_path = _create_test_audio_file('test_e2e.wav', duration=10.0)
    sample_rate = 44100
    duration = 10.0
    file_size = file_path.stat().st_size

    if 'session' not in context:
        context['session'] = context['db'].get_session()

    audio_file = AudioFile(
        file_path=str(file_path),
        filename='test_e2e.wav',
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


@when('я загружаю аудио файл через API')
def load_audio_file_via_api(context, client):
    """Загружаем аудио файл через API."""
    if 'test_file_path' not in context:
        file_path = _create_test_audio_file('test_api_load.wav', duration=5.0)
        context['test_file_path'] = str(file_path)

    response = client.post(
        '/api/audio/add',
        json={'file_path': context['test_file_path']},
        content_type='application/json'
    )

    context['api_response'] = response
    if response.is_json:
        context['api_response_data'] = response.get_json()
        if 'id' in context['api_response_data']:
            context['loaded_audio_file_id'] = context['api_response_data']['id']


@then('файл должен быть добавлен в БД')
def check_file_added_to_db(context):
    """Проверяем что файл добавлен в БД."""
    assert context['api_response'].status_code == 201, \
        f'Ожидался статус 201, получен {context["api_response"].status_code}'
    assert 'id' in context['api_response_data'], 'Ответ не содержит id файла'


@when('я получаю список аннотаций для файла')
def get_annotations_list(context, client):
    """Получаем список аннотаций для файла."""
    audio_file_id = context.get('loaded_audio_file_id') or context.get('audio_file_id')
    assert audio_file_id is not None, 'Audio file ID не установлен'

    response = client.get(f'/api/annotations?audio_file_id={audio_file_id}')
    context['annotations_response'] = response
    if response.is_json:
        context['annotations_list'] = response.get_json()


@then('список должен быть пустым')
def check_list_is_empty(context):
    """Проверяем что список пустой."""
    assert context['annotations_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["annotations_response"].status_code}'
    assert context['annotations_list'] == [], \
        f'Список не пустой: {context["annotations_list"]}'


@when('я создаю аннотацию через API')
def create_annotation_via_api(context, client):
    """Создаём аннотацию через API."""
    audio_file_id = context.get('loaded_audio_file_id') or context.get('audio_file_id')
    assert audio_file_id is not None, 'Audio file ID не установлен'

    annotation_data = {
        'audio_file_id': audio_file_id,
        'start_time': 1.5,
        'end_time': 3.2,
        'event_label': 'E2E Test Annotation'
    }

    response = client.post(
        '/api/annotations',
        json=annotation_data,
        content_type='application/json'
    )

    context['create_annotation_response'] = response
    if response.is_json:
        context['created_annotation'] = response.get_json()


@then('аннотация должна быть создана в БД')
def check_annotation_created(context):
    """Проверяем что аннотация создана."""
    assert context['create_annotation_response'].status_code == 201, \
        f'Ожидался статус 201, получен {context["create_annotation_response"].status_code}'
    assert 'id' in context['created_annotation'], 'Ответ не содержит id аннотации'
    context['created_annotation_id'] = context['created_annotation']['id']


@then('список должен содержать одну аннотацию')
def check_list_has_one_annotation(context):
    """Проверяем что список содержит одну аннотацию."""
    assert context['annotations_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["annotations_response"].status_code}'
    assert len(context['annotations_list']) == 1, \
        f'Список должен содержать одну аннотацию, получено {len(context["annotations_list"])}'


@when('я обновляю аннотацию через API')
def update_annotation_via_api(context, client):
    """Обновляем аннотацию через API."""
    annotation_id = context.get('created_annotation_id') or context.get('annotation_id')
    assert annotation_id is not None, 'Annotation ID не установлен'

    update_data = {
        'start_time': 2.0,
        'end_time': 4.5,
        'event_label': 'Updated E2E Annotation'
    }

    response = client.put(
        f'/api/annotations/{annotation_id}',
        json=update_data,
        content_type='application/json'
    )

    context['update_annotation_response'] = response
    if response.is_json:
        context['updated_annotation'] = response.get_json()


@then('аннотация должна быть обновлена в БД')
def check_annotation_updated(context):
    """Проверяем что аннотация обновлена."""
    assert context['update_annotation_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["update_annotation_response"].status_code}'
    assert context['updated_annotation']['event_label'] == 'Updated E2E Annotation', \
        'Аннотация не была обновлена'


@when('я экспортирую аннотации в JSON')
def export_annotations_json(context, client):
    """Экспортируем аннотации в JSON."""
    audio_file_id = context.get('loaded_audio_file_id') or context.get('audio_file_id')
    assert audio_file_id is not None, 'Audio file ID не установлен'

    response = client.get(f'/api/audio/{audio_file_id}/export?format=json')
    context['export_response'] = response
    if response.is_json:
        context['export_data'] = response.get_json()


@then('JSON должен содержать метаданные файла и аннотации')
def check_export_contains_data(context):
    """Проверяем что экспорт содержит данные."""
    assert context['export_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["export_response"].status_code}'
    assert 'audio_file' in context['export_data'], 'Экспорт не содержит audio_file'
    assert 'annotations' in context['export_data'], 'Экспорт не содержит annotations'
    assert 'export_date' in context['export_data'], 'Экспорт не содержит export_date'
    assert 'version' in context['export_data'], 'Экспорт не содержит version'


@when('я удаляю аннотацию через API')
def delete_annotation_via_api(context, client):
    """Удаляем аннотацию через API."""
    annotation_id = context.get('created_annotation_id') or context.get('annotation_id')
    assert annotation_id is not None, 'Annotation ID не установлен'

    response = client.delete(f'/api/annotations/{annotation_id}')
    context['delete_annotation_response'] = response
    if response.is_json:
        context['delete_annotation_data'] = response.get_json()


@then('аннотация должна быть удалена из БД')
def check_annotation_deleted(context):
    """Проверяем что аннотация удалена."""
    assert context['delete_annotation_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["delete_annotation_response"].status_code}'


@when('я получаю метаданные аудио файла через API')
def get_audio_file_metadata(context, client):
    """Получаем метаданные аудио файла через API."""
    audio_file_id = context.get('loaded_audio_file_id') or context.get('audio_file_id')
    assert audio_file_id is not None, 'Audio file ID не установлен'

    response = client.get(f'/api/audio/{audio_file_id}')
    context['metadata_response'] = response
    if response.is_json:
        context['metadata_data'] = response.get_json()


@then('ответ должен содержать метаданные файла')
def check_metadata_in_response(context):
    """Проверяем что ответ содержит метаданные."""
    assert context['metadata_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["metadata_response"].status_code}'
    assert 'id' in context['metadata_data'], 'Ответ не содержит id'
    assert 'filename' in context['metadata_data'], 'Ответ не содержит filename'
    assert 'duration' in context['metadata_data'], 'Ответ не содержит duration'


@when('я запрашиваю waveform для файла')
def request_waveform(context, client):
    """Запрашиваем waveform для файла."""
    audio_file_id = context.get('loaded_audio_file_id') or context.get('audio_file_id')
    assert audio_file_id is not None, 'Audio file ID не установлен'

    response = client.get(f'/api/audio/{audio_file_id}/waveform')
    context['waveform_response'] = response


@then('ответ должен быть PNG изображением')
def check_waveform_is_png(context):
    """Проверяем что ответ waveform является PNG изображением."""
    assert 'waveform_response' in context, 'waveform_response не найден в контексте'
    assert context['waveform_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["waveform_response"].status_code}'
    content_type = context['waveform_response'].headers.get('Content-Type', '')
    assert 'image/png' in content_type, \
        f'Ожидался Content-Type image/png, получен {content_type}'


@then('ответ спектрограммы должен быть PNG изображением')
def check_spectrogram_is_png(context):
    """Проверяем что ответ спектрограммы является PNG изображением."""
    assert 'spectrogram_response' in context, 'spectrogram_response не найден в контексте'
    assert context['spectrogram_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["spectrogram_response"].status_code}'
    content_type = context['spectrogram_response'].headers.get('Content-Type', '')
    assert 'image/png' in content_type, \
        f'Ожидался Content-Type image/png, получен {content_type}'


@when('я запрашиваю спектрограмму для файла')
def request_spectrogram(context, client):
    """Запрашиваем спектрограмму для файла."""
    audio_file_id = context.get('loaded_audio_file_id') or context.get('audio_file_id')
    assert audio_file_id is not None, 'Audio file ID не установлен'

    response = client.get(f'/api/audio/{audio_file_id}/spectrogram')
    context['spectrogram_response'] = response


@then('список должен содержать аннотацию')
def check_list_has_annotation(context):
    """Проверяем что список содержит аннотацию."""
    assert context['annotations_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["annotations_response"].status_code}'
    assert len(context['annotations_list']) > 0, \
        'Список должен содержать хотя бы одну аннотацию'


@when('я получаю одну аннотацию по ID')
def get_annotation_by_id(context, client):
    """Получаем одну аннотацию по ID."""
    annotation_id = context.get('created_annotation_id') or context.get('annotation_id')
    assert annotation_id is not None, 'Annotation ID не установлен'

    response = client.get(f'/api/annotations/{annotation_id}')
    context['get_annotation_response'] = response
    if response.is_json:
        context['get_annotation_data'] = response.get_json()


@then('ответ должен содержать данные аннотации')
def check_annotation_data_in_response(context):
    """Проверяем что ответ содержит данные аннотации."""
    assert context['get_annotation_response'].status_code == 200, \
        f'Ожидался статус 200, получен {context["get_annotation_response"].status_code}'
    assert 'id' in context['get_annotation_data'], 'Ответ не содержит id'
    assert 'event_label' in context['get_annotation_data'], 'Ответ не содержит event_label'


@when('я создаю вторую аннотацию через API')
def create_second_annotation_via_api(context, client):
    """Создаём вторую аннотацию через API."""
    audio_file_id = context.get('loaded_audio_file_id') or context.get('audio_file_id')
    assert audio_file_id is not None, 'Audio file ID не установлен'

    annotation_data = {
        'audio_file_id': audio_file_id,
        'start_time': 5.0,
        'end_time': 7.5,
        'event_label': 'Second E2E Annotation'
    }

    response = client.post(
        '/api/annotations',
        json=annotation_data,
        content_type='application/json'
    )

    context['create_second_annotation_response'] = response
    if response.is_json:
        context['created_second_annotation'] = response.get_json()


@then('в БД должно быть две аннотации для файла')
def check_two_annotations_in_db(context, client):
    """Проверяем что в БД две аннотации для файла."""
    audio_file_id = context.get('loaded_audio_file_id') or context.get('audio_file_id')
    assert audio_file_id is not None, 'Audio file ID не установлен'

    response = client.get(f'/api/annotations?audio_file_id={audio_file_id}')
    assert response.status_code == 200, \
        f'Ожидался статус 200, получен {response.status_code}'
    
    annotations_list = response.get_json()
    assert len(annotations_list) == 2, \
        f'Должно быть две аннотации, получено {len(annotations_list)}'

