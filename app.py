from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2
import psycopg2.extras
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# 🔥 DATABASE
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

# ---------------- INIT DB ---------------- #

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subjects(
        id SERIAL PRIMARY KEY,
        name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS units(
        id SERIAL PRIMARY KEY,
        subject_id INTEGER REFERENCES subjects(id),
        name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS materials(
        id SERIAL PRIMARY KEY,
        unit_id INTEGER REFERENCES units(id),
        content TEXT,
        video_link TEXT,
        pdf_file TEXT,
        image_url TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id SERIAL PRIMARY KEY,
        unit_id INTEGER REFERENCES units(id),
        question TEXT,
        o1 TEXT,
        o2 TEXT,
        o3 TEXT,
        o4 TEXT,
        answer TEXT,
        time_limit INTEGER,
        level TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS results(
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        unit_id INTEGER REFERENCES units(id),
        score INTEGER,
        total INTEGER
    )
    """)

    # default admin
    cur.execute("""
    INSERT INTO users (name,email,password,role)
    SELECT 'Admin','admin@gmail.com', %s, 'admin'
    WHERE NOT EXISTS (SELECT 1 FROM users WHERE email='admin@gmail.com')
    """, (generate_password_hash("admin123"),))

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ---------------- AUTH ---------------- #

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (request.form['email'],))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect('/admin_panel' if user['role']=='admin' else '/subjects')

        return "Invalid login"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO users (name,email,password,role)
            VALUES (%s,%s,%s,%s)
            """, (
                request.form['name'],
                request.form['email'],
                generate_password_hash(request.form['password']),
                'student'
            ))

            conn.commit()
            cur.close()
            conn.close()
            return redirect('/login')
        except:
            return "Email already exists ❌"

    return render_template('register.html')

# ---------------- ADMIN ---------------- #

@app.route('/admin_panel')
def admin_panel():
    return render_template('admin_panel.html')

# ---------------- SUBJECT ---------------- #

@app.route('/add_subject', methods=['GET','POST'])
def add_subject():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()

        cur.execute("INSERT INTO subjects(name) VALUES(%s)", (request.form['subject_name'],))
        conn.commit()

        cur.close()
        conn.close()

        return redirect('/manage_subjects')

    return render_template('add_subject.html')

@app.route('/manage_subjects')
def manage_subjects():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM subjects")
    subjects = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('manage_subjects.html', subjects=subjects)

# ---------------- UNIT ---------------- #

@app.route('/add_unit', methods=['GET','POST'])
def add_unit():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM subjects")
    subjects = cur.fetchall()

    if request.method == 'POST':
        cur.execute("INSERT INTO units(subject_id,name) VALUES(%s,%s)",
                    (request.form['subject_id'], request.form['unit_name']))
        conn.commit()

        cur.close()
        conn.close()

        return redirect('/manage_units')

    return render_template('add_unit.html', subjects=subjects)

@app.route('/manage_units')
def manage_units():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT units.*, subjects.name AS subject_name
    FROM units
    JOIN subjects ON subjects.id = units.subject_id
    """)

    units = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('manage_units.html', units=units)

# ---------------- MATERIAL ---------------- #

@app.route('/add_material', methods=['GET','POST'])
def add_material():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM units")
    units = cur.fetchall()

    if request.method == 'POST':
        cur.execute("""
        INSERT INTO materials(unit_id,content,video_link,pdf_file,image_url)
        VALUES(%s,%s,%s,%s,%s)
        """, (
            request.form['unit_id'],
            request.form['content'],
            request.form['video_link'],
            request.form['pdf_file'],
            request.form['image_url']
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect('/manage_materials')

    return render_template('add_material.html', units=units)

# ---------------- QUIZ ---------------- #

@app.route('/add_quiz', methods=['GET','POST'])
def add_quiz():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM units")
    units = cur.fetchall()

    if request.method == 'POST':
        cur.execute("""
        INSERT INTO questions(unit_id,question,o1,o2,o3,o4,answer,time_limit,level)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form['unit_id'],
            request.form['question'],
            request.form['o1'],
            request.form['o2'],
            request.form['o3'],
            request.form['o4'],
            request.form['answer'],
            request.form['time_limit'],
            request.form.get('level')
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect('/admin_panel')

    return render_template('add_quiz.html', units=units)

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
