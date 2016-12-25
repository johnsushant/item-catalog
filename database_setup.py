import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.sql.functions import current_timestamp
Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    description = Column(String(10000), nullable = False)
    created = Column(DateTime(timezone=True), default=current_timestamp())
    username = Column(String(80), nullable = False)
    cat_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Category)
    
    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'username': self.username,
            'category_id': self.cat_id
        }


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key = True)
    username = Column(String(80), nullable = False)
    email = Column(String(80), nullable = False)
    
engine = create_engine('postgresql+psycopg2://vagrant:1307@localhost:5432/catalog')

Base.metadata.create_all(engine)