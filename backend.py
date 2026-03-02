import sqlite3
import hashlib
from datetime import datetime, timedelta

# ==============================
# DATABASE CLASS
# ==============================

class LibraryDB:
    def __init__(self):
        self.conn = sqlite3.connect("library.db", check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cur = self.conn.cursor()
        self.create_tables()

    def search_books(self, keyword):
        self.cur.execute("""
            SELECT * FROM books
            WHERE name LIKE ? OR author LIKE ?
        """, ('%' + keyword + '%', '%' + keyword + '%'))
        
    def get_overdue_count(self):

        self.cur.execute("SELECT due_date FROM issued_books")
        records = self.cur.fetchall()

        overdue = 0
        today = datetime.now()

        for record in records:
            due_date = record[0]

            if due_date:
                due = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
                if today > due:
                    overdue += 1

        return overdue
    
    # --------------------------
    # CREATE TABLES
    # --------------------------
    def create_tables(self):

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            role TEXT,
            password TEXT
        )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS books(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            book_id TEXT UNIQUE,
            author TEXT,
            category TEXT,
            quantity INTEGER
        )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            student_id TEXT UNIQUE,
            department TEXT
        )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS issued_books(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT,
            student_id TEXT,
            issue_date TEXT,
            FOREIGN KEY(book_id) REFERENCES books(book_id),
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
        """)
        
        # Add due_date column if not exists
        try:
            self.cur.execute("ALTER TABLE issued_books ADD COLUMN due_date TEXT")
        except:
            pass    

        self.conn.commit()

    # ==============================
    # USER FUNCTIONS
    # ==============================

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, name, email, role, password):
        try:
            hashed_password = self.hash_password(password)
            self.cur.execute(
                "INSERT INTO users(name,email,role,password) VALUES (?,?,?,?)",
                (name, email, role, hashed_password)
            )
            self.conn.commit()
            return "User Registered Successfully"
        except sqlite3.IntegrityError:
            return "Email Already Exists"

    def login_user(self, email, password):
        hashed_password = self.hash_password(password)
        self.cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, hashed_password)
        )
        return self.cur.fetchone()

    # ==============================
    # BOOK FUNCTIONS
    # ==============================

    def add_book(self, name, book_id, author, category, quantity):
        try:
            self.cur.execute("""
                INSERT INTO books(name,book_id,author,category,quantity)
                VALUES (?,?,?,?,?)
            """, (name, book_id, author, category, quantity))
            self.conn.commit()
            return "Book Added Successfully"
        except sqlite3.IntegrityError:
            return "Book ID Already Exists"

    def get_all_books(self):
        self.cur.execute("SELECT * FROM books")
        return self.cur.fetchall()

    def delete_book(self, book_id):
        self.cur.execute("DELETE FROM books WHERE book_id=?", (book_id,))
        self.conn.commit()

    def search_book(self, keyword):
        self.cur.execute("""
            SELECT * FROM books
            WHERE name LIKE ? OR author LIKE ?
        """, ('%' + keyword + '%', '%' + keyword + '%'))
        return self.cur.fetchall()

    # ==============================
    # STUDENT FUNCTIONS
    # ==============================

    def add_student(self, name, student_id, department):
        try:
            self.cur.execute("""
                INSERT INTO students(name,student_id,department)
                VALUES (?,?,?)
            """, (name, student_id, department))
            self.conn.commit()
            return "Student Added Successfully"
        except sqlite3.IntegrityError:
            return "Student ID Already Exists"

    def get_all_students(self):
        self.cur.execute("SELECT * FROM students")
        return self.cur.fetchall()

    # ==============================
    # ISSUE BOOK
    # ==============================

    def issue_book(self, book_id, student_id):

        # Check if book exists
        self.cur.execute("SELECT quantity FROM books WHERE book_id=?", (book_id,))
        book = self.cur.fetchone()

        if book is None:
            return "Book Not Found!"

        if book[0] <= 0:
            return "Book Out of Stock!"

        # Check if student exists
        self.cur.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        student = self.cur.fetchone()

        if student is None:
            return "Student Not Found!"

        # Check if already issued
        self.cur.execute("""
            SELECT * FROM issued_books
            WHERE book_id=? AND student_id=?
        """, (book_id, student_id))

        if self.cur.fetchone():
            return "Book already issued to this student!"

        # Reduce quantity
        self.cur.execute(
            "UPDATE books SET quantity = quantity - 1 WHERE book_id=?",
            (book_id,)
        )

        # Set issue & due date
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=7)

        # Insert record
        self.cur.execute("""
            INSERT INTO issued_books (book_id, student_id, issue_date, due_date)
            VALUES (?, ?, ?, ?)
        """, (
            book_id,
            student_id,
            issue_date.strftime("%Y-%m-%d %H:%M:%S"),
            due_date.strftime("%Y-%m-%d %H:%M:%S")
        ))

        self.conn.commit()
        return "Book Issued Successfully!"

    # ==============================
    # RETURN BOOK
    # ==============================

    def return_book(self, book_id, student_id):

        self.cur.execute("""
            SELECT * FROM issued_books
            WHERE book_id=? AND student_id=?
        """, (book_id, student_id))

        record = self.cur.fetchone()

        if record is None:
            return "No Issue Record Found!"

        self.cur.execute(
            "UPDATE books SET quantity = quantity + 1 WHERE book_id=?",
            (book_id,)
        )

        self.cur.execute("""
            DELETE FROM issued_books
            WHERE book_id=? AND student_id=?
        """, (book_id, student_id))

        self.conn.commit()
        return "Book Returned Successfully!"

    def view_issued_books(self):

        self.cur.execute("""
            SELECT 
                books.name,
                books.book_id,
                students.name,
                students.student_id,
                issued_books.issue_date,
                issued_books.due_date
            FROM issued_books
            JOIN books ON issued_books.book_id = books.book_id
            JOIN students ON issued_books.student_id = students.student_id
        """)

        records = self.cur.fetchall()

        updated_records = []

        for record in records:
            book_name, book_id, student_name, student_id, issue_date, due_date = record

            fine = 0

            if due_date:
                due = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
                today = datetime.now()

                if today > due:
                    days_late = (today - due).days
                    fine = days_late * 10   # ₹10 per day

            updated_records.append(
                (book_name, book_id, student_name, student_id, issue_date, due_date, fine)
            )

        return updated_records
    
    def get_statistics(self):

        # Total Books
        self.cur.execute("SELECT COUNT(*) FROM books")
        total_books = self.cur.fetchone()[0]

        # Total Students
        self.cur.execute("SELECT COUNT(*) FROM students")
        total_students = self.cur.fetchone()[0]

        # Total Issued Books
        self.cur.execute("SELECT COUNT(*) FROM issued_books")
        total_issued = self.cur.fetchone()[0]

        # Total Available Books
        self.cur.execute("SELECT SUM(quantity) FROM books")
        available_books = self.cur.fetchone()[0]

        if available_books is None:
            available_books = 0

        return total_books, total_students, total_issued, available_books
    def close(self):
        self.conn.close()