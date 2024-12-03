from flask import Flask, render_template
from pathlib import Path
from db import db
from models import Book, Category, User
from sqlalchemy import select

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"

app.instance_path = Path("data").resolve()

db.init_app(app)

@app.route("/")
def home():
    return render_template("base.html")

@app.route("/users")
def users():
    statement = select(User).order_by(User.name)
    records = db.session.execute(statement).scalars()
    return render_template("users.html", users=records)

@app.route("/books")
def books():
    statement1 = select(Book).order_by(Book.title)
    records1 = db.session.execute(statement1).scalars()
    return render_template("books.html", books=records1)

@app.route("/categories")
def categories():
    statement = select(Category).order_by(Category.name)
    records = db.session.execute(statement).scalars()
    return render_template("categories.html", categories=records)

@app.route("/categories/<string:name>")
def category_detail(name):
    statement1 = select(Category).where(Category.name == name)
    records1 = db.session.execute(statement1).scalar()
    statement2 = select(Book).where(Book.category_id == records1.id)
    records2 = db.session.execute(statement2).scalars()
    return render_template("category.html", books=records2, category=name)


if __name__ == "__main__":
    app.run(debug=True, port=8888)