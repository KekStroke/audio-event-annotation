"""
Скрипт для инициализации базы данных.

Создаёт все таблицы и может добавить начальные данные.
"""
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models import init_db, EventType


def initialize_database(database_url=None):
    """
    Инициализировать базу данных.
    
    Args:
        database_url: URL подключения к БД (опционально)
    """
    print("Инициализация базы данных...")
    
    # Инициализируем БД
    db = init_db(database_url)
    print("✓ Таблицы созданы")
    
    # Добавляем начальные типы событий (опционально)
    session = db.get_session()
    
    try:
        # Проверяем есть ли уже типы событий
        existing_types = EventType.get_all(session)
        
        if not existing_types:
            print("\nДобавление начальных типов событий...")
            
            default_event_types = [
                {"name": "speech", "color": "#FF5733", "description": "Речь"},
                {"name": "music", "color": "#33C4FF", "description": "Музыка"},
                {"name": "noise", "color": "#808080", "description": "Шум"},
                {"name": "silence", "color": "#FFFFFF", "description": "Тишина"},
            ]
            
            for event_data in default_event_types:
                EventType.create(session, **event_data)
                print(f"  ✓ Добавлен тип: {event_data['name']}")
        else:
            print(f"\n✓ Типов событий уже существует: {len(existing_types)}")
    
    except Exception as e:
        print(f"✗ Ошибка при добавлении начальных данных: {e}")
        session.rollback()
    finally:
        session.close()
    
    print("\n✓ Инициализация завершена")
    return db


if __name__ == "__main__":
    # Запуск напрямую из командной строки
    import argparse
    
    parser = argparse.ArgumentParser(description='Инициализация базы данных')
    parser.add_argument(
        '--url',
        type=str,
        help='URL подключения к БД (по умолчанию: sqlite:///audio_annotation.db)'
    )
    
    args = parser.parse_args()
    initialize_database(args.url)

