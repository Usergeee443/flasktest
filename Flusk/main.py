from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Session uchun maxfiy kalit

def get_db_connection():
    return mysql.connector.connect(
        host="195.200.29.240",     # MySQL server manzili
        user="db", # MySQL foydalanuvchi nomi
        password="33608540414", # MySQL paroli
        database="flask_tests"  # MySQL bazasi nomi
    )

# Login talab qilinadigan sahifalar uchun dekorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT a.*, u.username FROM advertisements a JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC")
    ads = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', ads=ads)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                         (username, hashed_password))
            conn.commit()
            flash('Muvaffaqiyatli ro\'yxatdan o\'tdingiz!', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Bu foydalanuvchi nomi band!', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        flash('Noto\'g\'ri login yoki parol!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM advertisements WHERE user_id = %s ORDER BY created_at DESC", 
                  (session['user_id'],))
    ads = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('profile.html', ads=ads)

@app.route('/create_ad', methods=['GET', 'POST'])
@login_required
def create_ad():
    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        description = request.form['description']
        phone_number = request.form['phone_number']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO advertisements (user_id, title, price, description, phone_number)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], title, price, description, phone_number))
        conn.commit()
        cursor.close()
        conn.close()
        flash('E\'lon muvaffaqiyatli yaratildi!', 'success')
        return redirect(url_for('profile'))
    return render_template('create_ad.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)