"""
Модель EventType для хранения типов событий.
"""
from sqlalchemy import Column, String, Text
from datetime import datetime
import uuid

from .database import Base
from .types import GUID


class EventType(Base):
    """
    Модель для хранения типов событий для классификации.
    
    Attributes:
        id: Уникальный идентификатор (UUID)
        name: Название типа события (уникальное)
        color: Цвет для UI (hex-код)
        description: Описание типа события
    """
    
    __tablename__ = 'event_types'
    
    id = Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), nullable=False)  # hex color: #RRGGBB
    description = Column(Text, nullable=True)
    
    def __repr__(self):
        """Строковое представление модели."""
        return f"<EventType(id={self.id}, name='{self.name}', color='{self.color}')>"
    
    def to_dict(self):
        """
        Преобразовать модель в словарь.
        
        Returns:
            dict: Словарь с данными модели
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'color': self.color,
            'description': self.description
        }
    
    @classmethod
    def create(cls, session, **kwargs):
        """
        Создать новый EventType и сохранить в БД.
        
        Args:
            session: SQLAlchemy сессия
            **kwargs: Параметры модели
        
        Returns:
            EventType: Созданный экземпляр
        """
        event_type = cls(**kwargs)
        session.add(event_type)
        session.commit()
        return event_type
    
    @classmethod
    def get_by_id(cls, session, event_type_id):
        """
        Получить EventType по ID.
        
        Args:
            session: SQLAlchemy сессия
            event_type_id: UUID типа события
        
        Returns:
            EventType или None
        """
        return session.query(cls).filter_by(id=event_type_id).first()
    
    @classmethod
    def get_by_name(cls, session, name):
        """
        Получить EventType по имени.
        
        Args:
            session: SQLAlchemy сессия
            name: Название типа события
        
        Returns:
            EventType или None
        """
        return session.query(cls).filter_by(name=name).first()
    
    @classmethod
    def get_all(cls, session):
        """
        Получить все EventType.
        
        Args:
            session: SQLAlchemy сессия
        
        Returns:
            list: Список EventType
        """
        return session.query(cls).order_by(cls.name).all()
    
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
        Удалить EventType из БД.
        
        Args:
            session: SQLAlchemy сессия
        """
        session.delete(self)
        session.commit()

