"""
Тесты для проверки готовности regions plugin в WaveSurfer.

Эти тесты проверяют, что regions plugin правильно инициализируется
и становится доступен для selection-tool.js.
"""

import pytest
from pytest_bdd import scenarios, given, when, then
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

# Подключаем сценарии
scenarios('features/regions_plugin_ready.feature')


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
def test_audio_file(tmp_path):
    """Создаём тестовый аудио-файл."""
    audio_file = tmp_path / "test_audio.wav"
    # Создаём короткий аудио сигнал
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    
    # Сохраняем как WAV
    sf.write(str(audio_file), signal, sample_rate)
    
    return str(audio_file)


@pytest.fixture
def context(test_db):
    """Контекст для хранения данных между шагами теста."""
    from src.models import database
    database._db_instance = test_db
    return {'db': test_db}


@given('Flask приложение запущено')
def flask_app_running(app, context):
    """Flask приложение доступно."""
    context['app'] = app
    assert app is not None


@given('в системе есть аудио-файл')
def setup_audio_file(client, test_audio_file, context):
    """Создаём тестовый аудио-файл."""
    response = client.post(
        '/api/audio/add',
        json={'file_path': test_audio_file},
        content_type='application/json'
    )
    assert response.status_code == 201
    context['audio_file_id'] = response.get_json()['id']
    return response.get_json()


@when('я открываю главную страницу "/"')
def open_main_page(client):
    """Открываем главную страницу."""
    response = client.get('/')
    assert response.status_code == 200
    return response


@then('скрипт audio-player.js должен диспатчить событие "wavesurferRegionsReady"')
def check_wavesurfer_regions_ready_event(client):
    """Проверяем, что событие wavesurferRegionsReady диспатчится."""
    response = client.get('/')
    html = response.data.decode('utf-8')
    
    # Проверяем, что audio-player.js подключён
    assert 'audio-player.js' in html
    
    # Проверяем, что в audio-player.js есть функция notifyRegionsPluginReady
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    assert 'notifyRegionsPluginReady' in content, 'Функция notifyRegionsPluginReady не найдена'
    assert 'wavesurferRegionsReady' in content, 'Событие wavesurferRegionsReady не диспатчится'
    assert 'document.dispatchEvent' in content, 'dispatchEvent не вызывается'
    
    # НОВАЯ ПРОВЕРКА: событие wavesurferReady должно диспатчиться ДО regions
    assert 'notifyWavesurferReady' in content, 'Функция notifyWavesurferReady не найдена (нужна для уведомления о готовности wavesurfer)'
    assert 'wavesurferReady' in content, 'Событие wavesurferReady не диспатчится'


@then('событие должно содержать regions plugin в detail')
def check_event_contains_plugin():
    """Проверяем, что событие содержит plugin в detail."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем, что событие создаётся с detail
    assert 'new CustomEvent' in content or 'CustomEvent(' in content
    assert 'detail:' in content or 'detail =' in content


@then('selection-tool.js должен подписаться на событие "wavesurferRegionsReady"')
def check_selection_tool_subscribes():
    """Проверяем, что selection-tool подписан на событие."""
    from pathlib import Path
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    assert 'wavesurferRegionsReady' in content, 'selection-tool не подписан на wavesurferRegionsReady'
    assert 'addEventListener' in content, 'addEventListener не используется'
    
    # НОВАЯ ПРОВЕРКА: selection-tool должен подписаться на wavesurferReady чтобы избежать race condition
    assert 'wavesurferReady' in content, 'selection-tool не подписан на wavesurferReady (нужно для правильной последовательности инициализации)'


@then('selection-tool.js должен получить доступ к regions plugin')
def check_selection_tool_gets_plugin():
    """Проверяем, что selection-tool может получить plugin."""
    from pathlib import Path
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    assert 'getSelectionRegionsPlugin' in content, 'Функция getSelectionRegionsPlugin не найдена'
    assert 'getWaveSurferRegionsPlugin' in content, 'selection-tool должен запрашивать regions plugin через getWaveSurferRegionsPlugin'


@then('regions plugin должен быть доступен после загрузки аудио')
def check_plugin_available_after_load():
    """Проверяем, что plugin доступен после загрузки."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    assert 'wavesurfer.on("ready"' in content or 'wavesurfer.on(\'ready\'' in content
    assert 'notifyRegionsPluginReady' in content


@then('функция getWaveSurferRegionsPlugin должна возвращать plugin')
def check_get_plugin_function():
    """Проверяем, что функция getWaveSurferRegionsPlugin работает."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    assert 'function getWaveSurferRegionsPlugin' in content or 'getWaveSurferRegionsPlugin()' in content
    assert 'getActivePlugins' in content, 'Функция должна использовать wavesurfer.getActivePlugins()'


@then('получение plugin не должно зависеть от кэширования')
def ensure_plugin_access_without_cache():
    """Проверяем, что код не содержит кэширующей логики."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    assert 'cacheWaveSurferPlugins' not in content, 'Функция cacheWaveSurferPlugins должна быть удалена'
    assert 'window.waveSurferRegionsPlugin' not in content, 'Не должно быть ссылок на window.waveSurferRegionsPlugin'


@then('событие wavesurferRegionsReady должно срабатывать синхронно после инициализации')
def check_event_timing():
    """Проверяем, что событие срабатывает вовремя."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    assert 'notifyRegionsPluginReady()' in content, \
        'Ожидается вызов notifyRegionsPluginReady() для уведомления listeners'
    assert 'wavesurfer.on("ready"' in content or 'wavesurfer.on(\'ready\'' in content, \
        'Должен быть обработчик события ready'
    assert 'wavesurfer.on("decode"' in content or 'wavesurfer.on(\'decode\'' in content, \
        'Должен быть обработчик события decode'


@then('warning "Regions plugin не готов" не должен появляться')
def check_no_warning():
    """Проверяем, что warning не появляется при правильной инициализации."""
    from pathlib import Path
    selection_tool_path = Path(__file__).parent.parent / 'static' / 'js' / 'selection-tool.js'
    content = selection_tool_path.read_text(encoding='utf-8')
    
    # Проверяем, что есть правильная обработка случая, когда plugin готов
    assert 'initSelectionTool' in content, 'Функция initSelectionTool не найдена'
    
    # Проверяем, что в initSelectionTool есть проверка regions plugin
    assert 'getSelectionRegionsPlugin()' in content, 'Нет вызова getSelectionRegionsPlugin()'
    
    # Проверяем, что есть условная логика для проверки plugin
    assert 'if (!regionsPlugin)' in content or 'if (regionsPlugin)' in content or 'if (!plugin)' in content, \
        'Нет проверки доступности regions plugin'
    
    # Проверяем, что есть return при отсутствии plugin
    assert 'return false' in content or 'return;' in content, \
        'Нет return при отсутствии plugin'
    
    # FAILING TEST: НЕ должно быть setTimeout для инициализации (это причина race condition)
    lines = content.split('\n')
    in_dom_content_loaded = False
    has_settimeout_in_init = False
    
    for i, line in enumerate(lines):
        if "addEventListener('DOMContentLoaded'" in line or 'addEventListener("DOMContentLoaded"' in line:
            in_dom_content_loaded = True
        if in_dom_content_loaded and 'setTimeout' in line:
            # Проверяем следующие 5 строк на наличие initSelectionTool
            for j in range(i, min(i + 10, len(lines))):
                if 'initSelectionTool' in lines[j]:
                    has_settimeout_in_init = True
                    break
        if in_dom_content_loaded and line.strip() == '});':
            break
    
    assert not has_settimeout_in_init, \
        'В DOMContentLoaded используется setTimeout для initSelectionTool - это вызывает race condition. Нужно использовать wavesurferReady событие.'

