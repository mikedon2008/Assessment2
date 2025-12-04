from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, date

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
                 timestamp TEXT)''')
    # Create admin account
    c.execute('INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)',
              ('nguyen.don225@education.nsw.gov.au', 'Duc10042008@', 1))
    conn.commit()
    conn.close()

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
            flash("Account created! You can now log in.")
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already taken!")
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
            return redirect(url_for('user_home'))
        flash("Wrong username or password!")
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
    if session.get('username') != 'nguyen.don225@education.nsw.gov.au':
        flash("Access Denied")
        return redirect(url_for('user_home'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT r.id, u.username, r.score, r.level, r.timestamp FROM records r JOIN users u ON r.user_id = u.id ORDER BY r.timestamp DESC")
    records = c.fetchall()
    conn.close()
    return render_template('super_admin_panel.html', records=records)

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
# NORMAL QUIZ — WITH WRONG ANSWERS + PERSONAL BEST
# ========================================
@app.route('/collectingdata', methods=['GET', 'POST'])
def collecting_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    correct = [2, 3, 1, 2, 1, 1, 2, 2, 2, 1]  # Canberra, Antarctica, China, Canada, Vatican, Uganda, Nepal&China, Pacific, Brasília, Australia
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

    # Get current personal best
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT MAX(score) FROM records WHERE user_id=?", (session['user_id'],))
    best = c.fetchone()[0]
    high_score = best if best else 0

    if request.method == 'POST':
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

        c.execute("INSERT INTO records (user_id, score, level, timestamp) VALUES (?,?,?,?)",
                  (session['user_id'], score, level, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()

        return render_template('collectingData.html',
                               submitted=True, score=score, level=level, perfect=perfect,
                               wrong_questions=wrong_questions, high_score=max(high_score, score))

    conn.close()
    return render_template('collectingData.html', submitted=False, high_score=high_score)

# ========================================
# ADVANCED QUIZ — WITH WRONG ANSWERS + PERSONAL BEST
# ========================================
@app.route('/advanced_quiz', methods=['GET', 'POST'])
def advanced_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    correct = [2, 2, 1, 2, 1, 1, 1, 1, 2, 0]  # Russia, France, Baikal, Danube, Iran, Russia&USA, Thimphu, Lesotho, Mid-Atlantic, Sahara
    options = [
        ["Switzerland", "Italy", "Russia", "France"],
        ["Russia", "United States", "France", "China"],
        ["Caspian Sea", "Lake Baikal", "Lake Tanganyika", "Crater Lake"],
        ["Nile", "Amazon", "Danube", "Rhine"],
        ["Iraq", "Iran", "Azerbaijan", "Turkmenistan"],
        ["USA & Canada", "Russia & USA", "Japan & Russia", "Norway & Sweden"],
        ["Kathmandu", "Thimphu", "Ulaanbaatar", "Bandar Seri Begawan"],
        ["Eswatini", "Lesotho", "Namibia", "Botswana"],
        ["Andes", "Himalayas", "Mid-Atlantic Ridge", "Rockies"],
        ["Sahara", "Arabian", "Gobi", "Kalahari"]
    ]

    # Get advanced personal best
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT MAX(score) FROM records WHERE user_id=? AND (level LIKE '%Advanced%' OR level LIKE '%GOD%' OR level LIKE '%Master%')", (session['user_id'],))
    best = c.fetchone()[0]
    high_score = best if best else 0

    if request.method == 'POST':
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
        
        c.execute("INSERT INTO records (user_id, score, level, timestamp) VALUES (?,?,?,?)",
                  (session['user_id'], score, level + " (Advanced)", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()

        return render_template('advanced_quiz.html',
                               submitted=True, score=score, level=level,
                               wrong_questions=wrong_questions, high_score=max(high_score, score))

    conn.close()
    return render_template('advanced_quiz.html', submitted=False, high_score=high_score)

# ========================================
# RUN APP
# ========================================
if __name__ == '__main__':
    init_db()
    app.run(debug=True)