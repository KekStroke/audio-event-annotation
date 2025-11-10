"""
Модель Annotation для хранения аннотаций временных интервалов.
"""
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base
from .types import GUID


class Annotation(Base):
    """
    Модель для хранения аннотаций временных интервалов аудио.
    
    Attributes:
        id: Уникальный идентификатор (UUID)
        audio_file_id: ID связанного аудио-файла
        start_time: Время начала интервала (секунды)
        end_time: Время конца интервала (секунды)
        event_label: Метка события
        confidence: Уверенность в аннотации (0-1), опционально
        notes: Заметки, опционально
        created_at: Дата и время создания
        updated_at: Дата и время последнего обновления
        audio_file: Связь с AudioFile
    """
    
    __tablename__ = 'annotations'
    
    id = Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    
    audio_file_id = Column(
        GUID,
        ForeignKey('audio_files.id', ondelete='CASCADE'),
        nullable=False
    )
    
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    event_label = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Связь с AudioFile
    audio_file = relationship("AudioFile", back_populates="annotations")
    
    def __repr__(self):
        """Строковое представление модели."""
        return (
            f"<Annotation(id={self.id}, "
            f"label='{self.event_label}', "
            f"time={self.start_time}-{self.end_time}s)>"
        )
    
    def to_dict(self):
        """
        Преобразовать модель в словарь.
        
        Returns:
            dict: Словарь с данными модели
        """
        return {
            'id': str(self.id),
            'audio_file_id': str(self.audio_file_id),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'event_label': self.event_label,
            'confidence': self.confidence,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def create(cls, session, **kwargs):
        """
        Создать новую Annotation и сохранить в БД.
        
        Args:
            session: SQLAlchemy сессия
            **kwargs: Параметры модели
        
        Returns:
            Annotation: Созданный экземпляр
        """
        annotation = cls(**kwargs)
        session.add(annotation)
        session.commit()
        return annotation
    
    @classmethod
    def get_by_id(cls, session, annotation_id):
        """
        Получить Annotation по ID.
        
        Args:
            session: SQLAlchemy сессия
            annotation_id: UUID аннотации
        
        Returns:
            Annotation или None
        """
        return session.query(cls).filter_by(id=annotation_id).first()
    
    @classmethod
    def get_by_audio_file(cls, session, audio_file_id):
        """
        Получить все аннотации для аудио-файла.
        
        Args:
            session: SQLAlchemy сессия
            audio_file_id: UUID аудио-файла
        
        Returns:
            list: Список Annotation
        """
        return session.query(cls).filter_by(
            audio_file_id=audio_file_id
        ).order_by(cls.start_time).all()
    
    @classmethod
    def get_all(cls, session, limit=None, offset=None):
        """
        Получить все Annotation.
        
        Args:
            session: SQLAlchemy сессия
            limit: Максимальное количество записей
            offset: Смещение
        
        Returns:
            list: Список Annotation
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
        self.updated_at = datetime.utcnow()
        session.commit()
    
    def delete(self, session):
        """
        Удалить Annotation из БД.
        
        Args:
            session: SQLAlchemy сессия
        """
        session.delete(self)
        session.commit()
    
    @property
    def duration(self):
        """
        Вычислить длительность аннотации.
        
        Returns:
            float: Длительность в секундах
        """
        return self.end_time - self.start_time

