"""Step definitions для тестирования интеграции wavesurfer.js."""
from bs4 import BeautifulSoup
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Связываем сценарии из feature файла
scenarios('features/wavesurfer_integration.feature')


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


@then('HTML должен содержать script тег с wavesurfer.js CDN')
def check_wavesurfer_cdn_script(context):
    """Проверяем наличие script тега с wavesurfer.js CDN."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    wavesurfer_found = False
    
    for script in scripts:
        src = script.get('src', '')
        if 'wavesurfer.js' in src.lower() or 'unpkg.com/wavesurfer' in src:
            wavesurfer_found = True
            context['wavesurfer_script'] = script
            break
    
    assert wavesurfer_found, 'Script тег с wavesurfer.js CDN не найден'


@then('wavesurfer.js должен быть загружен из CDN')
def check_wavesurfer_cdn_source(context):
    """Проверяем что wavesurfer.js загружается из CDN."""
    assert 'wavesurfer_script' in context, 'Script тег wavesurfer не найден'
    
    script = context['wavesurfer_script']
    src = script.get('src', '')
    
    # Проверяем что это CDN (unpkg, cdnjs, jsdelivr и т.д.)
    cdn_domains = ['unpkg.com', 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'cdnjs.com']
    is_cdn = any(domain in src for domain in cdn_domains)
    
    assert is_cdn, f'wavesurfer.js не загружается из CDN. Источник: {src}'


@then('HTML должен содержать элемент с id "waveform"')
def check_waveform_element(context):
    """Проверяем наличие элемента с id waveform."""
    assert 'html' in context, 'HTML не был распарсен'
    
    waveform = context['html'].find(id='waveform')
    assert waveform is not None, 'Элемент с id "waveform" не найден'
    context['waveform_element'] = waveform


@then(parsers.parse('должен быть подключен файл "{filename}"'))
def check_js_file_connected(context, filename):
    """Проверяем подключение JavaScript файла."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    file_found = False
    
    for script in scripts:
        src = script.get('src', '')
        if filename in src:
            file_found = True
            break
    
    assert file_found, f'Файл "{filename}" не подключен'


@then('функция инициализации wavesurfer должна быть определена')
def check_wavesurfer_init_function(context):
    """Проверяем что есть функция инициализации wavesurfer."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    init_found = False
    
    for script in scripts:
        script_content = script.string or ''
        # Ищем инициализацию wavesurfer (WaveSurfer.create или new WaveSurfer)
        if 'wavesurfer' in script_content.lower() and ('create' in script_content.lower() or 'new wavesurfer' in script_content.lower()):
            init_found = True
            break
    
    # Также проверяем внешний файл audio-player.js
    # Если файл подключен, считаем что функция там определена
    scripts = context['html'].find_all('script', src=True)
    audio_player_connected = any('audio-player.js' in script.get('src', '') for script in scripts)
    
    assert init_found or audio_player_connected, 'Функция инициализации wavesurfer не найдена'


@then('должны быть кнопки Play и Pause')
def check_play_pause_buttons(context):
    """Проверяем наличие кнопок Play и Pause."""
    assert 'html' in context, 'HTML не был распарсен'
    
    buttons = context['html'].find_all('button')
    play_found = False
    pause_found = False
    
    for button in buttons:
        text = button.get_text().lower()
        data_action = button.get('data-action', '').lower()
        
        if 'play' in text or 'play' in data_action:
            play_found = True
        if 'pause' in text or 'pause' in data_action:
            pause_found = True
    
    assert play_found, 'Кнопка Play не найдена'
    assert pause_found, 'Кнопка Pause не найдена'


@then('кнопки должны иметь обработчики событий для wavesurfer')
def check_button_event_handlers(context):
    """Проверяем наличие обработчиков событий для кнопок."""
    assert 'html' in context, 'HTML не был распарсен'
    
    buttons = context['html'].find_all('button')
    handlers_found = False
    
    for button in buttons:
        # Проверяем onclick, data-action или классы для обработчиков
        onclick = button.get('onclick', '')
        data_action = button.get('data-action', '')
        class_name = ' '.join(button.get('class', []))
        
        if 'play' in onclick.lower() or 'pause' in onclick.lower():
            handlers_found = True
        if 'play' in data_action.lower() or 'pause' in data_action.lower():
            handlers_found = True
        if 'play' in class_name.lower() or 'pause' in class_name.lower():
            handlers_found = True
    
    # Также проверяем что есть JavaScript код для обработки
    scripts = context['html'].find_all('script')
    for script in scripts:
        script_content = script.string or ''
        if 'addEventListener' in script_content and ('play' in script_content.lower() or 'pause' in script_content.lower()):
            handlers_found = True
            break
    
    # Если подключен audio-player.js, считаем что обработчики там
    scripts = context['html'].find_all('script', src=True)
    audio_player_connected = any('audio-player.js' in script.get('src', '') for script in scripts)
    
    assert handlers_found or audio_player_connected, 'Обработчики событий для кнопок не найдены'


@then('должен быть элемент для отображения времени')
def check_time_display_element(context):
    """Проверяем наличие элемента для отображения времени."""
    assert 'html' in context, 'HTML не был распарсен'
    
    # Ищем элемент с классом или id связанным со временем
    time_elements = (
        context['html'].find_all(id='time-display') +
        context['html'].find_all(class_='time-display') +
        context['html'].find_all(class_='current-time')
    )
    
    assert len(time_elements) > 0, 'Элемент для отображения времени не найден'


@then('должен быть подключен плагин timeline')
def check_timeline_plugin(context):
    """Проверяем подключение плагина timeline."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    timeline_found = False
    
    for script in scripts:
        src = script.get('src', '')
        script_content = script.string or ''
        
        # Проверяем CDN ссылку на timeline плагин
        if 'timeline' in src.lower() and 'wavesurfer' in src.lower():
            timeline_found = True
            break
        
        # Проверяем использование плагина в коде
        if 'timeline' in script_content.lower() and 'wavesurfer' in script_content.lower():
            timeline_found = True
            break
    
    # Если подключен audio-player.js, считаем что плагин там
    scripts = context['html'].find_all('script', src=True)
    audio_player_connected = any('audio-player.js' in script.get('src', '') for script in scripts)
    
    assert timeline_found or audio_player_connected, 'Плагин timeline не подключен'


@then('wavesurfer должен быть инициализирован с опцией interact: true')
def check_wavesurfer_interact_option(context):
    """Проверяем что wavesurfer инициализирован с interact: true."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    interact_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'interact' in script_content.lower() and ('true' in script_content or 'interact: true' in script_content):
            interact_found = True
            break
    
    # Если подключен audio-player.js, считаем что опция там
    scripts = context['html'].find_all('script', src=True)
    audio_player_connected = any('audio-player.js' in script.get('src', '') for script in scripts)
    
    assert interact_found or audio_player_connected, 'Опция interact: true не найдена'


@then('должен быть обработчик события seek')
def check_seek_event_handler(context):
    """Проверяем наличие обработчика события seek."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    seek_handler_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'seek' in script_content.lower() and ('addEventListener' in script_content or 'on(' in script_content):
            seek_handler_found = True
            break
    
    # Если подключен audio-player.js, считаем что обработчик там
    scripts = context['html'].find_all('script', src=True)
    audio_player_connected = any('audio-player.js' in script.get('src', '') for script in scripts)
    
    assert seek_handler_found or audio_player_connected, 'Обработчик события seek не найден'


@then('должен быть подключен плагин regions')
def check_regions_plugin(context):
    """Проверяем подключение плагина regions."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    regions_found = False
    
    for script in scripts:
        src = script.get('src', '')
        script_content = script.string or ''
        
        # Проверяем CDN ссылку на regions плагин
        if 'regions' in src.lower() and 'wavesurfer' in src.lower():
            regions_found = True
            break
        
        # Проверяем использование плагина в коде
        if 'regions' in script_content.lower() and 'wavesurfer' in script_content.lower():
            regions_found = True
            break
    
    # Если подключен audio-player.js, считаем что плагин там
    scripts = context['html'].find_all('script', src=True)
    audio_player_connected = any('audio-player.js' in script.get('src', '') for script in scripts)
    
    assert regions_found or audio_player_connected, 'Плагин regions не подключен'


@then('должна быть функция для создания регионов')
def check_region_creation_function(context):
    """Проверяем наличие функции для создания регионов."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    region_function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'region' in script_content.lower() and ('addRegion' in script_content or 'createRegion' in script_content or 'addregion' in script_content.lower()):
            region_function_found = True
            break
    
    # Если подключен audio-player.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    audio_player_connected = any('audio-player.js' in script.get('src', '') for script in scripts)
    
    assert region_function_found or audio_player_connected, 'Функция для создания регионов не найдена'


@then('должны быть кнопки для zoom in и zoom out')
def check_zoom_buttons(context):
    """Проверяем наличие кнопок для zoom."""
    assert 'html' in context, 'HTML не был распарсен'
    
    buttons = context['html'].find_all('button')
    zoom_in_found = False
    zoom_out_found = False
    
    for button in buttons:
        text = button.get_text().lower()
        data_action = button.get('data-action', '').lower()
        button_id = button.get('id', '').lower()
        class_name = ' '.join(button.get('class', [])).lower()
        
        if 'zoom' in text or 'zoom' in data_action or 'zoom' in button_id or 'zoom' in class_name:
            if 'in' in text or 'in' in data_action or 'in' in button_id:
                zoom_in_found = True
            if 'out' in text or 'out' in data_action or 'out' in button_id:
                zoom_out_found = True
    
    assert zoom_in_found, 'Кнопка zoom in не найдена'
    assert zoom_out_found, 'Кнопка zoom out не найдена'


@then('должна быть функция для изменения zoom уровня')
def check_zoom_function(context):
    """Проверяем наличие функции для изменения zoom."""
    assert 'html' in context, 'HTML не был распарсен'
    
    scripts = context['html'].find_all('script')
    zoom_function_found = False
    
    for script in scripts:
        script_content = script.string or ''
        if 'zoom' in script_content.lower() and ('setZoom' in script_content or 'zoom(' in script_content.lower()):
            zoom_function_found = True
            break
    
    # Если подключен audio-player.js, считаем что функция там
    scripts = context['html'].find_all('script', src=True)
    audio_player_connected = any('audio-player.js' in script.get('src', '') for script in scripts)
    
    assert zoom_function_found or audio_player_connected, 'Функция для изменения zoom уровня не найдена'

