import logging
from itemadapter import ItemAdapter
from sqlalchemy import create_engine, insert
from contextlib import contextmanager
from sqlalchemy.orm import scoped_session, sessionmaker

# Импортируем из твоего текущего проекта
from .db import get_connection_string
from .models import PropertyTable, Base

# Настраиваем логгер
logger = logging.getLogger(__name__)

class DatabasePipeline:
    def __init__(self):
        # Инициализируем движок, используя твою функцию из db.py
        self.engine = create_engine(
            get_connection_string(),
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        # Создаем таблицы, если их нет
        Base.metadata.create_all(self.engine)
        self.session_factory = scoped_session(
            sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
        )

    @contextmanager
    def session_scope(self):
        """Контекстный менеджер для управления сессиями."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка в операции с БД: {e}")
            raise
        finally:
            session.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Собираем данные для недвижимости
        property_data = {
            "h1": adapter.get("h1"),
            "title": adapter.get("title"),
            "description": adapter.get("description"),
            "price_usd": adapter.get("price_usd"),
            "area": adapter.get("area"),
            "property_type": adapter.get("property_type"),
            "country": adapter.get("country"),
            "object_id": adapter.get("object_id"),
            "url": adapter.get("url"),
            "parse_date": adapter.get("parse_date"),
            "scrape_time": adapter.get("scrape_time")
        }

        try:
            with self.session_scope() as session:
                # Используем insert из SQLAlchemy
                stmt = insert(PropertyTable).values(**property_data)
                session.execute(stmt)
                spider.logger.debug(f"Объект сохранен: {property_data['title']}")
        except Exception as e:
            spider.logger.error(f"Ошибка при сохранении {property_data.get('title')}: {e}")
            # Не бросаем raise, чтобы паук не упал из-за одной ошибки записи
            return item 

        return item

    def close_spider(self, spider):
        self.session_factory.remove()
        self.engine.dispose()
        spider.logger.info("Соединение с БД закрыто")