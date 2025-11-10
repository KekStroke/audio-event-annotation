"""
REST API для управления аннотациями.
"""
import uuid
from flask import Blueprint, request, jsonify
from src.models import get_db, Annotation, AudioFile, EventType

annotation_bp = Blueprint('annotations', __name__, url_prefix='/api/annotations')


def validate_annotation_data(data):
    """
    Валидация данных аннотации.
    
    Args:
        data: Словарь с данными аннотации
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Проверка обязательных полей
    required_fields = ['audio_file_id', 'start_time', 'end_time', 'event_label']
    for field in required_fields:
        if field not in data:
            return False, f'Поле "{field}" обязательно'
    
    # Валидация start_time и end_time
    try:
        start_time = float(data['start_time'])
        end_time = float(data['end_time'])
    except (ValueError, TypeError):
        return False, 'start_time и end_time должны быть числами'
    
    if start_time < 0:
        return False, 'start_time должен быть неотрицательным'
    
    if end_time <= 0:
        return False, 'end_time должен быть положительным'
    
    if start_time >= end_time:
        return False, 'start_time должен быть меньше end_time'
    
    # Валидация event_label
    event_label = data.get('event_label', '').strip()
    if not event_label:
        return False, 'event_label не может быть пустым'
    
    if len(event_label) > 100:
        return False, 'event_label не может быть длиннее 100 символов'
    
    return True, None


@annotation_bp.route('', methods=['POST'])
def create_annotation():
    """
    Создание новой аннотации.
    
    POST /api/annotations
    
    Request body:
        {
            "audio_file_id": "uuid",
            "event_type_id": "uuid" (опционально),
            "start_time": 1.5,
            "end_time": 3.2,
            "event_label": "Speaker 1",
            "confidence": 0.95 (опционально),
            "notes": "Some notes" (опционально)
        }
    
    Returns:
        201: Аннотация создана
        400: Ошибка валидации
        404: AudioFile не найден
        500: Ошибка сервера
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body должен содержать JSON'}), 400
        
        # Валидация данных
        is_valid, error_message = validate_annotation_data(data)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Проверка существования AudioFile
        try:
            audio_file_id = uuid.UUID(data['audio_file_id'])
        except (ValueError, KeyError):
            return jsonify({'error': 'Неверный формат audio_file_id'}), 400
        
        db = get_db()
        session = db.get_session()
        
        try:
            audio_file = AudioFile.get_by_id(session, audio_file_id)
            if not audio_file:
                return jsonify({'error': 'AudioFile не найден'}), 404
            
            # Проверка event_type_id если указан
            event_type_id = None
            if 'event_type_id' in data and data['event_type_id']:
                try:
                    event_type_id = uuid.UUID(data['event_type_id'])
                    event_type = EventType.get_by_id(session, event_type_id)
                    if not event_type:
                        return jsonify({'error': 'EventType не найден'}), 404
                except (ValueError, TypeError):
                    return jsonify({'error': 'Неверный формат event_type_id'}), 400
            
            # Создание аннотации
            annotation = Annotation(
                audio_file_id=audio_file_id,
                start_time=float(data['start_time']),
                end_time=float(data['end_time']),
                event_label=data['event_label'].strip(),
                confidence=data.get('confidence'),
                notes=data.get('notes')
            )
            
            session.add(annotation)
            session.commit()
            
            return jsonify(annotation.to_dict()), 201
            
        except Exception as e:
            session.rollback()
            return jsonify({'error': f'Ошибка создания аннотации: {str(e)}'}), 500
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'Неожиданная ошибка: {str(e)}'}), 500


@annotation_bp.route('', methods=['GET'])
def list_annotations():
    """
    Получение списка аннотаций.
    
    GET /api/annotations?audio_file_id={id}
    
    Query parameters:
        audio_file_id: UUID аудио-файла (обязательно)
    
    Returns:
        200: Список аннотаций
        400: Ошибка валидации
        500: Ошибка сервера
    """
    try:
        audio_file_id_str = request.args.get('audio_file_id')
        if not audio_file_id_str:
            return jsonify({'error': 'Параметр audio_file_id обязателен'}), 400
        
        try:
            audio_file_id = uuid.UUID(audio_file_id_str)
        except ValueError:
            return jsonify({'error': 'Неверный формат audio_file_id'}), 400
        
        db = get_db()
        session = db.get_session()
        
        try:
            annotations = Annotation.get_by_audio_file(session, audio_file_id)
            annotations_data = [ann.to_dict() for ann in annotations]
            
            return jsonify(annotations_data), 200
            
        except Exception as e:
            return jsonify({'error': f'Ошибка получения аннотаций: {str(e)}'}), 500
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'Неожиданная ошибка: {str(e)}'}), 500


@annotation_bp.route('/<annotation_id>', methods=['GET'])
def get_annotation(annotation_id):
    """
    Получение одной аннотации по ID.
    
    GET /api/annotations/{id}
    
    Returns:
        200: Аннотация найдена
        400: Неверный формат ID
        404: Аннотация не найдена
        500: Ошибка сервера
    """
    try:
        try:
            annotation_uuid = uuid.UUID(annotation_id)
        except ValueError:
            return jsonify({'error': 'Неверный формат annotation_id'}), 400
        
        db = get_db()
        session = db.get_session()
        
        try:
            annotation = Annotation.get_by_id(session, annotation_uuid)
            if not annotation:
                return jsonify({'error': 'Annotation не найдена'}), 404
            
            return jsonify(annotation.to_dict()), 200
            
        except Exception as e:
            return jsonify({'error': f'Ошибка получения аннотации: {str(e)}'}), 500
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'Неожиданная ошибка: {str(e)}'}), 500


@annotation_bp.route('/<annotation_id>', methods=['PUT'])
def update_annotation(annotation_id):
    """
    Обновление аннотации.
    
    PUT /api/annotations/{id}
    
    Request body:
        {
            "start_time": 2.0 (опционально),
            "end_time": 4.5 (опционально),
            "event_label": "Updated label" (опционально),
            "confidence": 0.9 (опционально),
            "notes": "Updated notes" (опционально)
        }
    
    Returns:
        200: Аннотация обновлена
        400: Ошибка валидации
        404: Аннотация не найдена
        500: Ошибка сервера
    """
    try:
        try:
            annotation_uuid = uuid.UUID(annotation_id)
        except ValueError:
            return jsonify({'error': 'Неверный формат annotation_id'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body должен содержать JSON'}), 400
        
        db = get_db()
        session = db.get_session()
        
        try:
            annotation = Annotation.get_by_id(session, annotation_uuid)
            if not annotation:
                return jsonify({'error': 'Annotation не найдена'}), 404
            
            # Валидация обновляемых полей
            update_data = {}
            
            if 'start_time' in data:
                try:
                    start_time = float(data['start_time'])
                    if start_time < 0:
                        return jsonify({'error': 'start_time должен быть неотрицательным'}), 400
                    update_data['start_time'] = start_time
                except (ValueError, TypeError):
                    return jsonify({'error': 'start_time должен быть числом'}), 400
            
            if 'end_time' in data:
                try:
                    end_time = float(data['end_time'])
                    if end_time <= 0:
                        return jsonify({'error': 'end_time должен быть положительным'}), 400
                    update_data['end_time'] = end_time
                except (ValueError, TypeError):
                    return jsonify({'error': 'end_time должен быть числом'}), 400
            
            if 'event_label' in data:
                event_label = data['event_label'].strip()
                if not event_label:
                    return jsonify({'error': 'event_label не может быть пустым'}), 400
                if len(event_label) > 100:
                    return jsonify({'error': 'event_label не может быть длиннее 100 символов'}), 400
                update_data['event_label'] = event_label
            
            if 'confidence' in data:
                try:
                    confidence = float(data['confidence']) if data['confidence'] is not None else None
                    if confidence is not None and (confidence < 0 or confidence > 1):
                        return jsonify({'error': 'confidence должен быть между 0 и 1'}), 400
                    update_data['confidence'] = confidence
                except (ValueError, TypeError):
                    return jsonify({'error': 'confidence должен быть числом'}), 400
            
            if 'notes' in data:
                update_data['notes'] = data['notes']
            
            # Проверка start_time < end_time
            final_start_time = update_data.get('start_time', annotation.start_time)
            final_end_time = update_data.get('end_time', annotation.end_time)
            
            if final_start_time >= final_end_time:
                return jsonify({'error': 'start_time должен быть меньше end_time'}), 400
            
            # Обновление аннотации
            annotation.update(session, **update_data)
            
            return jsonify(annotation.to_dict()), 200
            
        except Exception as e:
            session.rollback()
            return jsonify({'error': f'Ошибка обновления аннотации: {str(e)}'}), 500
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'Неожиданная ошибка: {str(e)}'}), 500


@annotation_bp.route('/<annotation_id>', methods=['DELETE'])
def delete_annotation(annotation_id):
    """
    Удаление аннотации.
    
    DELETE /api/annotations/{id}
    
    Returns:
        200: Аннотация удалена
        400: Неверный формат ID
        404: Аннотация не найдена
        500: Ошибка сервера
    """
    try:
        try:
            annotation_uuid = uuid.UUID(annotation_id)
        except ValueError:
            return jsonify({'error': 'Неверный формат annotation_id'}), 400
        
        db = get_db()
        session = db.get_session()
        
        try:
            annotation = Annotation.get_by_id(session, annotation_uuid)
            if not annotation:
                return jsonify({'error': 'Annotation не найдена'}), 404
            
            annotation.delete(session)
            
            return jsonify({'message': 'Annotation удалена'}), 200
            
        except Exception as e:
            session.rollback()
            return jsonify({'error': f'Ошибка удаления аннотации: {str(e)}'}), 500
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'error': f'Неожиданная ошибка: {str(e)}'}), 500

