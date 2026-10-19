from flask import Flask, redirect, render_template, request, url_for
import sqlite3


app = Flask(__name__)
app.secret_key = "library-secret-key"
DB_NAME = "library.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER,
                borrower TEXT,
                available INTEGER
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM books")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO books (id, title, author, year, borrower, available) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (1, "Кобзар", "Тарас Шевченко", 1840, "Олена", 0),
                    (2, "Тигр і лебідь", "Сергій Бондарчук", 2021, "", 1)
                ]
            )
        conn.commit()

init_db()

class DatabaseBooksProxy:
    def __iter__(self):
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books")
            return iter([{**dict(row), "available": bool(row["available"])} for row in cursor.fetchall()])
    
    def append(self, book):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO books (id, title, author, year, borrower, available)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (book["id"], book["title"], book["author"], book["year"], book["borrower"], int(book["available"])))
            conn.commit()

    def pop(self, index):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM books")
            ids = [row[0] for row in cursor.fetchall()]
            if 0 <= index < len(ids):
                cursor.execute("DELETE FROM books WHERE id = ?", (ids[index],))
                conn.commit()

BOOKS = DatabaseBooksProxy()


def get_next_id():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM books")
        max_id = cursor.fetchone()[0]
        return 1 if max_id is None else max_id + 1


def find_book(book_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if row:
            book = dict(row)
            book["available"] = bool(book["available"])
            return book
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/library")
def library():
    return render_template("library.html", books=BOOKS)


@app.route("/library/add", methods=["POST"])
def add_book():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    year = request.form.get("year", "").strip()
    borrower = request.form.get("borrower", "").strip()

    if title and author:
        BOOKS.append(
            {
                "id": get_next_id(),
                "title": title,
                "author": author,
                "year": int(year) if year.isdigit() else 0,
                "borrower": borrower,
                "available": not borrower,
            }
        )

    return redirect(url_for("library"))


@app.route("/library/<int:book_id>/edit", methods=["GET", "POST"])
def edit_book(book_id):
    book = find_book(book_id)
    if book is None:
        return redirect(url_for("library"))

    if request.method == "POST":
        title = request.form.get("title", book["title"]).strip() or book["title"]
        author = request.form.get("author", book["author"]).strip() or book["author"]
        year = request.form.get("year", str(book["year"])).strip()
        book_year = int(year) if year.isdigit() else book["year"]
        borrower = request.form.get("borrower", "").strip()
        available = not borrower

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE books 
                SET title = ?, author = ?, year = ?, borrower = ?, available = ? 
                WHERE id = ?
            """, (title, author, book_year, borrower, int(available), book_id))
            conn.commit()
            
        return redirect(url_for("library"))

    return render_template("edit_book.html", book=book)


@app.route("/library/<int:book_id>/lend", methods=["POST"])
def lend_book(book_id):
    book = find_book(book_id)
    if book is not None:
        borrower = request.form.get("borrower", "").strip()
        if borrower:
            new_borrower = borrower
            available = False
        else:
            new_borrower = ""
            available = True
            
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE books SET borrower = ?, available = ? WHERE id = ?
            """, (new_borrower, int(available), book_id))
            conn.commit()
            
    return redirect(url_for("library"))


@app.route("/library/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    for index, book in enumerate(BOOKS):
        if book["id"] == book_id:
            BOOKS.pop(index)
            break
    return redirect(url_for("library"))


if __name__ == "__main__":
    app.run(debug=True)
