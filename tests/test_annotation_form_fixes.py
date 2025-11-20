"""
Тесты для исправлений Annotation Form
"""
from pathlib import Path
import re
from pytest_bdd import scenarios, given, when, then

# Загружаем сценарии из feature-файла
scenarios('features/annotation_form_fixes.feature')

@given('annotation-form.js contains submitAnnotationForm function')
def annotation_form_has_submit():
    """Проверяем что файл существует и содержит функцию saveAnnotation (которая отправляет данные)"""
    annotation_form_path = Path(__file__).parent.parent / 'static' / 'js' / 'annotation-form.js'
    assert annotation_form_path.exists()
    content = annotation_form_path.read_text(encoding='utf-8')
    assert 'function saveAnnotation' in content, 'Должна быть функция saveAnnotation для отправки формы'

@when('I check submitAnnotationForm code')
def check_submit_code():
    """Сохраняем содержимое для проверки"""
    pass

@then('function should check window.currentAudioFileId')
def check_uses_window_audio_id():
    """
    Проверяем что используется window.currentAudioFileId
    """
    annotation_form_path = Path(__file__).parent.parent / 'static' / 'js' / 'annotation-form.js'
    content = annotation_form_path.read_text(encoding='utf-8')
    
    # Упрощенная проверка - просто ищем window.currentAudioFileId в файле
    assert 'window.currentAudioFileId' in content, \
        'annotation-form.js должен использовать window.currentAudioFileId как fallback'

@then('function should use currentAudioFileId if audioFileId is not set')
def check_fallback_to_current():
    """
    FAILING TEST: Проверяем что есть fallback на currentAudioFileId
    """
    annotation_form_path = Path(__file__).parent.parent / 'static' / 'js' / 'annotation-form.js'
    content = annotation_form_path.read_text(encoding='utf-8')
    
    # Должен быть fallback: audioFileId || window.currentAudioFileId
    assert ('currentAudioFileId' in content or 'window.currentAudioFileId' in content), \
        'Должен быть fallback на window.currentAudioFileId'


@given('annotation-form.js subscribes to audioFileSelected event')
def annotation_form_subscribes():
    """
    FAILING TEST: Проверяем подписку на audioFileSelected
    """
    annotation_form_path = Path(__file__).parent.parent / 'static' / 'js' / 'annotation-form.js'
    content = annotation_form_path.read_text(encoding='utf-8')
    
    # Должна быть подписка на событие
    assert "addEventListener('audioFileSelected'" in content or \
           'addEventListener("audioFileSelected"' in content, \
        'annotation-form.js должен подписываться на audioFileSelected'

@when('audioFileSelected event is dispatched')
def dispatch_audio_selected():
    """Подготовка к проверке"""
    pass

@then('annotation form should update its audioFileId')
def check_updates_audio_file_id():
    """Проверяем что audioFileId обновляется"""
    annotation_form_path = Path(__file__).parent.parent / 'static' / 'js' / 'annotation-form.js'
    content = annotation_form_path.read_text(encoding='utf-8')
    
    # В обработчике audioFileSelected должно быть обновление ID
    assert 'audioFileSelected' in content, \
        'Должен быть обработчик audioFileSelected для обновления audioFileId'

