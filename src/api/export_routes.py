"""
REST API для экспорта аннотаций.
"""
import json
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, Response, request
from src.models import get_db, AudioFile, Annotation

export_bp = Blueprint('export', __name__, url_prefix='/api/audio')


@export_bp.route('/<audio_file_id>/export', methods=['GET'])
def export_annotations(audio_file_id):
    """
    Экспорт аннотаций для аудио-файла в JSON формате.
    
    GET /api/audio/{id}/export?format=json
    
    Query parameters:
        format: Формат экспорта (json) - опционально, по умолчанию json
    
    Returns:
        200: JSON файл с аннотациями
        400: Неверный формат ID
        404: AudioFile не найден
        500: Ошибка сервера
    """
    try:
        # Валидация UUID
        try:
            audio_file_uuid = uuid.UUID(audio_file_id)
        except ValueError:
            return jsonify({'error': 'Неверный формат audio_file_id'}), 400
        
        # Получение формата экспорта
        format_type = request.args.get('format', 'json').lower()
        
        if format_type != 'json':
            return jsonify({'error': f'Неподдерживаемый формат: {format_type}'}), 400
        
        db = get_db()
        session = db.get_session()
        
        try:
            # Получение AudioFile
            audio_file = AudioFile.get_by_id(session, audio_file_uuid)
            if not audio_file:
                return jsonify({'error': 'AudioFile не найден'}), 404
            
            # Получение всех аннотаций для файла
            annotations = Annotation.get_by_audio_file(session, audio_file_uuid)
            
            # Формирование JSON структуры
            export_data = {
                'audio_file': {
                    'id': str(audio_file.id),
                    'filename': audio_file.filename,
                    'file_path': audio_file.file_path,
                    'duration': audio_file.duration,
                    'sample_rate': audio_file.sample_rate,
                    'channels': audio_file.channels,
                    'file_size': audio_file.file_size,
                    'status': audio_file.status.value if hasattr(audio_file.status, 'value') else str(audio_file.status),
                    'created_at': audio_file.created_at.isoformat() if audio_file.created_at else None
                },
                'annotations': [annotation.to_dict() for annotation in annotations],
                'export_date': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0'
            }
            
            # Формирование имени файла
            filename = f"{audio_file.filename}_annotations.json"
            
            # Создание JSON ответа
            import json
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            # Возвращаем JSON с правильными заголовками
            response = Response(
                json_str,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
            
            return response
            
        except Exception as e:
            return jsonify({'error': f'Ошибка экспорта аннотаций: {str(e)}'}), 500
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'Неожиданная ошибка: {str(e)}'}), 500

