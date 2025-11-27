from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'lawrence-is-the-goat-2025'

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
    c.execute('INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)',
              ('nguyen.don225@education.nsw.gov.au', 'Duc10042008@', 1))
    conn.commit()
    conn.close()

@app.route('/')
def index(): return redirect(url_for('login'))

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
            flash("Account created! Login now")
            conn.close()
            return redirect(url_for('login'))
        except:
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
            # Update last login
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE users SET last_login=? WHERE id=?", (date.today().strftime("%Y-%m-%d"), user[0]))
            conn.commit()
            conn.close()
            if username == 'nguyen.don225@education.nsw.gov.au':
                return redirect(url_for('admin_security'))
            return redirect(url_for('user_home'))
        flash("Wrong username/password")
    return render_template('login.html')

@app.route('/admin_security', methods=['GET', 'POST'])
def admin_security():
    if session.get('username') != 'nguyen.don225@education.nsw.gov.au':
        flash("Not allowed")
        return redirect(url_for('user_home'))
    if request.method == 'POST':
        if request.form.get('answer') == 'D':
            return redirect(url_for('super_admin_panel'))
        flash("WRONG ANSWER. BLOCKED.")
        return render_template('admin_security.html', blocked=True)
    return render_template('admin_security.html', blocked=False)

@app.route('/super_admin_panel')
def super_admin_panel():
    if session.get('username') != 'nguyen.don225@education.nsw.gov.au':
        return "NO.", 403
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT u.username, u.password, 
                        COALESCE(MAX(r.score),0), 
                        COUNT(r.id), 
                        u.last_login 
                 FROM users u LEFT JOIN records r ON u.id = r.user_id 
                 GROUP BY u.id''')
    users = c.fetchall()
    
    today = date.today().strftime("%Y-%m-%d")
    c.execute("SELECT u.username, COUNT(*) FROM records r JOIN users u ON r.user_id = u.id WHERE substr(r.timestamp,1,10)=? GROUP BY u.username", (today,))
    daily_dict = dict(c.fetchall())  # ← THIS WAS MISSING!
    
    conn.close()
    return render_template('super_admin_panel.html', users=users, daily_access=daily_dict, today=today)

@app.route('/userhome')
def user_home():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT score, level, timestamp FROM records WHERE user_id=? ORDER BY timestamp DESC", (session['user_id'],))
    records = c.fetchall()
    conn.close()
    return render_template('userHome.html', records=records, username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/collectingdata', methods=['GET', 'POST'])
def collecting_data():
    if 'user_id' not in session: return redirect(url_for('login'))
    correct = [2,3,1,1,1,1,2,1,2,1]
    if request.method == 'POST':
        score = sum(int(request.form.get(f'q{i}','0')) == correct[i] for i in range(10))
        level = "Geography God" if score==10 else "Expert" if score>=8 else "Good"
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO records (user_id, score, level, timestamp) VALUES (?,?,?,?)",
                  (session['user_id'], score, level, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        return render_template('collectingData.html', submitted=True, score=score, level=level, show_challenge=(score==10))
    return render_template('collectingData.html', submitted=False)

@app.route('/advanced_quiz', methods=['GET', 'POST'])
def advanced_quiz():
    if 'user_id' not in session: return redirect(url_for('login'))
    correct = [2,2,1,2,1,1,1,1,2,0]
    if request.method == 'POST':
        score = sum(int(request.form.get(f'q{i}','0')) == correct[i] for i in range(10))
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO records (user_id, score, level, timestamp) VALUES (?,?,?,?)",
                  (session['user_id'], score, "Advanced", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        return render_template('advancedCollectingData.html', submitted=True, score=score)
    return render_template('advancedCollectingData.html', submitted=False)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)