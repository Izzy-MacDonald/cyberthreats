from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import json
import os
import hashlib
from collections import deque
import time

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'supersecretkey'  # In production, use environment variable

USER_FILE = 'users.json'

# Rate limiting storage
login_attempts = {}
account_creation_attempts = {}

def hash_password(password):
    """Hash password using SHA3-256"""
    return hashlib.sha3_256(password.encode('utf-8')).hexdigest()

def load_users():
    if not os.path.exists(USER_FILE):
        # Create default user with hashed password
        with open(USER_FILE, 'w') as f:
            json.dump({"user123": hash_password("pass123")}, f)
    with open(USER_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

users = load_users()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    ip = request.remote_addr
    now = time.time()
    
    # Track requests per IP (allow 5 attempts per minute)
    if ip not in login_attempts:
        login_attempts[ip] = deque(maxlen=5)
    
    if len(login_attempts[ip]) == 5 and now - login_attempts[ip][0] < 60:
        flash("Too many login attempts. Try again later.")
        return redirect(url_for('login'))
    
    login_attempts[ip].append(now)
    
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Please enter both username and password")
        return redirect(url_for('login'))

    if username not in users:
        flash("User not found. Try again or create an account.")
        return redirect(url_for('login'))

    if users[username] == hash_password(password):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        flash("Incorrect password.")
        return redirect(url_for('login'))

@app.route('/create_account', methods=['POST'])
def create_account():
    ip = request.remote_addr
    now = time.time()
    
    # Track account creation attempts (allow 3 per hour)
    if ip not in account_creation_attempts:
        account_creation_attempts[ip] = deque(maxlen=3)
    
    if len(account_creation_attempts[ip]) == 3 and now - account_creation_attempts[ip][0] < 3600:
        flash("Too many account creation attempts. Try again later.")
        return redirect(url_for('login'))
    
    account_creation_attempts[ip].append(now)
    
    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')

    if not new_username or not new_password:
        flash("Please enter a valid username and password.")
        return redirect(url_for('login'))

    if new_username in users:
        flash("Username already exists.")
        return redirect(url_for('login'))

    users[new_username] = hash_password(new_password)
    save_users(users)
    flash(f"Account created successfully for {new_username}")
    return redirect(url_for('login'))

@app.route('/home_page.html')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home_page.html')

@app.route('/Top_Secret.txt')
def top_secret():
    if 'username' not in session:
        return redirect(url_for('login'))
    return send_from_directory('static', 'Top_Secret.txt')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)  # debug=False in production