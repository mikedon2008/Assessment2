from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import os

if os.environ.get('RENDER'):
    from waitress import serve

app = Flask(__name__)
app.secret_key = 'mikedon-geography-quiz-final-2025'

# ========================================
# DATABASE SETUP
# ========================================
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 is_admin INTEGER DEFAULT 0,
                 last_login TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS records (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 score INTEGER,
                 level TEXT,
                 timestamp TEXT,
                 time_taken INTEGER DEFAULT 0)''')
    c.execute('INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)',
              ('nguyen.don225@education.nsw.gov.au', 'Duc10042008@', 1))
    conn.commit()
    conn.close()

# Helper: check if user is admin
def is_user_admin(username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

# ========================================
# ROUTES
# ========================================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Account created!")
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username taken!")
        conn.close()
    return render_template('signUp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, username, is_admin FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = bool(user[2])

            if username == 'nguyen.don225@education.nsw.gov.au':
                return redirect(url_for('admin_security'))
            elif session['is_admin']:
                return redirect(url_for('super_admin_panel'))
            else:
                return redirect(url_for('user_home'))
        flash("Wrong username/password")
    return render_template('login.html')

@app.route('/admin_security', methods=['GET', 'POST'])
def admin_security():
    if session.get('username') != 'nguyen.don225@education.nsw.gov.au':
        return redirect(url_for('user_home'))
    if request.method == 'POST':
        if request.form.get('answer') == 'D':
            return redirect(url_for('super_admin_panel'))
        flash("WRONG! NOT MIKEDON.")
    return render_template('admin_security.html')

@app.route('/super_admin_panel')
def super_admin_panel():
    if 'username' not in session:
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        flash("Access Denied — Admin rights required")
        return redirect(url_for('user_home'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""SELECT r.id, u.username, r.score, r.level, r.timestamp, r.time_taken
                 FROM records r JOIN users u ON r.user_id = u.id
                 ORDER BY r.timestamp DESC""")
    records = c.fetchall()
    conn.close()

    return render_template('super_admin_panel.html', records=records, is_admin=is_user_admin)

@app.route('/make_admin/<username>', methods=['POST'])
def make_admin(username):
    if session.get('username') != 'nguyen.don225@education.nsw.gov.au':
        flash("Only Super Admin can promote users.")
        return redirect(url_for('user_home'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
    if c.rowcount > 0:
        conn.commit()
        flash(f"{username} is now an Admin.")
    else:
        flash("User not found.")
    conn.close()
    return redirect(url_for('super_admin_panel'))

@app.route('/remove_admin/<username>', methods=['POST'])
def remove_admin(username):
    if session.get('username') != 'nguyen.don225@education.nsw.gov.au':
        flash("Only Super Admin can remove admin rights.")
        return redirect(url_for('user_home'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_admin = 0 WHERE username = ?", (username,))
    if c.rowcount > 0:
        conn.commit()
        flash(f"{username} is no longer an admin.")
    else:
        flash("User not found.")
    conn.close()
    return redirect(url_for('super_admin_panel'))

@app.route('/userhome')
def user_home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT score, level, timestamp FROM records WHERE user_id=? ORDER BY timestamp DESC", (session['user_id'],))
    records = c.fetchall()
    conn.close()
    return render_template('userHome.html', username=session['username'], records=records)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ========================================
# NORMAL QUIZ
# ========================================
@app.route('/collectingdata', methods=['GET', 'POST'])
def collecting_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    correct = [2, 3, 1, 2, 1, 1, 2, 2, 2, 1]
    options = [
        ["Sydney", "Melbourne", "Canberra", "Brisbane"],
        ["Asia", "Africa", "Australia", "Antarctica"],
        ["Japan", "China", "India", "Mongolia"],
        ["Australia", "Indonesia", "Canada", "Russia"],
        ["Monaco", "Vatican City", "San Marino", "Liechtenstein"],
        ["Kenya", "Uganda", "Tanzania", "Rwanda"],
        ["India & China", "Nepal & India", "Nepal & China", "Bhutan & China"],
        ["Atlantic", "Indian", "Pacific", "Arctic"],
        ["Rio de Janeiro", "São Paulo", "Brasília", "Salvador"],
        ["New Zealand", "Australia", "South Africa", "Indonesia"]
    ]

    if request.method == 'GET':
        session['quiz_start_time'] = datetime.now().timestamp()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT MAX(score) FROM records WHERE user_id=?", (session['user_id'],))
    best = c.fetchone()[0]
    high_score = best if best else 0

    if request.method == 'POST':
        start_time = session.get('quiz_start_time', datetime.now().timestamp())
        time_taken = int(datetime.now().timestamp() - start_time)
        score = 0
        wrong_questions = []
        for i in range(10):
            ans = request.form.get(f'q{i}')
            if ans and int(ans) == correct[i]:
                score += 1
            else:
                wrong_questions.append({
                    'num': i+1,
                    'your_answer': options[i][int(ans)] if ans else "No answer",
                    'correct_answer': options[i][correct[i]]
                })

        level = "Geography God" if score == 10 else "Expert" if score >= 8 else "Good" if score >= 6 else "Beginner"
        perfect = (score == 10)

        c.execute("INSERT INTO records (user_id, score, level, timestamp, time_taken) VALUES (?,?,?,?,?)",
                  (session['user_id'], score, level, datetime.now().strftime("%Y-%m-%d %H:%M"), time_taken))
        conn.commit()
        conn.close()
        session.pop('quiz_start_time', None)

        return render_template('collectingData.html',
                               submitted=True, score=score, level=level, perfect=perfect,
                               wrong_questions=wrong_questions, high_score=max(high_score, score),
                               time_taken=time_taken)

    conn.close()
    return render_template('collectingData.html', submitted=False, high_score=high_score)

# ========================================
# ADVANCED QUIZ — FIXED: Antarctica is correct for most desert area
# ========================================
@app.route('/advanced_quiz', methods=['GET', 'POST'])
def advanced_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    correct = [2, 3, 1, 2, 1, 1, 1, 1, 2, 0]  # Q2 correct = Antarctica (index 3)
    options = [
        ["Switzerland", "Italy", "Russia", "France"],
        ["Australia", "Africa", "Asia", "Antarctica"],  # Antarctica is correct
        ["Caspian Sea", "Lake Baikal", "Lake Tanganyika", "Crater Lake"],
        ["Nile", "Amazon", "Danube", "Rhine"],
        ["Iraq", "Iran", "Azerbaijan", "Turkmenistan"],
        ["USA & Canada", "Russia & USA", "Japan & Russia", "Norway & Sweden"],
        ["Kathmandu", "Thimphu", "Ulaanbaatar", "Bandar Seri Begawan"],
        ["Eswatini", "Lesotho", "Namibia", "Botswana"],
        ["Andes", "Himalayas", "Mid-Atlantic Ridge", "Rockies"],
        ["Sahara", "Arabian", "Gobi", "Kalahari"]
    ]

    if request.method == 'GET':
        session['quiz_start_time'] = datetime.now().timestamp()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT MAX(score) FROM records WHERE user_id=? AND (level LIKE '%Advanced%' OR level LIKE '%GOD%' OR level LIKE '%Master%')", (session['user_id'],))
    best = c.fetchone()[0]
    high_score = best if best else 0

    if request.method == 'POST':
        start_time = session.get('quiz_start_time', datetime.now().timestamp())
        time_taken = int(datetime.now().timestamp() - start_time)
        score = 0
        wrong_questions = []
        for i in range(10):
            ans = request.form.get(f'q{i}')
            if ans and int(ans) == correct[i]:
                score += 1
            else:
                wrong_questions.append({
                    'num': i+1,
                    'your_answer': options[i][int(ans)] if ans else "No answer",
                    'correct_answer': options[i][correct[i]]
                })

        level = "GEOGRAPHY GOD" if score == 10 else "Master" if score >= 8 else "Advanced Challenger"

        c.execute("INSERT INTO records (user_id, score, level, timestamp, time_taken) VALUES (?,?,?,?,?)",
                  (session['user_id'], score, level + " (Advanced)", datetime.now().strftime("%Y-%m-%d %H:%M"), time_taken))
        conn.commit()
        conn.close()
        session.pop('quiz_start_time', None)

        return render_template('advanced_quiz.html',
                               submitted=True, score=score, level=level,
                               wrong_questions=wrong_questions, high_score=max(high_score, score),
                               time_taken=time_taken)

    conn.close()
    return render_template('advanced_quiz.html', submitted=False, high_score=high_score)

# ========================================
# RUN APP
# ========================================
if __name__ == '__main__':
    init_db()
    if not os.environ.get('RENDER'):
        print("Running locally — Flask debug server")
        app.run(host='0.0.0.0', port=8000, debug=True)
    else:
        print("Deployed on Render.com — using Waitress")
        serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))