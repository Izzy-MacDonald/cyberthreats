from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import os
import hashlib

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'supersecretkey'  # Use env var in production

# Rate limiting setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

USER_FILE = 'users.json'

# Load users from file, handle empty/corrupt file
def load_users():
    if not os.path.exists(USER_FILE):
        default_users = {"user123": "pass123"}
        save_users(default_users)
        return default_users
    try:
        if os.path.getsize(USER_FILE) == 0:
            raise ValueError("File is empty")
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        default_users = {"user123": "pass123"}
        save_users(default_users)
        return default_users

# Save users to file with indent
def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Initialize user data
users = load_users()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Please enter both username and password")
        return redirect(url_for('login'))

    if username not in users:
        flash("User not found. Try again or create an account.")
        return redirect(url_for('login'))

    if users[username] == hashlib.sha3_256(password.encode('utf-8')).hexdigest():
        session['username'] = username
        return redirect(url_for('home'))
    else:
        flash("Incorrect password.")
        return redirect(url_for('login'))

@app.route('/create_account', methods=['POST'])
@limiter.limit("3 per hour")
def create_account():
    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')

    if not new_username or not new_password:
        flash("Please enter a valid username and password.")
        return redirect(url_for('login'))

    if new_username in users:
        flash("Username already exists.")
        return redirect(url_for('login'))

    hashed = hashlib.sha3_256(new_password.encode('utf-8')).hexdigest()
    users[new_username] = hashed
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
    if not os.path.exists(USER_FILE):
        save_users(users)
    app.run(host='0.0.0.0', port=5001, debug=False)
