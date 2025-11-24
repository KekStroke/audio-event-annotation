"""
Кастомные типы данных для SQLAlchemy.
"""
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid


class GUID(TypeDecorator):
    """
    Платформо-независимый тип GUID.
    
    Использует PostgreSQL UUID когда доступен, иначе CHAR(36) для других БД.
    """
    
    impl = CHAR
    cache_ok = False
    
    def load_dialect_impl(self, dialect):
        """Выбор типа в зависимости от диалекта БД."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))
    
    def process_bind_param(self, value, dialect):
        """Конвертация Python UUID в строку для БД."""
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value))
    
    def process_result_value(self, value, dialect):
        """Конвертация строки из БД в Python UUID."""
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        else:
            return uuid.UUID(value)

