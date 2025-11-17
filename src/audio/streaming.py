"""
Модуль для потоковой загрузки больших аудио-файлов.

Обеспечивает chunked-загрузку файлов размером до нескольких ГБ
без загрузки всего файла в память.
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from flask import Response, request, send_file
import mimetypes


# Размер чанка: 1MB
CHUNK_SIZE = 1024 * 1024  # 1MB


def parse_range_header(range_header: str, file_size: int) -> Optional[Tuple[int, int]]:
    """
    Парсит HTTP Range заголовок.

    Args:
        range_header: Значение заголовка Range (например, "bytes=0-1048575")
        file_size: Размер файла в байтах

    Returns:
        Tuple (start, end) или None если заголовок невалиден
    """
    if not range_header or not range_header.startswith("bytes="):
        return None

    range_spec = range_header[6:]  # Убираем "bytes="

    try:
        # Формат: "start-end" или "-suffix" или "start-"
        if range_spec.startswith("-"):
            # Суффикс: последние N байт
            suffix = int(range_spec[1:])
            start = max(0, file_size - suffix)
            end = file_size - 1
        elif "-" in range_spec:
            parts = range_spec.split("-", 1)
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
        else:
            return None

        # Валидация
        if start < 0 or end >= file_size or start > end:
            return None

        return (start, end)

    except (ValueError, IndexError):
        return None


def stream_audio_file(file_path: str, audio_file_id: str) -> Response:
    """
    Потоковая загрузка аудио-файла с поддержкой Range requests.

    Args:
        file_path: Путь к аудио-файлу
        audio_file_id: UUID аудио-файла (для логирования)

    Returns:
        Flask Response с потоковыми данными
    """
    # Проверка существования файла
    if not os.path.exists(file_path):
        from flask import jsonify

        return jsonify({"error": "Audio file not found on disk"}), 404

    if not os.path.isfile(file_path):
        from flask import jsonify

        return jsonify({"error": "Path is not a file"}), 400

    file_size = os.path.getsize(file_path)

    # Определяем MIME тип
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "audio/wav"  # По умолчанию

    # Проверяем Range заголовок
    range_header = request.headers.get("Range")

    if range_header:
        # Парсим Range
        range_result = parse_range_header(range_header, file_size)

        if range_result:
            start, end = range_result
            content_length = end - start + 1

            # Создаём generator для чтения чанками
            def generate():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    remaining = content_length

                    while remaining > 0:
                        chunk_size = min(CHUNK_SIZE, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                        remaining -= len(chunk)

            # Возвращаем 206 Partial Content
            response = Response(
                generate(),
                status=206,
                headers={
                    "Content-Type": mime_type,
                    "Content-Length": str(content_length),
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                },
            )
            return response

    # Полная загрузка файла (без Range)
    # Используем send_file с conditional=True для поддержки Range
    response = send_file(
        file_path,
        mimetype=mime_type,
        as_attachment=False,
        conditional=True,  # Включает поддержку Range requests
        etag=False,  # Не используем ETag на этом этапе
    )

    # Убеждаемся что заголовок Accept-Ranges установлен
    response.headers["Accept-Ranges"] = "bytes"

    return response
