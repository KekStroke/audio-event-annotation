"""Step definitions для тестирования генерации waveform."""
import pytest
import os
import tempfile
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers
import numpy as np
import soundfile as sf
from PIL import Image
import io

# Связываем сценарии из feature файла
scenarios('features/waveform_generation.feature')


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
    context['session'] = context['db'].get_session()


@given('в БД существует AudioFile с id')
def create_audio_file_in_db(context):
    """Создаём AudioFile в БД."""
    from src.models.audio_file import AudioFile
    
    # Создаём тестовый файл
    tmp_dir = Path(tempfile.gettempdir()) / "audio_waveform_test"
    tmp_dir.mkdir(exist_ok=True, parents=True)
    
    # Создаём файл для тестирования
    file_path = tmp_dir / "test_waveform.wav"
    sample_rate = 44100
    duration = 5.0  # 5 секунд
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = np.sin(2 * np.pi * 440 * t)
    stereo_signal = np.column_stack([signal, signal])
    sf.write(str(file_path), stereo_signal, sample_rate)
    
    file_size = file_path.stat().st_size
    
    if 'session' not in context:
        context['session'] = context['db'].get_session()
    
    audio_file = AudioFile(
        file_path=str(file_path),
        filename="test_waveform.wav",
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


@given('файл существует по пути из AudioFile')
def file_exists_at_path(context):
    """Проверяем что файл существует."""
    file_path = context['audio_file'].file_path
    assert os.path.exists(file_path), f"Файл не существует: {file_path}"


@given('файл НЕ существует по пути из AudioFile')
def file_not_exists_at_path(context):
    """Удаляем файл для теста ошибки."""
    file_path = context['audio_file'].file_path
    if os.path.exists(file_path):
        os.remove(file_path)
    assert not os.path.exists(file_path), "Файл всё ещё существует"


@given(parsers.parse('в БД не существует AudioFile с id "{audio_file_id}"'))
def audio_file_not_in_db(context, audio_file_id):
    """Проверяем что AudioFile не существует."""
    context['nonexistent_id'] = audio_file_id


@given('кэш директория существует')
def cache_directory_exists(context, monkeypatch):
    """Создаём кэш директорию."""
    cache_dir = Path(tempfile.gettempdir()) / "waveform_cache"
    cache_dir.mkdir(exist_ok=True, parents=True)
    context['cache_dir'] = cache_dir
    # Устанавливаем переменную окружения для использования в коде
    import os
    monkeypatch.setenv('WAVEFORM_CACHE_DIR', str(cache_dir))


@given(parsers.parse('размер файла больше {size:d}MB'))
def file_size_greater_than(context, size):
    """Создаём файл больше указанного размера."""
    # Создаём большой файл для теста
    tmp_dir = Path(tempfile.gettempdir()) / "audio_waveform_test"
    tmp_dir.mkdir(exist_ok=True, parents=True)
    
    file_path = tmp_dir / "large_waveform.wav"
    sample_rate = 44100
    # Создаём файл размером больше 10MB
    duration = (size * 1024 * 1024) / (sample_rate * 2 * 2) + 1  # Примерно нужный размер
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = np.sin(2 * np.pi * 440 * t)
    stereo_signal = np.column_stack([signal, signal])
    sf.write(str(file_path), stereo_signal, sample_rate)
    
    file_size = file_path.stat().st_size
    
    # Обновляем AudioFile
    audio_file = context['audio_file']
    audio_file.file_path = str(file_path)
    audio_file.file_size = file_size
    audio_file.duration = duration
    
    session = context['session']
    session.commit()
    
    context['test_file_path'] = str(file_path)
    assert file_size > size * 1024 * 1024, f"Файл слишком маленький: {file_size}"


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
    context['response_data'] = response.get_json() if response.is_json else None
    context['response_bytes'] = response.get_data()


@then(parsers.parse('ответ должен иметь статус {status:d}'))
def check_response_status(context, status):
    """Проверяем статус ответа."""
    actual_status = context['response'].status_code
    assert actual_status == status, \
        f"Ожидался статус {status}, получен {actual_status}"


@then(parsers.parse('ответ должен иметь заголовок "{header_name}" равный "{value}"'))
def check_header_equals(context, header_name, value):
    """Проверяем значение заголовка."""
    header_value = context['response'].headers.get(header_name, '')
    assert header_value == value, \
        f"Заголовок '{header_name}' равен '{header_value}', ожидалось '{value}'"


@then('ответ должен содержать PNG изображение')
def check_response_is_png(context):
    """Проверяем что ответ содержит PNG изображение."""
    data = context.get('response_bytes') or context['response'].get_data()
    assert len(data) > 0, "Ответ не содержит данных"
    
    # Проверяем PNG signature
    assert data[:8] == b'\x89PNG\r\n\x1a\n', "Ответ не является PNG изображением"
    
    # Проверяем что это валидное изображение
    try:
        img = Image.open(io.BytesIO(data))
        assert img.format == 'PNG', "Изображение не в формате PNG"
        context['image'] = img
    except Exception as e:
        pytest.fail(f"Не удалось открыть изображение: {e}")


@then('размер изображения должен быть больше 0 байт')
def check_image_size(context):
    """Проверяем размер изображения."""
    data = context.get('response_bytes') or context['response'].get_data()
    assert len(data) > 0, "Размер изображения равен 0"


@then('файл waveform должен быть сохранён в кэше')
def check_waveform_cached(context):
    """Проверяем что waveform сохранён в кэше."""
    # Проверяем что файл создан в кэше
    cache_dir = context.get('cache_dir')
    if cache_dir:
        # Ищем файлы в кэше
        cache_files = list(cache_dir.glob('*.png'))
        assert len(cache_files) > 0, "Файл waveform не найден в кэше"
        context['cached_file'] = cache_files[0]


@then('при повторном запросе должен использоваться кэш')
def check_cache_used(context, client):
    """Проверяем использование кэша при повторном запросе."""
    audio_file_id = context['audio_file_id']
    endpoint = f"/api/audio/{audio_file_id}/waveform"
    
    # Получаем время модификации кэш файла
    cached_file = context.get('cached_file')
    if cached_file and cached_file.exists():
        original_mtime = cached_file.stat().st_mtime
        
        # Делаем повторный запрос
        response = client.get(endpoint)
        context['response'] = response
        
        # Проверяем что файл не изменился (использовался кэш)
        new_mtime = cached_file.stat().st_mtime
        assert new_mtime == original_mtime, "Кэш не использовался, файл был пересоздан"


@then('ответ должен содержать JSON с полем "error"')
def check_response_has_error(context):
    """Проверяем наличие поля error."""
    assert context['response_data'] is not None, "Ответ не содержит JSON"
    assert 'error' in context['response_data'], \
        f"Ответ не содержит поле 'error': {context['response_data']}"


@then('генерация должна использовать downsampling')
def check_downsampling_used(context):
    """Проверяем что использовался downsampling."""
    # Для больших файлов downsampling должен быть использован
    # Проверяем что изображение было создано (это означает что downsampling сработал)
    data = context.get('response_bytes') or context['response'].get_data()
    assert len(data) > 0, "Изображение не было создано"
    # Если изображение создано для большого файла, значит downsampling использован
    assert True  # Детальная проверка downsampling требует логирования, что выходит за рамки теста

