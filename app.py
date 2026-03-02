from unittest import result

from flask import Flask, render_template, request, redirect, session
from backend import LibraryDB

app = Flask(__name__)
app.secret_key = "supersecretkey"

db = LibraryDB()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        role = request.form["role"]
        password = request.form["password"]

        result = db.register_user(name, email, role, password)
        return render_template("register.html", message=result)

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.login_user(email, password)

        if user:
            session["user"] = user[1]
            session["role"] = user[3]
            return redirect("/dashboard")
        else:
            return render_template("login.html", message="Invalid Credentials!")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    books = db.get_all_books()
    stats = db.get_statistics()
    overdue = db.get_overdue_count()

    return render_template(
        "dashboard.html",
        user=session["user"],
        role=session["role"],
        books=books,
        stats=stats,
        overdue=overdue
    )

# ---------------- ADD BOOK ----------------
@app.route("/add_book", methods=["GET", "POST"])
def add_book():

    if "user" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied! Admin Only"

    if request.method == "POST":
        name = request.form["name"]
        book_id = request.form["book_id"]
        author = request.form["author"]
        category = request.form["category"]
        quantity = request.form["quantity"]

        result = db.add_book(name, book_id, author, category, int(quantity))
        return render_template("add_book.html", message=result)

    return render_template("add_book.html")

# ---------------- ADD STUDENT ----------------
@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    if "user" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied! Admin Only"

    if request.method == "POST":
        name = request.form["name"]
        student_id = request.form["student_id"]
        department = request.form["department"]

        result = db.add_student(name, student_id, department)
        return render_template("add_student.html", message=result)

    return render_template("add_student.html")

# ---------------- search BOOK ----------------
@app.route("/search_books", methods=["GET", "POST"])
def search_books():
    results = []

    if request.method == "POST":
        keyword = request.form["keyword"]
        results = db.search_books(keyword)

    return render_template("search_books.html", results=results)

# ---------------- ISSUE BOOK ----------------
@app.route("/issue_book", methods=["GET", "POST"])
def issue_book():

    if "user" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied! Admin Only"

    students = db.get_all_students()
    books = db.get_all_books()

    if request.method == "POST":
        book_id = request.form["book_id"]
        student_id = request.form["student_id"]

        result = db.issue_book(book_id, student_id)
        return render_template("issue_book.html",
                               students=students,
                               books=books,
                               message=result)

    return render_template("issue_book.html",
                           students=students,
                           books=books)
    
# ---------------- RETURN BOOK ----------------
@app.route("/return_book", methods=["GET", "POST"])
def return_book():

    if "user" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied! Admin Only"

    students = db.get_all_students()
    books = db.get_all_books()

    if request.method == "POST":
        student_id = request.form["student_id"]
        book_id = request.form["book_id"]

        result = db.return_book(book_id, student_id)

        return render_template("return_book.html",
                               students=students,
                               books=books,
                               message=result)

    return render_template("return_book.html",
                           students=students,
                           books=books)
    
# ---------------- VIEW ISSUED BOOKS ----------------
@app.route("/issued_books")
def issued_books():

    if "user" not in session:
        return redirect("/login")

    records = db.view_issued_books()

    return render_template("issued_books.html", records=records)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)