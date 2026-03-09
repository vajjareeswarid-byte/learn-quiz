from flask import Flask,render_template,request,redirect,session
import sqlite3

app = Flask(__name__)
app.secret_key="secret123"

# ---------- DATABASE ----------
conn = sqlite3.connect("quiz.db",check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# ---------- TABLES ----------
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
o1 TEXT,o2 TEXT,o3 TEXT,o4 TEXT,
answer TEXT)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS results(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
unit_id INTEGER,
level TEXT,
score INTEGER,
total INTEGER,
date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
""")

# default admin
cur.execute("""
INSERT OR IGNORE INTO users(id,name,email,password,role)
VALUES(1,'Admin','admin@gmail.com','admin123','admin')
""")
conn.commit()

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("home.html")

# ---------- REGISTER ----------
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        cur.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                    (request.form["name"],
                     request.form["email"],
                     request.form["password"],
                     "student"))
        conn.commit()
        return redirect("/login")
    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        cur.execute("SELECT * FROM users WHERE email=? AND password=?",
                    (request.form["email"],request.form["password"]))
        user=cur.fetchone()

        if user:
            session["uid"]=user["id"]
            session["role"]=user["role"]

            if user["role"]=="admin":
                return redirect("/admin")
            else:
                return redirect("/subjects")
        else:
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
@app.route("/add_subject",methods=["GET","POST"])
def add_subject():
    if request.method=="POST":
        cur.execute("INSERT INTO subjects(name) VALUES(?)",
                    (request.form["name"],))
        conn.commit()
        return redirect("/admin")
    return render_template("add_subject.html")

# ---------- ADD UNIT ----------
@app.route("/add_unit",methods=["GET","POST"])
def add_unit():

    cur.execute("SELECT * FROM subjects")
    subs=cur.fetchall()

    if request.method=="POST":
        cur.execute("INSERT INTO units(subject_id,name) VALUES(?,?)",
                    (request.form["subject"],
                     request.form["unit"]))
        conn.commit()
        return redirect("/admin")

    return render_template("add_unit.html",subs=subs)

# ---------- ADD QUIZ ----------
@app.route("/add_quiz",methods=["GET","POST"])
def add_quiz():

    cur.execute("SELECT * FROM units")
    units=cur.fetchall()

    if request.method=="POST":
        cur.execute("""
        INSERT INTO questions(unit_id,level,question,o1,o2,o3,o4,answer)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (request.form["unit"],
         request.form["level"],
         request.form["question"],
         request.form["o1"],
         request.form["o2"],
         request.form["o3"],
         request.form["o4"],
         request.form["answer"]))
        conn.commit()
        return redirect("/admin")

    return render_template("add_quiz.html",units=units)

# ---------- SUBJECT LIST ----------
@app.route("/subjects")
def subjects():
    cur.execute("SELECT * FROM subjects")
    return render_template("subjects.html",subs=cur.fetchall())

# ---------- UNITS ----------
@app.route("/units/<int:sid>")
def units(sid):
    cur.execute("SELECT * FROM units WHERE subject_id=?",(sid,))
    return render_template("units.html",units=cur.fetchall())

# ---------- LEVEL SELECT ----------
@app.route("/levels/<int:uid>")
def levels(uid):
    return render_template("level.html",uid=uid)

# ---------- QUIZ ----------
@app.route("/quiz/<int:uid>/<level>",methods=["GET","POST"])
def quiz(uid,level):

    cur.execute("SELECT * FROM questions WHERE unit_id=? AND level=?",(uid,level))
    qs=cur.fetchall()

    if request.method=="POST":
        score=0

        for q in qs:
            if request.form.get(str(q["id"])) == q["answer"]:
                score+=1

        cur.execute("""
        INSERT INTO results(user_id,unit_id,level,score,total)
        VALUES(?,?,?,?,?)
        """,(session["uid"],uid,level,score,len(qs)))
        conn.commit()

        return f"Score: {score}/{len(qs)}"

    return render_template("quiz.html",qs=qs)

# ---------- VIEW RESULTS ----------
@app.route("/view_results")
def view_results():

    cur.execute("""
    SELECT users.name AS student,
           subjects.name AS subject,
           results.score,
           results.total,
           results.date
    FROM results
    JOIN users ON users.id = results.user_id
    JOIN units ON units.id = results.unit_id
    JOIN subjects ON subjects.id = units.subject_id
    ORDER BY results.score DESC
    """)
    results = cur.fetchall()

    cur.execute("""
    SELECT users.name AS name, MAX(score) AS score
    FROM results
    JOIN users ON users.id = results.user_id
    """)
    topper = cur.fetchone()

    return render_template("view_results.html",
                           results=results,
                           topper=topper)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run()


