"""
Модель Project для хранения информации о проектах аннотации.
"""
from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
import uuid

from .database import Base
from .types import GUID


class Project(Base):
    """
    Модель для хранения проектов аннотации.
    
    Attributes:
        id: Уникальный идентификатор (UUID)
        name: Название проекта
        description: Описание проекта
        created_at: Дата и время создания
    """
    
    __tablename__ = 'projects'
    
    id = Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        """Строковое представление модели."""
        return f"<Project(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """
        Преобразовать модель в словарь.
        
        Returns:
            dict: Словарь с данными модели
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def create(cls, session, **kwargs):
        """
        Создать новый Project и сохранить в БД.
        
        Args:
            session: SQLAlchemy сессия
            **kwargs: Параметры модели
        
        Returns:
            Project: Созданный экземпляр
        """
        project = cls(**kwargs)
        session.add(project)
        session.commit()
        return project
    
    @classmethod
    def get_by_id(cls, session, project_id):
        """
        Получить Project по ID.
        
        Args:
            session: SQLAlchemy сессия
            project_id: UUID проекта
        
        Returns:
            Project или None
        """
        return session.query(cls).filter_by(id=project_id).first()
    
    @classmethod
    def get_all(cls, session, limit=None, offset=None):
        """
        Получить все Project.
        
        Args:
            session: SQLAlchemy сессия
            limit: Максимальное количество записей
            offset: Смещение
        
        Returns:
            list: Список Project
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
        Удалить Project из БД.
        
        Args:
            session: SQLAlchemy сессия
        """
        session.delete(self)
        session.commit()

