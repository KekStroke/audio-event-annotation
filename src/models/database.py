"""
Модуль для управления подключением к базе данных.

Предоставляет класс Database для инициализации и управления SQLAlchemy сессиями.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
import os

# Базовый класс для всех моделей
Base = declarative_base()


class Database:
    """Класс для управления подключением к базе данных."""
    
    def __init__(self, database_url=None):
        """
        Инициализация подключения к БД.
        
        Args:
            database_url: URL подключения к БД. 
                         Если None, используется DATABASE_URL из env или SQLite по умолчанию.
        """
        if database_url is None:
            database_url = os.getenv(
                'DATABASE_URL',
                'sqlite:///audio_annotation.db'
            )
        
        # Конфигурация engine
        engine_kwargs = {
            'echo': os.getenv('SQL_ECHO', 'False').lower() == 'true',
        }
        
        # Для SQLite в памяти используем StaticPool
        if 'sqlite://' in database_url and ':memory:' in database_url:
            engine_kwargs['connect_args'] = {'check_same_thread': False}
            engine_kwargs['poolclass'] = StaticPool
        
        self.engine = create_engine(database_url, **engine_kwargs)
        
        # Создаём фабрику сессий
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
    
    def create_all(self):
        """Создать все таблицы в БД."""
        Base.metadata.create_all(self.engine)
    
    def drop_all(self):
        """Удалить все таблицы из БД."""
        Base.metadata.drop_all(self.engine)
    
    def get_session(self):
        """
        Получить новую сессию БД.
        
        Returns:
            Session: SQLAlchemy сессия
        """
        return self.Session()
    
    def close_session(self):
        """Закрыть текущую сессию."""
        self.Session.remove()
    
    def __enter__(self):
        """Context manager вход."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager выход."""
        self.close_session()


# Глобальный экземпляр БД (инициализируется при первом использовании)
_db_instance = None


def get_db():
    """
    Получить глобальный экземпляр Database.
    
    Returns:
        Database: Экземпляр базы данных
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.create_all()
    return _db_instance


def init_db(database_url=None):
    """
    Инициализировать базу данных с заданным URL.
    
    Args:
        database_url: URL подключения к БД
    
    Returns:
        Database: Экземпляр базы данных
    """
    global _db_instance
    _db_instance = Database(database_url)
    _db_instance.create_all()
    return _db_instance

