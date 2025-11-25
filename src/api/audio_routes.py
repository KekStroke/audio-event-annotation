"""
API endpoints для работы с аудио-файлами.

Предоставляет REST API для:
- Добавления аудио-файлов из файловой системы
- Получения метаданных аудио-файлов
- Получения списка всех аудио-файлов
- Потоковой загрузки аудио-файлов
- Генерации waveform визуализации
- Генерации спектрограммы аудио
"""

import os
from flask import Blueprint, request, jsonify
from src.audio.metadata import (
    extract_metadata,
    get_filename,
    validate_file_exists,
    validate_audio_format,
)
from src.audio.streaming import stream_audio_file
from src.audio.waveform import generate_waveform
from src.audio.spectrogram import SpectrogramParams, generate_spectrogram
from src.models import get_db, AudioFile, AudioFileStatus
from src.models.audio_file import AudioFileStatus

# Создаём Blueprint для audio API
audio_bp = Blueprint("audio", __name__, url_prefix="/api/audio")


@audio_bp.route("/add", methods=["POST"])
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

        file_path = data.get("file_path")
        if not file_path:
            return jsonify({"error": "file_path is required"}), 400

        # Валидация файла
        try:
            validate_file_exists(file_path)
            validate_audio_format(file_path)
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Извлечение метаданных
        try:
            metadata = extract_metadata(file_path)
        except Exception as e:
            return jsonify({"error": f"Error reading audio file: {str(e)}"}), 500

        # Сохранение в БД
        db = get_db()
        session = db.get_session()

        try:
            audio_file = AudioFile(
                file_path=file_path,
                filename=get_filename(file_path),
                duration=metadata["duration"],
                sample_rate=metadata["sample_rate"],
                channels=metadata["channels"],
                file_size=metadata["file_size"],
                status=AudioFileStatus.LOADED,
            )

            session.add(audio_file)
            session.commit()

            return jsonify(audio_file.to_dict()), 201

        except Exception as e:
            session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@audio_bp.route("/<audio_file_id>", methods=["GET"])
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
            return jsonify({"error": "Invalid audio file ID format"}), 400

        # Получение из БД
        db = get_db()
        session = db.get_session()

        try:
            audio_file = AudioFile.get_by_id(session, audio_file_uuid)

            if not audio_file:
                return jsonify({"error": "Audio file not found"}), 404

            return jsonify(audio_file.to_dict()), 200

        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@audio_bp.route("", methods=["GET"])
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
        limit = request.args.get("limit", type=int)
        offset = request.args.get("offset", type=int)

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
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@audio_bp.route("/<audio_file_id>/stream", methods=["GET"])
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
            return jsonify({"error": "Invalid audio file ID format"}), 400

        # Получение из БД
        db = get_db()
        session = db.get_session()

        try:
            audio_file = AudioFile.get_by_id(session, audio_file_uuid)

            if not audio_file:
                return jsonify({"error": "Audio file not found"}), 404

            # Потоковая загрузка файла
            return stream_audio_file(audio_file.file_path, audio_file_id)

        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@audio_bp.route("/<audio_file_id>/waveform", methods=["GET"])
def get_waveform(audio_file_id: str):
    """
    Генерация waveform изображения для аудио-файла.

    GET /api/audio/{id}/waveform?width=1200&height=300&color=FF5733

    Query parameters:
        width: Ширина изображения в пикселях (по умолчанию 1200)
        height: Высота изображения в пикселях (по умолчанию 300)
        color: Цвет waveform в hex формате без # (по умолчанию 1f77b4)

    Args:
        audio_file_id: UUID аудио-файла

    Returns:
        PNG изображение waveform (200)
        или ошибка (404, 500)
    """
    try:
        import uuid

        # Валидация UUID
        try:
            audio_file_uuid = uuid.UUID(audio_file_id)
        except ValueError:
            return jsonify({"error": "Invalid audio file ID format"}), 400

        # Получение параметров запроса
        width = request.args.get("width", type=int, default=1200)
        height = request.args.get("height", type=int, default=300)
        color = request.args.get("color", type=str, default="1f77b4")

        # Валидация параметров
        if width <= 0 or width > 5000:
            return jsonify({"error": "Width must be between 1 and 5000"}), 400
        if height <= 0 or height > 2000:
            return jsonify({"error": "Height must be between 1 and 2000"}), 400

        # Получение из БД
        db = get_db()
        session = db.get_session()

        try:
            audio_file = AudioFile.get_by_id(session, audio_file_uuid)

            if not audio_file:
                return jsonify({"error": "Audio file not found"}), 404

            # Проверка существования файла
            if not os.path.exists(audio_file.file_path):
                return jsonify({"error": "Audio file not found on disk"}), 404

            # Генерация waveform
            try:
                png_data = generate_waveform(
                    audio_file.file_path, width=width, height=height, color=color
                )
            except Exception as e:
                return jsonify({"error": f"Error generating waveform: {str(e)}"}), 500

            # Возвращаем PNG изображение
            from flask import Response

            return Response(
                png_data, mimetype="image/png", headers={"Content-Type": "image/png"}
            )

        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@audio_bp.route("/<audio_file_id>/spectrogram", methods=["GET"])
def get_spectrogram(audio_file_id: str):
    """
    Генерация спектрограммы выбранного интервала аудио-файла.

    GET /api/audio/{id}/spectrogram?start_time=0&end_time=5&width=1024&height=512&color_map=viridis

    Query parameters:
        start_time: Начало интервала в секундах (по умолчанию 0)
        end_time: Конец интервала в секундах (опционально)
        width: Ширина изображения в пикселях (по умолчанию 1024)
        height: Высота изображения в пикселях (по умолчанию 512)
        color_map: Название цветовой карты matplotlib (по умолчанию viridis)

    Returns:
        PNG изображение спектрограммы (200)
        или ошибка (400, 404, 500)
    """
    try:
        import uuid

        try:
            audio_file_uuid = uuid.UUID(audio_file_id)
        except ValueError:
            return jsonify({"error": "Invalid audio file ID format"}), 400

        # Параметры запроса
        start_time = request.args.get("start_time", default=0.0, type=float)
        end_time = request.args.get("end_time", type=float)
        width = request.args.get("width", type=int, default=1024)
        height = request.args.get("height", type=int, default=512)
        color_map = request.args.get("color_map", type=str, default="viridis")

        if start_time < 0:
            return jsonify({"error": "start_time must be non-negative"}), 400
        if end_time is not None and end_time <= 0:
            return jsonify({"error": "end_time must be positive"}), 400
        if width <= 0 or width > 5000:
            return jsonify({"error": "Width must be between 1 and 5000"}), 400
        if height <= 0 or height > 2000:
            return jsonify({"error": "Height must be between 1 and 2000"}), 400

        params = SpectrogramParams(
            start_time=start_time,
            end_time=end_time,
            width=width,
            height=height,
            color_map=color_map,
        )

        db = get_db()
        session = db.get_session()

        try:
            audio_file = AudioFile.get_by_id(session, audio_file_uuid)
            if not audio_file:
                return jsonify({"error": "Audio file not found"}), 404

            if not os.path.exists(audio_file.file_path):
                return jsonify({"error": "Audio file not found on disk"}), 404

            try:
                png_data = generate_spectrogram(audio_file.file_path, params)
            except ValueError as value_error:
                return jsonify({"error": str(value_error)}), 400
            except Exception as e:
                return (
                    jsonify({"error": f"Error generating spectrogram: {str(e)}"}),
                    500,
                )

            from flask import Response

            return Response(
                png_data, mimetype="image/png", headers={"Content-Type": "image/png"}
            )

        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@audio_bp.route("/<audio_file_id>", methods=["DELETE"])
def delete_audio_file(audio_file_id: str):
    """
    Удалить аудио-файл из системы.

    DELETE /api/audio/{id}

    Args:
        audio_file_id: UUID аудио-файла

    Returns:
        JSON с подтверждением удаления (200)
        или ошибка (404, 500)
    """
    try:
        import uuid

        # Валидация UUID
        try:
            audio_file_uuid = uuid.UUID(audio_file_id)
        except ValueError:
            return jsonify({"error": "Invalid audio file ID format"}), 400

        # Удаление из БД
        db = get_db()
        session = db.get_session()

        try:
            audio_file = AudioFile.get_by_id(session, audio_file_uuid)

            if not audio_file:
                return jsonify({"error": "Audio file not found"}), 404

            # Удаляем запись из БД
            # Примечание: сам файл с диска мы не удаляем, так как это может быть
            # внешний файл, на который мы просто ссылаемся.
            # Если нужно удалять и файл, это должно быть явно указано в требованиях.
            # Пока удаляем только метаданные из системы.

            session.delete(audio_file)
            session.commit()

            return jsonify(
                {"message": "Audio file deleted successfully", "id": audio_file_id}
            ), 200

        except Exception as e:
            session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@audio_bp.route("/import", methods=["POST"])
def import_audio_folder():
    """
    Импортировать все аудио-файлы из директории.

    POST /api/audio/import
    Body: {"path": "/path/to/folder"}

    Returns:
        JSON с результатами импорта (200)
        или ошибка (400, 404)
    """
    try:
        data = request.get_json() or {}
        folder_path = data.get("path")

        if not folder_path:
            return jsonify({"error": "path is required"}), 400

        if not os.path.exists(folder_path):
            return jsonify({"error": "Directory not found"}), 404

        if not os.path.isdir(folder_path):
            return jsonify({"error": "Path is not a directory"}), 400

        # Поддерживаемые расширения
        supported_extensions = {".wav", ".mp3", ".flac", ".ogg", ".aiff"}

        imported_count = 0
        errors = []

        db = get_db()
        session = db.get_session()

        try:
            for filename in os.listdir(folder_path):
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in supported_extensions:
                    continue

                file_path = os.path.join(folder_path, filename)

                try:
                    # Проверяем, не добавлен ли уже файл (по пути)
                    existing = session.query(AudioFile).filter_by(file_path=file_path).first()
                    if existing:
                        continue

                    # Извлекаем метаданные
                    metadata = extract_metadata(file_path)

                    audio_file = AudioFile(
                        file_path=file_path,
                        filename=filename,
                        duration=metadata["duration"],
                        sample_rate=metadata["sample_rate"],
                        channels=metadata["channels"],
                        file_size=metadata["file_size"],
                        status=AudioFileStatus.LOADED,
                    )
                    session.add(audio_file)
                    imported_count += 1

                except Exception as e:
                    errors.append({"file": filename, "error": str(e)})

            session.commit()

            return jsonify(
                {
                    "imported_count": imported_count,
                    "errors": errors,
                    "message": f"Successfully imported {imported_count} files",
                }
            ), 200

        except Exception as e:
            session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
