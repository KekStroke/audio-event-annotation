"""
API endpoints для работы с аудио-файлами.

Предоставляет REST API для:
- Добавления аудио-файлов из файловой системы
- Получения метаданных аудио-файлов
- Получения списка всех аудио-файлов
"""
from flask import Blueprint, request, jsonify
from src.audio.metadata import (
    extract_metadata,
    get_filename,
    validate_file_exists,
    validate_audio_format
)
from src.audio.streaming import stream_audio_file
from src.models import get_db, AudioFile, AudioFileStatus
from src.models.audio_file import AudioFileStatus

# Создаём Blueprint для audio API
audio_bp = Blueprint('audio', __name__, url_prefix='/api/audio')


@audio_bp.route('/add', methods=['POST'])
def add_audio_file():
    """
    Добавить аудио-файл в систему.
    
    POST /api/audio/add
    Body: {"file_path": "/path/to/audio.wav"}
    
    Returns:
        JSON с метаданными созданного AudioFile (201)
        или ошибка (400, 404)
    """
    try:
        # Валидация входных данных
        data = request.get_json() or {}
        
        file_path = data.get('file_path')
        if not file_path:
            return jsonify({'error': 'file_path is required'}), 400
        
        # Валидация файла
        try:
            validate_file_exists(file_path)
            validate_audio_format(file_path)
        except FileNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Извлечение метаданных
        try:
            metadata = extract_metadata(file_path)
        except Exception as e:
            return jsonify({'error': f'Error reading audio file: {str(e)}'}), 500
        
        # Сохранение в БД
        db = get_db()
        session = db.get_session()
        
        try:
            audio_file = AudioFile(
                file_path=file_path,
                filename=get_filename(file_path),
                duration=metadata['duration'],
                sample_rate=metadata['sample_rate'],
                channels=metadata['channels'],
                file_size=metadata['file_size'],
                status=AudioFileStatus.LOADED
            )
            
            session.add(audio_file)
            session.commit()
            
            return jsonify(audio_file.to_dict()), 201
        
        except Exception as e:
            session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            session.close()
    
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@audio_bp.route('/<audio_file_id>', methods=['GET'])
def get_audio_file(audio_file_id: str):
    """
    Получить метаданные аудио-файла по ID.
    
    GET /api/audio/{id}
    
    Args:
        audio_file_id: UUID аудио-файла
    
    Returns:
        JSON с метаданными AudioFile (200)
        или ошибка (404)
    """
    try:
        import uuid
        # Валидация UUID
        try:
            audio_file_uuid = uuid.UUID(audio_file_id)
        except ValueError:
            return jsonify({'error': 'Invalid audio file ID format'}), 400
        
        # Получение из БД
        db = get_db()
        session = db.get_session()
        
        try:
            audio_file = AudioFile.get_by_id(session, audio_file_uuid)
            
            if not audio_file:
                return jsonify({'error': 'Audio file not found'}), 404
            
            return jsonify(audio_file.to_dict()), 200
        
        finally:
            session.close()
    
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@audio_bp.route('', methods=['GET'])
def list_audio_files():
    """
    Получить список всех аудио-файлов.
    
    GET /api/audio
    
    Query parameters:
        limit: максимальное количество записей (опционально)
        offset: смещение для пагинации (опционально)
    
    Returns:
        JSON массив с метаданными всех AudioFile (200)
    """
    try:
        # Получение параметров пагинации
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)
        
        # Получение из БД
        db = get_db()
        session = db.get_session()
        
        try:
            audio_files = AudioFile.get_all(session, limit=limit, offset=offset)
            
            result = [audio_file.to_dict() for audio_file in audio_files]
            
            return jsonify(result), 200
        
        finally:
            session.close()
    
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@audio_bp.route('/<audio_file_id>/stream', methods=['GET'])
def stream_audio(audio_file_id: str):
    """
    Потоковая загрузка аудио-файла с поддержкой Range requests.
    
    GET /api/audio/{id}/stream
    Headers: Range: bytes=start-end (опционально)
    
    Args:
        audio_file_id: UUID аудио-файла
    
    Returns:
        Потоковые данные аудио-файла (200 или 206)
        или ошибка (404)
    """
    try:
        import uuid
        # Валидация UUID
        try:
            audio_file_uuid = uuid.UUID(audio_file_id)
        except ValueError:
            return jsonify({'error': 'Invalid audio file ID format'}), 400
        
        # Получение из БД
        db = get_db()
        session = db.get_session()
        
        try:
            audio_file = AudioFile.get_by_id(session, audio_file_uuid)
            
            if not audio_file:
                return jsonify({'error': 'Audio file not found'}), 404
            
            # Потоковая загрузка файла
            return stream_audio_file(audio_file.file_path, audio_file_id)
        
        finally:
            session.close()
    
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

