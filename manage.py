from db import db
from app import app
from models import Book, Category, User
from pathlib import Path
import csv
import sys

from sqlalchemy import select

def create_tables():
    db.create_all()

def drop_tables():
    db.drop_all()

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
            with app.app_context():
                drop_tables()
                create_tables()
        if sys.argv[1] == "import":
            Importer("data/books.csv")
            Importer("data/users.csv")