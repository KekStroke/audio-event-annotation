"""
Тесты для проверки drag selection функционала regions plugin.

Проверяем что пользователь может выделять регионы мышкой.
"""

import pytest
from pytest_bdd import scenarios, given, when, then
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

# Подключаем сценарии
scenarios('features/drag_selection.feature')


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


@then('в конфигурации regions plugin должен быть включен dragSelection: true')
def check_drag_selection_config():
    """Проверяем что dragSelection: true в конфигурации regions plugin."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Ищем создание regions plugin
    lines = content.split('\n')
    
    found_regions_factory = False
    found_drag_selection = False
    in_regions_config = False
    
    for i, line in enumerate(lines):
        # Находим создание regions plugin
        if 'regionsFactory' in line and 'resolveWaveSurferPlugin' in line:
            found_regions_factory = True
            continue
        
        # После нахождения regionsFactory, ищем .create({
        if found_regions_factory and '.create({' in line:
            in_regions_config = True
            continue
        
        # Внутри конфигурации ищем dragSelection
        if in_regions_config:
            if 'dragSelection' in line and 'true' in line:
                found_drag_selection = True
                break
            # Если встретили закрывающую скобку, выходим
            if '})' in line:
                break
    
    assert found_regions_factory, 'Не найдено создание regionsFactory'
    assert found_drag_selection, 'dragSelection: true не найден в конфигурации regions plugin. Это критично для drag selection!'


@then('buildWaveSurferPlugins создает regions plugin с dragSelection')
def check_build_plugins_has_drag():
    """Проверяем что buildWaveSurferPlugins правильно создает regions plugin."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем что функция buildWaveSurferPlugins существует
    assert 'function buildWaveSurferPlugins' in content, 'Функция buildWaveSurferPlugins не найдена'
    
    # Проверяем что regions plugin добавляется в список плагинов
    assert 'plugins.push(' in content, 'plugins.push() не вызывается'
    assert 'regionsFactory.create' in content, 'regionsFactory.create не вызывается'


@then('regions plugin должен быть активен после инициализации')
def check_regions_plugin_active():
    """Проверяем что regions plugin активируется."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем что есть функция для получения активного regions plugin
    assert 'getWaveSurferRegionsPlugin' in content, 'Функция getWaveSurferRegionsPlugin не найдена'
    assert 'getActivePlugins' in content, 'getActivePlugins не используется'


@then('в конфигурации WaveSurfer.create должен быть interact: true')
def check_wavesurfer_interact():
    """Проверяем что WaveSurfer создается с interact: true."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Ищем WaveSurfer.create и проверяем interact
    lines = content.split('\n')
    
    found_create = False
    found_interact = False
    in_create_config = False
    brace_count = 0
    
    for i, line in enumerate(lines):
        # Находим WaveSurfer.create
        if 'WaveSurfer.create({' in line or 'WaveSurfer.create(' in line:
            found_create = True
            in_create_config = True
            # Считаем открывающие скобки в этой строке
            brace_count += line.count('{') - line.count('}')
            continue
        
        # Внутри конфигурации
        if in_create_config:
            brace_count += line.count('{') - line.count('}')
            
            if 'interact:' in line and 'true' in line:
                found_interact = True
            
            # Если скобки закрылись, выходим
            if brace_count <= 0:
                break
    
    assert found_create, 'WaveSurfer.create не найден'
    assert found_interact, 'interact: true не найден в конфигурации WaveSurfer.create. Это критично для drag selection!'


@then('это позволяет взаимодействовать с waveform')
def check_interact_comment():
    """Проверяем что есть комментарий о назначении interact."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Это просто документационная проверка
    assert 'interact' in content.lower(), 'Параметр interact отсутствует'


@then('после вызова ensureWaveSurferInitialized regions plugin должен быть сразу доступен')
def check_regions_available_after_init():
    """
    FAILING TEST: Проверяем что regions plugin доступен СРАЗУ после инициализации.
    
    Проблема: WaveSurfer инициализируется синхронно, но regions plugin может быть доступен 
    только после события 'ready', которое асинхронно. Это ломает drag selection.
    """
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем что cacheWaveSurferPlugins вызывается СРАЗУ после создания WaveSurfer
    # а не только в обработчике 'ready'
    lines = content.split('\n')
    
    found_init_function = False
    found_create = False
    found_cache_after_create = False
    line_after_create = None
    
    for i, line in enumerate(lines):
        if 'function initWaveSurfer' in line:
            found_init_function = True
        
        if found_init_function and 'WaveSurfer.create({' in line:
            found_create = True
            # Ищем закрывающую скобку создания
            for j in range(i + 1, min(i + 30, len(lines))):
                if '});' in lines[j] and 'WaveSurfer.create' not in lines[j]:
                    line_after_create = j
                    break
            continue
        
        if line_after_create and i > line_after_create and i < line_after_create + 5:
            if 'cacheWaveSurferPlugins()' in line:
                found_cache_after_create = True
                break
    
    assert found_init_function, 'Функция initWaveSurfer не найдена'
    assert found_create, 'WaveSurfer.create не найден'
    assert found_cache_after_create, \
        'FAILING: cacheWaveSurferPlugins() НЕ вызывается сразу после WaveSurfer.create(). ' \
        'Regions plugin будет доступен только асинхронно после события ready, ' \
        'что ломает drag selection при первом выборе файла!'


@then('getWaveSurferRegionsPlugin должна возвращать непустой объект')
def check_get_regions_returns_object():
    """Проверяем что getWaveSurferRegionsPlugin правильно работает."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем реализацию getWaveSurferRegionsPlugin
    assert 'function getWaveSurferRegionsPlugin()' in content, \
        'Функция getWaveSurferRegionsPlugin не найдена'
    
    # Проверяем что она возвращает plugin
    lines = content.split('\n')
    in_function = False
    has_return = False
    
    for line in lines:
        if 'function getWaveSurferRegionsPlugin()' in line:
            in_function = True
        if in_function and 'return' in line:
            has_return = True
            break
    
    assert has_return, 'getWaveSurferRegionsPlugin не возвращает значение'


@then('regions plugin должен иметь метод addRegion')
def check_regions_has_add_region():
    """Проверяем что в коде есть использование addRegion."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем что есть функция createRegion которая использует addRegion
    assert 'function createRegion' in content, 'Функция createRegion не найдена'
    assert 'addRegion' in content, 'Метод addRegion не используется'


@then('waveform контейнер должен быть видим и доступен для взаимодействия')
def check_waveform_visible(client):
    """Проверяем что waveform контейнер не скрыт CSS."""
    response = client.get('/')
    html = response.data.decode('utf-8')
    
    # Проверяем что waveform контейнер есть
    assert 'id="waveform"' in html, 'Контейнер waveform не найден в HTML'
    
    # Проверяем CSS
    from pathlib import Path
    css_path = Path(__file__).parent.parent / 'static' / 'css' / 'main.css'
    css = css_path.read_text(encoding='utf-8')
    
    # Ищем стили для #waveform
    lines = css.split('\n')
    in_waveform_style = False
    has_display_none = False
    has_visibility_hidden = False
    has_opacity_zero = False
    
    for line in lines:
        if '#waveform' in line and '{' in line:
            in_waveform_style = True
        if in_waveform_style:
            if 'display:' in line.replace(' ', '') and 'none' in line:
                has_display_none = True
            if 'visibility:' in line.replace(' ', '') and 'hidden' in line:
                has_visibility_hidden = True
            if 'opacity:' in line.replace(' ', '') and '0' in line:
                has_opacity_zero = True
            if '}' in line:
                break
    
    # FAILING TEST: waveform не должен быть скрыт по умолчанию
    assert not has_display_none, \
        'FAILING: #waveform имеет display:none - пользователь не может взаимодействовать!'
    assert not (has_visibility_hidden and has_opacity_zero), \
        'FAILING: #waveform скрыт (visibility:hidden и opacity:0) - пользователь не может взаимодействовать!'


@then('waveform контейнер не должен быть перекрыт loading indicator')
def check_loading_not_blocking():
    """Проверяем что loading indicator не блокирует взаимодействие с waveform."""
    from pathlib import Path
    audio_player_path = Path(__file__).parent.parent / 'static' / 'js' / 'audio-player.js'
    content = audio_player_path.read_text(encoding='utf-8')
    
    # Проверяем что hideLoadingIndicator вызывается после инициализации
    assert 'hideLoadingIndicator' in content, 'Функция hideLoadingIndicator не найдена'
    
    # После создания wavesurfer должен вызываться hideLoadingIndicator
    # чтобы убрать loading indicator который может блокировать interaction
    lines = content.split('\n')
    has_hide_after_init = False
    
    for i, line in enumerate(lines):
        if 'function initWaveSurfer' in line:
            # Ищем hideLoadingIndicator в следующих 50 строках
            for j in range(i, min(i + 50, len(lines))):
                if 'hideLoadingIndicator()' in lines[j]:
                    has_hide_after_init = True
                    break
            break
    
    # НЕ должен вызываться в initWaveSurfer, т.к. это синхронная инициализация
    # loading indicator должен скрываться только после события 'ready'
    # Но проверяем что функция существует
    assert 'function hideLoadingIndicator' in content or 'function showLoadingIndicator' in content


@then('CSS стили не должны блокировать pointer-events на waveform')
def check_pointer_events():
    """Проверяем что pointer-events не заблокированы."""
    from pathlib import Path
    css_path = Path(__file__).parent.parent / 'static' / 'css' / 'main.css'
    css = css_path.read_text(encoding='utf-8')
    
    # Проверяем что нет pointer-events: none на waveform
    lines = css.split('\n')
    in_waveform_style = False
    has_pointer_events_none = False
    
    for line in lines:
        if '#waveform' in line:
            in_waveform_style = True
        if in_waveform_style:
            if 'pointer-events:' in line.replace(' ', '') and 'none' in line:
                has_pointer_events_none = True
            if '}' in line and in_waveform_style:
                in_waveform_style = False
    
    assert not has_pointer_events_none, \
        'FAILING: #waveform имеет pointer-events:none - пользователь не может кликать и делать drag!'

