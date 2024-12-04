from db import db
from app import app
from models import Book, Category, User, BookRental
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.sql import func
from random import random, randint
import csv
import sys

from sqlalchemy import select

def create_tables():
    with app.app_context():
        db.create_all()

def drop_tables():
    with app.app_context():
        db.drop_all()

def create_rentals():
    now = datetime.now()
    with app.app_context():
        for _ in range(10):
            user = db.session.execute(select(User).order_by(func.random())).scalar()
            book = db.session.execute(select(Book).order_by(func.random())).scalar()
            rented = now - timedelta(days=randint(10, 25), hours=randint(0, 5))
            returned = random() > 0.5
            if returned:
                returned = rented + timedelta(days=randint(2, 9), hours=randint(0, 100), minutes=(randint(0,100)))
            else:
                returned = None

            rental = BookRental(user=user, book=book, rented=rented, returned=returned)
            db.session.add(rental)
            db.session.commit()

class Importer:
    def __init__(self, filename):
        self.filename = filename
        self.load_data_from_csv()

    def get_category_by_name(self, name):
        with app.app_context():
            statement = select(Category).where(Category.name == name)
            possible = db.session.execute(statement).scalar()
            return possible

    def get_or_create_category(self, name):
        possible = self.get_category_by_name(name)

        if possible:
            return possible
        
        category = Category(name=name)
        with app.app_context():
            db.session.add(category)
            return category
        
    def load_data_from_csv(self):
        with open(self.filename, "r") as fp:
            reader = csv.DictReader(fp)
            if "books" in self.filename:
                for row in reader:
                    category = row.pop("category")
                    row["category"] = self.get_or_create_category(category)
                    book = Book(**row)
                    with app.app_context():
                        db.session.add(book)
                        db.session.commit()
            if "users" in self.filename:
                for row in reader:
                    user = User(**row)
                    with app.app_context():
                        db.session.add(user)
                        db.session.commit()

    def import_tables():
        with open(Path("data/users"), "r") as fp:
            reader = csv.DictReader(fp)
            for book in reader:
                book_obj = Book(**book)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            drop_tables()
            create_tables()
        if sys.argv[1] == "import":
            Importer("data/books.csv")
            Importer("data/users.csv")
        if sys.argv[1] == "rentals":
            create_rentals()