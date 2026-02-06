from sqlalchemy import Column, Text, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PropertyTable(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, autoincrement=True)

    h1 = Column(Text)
    title = Column(Text)
    description = Column(Text)
    price_usd = Column(Text)
    area = Column(Text)
    property_type = Column(Text)
    country = Column(Text)
    object_id = Column(Text)
    url = Column(Text)
