"""Step definitions для тестирования моделей данных."""
import pytest
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers
from sqlalchemy.exc import IntegrityError

# Связываем сценарии из feature файла
scenarios('features/database_models.feature')


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


@given('база данных инициализирована')
def database_initialized(test_db, context):
    """Инициализируем БД."""
    context['db'] = test_db
    context['session'] = test_db.get_session()


@given('все таблицы созданы')
def tables_created(context):
    """Проверяем что таблицы созданы."""
    db = context['db']
    assert db.engine is not None
    # Таблицы уже созданы в test_db fixture


@when(parsers.parse('я создаю новый AudioFile с данными:\n{table}'))
def create_audio_file(context, table):
    """Создаём AudioFile из таблицы данных."""
    from src.models.audio_file import AudioFile
    
    # Парсим таблицу (упрощённо)
    lines = table.strip().split('\n')
    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    values = [v.strip() for v in lines[1].split('|')[1:-1]]
    data = dict(zip(headers, values))
    
    # Конвертируем типы
    audio_file = AudioFile(
        file_path=data['file_path'],
        filename=data['filename'],
        duration=float(data['duration']),
        sample_rate=int(data['sample_rate']),
        channels=int(data['channels']),
        file_size=int(data['file_size'])
    )
    
    session = context['session']
    session.add(audio_file)
    session.commit()
    context['audio_file'] = audio_file


@then('AudioFile должен быть сохранён в БД')
def audio_file_saved(context):
    """Проверяем что AudioFile сохранён."""
    from src.models.audio_file import AudioFile
    session = context['session']
    audio_file = context['audio_file']
    
    db_audio_file = session.query(AudioFile).filter_by(
        id=audio_file.id
    ).first()
    assert db_audio_file is not None


@then('AudioFile должен иметь UUID id')
def audio_file_has_uuid(context):
    """Проверяем наличие UUID."""
    audio_file = context['audio_file']
    assert audio_file.id is not None
    assert isinstance(str(audio_file.id), str)
    assert len(str(audio_file.id)) == 36  # UUID format


@then('AudioFile должен иметь created_at timestamp')
def audio_file_has_created_at(context):
    """Проверяем наличие created_at."""
    audio_file = context['audio_file']
    assert audio_file.created_at is not None


@then(parsers.parse('AudioFile должен иметь status "{status}"'))
def audio_file_has_status(context, status):
    """Проверяем статус AudioFile."""
    audio_file = context['audio_file']
    assert audio_file.status.value == status


@given(parsers.parse('в БД существует AudioFile с filename "{filename}"'))
def create_audio_file_with_filename(context, filename):
    """Создаём AudioFile с заданным filename."""
    from src.models.audio_file import AudioFile
    
    audio_file = AudioFile(
        file_path=f"/test/{filename}",
        filename=filename,
        duration=100.0,
        sample_rate=44100,
        channels=2,
        file_size=1024000
    )
    
    session = context['session']
    session.add(audio_file)
    session.commit()
    context['audio_file'] = audio_file
    context['audio_file_id'] = audio_file.id


@when('я получаю AudioFile по его id')
def get_audio_file_by_id(context):
    """Получаем AudioFile по ID."""
    from src.models.audio_file import AudioFile
    session = context['session']
    # Пытаемся получить audio_file_id из контекста, если нет - используем audio_file.id
    audio_file_id = context.get('audio_file_id') or context.get('audio_file').id
    
    audio_file = session.query(AudioFile).filter_by(id=audio_file_id).first()
    context['retrieved_audio_file'] = audio_file


@then(parsers.parse('я должен получить AudioFile с filename "{filename}"'))
def check_retrieved_filename(context, filename):
    """Проверяем filename полученного AudioFile."""
    audio_file = context['retrieved_audio_file']
    assert audio_file is not None
    assert audio_file.filename == filename


@then('все поля должны быть корректно загружены')
def check_all_fields_loaded(context):
    """Проверяем что все поля загружены."""
    audio_file = context['retrieved_audio_file']
    assert audio_file.id is not None
    assert audio_file.file_path is not None
    assert audio_file.duration is not None
    assert audio_file.sample_rate is not None
    assert audio_file.channels is not None
    assert audio_file.file_size is not None
    assert audio_file.created_at is not None
    assert audio_file.status is not None


@given(parsers.parse('в БД существует AudioFile с status "{status}"'))
def create_audio_file_with_status(context, status):
    """Создаём AudioFile с заданным статусом."""
    from src.models.audio_file import AudioFile, AudioFileStatus
    
    # Конвертируем строку в enum
    status_enum = AudioFileStatus[status.upper()]
    
    audio_file = AudioFile(
        file_path="/test/file.wav",
        filename="file.wav",
        duration=100.0,
        sample_rate=44100,
        channels=2,
        file_size=1024000,
        status=status_enum
    )
    
    session = context['session']
    session.add(audio_file)
    session.commit()
    context['audio_file'] = audio_file


@when(parsers.parse('я обновляю status на "{new_status}"'))
def update_audio_file_status(context, new_status):
    """Обновляем статус AudioFile."""
    from src.models.audio_file import AudioFileStatus
    
    audio_file = context['audio_file']
    # Конвертируем строку в enum
    audio_file.status = AudioFileStatus[new_status.upper()]
    session = context['session']
    session.commit()


@then(parsers.parse('AudioFile в БД должен иметь status "{status}"'))
def check_audio_file_status_in_db(context, status):
    """Проверяем статус в БД."""
    from src.models.audio_file import AudioFile
    session = context['session']
    audio_file_id = context['audio_file'].id
    
    audio_file = session.query(AudioFile).filter_by(id=audio_file_id).first()
    assert audio_file.status.value == status


@when('я удаляю этот AudioFile')
def delete_audio_file(context):
    """Удаляем AudioFile."""
    audio_file = context.get('audio_file')
    session = context['session']
    session.delete(audio_file)
    session.commit()


@then('AudioFile не должен существовать в БД')
def check_audio_file_deleted(context):
    """Проверяем что AudioFile удалён."""
    from src.models.audio_file import AudioFile
    session = context['session']
    audio_file_id = context['audio_file'].id
    
    audio_file = session.query(AudioFile).filter_by(id=audio_file_id).first()
    assert audio_file is None


@given('в БД существует AudioFile с id')
def create_audio_file_for_annotation(context):
    """Создаём AudioFile для аннотаций."""
    from src.models.audio_file import AudioFile
    
    audio_file = AudioFile(
        file_path="/test/annotated.wav",
        filename="annotated.wav",
        duration=100.0,
        sample_rate=44100,
        channels=2,
        file_size=1024000
    )
    
    session = context['session']
    session.add(audio_file)
    session.commit()
    context['audio_file'] = audio_file


@when(parsers.parse('я создаю Annotation для этого AudioFile:\n{table}'))
def create_annotation(context, table):
    """Создаём Annotation."""
    from src.models.annotation import Annotation
    
    lines = table.strip().split('\n')
    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    values = [v.strip() for v in lines[1].split('|')[1:-1]]
    data = dict(zip(headers, values))
    
    annotation = Annotation(
        audio_file_id=context['audio_file'].id,
        start_time=float(data['start_time']),
        end_time=float(data['end_time']),
        event_label=data['event_label'],
        confidence=float(data['confidence']) if data['confidence'] else None,
        notes=data['notes'] if data['notes'] else None
    )
    
    session = context['session']
    session.add(annotation)
    session.commit()
    context['annotation'] = annotation


@then('Annotation должна быть сохранена в БД')
def annotation_saved(context):
    """Проверяем что Annotation сохранена."""
    from src.models.annotation import Annotation
    session = context['session']
    annotation = context['annotation']
    
    db_annotation = session.query(Annotation).filter_by(id=annotation.id).first()
    assert db_annotation is not None


@then('Annotation должна иметь UUID id')
def annotation_has_uuid(context):
    """Проверяем UUID аннотации."""
    annotation = context['annotation']
    assert annotation.id is not None
    assert len(str(annotation.id)) == 36


@then('Annotation должна иметь created_at и updated_at timestamps')
def annotation_has_timestamps(context):
    """Проверяем timestamps."""
    annotation = context['annotation']
    assert annotation.created_at is not None
    assert annotation.updated_at is not None


@then('Annotation должна быть связана с AudioFile')
def annotation_linked_to_audio_file(context):
    """Проверяем связь с AudioFile."""
    annotation = context['annotation']
    audio_file = context['audio_file']
    assert annotation.audio_file_id == audio_file.id


@given(parsers.parse('в БД существует AudioFile с {count:d} аннотациями'))
def create_audio_file_with_annotations(context, count):
    """Создаём AudioFile с несколькими аннотациями."""
    from src.models.audio_file import AudioFile
    from src.models.annotation import Annotation
    
    audio_file = AudioFile(
        file_path="/test/multi_annotated.wav",
        filename="multi_annotated.wav",
        duration=100.0,
        sample_rate=44100,
        channels=2,
        file_size=1024000
    )
    
    session = context['session']
    session.add(audio_file)
    session.flush()
    
    for i in range(count):
        annotation = Annotation(
            audio_file_id=audio_file.id,
            start_time=i * 10.0,
            end_time=(i + 1) * 10.0,
            event_label=f"event_{i}"
        )
        session.add(annotation)
    
    session.commit()
    context['audio_file'] = audio_file
    context['annotation_count'] = count


@when('я получаю все аннотации для этого AudioFile')
def get_all_annotations(context):
    """Получаем все аннотации."""
    from src.models.annotation import Annotation
    session = context['session']
    audio_file = context['audio_file']
    
    annotations = session.query(Annotation).filter_by(
        audio_file_id=audio_file.id
    ).all()
    context['annotations'] = annotations


@then(parsers.parse('я должен получить список из {count:d} аннотаций'))
def check_annotations_count(context, count):
    """Проверяем количество аннотаций."""
    annotations = context['annotations']
    assert len(annotations) == count


@then('все аннотации должны быть связаны с этим AudioFile')
def check_annotations_linked(context):
    """Проверяем связь всех аннотаций."""
    annotations = context['annotations']
    audio_file = context['audio_file']
    
    for annotation in annotations:
        assert annotation.audio_file_id == audio_file.id


@when(parsers.parse('я создаю EventType с данными:\n{table}'))
def create_event_type(context, table):
    """Создаём EventType."""
    from src.models.event_type import EventType
    
    lines = table.strip().split('\n')
    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    values = [v.strip() for v in lines[1].split('|')[1:-1]]
    data = dict(zip(headers, values))
    
    event_type = EventType(
        name=data['name'],
        color=data['color'],
        description=data['description']
    )
    
    session = context['session']
    session.add(event_type)
    session.commit()
    context['event_type'] = event_type


@then('EventType должен быть сохранён в БД')
def event_type_saved(context):
    """Проверяем сохранение EventType."""
    from src.models.event_type import EventType
    session = context['session']
    event_type = context['event_type']
    
    db_event_type = session.query(EventType).filter_by(id=event_type.id).first()
    assert db_event_type is not None


@then('EventType должен иметь UUID id')
def event_type_has_uuid(context):
    """Проверяем UUID."""
    event_type = context['event_type']
    assert event_type.id is not None
    assert len(str(event_type.id)) == 36


@given(parsers.parse('в БД существует {count:d} различных EventType'))
def create_multiple_event_types(context, count):
    """Создаём несколько EventType."""
    from src.models.event_type import EventType
    session = context['session']
    
    for i in range(count):
        event_type = EventType(
            name=f"event_type_{i}",
            color=f"#FF{i:04X}",
            description=f"Description {i}"
        )
        session.add(event_type)
    
    session.commit()


@when('я получаю все EventType')
def get_all_event_types(context):
    """Получаем все EventType."""
    from src.models.event_type import EventType
    session = context['session']
    
    event_types = session.query(EventType).all()
    context['event_types'] = event_types


@then(parsers.parse('я должен получить список из {count:d} EventType'))
def check_event_types_count(context, count):
    """Проверяем количество EventType."""
    event_types = context['event_types']
    assert len(event_types) == count


@when(parsers.parse('я создаю Project с данными:\n{table}'))
def create_project(context, table):
    """Создаём Project."""
    from src.models.project import Project
    
    lines = table.strip().split('\n')
    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    values = [v.strip() for v in lines[1].split('|')[1:-1]]
    data = dict(zip(headers, values))
    
    project = Project(
        name=data['name'],
        description=data['description']
    )
    
    session = context['session']
    session.add(project)
    session.commit()
    context['project'] = project


@then('Project должен быть сохранён в БД')
def project_saved(context):
    """Проверяем сохранение Project."""
    from src.models.project import Project
    session = context['session']
    project = context['project']
    
    db_project = session.query(Project).filter_by(id=project.id).first()
    assert db_project is not None


@then('Project должен иметь UUID id')
def project_has_uuid(context):
    """Проверяем UUID."""
    project = context['project']
    assert project.id is not None
    assert len(str(project.id)) == 36


@then('Project должен иметь created_at timestamp')
def project_has_created_at(context):
    """Проверяем created_at."""
    project = context['project']
    assert project.created_at is not None


@then('все связанные аннотации должны быть удалены')
def check_annotations_cascade_deleted(context):
    """Проверяем каскадное удаление."""
    from src.models.annotation import Annotation
    session = context['session']
    audio_file_id = context['audio_file'].id
    
    annotations = session.query(Annotation).filter_by(
        audio_file_id=audio_file_id
    ).all()
    assert len(annotations) == 0


@given(parsers.parse('в БД существует EventType с name "{name}"'))
def create_event_type_with_name(context, name):
    """Создаём EventType с заданным именем."""
    from src.models.event_type import EventType
    
    event_type = EventType(
        name=name,
        color="#000000",
        description="Test"
    )
    
    session = context['session']
    session.add(event_type)
    session.commit()


@when(parsers.parse('я пытаюсь создать ещё один EventType с name "{name}"'))
def try_create_duplicate_event_type(context, name):
    """Пытаемся создать дубликат EventType."""
    from src.models.event_type import EventType
    
    event_type = EventType(
        name=name,
        color="#111111",
        description="Duplicate"
    )
    
    session = context['session']
    session.add(event_type)
    
    try:
        session.commit()
        context['error'] = None
    except IntegrityError as e:
        session.rollback()
        context['error'] = e


@then('операция должна завершиться с ошибкой')
def check_operation_failed(context):
    """Проверяем что операция завершилась с ошибкой."""
    assert context['error'] is not None

