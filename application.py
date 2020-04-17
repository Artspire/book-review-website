import os
import requests

from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():
    """Show homepage"""

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="please provide a username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="please provide a password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()
        db.commit()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html", message="invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="please provide a username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="please provide a password")

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="please provide the password confirmation")

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("error.html", message="passwords do not match")

        # Hash password
        hash_pw = generate_password_hash(request.form.get("password"))

        # Store user into users
        user = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                          {"username": request.form.get("username"), "hash": hash_pw})
        db.commit()

        # If user already in databse
        if not user:
            return render_template("error.html", message="user already exists")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()
        db.commit()

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Return success page
        return render_template("success.html", message="Account successfully created")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Account settings (change password)"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure old password was submitted
        if not request.form.get("oldpassword"):
            return render_template("error.html", message="please provide your old password")

        # Ensure new password was submitted
        elif not request.form.get("newpassword"):
            return render_template("error.html", message="please provide your new password")

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="please provide the password confirmation")

        # Ensure passwords match
        elif request.form.get("newpassword") != request.form.get("confirmation"):
            return render_template("error.html", message="passwords do not match")

        # Query database for username
        pw = db.execute("SELECT hash FROM users WHERE id = :id", {"id": session.get("user_id")}).fetchall()
        db.commit()

        # Ensure old password is correct
        if not check_password_hash(pw[0]["hash"], request.form.get("oldpassword")):
            return render_template("error.html", message="password is not correct")

        # Hash password
        hash_pw = generate_password_hash(request.form.get("newpassword"))

        # Update user's password
        db.execute("UPDATE users SET hash = :hash WHERE id = :id",
                   {"id": session.get("user_id"), "hash": hash_pw})
        db.commit()

        # Return success page
        return render_template("success.html", message="Password successfully changed")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """Account settings (delete account)"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure old password was submitted
        if not request.form.get("password"):
            return render_template("error.html", message="please provide your password")

        # Query database for username
        pw = db.execute("SELECT hash FROM users WHERE id = :id", {"id": session.get("user_id")}).fetchall()
        db.commit()

        # Ensure old password is correct
        if not check_password_hash(pw[0]["hash"], request.form.get("password")):
            return render_template("error.html", message="password is not correct")

        # Delete reviews of user from database
        db.execute("DELETE FROM reviews WHERE user_id = :user_id", {"user_id": session.get("user_id")})

        # Delete user account from database
        db.execute("DELETE FROM users WHERE id = :id", {"id": session.get("user_id")})
        db.commit()

        # Forget any user_id
        session.clear()

        # Redirect user to login form
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("delete.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search for a book from the database"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure search term was submitted
        if not request.form.get("search"):
            return render_template("error.html", message="please enter a search term")

        # User input
        input = str(request.form.get("search")).lower()

        # Variable to store whether user selected the ISBN, title or author option
        option = request.form.get("inlineRadioOptions")

        # Ensure user selected one the options
        if not option:
            return render_template("error.html", message="please specify your search query")

        # If user is searching by ISBN number
        if option == 'isbn':
            books = db.execute("SELECT * FROM books WHERE lower(isbn) LIKE :input LIMIT 50",
                               {"input": '%' + input + '%'}).fetchall()
            db.commit()

            # Error message if no results for search query
            if not books:
                return render_template("error.html", message="no book(s) found with that ISBN number")

        # If user is searching by title
        if option == 'title':
            books = db.execute("SELECT * FROM books WHERE lower(title) LIKE :input LIMIT 50",
                                       {"input": '%' + input + '%'}).fetchall()
            db.commit()

            # Error message if no results for search query
            if not books:
                return render_template("error.html", message="no book(s) found with that title")

        # If user is searching by author
        if option == 'author':
            books = db.execute("SELECT * FROM books WHERE lower(author) LIKE :input LIMIT 50",
                                       {"input": '%' + input + '%'}).fetchall()
            db.commit()

            # Error message if no results for search query
            if not books:
                return render_template("error.html", message="no book(s) found with that author")

        # Return page with search results
        return render_template("results.html", input=input, books=books)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("search.html")


@app.route("/book/<string:book_isbn>", methods=["GET", "POST"])
@login_required
def book(book_isbn):
    """Return details about a single book"""

    # Retrieve details about book from database
    details = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchall()
    db.commit()

    # Goodreads API request
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": 'qLpIHOParEa28DxFxLQ', "isbns": book_isbn})
    data = res.json()

    # Convert dict to list
    book = data["books"]

    # Retrieve book reviews from database
    reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :book_isbn", {"book_isbn": book_isbn}).fetchall()
    db.commit()

    # Query database for username of user
    user = db.execute("SELECT username FROM users WHERE id = :id", {"id": session.get("user_id")}).fetchone()
    db.commit()

    username = user[0]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure review was written
        if not request.form.get("review"):
            return render_template("error.html", message="please type a review")

        # Variable to store rating (scale 1 to 5)
        rating = int(request.form.get("inlineRadioOptions"))

        # Ensure user rated the book
        if not rating:
            return render_template("error.html", message="please rate the book")

        # Ensure user has not already reviewed the book
        if db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_isbn = :book_isbn",
                      {"user_id": session.get("user_id"), "book_isbn": book_isbn}).rowcount != 0:
            return render_template("error.html", message="you have already reviewed this book")

        # Store user review into reviews table
        db.execute("INSERT INTO reviews (user_id, username, book_isbn, rating, review) VALUES (:user_id, :username, :book_isbn, :rating, :review)",
                   {"user_id": session.get("user_id"), "username": username, "book_isbn": book_isbn, "rating": rating, "review": request.form.get("review")})
        db.commit()

        # Show success message
        return render_template("success.html", message="Your review has been submitted")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("book.html", details=details, book=book, reviews=reviews)


@app.route("/api/<string:isbn>", methods=["GET"])
@login_required
def book_api(isbn):
    """Return JSON response"""

    # Make sure ISBN exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    db.commit()

    # If the ISBN is invalid or not in database
    if book is None:
        return jsonify({"error": "ISBN not found"}), 404

    avg = db.execute("SELECT AVG(rating) FROM reviews WHERE book_isbn = :book_isbn", {"book_isbn": isbn}).fetchall()

    total = db.execute("SELECT COUNT(rating) FROM reviews WHERE book_isbn = :book_isbn", {"book_isbn": isbn}).fetchall()

    # Goodreads API request
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": 'qLpIHOParEa28DxFxLQ', "isbns": isbn})
    data = res.json()

    # Convert dict to list
    goodreads = data["books"]

    # Return JSON object
    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": goodreads[0]["work_ratings_count"],
            "average_score": goodreads[0]["average_rating"]
        })


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
