"""
Модуль для извлечения метаданных из аудио-файлов.

Использует librosa и soundfile для чтения метаданных без загрузки всего файла в память.
"""
import os
from pathlib import Path
from typing import Dict, Optional
import soundfile as sf
import librosa


# Поддерживаемые форматы
SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac'}


def is_audio_file(file_path: str) -> bool:
    """
    Проверяет является ли файл поддерживаемым аудио-форматом.
    
    Args:
        file_path: Путь к файлу
    
    Returns:
        bool: True если файл поддерживается
    """
    path = Path(file_path)
    return path.suffix.lower() in SUPPORTED_FORMATS


def validate_file_exists(file_path: str) -> None:
    """
    Проверяет существование файла.
    
    Args:
        file_path: Путь к файлу
    
    Raises:
        FileNotFoundError: Если файл не существует
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")


def validate_audio_format(file_path: str) -> None:
    """
    Проверяет формат аудио-файла.
    
    Args:
        file_path: Путь к файлу
    
    Raises:
        ValueError: Если формат не поддерживается
    """
    if not is_audio_file(file_path):
        raise ValueError(
            f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )


def extract_metadata(file_path: str) -> Dict[str, any]:
    """
    Извлекает метаданные из аудио-файла.
    
    Не загружает весь файл в память, только читает заголовок.
    
    Args:
        file_path: Путь к аудио-файлу
    
    Returns:
        dict: Словарь с метаданными:
            - duration: длительность в секундах (float)
            - sample_rate: частота дискретизации (int)
            - channels: количество каналов (int)
            - file_size: размер файла в байтах (int)
    
    Raises:
        FileNotFoundError: Если файл не существует
        ValueError: Если формат не поддерживается
        Exception: При ошибках чтения файла
    """
    # Валидация
    validate_file_exists(file_path)
    validate_audio_format(file_path)
    
    # Получаем размер файла
    file_size = os.path.getsize(file_path)
    
    try:
        # Используем soundfile для чтения метаданных (быстрее чем librosa)
        # soundfile.read() с frames=0 читает только заголовок
        info = sf.info(file_path)
        
        # Для получения длительности нужно прочитать файл, но можно использовать librosa
        # librosa.get_duration() эффективно читает только метаданные
        duration = librosa.get_duration(path=file_path)
        
        return {
            'duration': float(duration),
            'sample_rate': int(info.samplerate),
            'channels': int(info.channels),
            'file_size': int(file_size)
        }
    
    except Exception as e:
        raise Exception(f"Error reading audio file metadata: {str(e)}")


def get_filename(file_path: str) -> str:
    """
    Извлекает имя файла из пути.
    
    Args:
        file_path: Полный путь к файлу
    
    Returns:
        str: Имя файла
    """
    return Path(file_path).name

