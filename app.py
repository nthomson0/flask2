from flask import Flask, render_template, request, jsonify
from pathlib import Path
from db import db
from models import Book, Category, User, BookRental
from sqlalchemy import select
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"

app.instance_path = Path("data").resolve()

db.init_app(app)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/users")
def users():
    statement = select(User).order_by(User.name)
    records = db.session.execute(statement).scalars()
    return render_template("users.html", users=records)

@app.route("/books")
def books():
    statement1 = select(Book).order_by(Book.id)
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

@app.route("/book/<int:id>")
def book_detail(id):
    statement = select(Book).where(Book.id == id)
    record = db.session.execute(statement).scalar()
    if not record:
        return "NOT FOUND", 404
    return render_template("book.html", book=record)

@app.route("/user/<int:id>")
def user_detail(id):
    statement = select(User).where(User.id == id)
    record = db.session.execute(statement).scalar()
    if not record:
        return "NOT FOUND", 404
    return render_template("user.html", user=record)

@app.route("/available")
def available():
    statement = select(Book).where(~Book.rentals.any() | Book.rentals.any() & ~Book.rentals.any(BookRental.returned == None)).order_by(Book.id)
    records = db.session.execute(statement).scalars()
    return render_template("available.html", books=records)

@app.route("/rented")
def rented():
    book_ids_stmt = select(BookRental.book_id).where(BookRental.rented < datetime.now()).where(BookRental.returned == None)
    book_ids = [id for id in db.session.execute(book_ids_stmt).scalars()]
    ordered_books = select(Book).where(Book.id.in_(book_ids)).order_by(Book.id)
    books = db.session.execute(ordered_books).scalars()
    return render_template("rented.html", books=books)

@app.route("/api/books")
def books_api():
    statement = select(Book).order_by(Book.id)
    records = db.session.execute(statement).scalars()
    books = []
    for book in records:
        books.append(book.to_dict())
    return jsonify(books)

@app.route("/api/books", methods=["POST"])
def books_api_post():
    data = request.get_json()
    # Validation functions
    is_positive_number = lambda num: isinstance(num, (int, float)) and num >= 0
    is_non_empty_string = lambda s: isinstance(s, str) and len(s) > 0
    is_valid_rating = lambda num: isinstance(num, int) and 1 <= num <= 5

    # Field mapping
    required_fields = {
    "title": is_non_empty_string,
    "price": is_positive_number,
    "available": is_positive_number,
    "rating": is_valid_rating,
    "url": is_non_empty_string,
    "upc": is_non_empty_string,
    "category": is_non_empty_string,
    }

    # Field validation
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400
        else:
            func = required_fields[field]
            value = data[field]
        if not func(value):
            return {"error": f"Invalid value for field {field}: {value}"}, 400
        
    if db.session.execute(select(Book).where(Book.upc == data["upc"])).scalar(): return "Error: That UPC already exists", 404

    category = db.session.execute(select(Category).where(Category.name == data["category"])).scalar()

    if not category: 
        category = Category(name=data["category"])
        db.session.add(category)
        db.session.commit()

    book = Book(title=data["title"], price=data["price"], available=data["available"], rating=data["rating"], upc=data["upc"], url=data["url"], category=category)
    db.session.add(book)
    db.session.commit()
    return data

@app.route("/api/books/<int:book_id>")
def books_api_detailed(book_id):
    statement = select(Book).where(Book.id == book_id)
    record = db.session.execute(statement).scalar()

    rentals_stmt = select(BookRental).where(BookRental.book_id == book_id)
    rentals = db.session.execute(rentals_stmt).scalars()
    
    if not record:
        return f"Error: Book id:{book_id} not found", 404

    record.available = True
    for rental in rentals:
        if rental.returned == None:
            record.available = False
            
    book = record.to_dict()
    return jsonify(book)

@app.route("/api/books/<int:book_id>/rent", methods=["POST"])
def rent_book(book_id):
    data = request.get_json()

    # Check request has valid field
    if "user_id" not in data: return "Error: Missing userID field", 404

    # Check book exists
    statement = select(Book).where(Book.id == book_id)
    record = db.session.execute(statement).scalar()
    if not record: return "Error: Book does not exist", 404

    rentals_stmt = select(BookRental).where(BookRental.book_id == book_id)
    rentals = db.session.execute(rentals_stmt).scalars()

    for rental in rentals:
        if rental.returned == None: 
            return "Error: Book is rented", 403

    book_rental = BookRental(user_id=data["user_id"], book_id=book_id, rented=datetime.now())

    db.session.add(book_rental)
    db.session.commit()

    return f"Book id:{book_id} has been successfully returned."

@app.route("/api/books/<int:book_id>/return", methods=["PUT"])
def return_book(book_id):
    # Check book exists
    statement = select(Book).where(Book.id == book_id)
    record = db.session.execute(statement).scalar()
    if not record: return "Error: Book does not exist", 404

    rentals_stmt = select(BookRental).where(BookRental.book_id == book_id)
    rentals = db.session.execute(rentals_stmt).scalars()

    rental_id = ""
    is_rented = False
    for rental in rentals:
        if rental.returned == None:
            is_rented = True
            rental_id = rental.id

    if not is_rented:
        return "Error: Book is not rented currently", 403
    
    return_rental_stmt = select(BookRental).where(BookRental.id == rental_id)
    return_rental = db.session.execute(return_rental_stmt).scalar()

    return_rental.returned = datetime.now()

    db.session.commit()
    return f"Book id:{book_id} was successfully returned."

if __name__ == "__main__":
    app.run(debug=True, port=8888)