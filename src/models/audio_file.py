"""
Модель AudioFile для хранения информации об аудио-файлах.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from .database import Base
from .types import GUID


class AudioFileStatus(enum.Enum):
    """Статусы обработки аудио-файла."""
    PENDING = "pending"
    LOADED = "loaded"
    ERROR = "error"


class AudioFile(Base):
    """
    Модель для хранения информации об аудио-файлах.
    
    Attributes:
        id: Уникальный идентификатор (UUID)
        file_path: Абсолютный путь к файлу в файловой системе
        filename: Имя файла
        duration: Длительность аудио в секундах
        sample_rate: Частота дискретизации (Hz)
        channels: Количество каналов
        file_size: Размер файла в байтах
        created_at: Дата и время создания записи
        status: Статус обработки файла
        annotations: Список аннотаций для этого файла
    """
    
    __tablename__ = 'audio_files'
    
    id = Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    
    file_path = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    duration = Column(Float, nullable=False)
    sample_rate = Column(Integer, nullable=False)
    channels = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=False)
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    status = Column(
        Enum(AudioFileStatus),
        default=AudioFileStatus.PENDING,
        nullable=False
    )
    
    # Связь с аннотациями (cascade delete)
    annotations = relationship(
        "Annotation",
        back_populates="audio_file",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        """Строковое представление модели."""
        return (
            f"<AudioFile(id={self.id}, "
            f"filename='{self.filename}', "
            f"duration={self.duration}s, "
            f"status={self.status.value})>"
        )
    
    def to_dict(self):
        """
        Преобразовать модель в словарь.
        
        Returns:
            dict: Словарь с данными модели
        """
        return {
            'id': str(self.id),
            'file_path': self.file_path,
            'filename': self.filename,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value
        }
    
    @classmethod
    def create(cls, session, **kwargs):
        """
        Создать новый AudioFile и сохранить в БД.
        
        Args:
            session: SQLAlchemy сессия
            **kwargs: Параметры модели
        
        Returns:
            AudioFile: Созданный экземпляр
        """
        audio_file = cls(**kwargs)
        session.add(audio_file)
        session.commit()
        return audio_file
    
    @classmethod
    def get_by_id(cls, session, audio_file_id):
        """
        Получить AudioFile по ID.
        
        Args:
            session: SQLAlchemy сессия
            audio_file_id: UUID файла
        
        Returns:
            AudioFile или None
        """
        return session.query(cls).filter_by(id=audio_file_id).first()
    
    @classmethod
    def get_all(cls, session, limit=None, offset=None):
        """
        Получить все AudioFile.
        
        Args:
            session: SQLAlchemy сессия
            limit: Максимальное количество записей
            offset: Смещение
        
        Returns:
            list: Список AudioFile
        """
        query = session.query(cls).order_by(cls.created_at.desc())
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update(self, session, **kwargs):
        """
        Обновить поля модели.
        
        Args:
            session: SQLAlchemy сессия
            **kwargs: Поля для обновления
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        session.commit()
    
    def delete(self, session):
        """
        Удалить AudioFile из БД.
        
        Args:
            session: SQLAlchemy сессия
        """
        session.delete(self)
        session.commit()

