from sqlalchemy import Boolean, Float, Numeric, ForeignKey, Integer, String, DECIMAL
from sqlalchemy.orm import mapped_column, relationship

from db import db

class Book(db.Model):
    id = mapped_column(Integer, primary_key=True) 
    title = mapped_column(String) 
    price = mapped_column(DECIMAL(10, 2)) 
    available = mapped_column(Integer, default=0)
    rating = mapped_column(Integer)
    upc = mapped_column(String)
    url = mapped_column(String)
    category = mapped_column(String)
    category_id = mapped_column(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="books")

class Category(db.Model):
    id = mapped_column(Integer, primary_key=True) 
    name = mapped_column(String) 
    books = relationship("Book", back_populates="category") 

class User(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String)