"""Step definitions для тестирования API загрузки аудио-файлов."""
import pytest
import json
import os
import tempfile
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import patch, MagicMock

# Связываем сценарии из feature файла
scenarios('features/audio_api.feature')


@pytest.fixture
def app():
    """Создаём Flask приложение для тестов."""
    from app import app
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = 'sqlite:///:memory:'
    return app


@pytest.fixture
def client(app):
    """Создаём тестовый клиент Flask."""
    return app.test_client()


@pytest.fixture
def test_db(tmp_path):
    """Создаём временную тестовую БД."""
    from src.models.database import Database
    db_path = tmp_path / "test.db"
    db = Database(f"sqlite:///{db_path}")
    db.create_all()
    return db


@pytest.fixture
def context():
    """Контекст для хранения данных между шагами теста."""
    return {}


@given('Flask приложение запущено')
def flask_app_running(app, test_db, context):
    """Устанавливаем Flask приложение в контекст."""
    # Мокаем get_db чтобы использовать тестовую БД
    from src.models import database
    database._db_instance = test_db
    context['app'] = app
    context['db'] = test_db


@given('база данных инициализирована')
def database_initialized(context):
    """Инициализируем БД."""
    # БД уже инициализирована в flask_app_running
    context['session'] = context['db'].get_session()


@given(parsers.parse('существует аудио-файл "{filename}" по пути "{file_path}"'))
def create_audio_file(context, filename, file_path):
    """Создаём тестовый аудио-файл."""
    # Создаём временный файл для теста
    tmp_dir = Path(tempfile.gettempdir()) / "audio_test"
    tmp_dir.mkdir(exist_ok=True, parents=True)
    
    full_path = tmp_dir / filename
    # Создаём минимальный WAV файл с правильной структурой
    # Используем librosa для создания валидного файла
    import numpy as np
    import soundfile as sf
    
    # Создаём короткий аудио сигнал (1 секунда, 44100 Hz, 2 канала)
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Простой синусоидальный сигнал
    signal = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    # Стерео (2 канала)
    stereo_signal = np.column_stack([signal, signal])
    
    # Сохраняем как WAV
    sf.write(str(full_path), stereo_signal, sample_rate)
    
    context['test_file_path'] = str(full_path)
    context['test_filename'] = filename


@given(parsers.parse('существует файл "{filename}" по пути "{file_path}"'))
def create_test_file(context, filename, file_path):
    """Создаём тестовый файл (не аудио)."""
    tmp_dir = Path(tempfile.gettempdir()) / "audio_test"
    tmp_dir.mkdir(exist_ok=True)
    
    full_path = tmp_dir / filename
    with open(full_path, 'w') as f:
        f.write("test content")
    
    context['test_file_path'] = str(full_path)
    context['test_filename'] = filename


@given(parsers.parse('файл "{file_path}" не существует'))
def file_not_exists(context, file_path):
    """Проверяем что файл не существует."""
    context['nonexistent_file'] = file_path


@given('в БД существует AudioFile с id')
def create_audio_file_in_db(context):
    """Создаём AudioFile в БД."""
    from src.models.audio_file import AudioFile
    
    # Получаем новую сессию если нужно
    if 'session' not in context:
        context['session'] = context['db'].get_session()
    
    audio_file = AudioFile(
        file_path="/test/audio.wav",
        filename="audio.wav",
        duration=120.5,
        sample_rate=44100,
        channels=2,
        file_size=10485760
    )
    
    session = context['session']
    session.add(audio_file)
    session.commit()
    context['audio_file'] = audio_file
    context['audio_file_id'] = str(audio_file.id)


@given(parsers.parse('в БД существует {count:d} AudioFile'))
def create_multiple_audio_files(context, count):
    """Создаём несколько AudioFile в БД."""
    from src.models.audio_file import AudioFile
    
    # Получаем новую сессию если нужно
    if 'session' not in context:
        context['session'] = context['db'].get_session()
    
    session = context['session']
    audio_files = []
    
    for i in range(count):
        audio_file = AudioFile(
            file_path=f"/test/audio_{i}.wav",
            filename=f"audio_{i}.wav",
            duration=100.0 + i,
            sample_rate=44100,
            channels=2,
            file_size=1024000 + i * 1000
        )
        session.add(audio_file)
        audio_files.append(audio_file)
    
    session.commit()
    context['audio_files'] = audio_files


@given(parsers.parse('в БД не существует AudioFile с id "{audio_file_id}"'))
def audio_file_not_in_db(context, audio_file_id):
    """Проверяем что AudioFile не существует."""
    context['nonexistent_id'] = audio_file_id


@when(parsers.parse('я отправляю POST запрос на "{endpoint}" с телом:\n{body}'))
def send_post_request(context, endpoint, body, client):
    """Отправляем POST запрос."""
    # Заменяем переменные в endpoint
    if 'audio_file_id' in context:
        endpoint = endpoint.replace('{id}', context['audio_file_id'])
    elif 'nonexistent_id' in context:
        endpoint = endpoint.replace('{id}', context['nonexistent_id'])
    
    # Обрабатываем пустое тело
    if body.strip() == '{}':
        data = {}
    else:
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}
    
    # Заменяем переменные в данных запроса
    if 'test_file_path' in context:
        if 'file_path' in data:
            data['file_path'] = context['test_file_path']
    
    if 'import_dir' in context and 'path' in data:
        # Если в тесте используется алиас пути (например /test/audio_folder), заменяем его на реальный
        if data['path'] == context.get('import_path_alias'):
            data['path'] = context['import_dir']
            
    response = client.post(endpoint, json=data, content_type='application/json')
    context['response'] = response
    context['response_data'] = response.get_json() or {}


@when(parsers.parse('я отправляю GET запрос на "{endpoint}"'))
def send_get_request(context, endpoint, client):
    """Отправляем GET запрос."""
    # Заменяем переменные в endpoint
    if 'audio_file_id' in context:
        endpoint = endpoint.replace('{id}', context['audio_file_id'])
    elif 'nonexistent_id' in context:
        endpoint = endpoint.replace('{id}', context['nonexistent_id'])
    
    response = client.get(endpoint)
    context['response'] = response
    context['response_data'] = response.get_json()


@when(parsers.parse('я отправляю DELETE запрос на "{endpoint}"'))
def send_delete_request(context, endpoint, client):
    """Отправляем DELETE запрос."""
    # Заменяем переменные в endpoint
    if 'audio_file_id' in context:
        endpoint = endpoint.replace('{id}', context['audio_file_id'])
    elif 'nonexistent_id' in context:
        endpoint = endpoint.replace('{id}', context['nonexistent_id'])
    
    response = client.delete(endpoint)
    context['response'] = response
    context['response_data'] = response.get_json()


@then(parsers.parse('ответ должен иметь статус {status:d}'))
def check_response_status(context, status):
    """Проверяем статус ответа."""
    actual_status = context['response'].status_code
    assert actual_status == status, \
        f"Ожидался статус {status}, получен {actual_status}. Response: {context.get('response_data', {})}"


@then('ответ должен содержать JSON с полем "id"')
def check_response_has_id(context):
    """Проверяем наличие поля id."""
    assert 'id' in context['response_data'], \
        f"Ответ не содержит поле 'id': {context['response_data']}"


@then(parsers.parse('ответ должен содержать JSON с полем "{field}"'))
def check_response_has_field(context, field):
    """Проверяем наличие поля в ответе."""
    assert field in context['response_data'], \
        f"Ответ не содержит поле '{field}': {context['response_data']}"


@then(parsers.parse('ответ должен содержать JSON с полем "{field}" равным "{value}"'))
def check_response_field_value(context, field, value):
    """Проверяем значение поля."""
    assert context['response_data'][field] == value, \
        f"Поле '{field}' имеет значение '{context['response_data'][field]}', ожидалось '{value}'"


@then(parsers.parse('ответ должен содержать JSON с полем "{field}" равным {value:d}'))
def check_response_int_field(context, field, value):
    """Проверяем целочисленное поле."""
    assert context['response_data'][field] == value, \
        f"Поле '{field}' равно {context['response_data'][field]}, ожидалось {value}"


@then('AudioFile должен быть сохранён в БД')
def check_audio_file_saved(context):
    """Проверяем что AudioFile сохранён в БД."""
    from src.models.audio_file import AudioFile
    session = context['session']
    
    audio_file_id = context['response_data']['id']
    audio_file = session.query(AudioFile).filter_by(id=audio_file_id).first()
    assert audio_file is not None, "AudioFile не найден в БД"


@then('AudioFile не должен существовать в БД')
def check_audio_file_deleted(context):
    """Проверяем что AudioFile удалён из БД."""
    from src.models.audio_file import AudioFile
    session = context['session']
    
    # Используем ID из контекста, так как в ответе его может не быть или он может быть другим
    audio_file_id = context.get('audio_file_id')
    if not audio_file_id:
        # Если нет в контексте, пробуем взять из ответа (хотя для DELETE это может быть неактуально)
        audio_file_id = context.get('response_data', {}).get('id')
    
    assert audio_file_id is not None, "ID аудио файла не найден в контексте"
    
    audio_file = session.query(AudioFile).filter_by(id=audio_file_id).first()
    assert audio_file is None, "AudioFile всё ещё существует в БД"


@then('ответ должен содержать JSON массив')
def check_response_is_array(context):
    """Проверяем что ответ - массив."""
    assert isinstance(context['response_data'], list), \
        f"Ответ не является массивом: {type(context['response_data'])}"


@then(parsers.parse('массив должен содержать {count:d} элемента'))
def check_array_length(context, count):
    """Проверяем длину массива."""
    assert len(context['response_data']) == count, \
        f"Массив содержит {len(context['response_data'])} элементов, ожидалось {count}"


@then('каждый элемент должен содержать поле "id"')
def check_each_element_has_id(context):
    """Проверяем что каждый элемент имеет поле id."""
    for item in context['response_data']:
        assert 'id' in item, f"Элемент не содержит поле 'id': {item}"


@then(parsers.parse('каждый элемент должен содержать поле "{field}"'))
def check_each_element_has_field(context, field):
    """Проверяем что каждый элемент имеет поле."""
    for item in context['response_data']:
        assert field in item, f"Элемент не содержит поле '{field}': {item}"


@then(parsers.parse('поле "{field}" должно содержать "{text}"'))
def check_field_contains_text(context, field, text):
    """Проверяем что поле содержит текст."""
    error_message = context['response_data'][field]
    assert text in error_message, \
        f"Поле '{field}' содержит '{error_message}', ожидалось '{text}'"


@given(parsers.parse('существует директория "{path}" с {count:d} аудио-файлами'))
def create_directory_with_files(context, path, count):
    """Создаём директорию с аудио-файлами."""
    tmp_dir = Path(tempfile.gettempdir()) / "audio_import_test"
    if tmp_dir.exists():
        import shutil
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(exist_ok=True, parents=True)
    
    # Создаём файлы
    import numpy as np
    import soundfile as sf
    
    sample_rate = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = np.sin(2 * np.pi * 440 * t)
    stereo_signal = np.column_stack([signal, signal])
    
    for i in range(count):
        file_path = tmp_dir / f"audio_{i}.wav"
        sf.write(str(file_path), stereo_signal, sample_rate)
    
    context['import_dir'] = str(tmp_dir)
    context['import_path_alias'] = path


@given(parsers.parse('директория "{path}" не существует'))
def directory_not_exists(context, path):
    """Помечаем директорию как несуществующую."""
    context['nonexistent_dir'] = path


@then(parsers.parse('в БД существует {count:d} AudioFile'))
def check_audio_files_count(context, count):
    """Проверяем количество AudioFile в БД."""
    from src.models.audio_file import AudioFile
    
    if 'session' not in context:
        context['session'] = context['db'].get_session()
    
    session = context['session']
    actual_count = session.query(AudioFile).count()
    assert actual_count == count, \
        f"В БД найдено {actual_count} AudioFile, ожидалось {count}"

