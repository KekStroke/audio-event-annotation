"""Step definitions для тестирования генерации спектрограммы."""
import io
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from PIL import Image
from pytest_bdd import given, parsers, scenarios, then, when

# Связываем сценарии из feature файла
scenarios('features/spectrogram_generation.feature')


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


def _create_test_audio_file(filename: str, duration: float = 5.0) -> Path:
    """Создаёт временной WAV файл для тестов."""
    tmp_dir = Path(tempfile.gettempdir()) / 'audio_spectrogram_test'
    tmp_dir.mkdir(exist_ok=True, parents=True)

    file_path = tmp_dir / filename
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Сигнал: комбинация синусов для спектрограммы
    signal = np.sin(2 * np.pi * 220 * t) + 0.5 * np.sin(2 * np.pi * 440 * t)
    stereo_signal = np.column_stack([signal, signal])
    sf.write(str(file_path), stereo_signal, sample_rate)

    return file_path


@given('в БД существует AudioFile с id')
def create_audio_file_in_db(context):
    """Создаём AudioFile в БД."""
    from src.models.audio_file import AudioFile

    file_path = _create_test_audio_file('test_spectrogram.wav', duration=6.0)
    sample_rate = 44100
    duration = 6.0
    file_size = file_path.stat().st_size

    if 'session' not in context:
        context['session'] = context['db'].get_session()

    audio_file = AudioFile(
        file_path=str(file_path),
        filename='test_spectrogram.wav',
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
    assert os.path.exists(file_path), f'Файл не существует: {file_path}'


@given('файл НЕ существует по пути из AudioFile')
def file_not_exists_at_path(context):
    """Удаляем файл для теста ошибки."""
    file_path = context['audio_file'].file_path
    if os.path.exists(file_path):
        os.remove(file_path)
    assert not os.path.exists(file_path), 'Файл всё ещё существует'


@given(parsers.parse('в БД не существует AudioFile с id "{audio_file_id}"'))
def audio_file_not_in_db(context, audio_file_id):
    """Сохраняем несуществующий ID."""
    context['nonexistent_id'] = audio_file_id


@given('кэш директория для спектрограмм существует')
def spectrogram_cache_directory_exists(context, monkeypatch):
    """Создаём кэш директорию и настраиваем переменную окружения."""
    cache_dir = Path(tempfile.gettempdir()) / 'spectrogram_cache'
    cache_dir.mkdir(exist_ok=True, parents=True)
    context['spectrogram_cache_dir'] = cache_dir
    monkeypatch.setenv('SPECTROGRAM_CACHE_DIR', str(cache_dir))


@when(parsers.parse('я отправляю GET запрос на "{endpoint}"'))
def send_get_request(context, endpoint, client):
    """Отправляем GET запрос и сохраняем ответ."""
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
    assert actual_status == status, (
        f'Ожидался статус {status}, получен {actual_status}. '
        f'Ответ: {context.get("response_data")}'
    )


@then(parsers.parse('ответ должен иметь заголовок "{header_name}" равный "{value}"'))
def check_header_equals(context, header_name, value):
    """Проверяем значение заголовка."""
    header_value = context['response'].headers.get(header_name, '')
    assert header_value == value, (
        f"Заголовок '{header_name}' равен '{header_value}', ожидалось '{value}'"
    )


@then('ответ должен содержать PNG изображение')
def check_response_is_png(context):
    """Проверяем что ответ содержит корректное PNG изображение."""
    data = context.get('response_bytes') or context['response'].get_data()
    assert len(data) > 0, 'Ответ не содержит данных'

    # Проверяем PNG signature
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'Ответ не является PNG изображением'

    # Проверяем что изображение открывается
    try:
        img = Image.open(io.BytesIO(data))
        assert img.format == 'PNG', 'Изображение не в формате PNG'
        context['image'] = img
    except Exception as exc:  # pragma: no cover
        pytest.fail(f'Не удалось открыть изображение: {exc}')


@then('файл спектрограммы должен быть сохранён в кэше')
def check_spectrogram_cached(context):
    """Проверяем наличие файла в кэш директории."""
    cache_dir = context.get('spectrogram_cache_dir')
    assert cache_dir is not None, 'Кэш директория не определена'
    cache_files = list(cache_dir.glob('*.png'))
    assert len(cache_files) > 0, 'Файл спектрограммы не найден в кэше'
    context['cached_file'] = cache_files[0]


@then('при повторном запросе спектрограмма должна использовать кэш')
def check_cache_used(context, client):
    """Делаем повторный запрос и убеждаемся что кэш не изменился."""
    cached_file = context.get('cached_file')
    assert cached_file is not None and cached_file.exists(), 'Нет кэшированного файла'

    original_mtime = cached_file.stat().st_mtime
    endpoint = f"/api/audio/{context['audio_file_id']}/spectrogram?start_time=0.5&end_time=2.5"

    response = client.get(endpoint)
    context['response'] = response

    new_mtime = cached_file.stat().st_mtime
    assert new_mtime == original_mtime, 'Кэш не использовался, файл был перезаписан'


@then('ответ должен содержать JSON с полем "error"')
def check_response_has_error(context):
    """Проверяем наличие поля error в JSON ответе."""
    assert context['response_data'] is not None, 'Ответ не содержит JSON'
    assert 'error' in context['response_data'], (
        f"Ответ не содержит поле 'error': {context['response_data']}"
    )
