"""
Модуль для генерации waveform визуализации аудио-файлов.

Генерирует PNG изображения waveform с поддержкой:
- Настраиваемых размеров (width, height)
- Настраиваемого цвета
- Downsampling для больших файлов
- Кэширования на диске
"""
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import soundfile as sf
import matplotlib
matplotlib.use('Agg')  # Неинтерактивный backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io


# Константы
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 300
DEFAULT_COLOR = '#1f77b4'  # Синий цвет matplotlib
DEFAULT_CACHE_DIR = Path('cache/waveforms')
MAX_SAMPLES_PER_PIXEL = 1000  # Для downsampling


def get_cache_dir() -> Path:
    """Получает путь к кэш директории из переменной окружения или использует дефолтный."""
    cache_dir_env = os.environ.get('WAVEFORM_CACHE_DIR')
    if cache_dir_env:
        return Path(cache_dir_env)
    return DEFAULT_CACHE_DIR


def ensure_cache_dir():
    """Создаёт кэш директорию если её нет."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cache_path(audio_file_path: str, width: int, height: int, color: str) -> Path:
    """
    Генерирует путь к кэш файлу waveform.
    
    Args:
        audio_file_path: Путь к аудио-файлу
        width: Ширина изображения
        height: Высота изображения
        color: Цвет waveform
    
    Returns:
        Path к кэш файлу
    """
    cache_dir = ensure_cache_dir()
    
    # Создаём уникальный ключ на основе параметров
    cache_key = f"{audio_file_path}_{width}_{height}_{color}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    return cache_dir / f"{cache_hash}.png"


def load_audio_samples(file_path: str, max_samples: Optional[int] = None) -> Tuple[np.ndarray, int]:
    """
    Загружает аудио-данные с downsampling если нужно.
    
    Args:
        file_path: Путь к аудио-файлу
        max_samples: Максимальное количество сэмплов для загрузки (для downsampling)
    
    Returns:
        Tuple (audio_data, sample_rate)
    """
    # Загружаем метаданные для определения размера
    info = sf.info(file_path)
    total_samples = info.frames
    
    # Если нужен downsampling
    if max_samples and total_samples > max_samples:
        # Вычисляем шаг для downsampling
        step = max(1, total_samples // max_samples)
        
        # Загружаем только нужные сэмплы
        with sf.SoundFile(file_path, 'r') as f:
            # Читаем каждый N-й сэмпл
            samples = []
            for i in range(0, total_samples, step):
                f.seek(i)
                sample = f.read(1)
                if len(sample) > 0:
                    samples.append(sample[0])
            
            audio_data = np.array(samples)
            sample_rate = info.samplerate // step  # Уменьшаем sample_rate пропорционально
    else:
        # Загружаем весь файл
        audio_data, sample_rate = sf.read(file_path)
    
    # Если стерео, конвертируем в моно (среднее значение каналов)
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    return audio_data, sample_rate


def generate_waveform_image(
    audio_file_path: str,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    color: str = DEFAULT_COLOR
) -> bytes:
    """
    Генерирует PNG изображение waveform.
    
    Args:
        audio_file_path: Путь к аудио-файлу
        width: Ширина изображения в пикселях
        height: Высота изображения в пикселях
        color: Цвет waveform (hex формат, например '#FF5733')
    
    Returns:
        PNG изображение в виде bytes
    """
    # Вычисляем максимальное количество сэмплов для downsampling
    max_samples = width * MAX_SAMPLES_PER_PIXEL
    
    # Загружаем аудио-данные
    audio_data, sample_rate = load_audio_samples(audio_file_path, max_samples)
    
    # Создаём фигуру matplotlib
    fig = Figure(figsize=(width / 100, height / 100), dpi=100)
    ax = fig.add_subplot(111)
    
    # Убираем отступы
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.axis('off')
    
    # Генерируем waveform
    # Если данных больше чем ширина, делаем downsampling для визуализации
    if len(audio_data) > width:
        # Разбиваем на сегменты по ширине
        segment_size = len(audio_data) // width
        waveform = []
        for i in range(width):
            start = i * segment_size
            end = min((i + 1) * segment_size, len(audio_data))
            segment = audio_data[start:end]
            # Берем максимум и минимум для каждого сегмента
            waveform.append([np.min(segment), np.max(segment)])
        waveform = np.array(waveform)
        
        # Создаём x координаты
        x = np.arange(width)
        
        # Рисуем waveform как заполненную область
        ax.fill_between(x, waveform[:, 0], waveform[:, 1], color=color, alpha=0.7)
        ax.plot(x, waveform[:, 0], color=color, linewidth=0.5)
        ax.plot(x, waveform[:, 1], color=color, linewidth=0.5)
    else:
        # Если данных меньше ширины, просто рисуем
        x = np.linspace(0, width, len(audio_data))
        ax.plot(x, audio_data, color=color, linewidth=0.5)
        ax.fill_between(x, audio_data, 0, color=color, alpha=0.7)
    
    # Устанавливаем пределы
    ax.set_xlim(0, width)
    ax.set_ylim(-1, 1)
    
    # Сохраняем в bytes
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
    buf.seek(0)
    png_data = buf.read()
    buf.close()
    
    # Закрываем фигуру для освобождения памяти
    plt.close(fig)
    
    return png_data


def get_or_generate_waveform(
    audio_file_path: str,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    color: str = DEFAULT_COLOR
) -> bytes:
    """
    Получает waveform из кэша или генерирует новый.
    
    Args:
        audio_file_path: Путь к аудио-файлу
        width: Ширина изображения
        height: Высота изображения
        color: Цвет waveform
    
    Returns:
        PNG изображение в виде bytes
    """
    # Нормализуем цвет (убираем # если есть)
    if color.startswith('#'):
        color = color[1:]
    color = f"#{color}"  # Добавляем обратно для консистентности
    
    # Проверяем кэш
    cache_path = get_cache_path(audio_file_path, width, height, color)
    
    if cache_path.exists():
        # Читаем из кэша
        with open(cache_path, 'rb') as f:
            return f.read()
    
    # Генерируем новый waveform
    png_data = generate_waveform_image(audio_file_path, width, height, color)
    
    # Сохраняем в кэш
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'wb') as f:
        f.write(png_data)
    
    return png_data

