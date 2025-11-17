"""
Модуль для генерации спектрограмм аудио-файлов.

Поддерживаемый функционал:
- Генерация спектрограммы выбранного временного интервала
- Настраиваемые параметры изображения (width, height, color_map)
- STFT с параметрами n_fft=2048, hop_length=512
- Кэширование изображений на диске с учётом параметров
"""
from __future__ import annotations

import hashlib
import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')  # Неинтерактивный backend для генерации изображений
import matplotlib.pyplot as plt
import numpy as np

# Константы
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 512
DEFAULT_COLOR_MAP = 'viridis'
DEFAULT_CACHE_DIR = Path('cache/spectrograms')

# STFT параметры
N_FFT = 2048
HOP_LENGTH = 512


@dataclass
class SpectrogramParams:
    """Параметры генерации спектрограммы."""

    start_time: float = 0.0
    end_time: Optional[float] = None
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    color_map: str = DEFAULT_COLOR_MAP


def get_cache_dir() -> Path:
    """Возвращает директорию для кэширования спектрограмм."""
    cache_dir_env = os.environ.get('SPECTROGRAM_CACHE_DIR')
    if cache_dir_env:
        return Path(cache_dir_env)
    return DEFAULT_CACHE_DIR


def ensure_cache_dir() -> Path:
    """Убеждаемся, что кэш директория существует."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def build_cache_key(file_path: str, params: SpectrogramParams) -> str:
    """Строит уникальный ключ для кэширования спектрограммы."""
    parts = [
        file_path,
        f"{params.start_time:.3f}",
        f"{params.end_time:.3f}" if params.end_time is not None else 'None',
        str(params.width),
        str(params.height),
        params.color_map,
    ]
    joined = '|'.join(parts)
    return hashlib.md5(joined.encode('utf-8')).hexdigest()


def get_cache_path(file_path: str, params: SpectrogramParams) -> Path:
    """Возвращает путь к кэш файлу."""
    cache_dir = ensure_cache_dir()
    cache_key = build_cache_key(file_path, params)
    return cache_dir / f'{cache_key}.png'


def validate_time_range(params: SpectrogramParams, audio_duration: float) -> None:
    """Проверяет корректность временного интервала."""
    start = max(0.0, params.start_time)
    end = params.end_time if params.end_time is not None else audio_duration

    if start >= end:
        raise ValueError('start_time must be less than end_time')
    if start >= audio_duration:
        raise ValueError('start_time is outside audio duration')
    if end > audio_duration:
        end = audio_duration
    params.start_time = start
    params.end_time = end


def load_audio_segment(file_path: str, params: SpectrogramParams) -> tuple[np.ndarray, int]:
    """Загружает указанную часть аудио файла."""
    # Сначала получаем длительность
    total_duration = librosa.get_duration(path=file_path)
    validate_time_range(params, total_duration)

    offset = params.start_time
    duration = params.end_time - params.start_time if params.end_time else None

    audio_data, sample_rate = librosa.load(
        file_path,
        sr=None,
        mono=True,
        offset=offset,
        duration=duration
    )
    return audio_data, sample_rate


def generate_spectrogram_image(file_path: str, params: SpectrogramParams) -> bytes:
    """Генерирует PNG изображение спектрограммы."""
    audio_data, sample_rate = load_audio_segment(file_path, params)

    # Вычисляем STFT
    stft_result = librosa.stft(audio_data, n_fft=N_FFT, hop_length=HOP_LENGTH)
    spectrogram = np.abs(stft_result)
    spectrogram_db = librosa.amplitude_to_db(spectrogram, ref=np.max)

    # Создаём фигуру
    fig = plt.figure(figsize=(params.width / 100, params.height / 100), dpi=100)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Колор мап
    try:
        cmap = plt.get_cmap(params.color_map)
    except ValueError as exc:
        raise ValueError(f'Invalid color_map: {params.color_map}') from exc

    # Отображаем спектрограмму
    librosa.display.specshow(
        spectrogram_db,
        sr=sample_rate,
        hop_length=HOP_LENGTH,
        x_axis='time',
        y_axis='hz',
        cmap=cmap,
        ax=ax
    )

    ax.axis('off')

    # Сохраняем в PNG
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
    buffer.seek(0)
    png_data = buffer.read()
    buffer.close()

    plt.close(fig)
    return png_data


def get_or_generate_spectrogram(file_path: str, params: SpectrogramParams) -> bytes:
    """Возвращает спектрограмму из кэша или генерирует её."""
    cache_path = get_cache_path(file_path, params)

    if cache_path.exists():
        return cache_path.read_bytes()

    png_data = generate_spectrogram_image(file_path, params)

    cache_path.write_bytes(png_data)
    return png_data
