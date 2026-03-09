from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "quizsecret"


# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect("quiz.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------- CREATE TABLES ----------
def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT,
    role TEXT)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subjects(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS units(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER,
    name TEXT)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER,
    level TEXT,
    question TEXT,
    o1 TEXT,
    o2 TEXT,
    o3 TEXT,
    o4 TEXT,
    answer TEXT)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS results(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    unit_id INTEGER,
    level TEXT,
    score INTEGER,
    total INTEGER)
    """)

    # default admin
    cur.execute("""
    INSERT OR IGNORE INTO users(id,name,email,password,role)
    VALUES(1,'Admin','admin@gmail.com','admin123','admin')
    """)

    conn.commit()
    conn.close()


init_db()


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("home.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
        "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
        (
            request.form["name"],
            request.form["email"],
            request.form["password"],
            "student"
        ))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------- LOGIN ----------
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (request.form["email"],request.form["password"])
        )

        user = cur.fetchone()
        conn.close()

        if user:

            session["uid"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")
            else:
                return redirect("/subjects")

        return "Invalid Login"

    return render_template("login.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- ADMIN PANEL ----------
@app.route("/admin")
def admin():
    return render_template("admin_panel.html")


# ---------- ADD SUBJECT ----------
@app.route("/add_subject", methods=["GET","POST"])
def add_subject():

    if request.method == "POST":

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
        "INSERT INTO subjects(name) VALUES(?)",
        (request.form["name"],))

        conn.commit()
        conn.close()

        return redirect("/manage_subjects")

    return render_template("add_subject.html")


# ---------- DELETE SUBJECT ----------
@app.route("/delete_subject/<int:id>")
def delete_subject(id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM subjects WHERE id=?", (id,))
    
    conn.commit()
    conn.close()

    return redirect("/manage_subjects")


# ---------- MANAGE SUBJECTS ----------
@app.route("/manage_subjects")
def manage_subjects():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM subjects")
    subjects = cur.fetchall()

    conn.close()

    return render_template("manage_subjects.html",subjects=subjects)


# ---------- ADD UNIT ----------
@app.route("/add_unit", methods=["GET","POST"])
def add_unit():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM subjects")
    subs = cur.fetchall()

    if request.method == "POST":

        cur.execute(
        "INSERT INTO units(subject_id,name) VALUES(?,?)",
        (
            request.form["subject"],
            request.form["unit"]
        ))

        conn.commit()
        conn.close()

        return redirect("/manage_units")

    conn.close()

    return render_template("add_unit.html",subs=subs)


# ---------- DELETE UNIT ----------
@app.route("/delete_unit/<int:id>")
def delete_unit(id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM units WHERE id=?", (id,))
    
    conn.commit()
    conn.close()

    return redirect("/manage_units")


# ---------- MANAGE UNITS ----------
@app.route("/manage_units")
def manage_units():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT units.id,units.name,subjects.name AS subject
    FROM units
    JOIN subjects ON subjects.id = units.subject_id
    """)

    units = cur.fetchall()
    conn.close()

    return render_template("manage_units.html",units=units)


# ---------- ADD QUIZ ----------
@app.route("/add_quiz", methods=["GET","POST"])
def add_quiz():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM units")
    units = cur.fetchall()

    if request.method == "POST":

        cur.execute("""
        INSERT INTO questions(unit_id,level,question,o1,o2,o3,o4,answer)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            request.form["unit"],
            request.form["level"],
            request.form["question"],
            request.form["o1"],
            request.form["o2"],
            request.form["o3"],
            request.form["o4"],
            request.form["answer"]
        ))

        conn.commit()
        conn.close()

        return redirect("/admin")

    conn.close()

    return render_template("add_quiz.html",units=units)


# ---------- SUBJECT LIST ----------
@app.route("/subjects")
def subjects():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM subjects")
    subs = cur.fetchall()

    conn.close()

    return render_template("subjects.html",subs=subs)


# ---------- UNITS ----------
@app.route("/units/<int:sid>")
def units(sid):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM units WHERE subject_id=?", (sid,))
    units = cur.fetchall()

    conn.close()

    return render_template("units.html",units=units)


# ---------- LEVELS ----------
@app.route("/levels/<int:uid>")
def levels(uid):
    return render_template("levels.html",uid=uid)


# ---------- QUIZ ----------
@app.route("/quiz/<int:uid>/<level>", methods=["GET","POST"])
def quiz(uid,level):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
    "SELECT * FROM questions WHERE unit_id=? AND level=?",
    (uid,level))

    qs = cur.fetchall()

    if request.method == "POST":

        score = 0

        for q in qs:
            if request.form.get(str(q["id"])) == q["answer"]:
                score += 1

        return f"Score: {score}/{len(qs)}"

    return render_template("quiz.html",qs=qs)


# ---------- VIEW RESULTS ----------
@app.route("/view_results")
def view_results():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM results")
    results = cur.fetchall()

    conn.close()

    return render_template("view_results.html",results=results)


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
