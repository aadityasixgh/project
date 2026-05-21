from flask import Flask, render_template, request, redirect, session
import pandas as pd
import sqlite3
import os
import re
from rapidfuzz import fuzz

app = Flask(__name__)
app.secret_key = "viraj_secret"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# DATABASE
conn = sqlite3.connect("users.db")
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
''')

conn.commit()
conn.close()


@app.route("/")
def home():

    if "user" in session:
        return redirect("/dashboard")

    return redirect("/login")


# SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = c.fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")

        else:
            error = "Invalid Username or Password"

    return render_template("login.html", error=error)


# DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user" not in session:
        return redirect("/login")

    tables = ""
    total_rows = 0
    total_columns = 0
    total_matches = 0

    if request.method == "POST":

        file = request.files["excel"]
        keyword = request.form["keyword"]

        if file:

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                file.filename
            )

            file.save(filepath)

            df = pd.read_excel(filepath)

            total_rows = len(df)
            total_columns = len(df.columns)

            def highlight_cell(x):

                nonlocal total_matches

                x = str(x)

                similarity = fuzz.partial_ratio(
                    keyword.lower(),
                    x.lower()
                )

                reverse_similarity = fuzz.partial_ratio(
                    keyword[::-1].lower(),
                    x.lower()
                )

                if (
                    keyword.lower() in x.lower()
                    or similarity > 70
                    or reverse_similarity > 70
                ):

                    total_matches += 1

                    return re.sub(
                        f"({keyword})",
                        r"<mark>\1</mark>",
                        x,
                        flags=re.IGNORECASE
                    )

                return x

            styled_df = df.map(highlight_cell)

            tables = styled_df.to_html(
                classes="excel-table",
                index=False,
                escape=False
            )

    return render_template(
        "dashboard.html",
        tables=tables,
        total_rows=total_rows,
        total_columns=total_columns,
        total_matches=total_matches
    )


# LOGOUT
@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)