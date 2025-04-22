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

def load_users():
    if not os.path.exists(USER_FILE):
        # Create default user with hashed password
        default_users = {"user123": ("pass123")}
        with open(USER_FILE, 'w') as f:
            json.dump(default_users, f)
        return default_users
   
    try:
        with open(USER_FILE, 'r') as f:
            # Check if file is empty
            if os.path.getsize(USER_FILE) == 0:
                raise ValueError("File is empty")
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        # If file is corrupted or empty, recreate it
        default_users = {"user123": ("pass123")}
        with open(USER_FILE, 'w') as f:
            json.dump(default_users, f)
        return default_users

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)  # Added indent for better readability

# Initialize users with error handling
try:
    users = load_users()
except Exception as e:
    print(f"Error loading users: {e}")
    # Fallback to default users
    users = {"user123": ("pass123")}
    save_users(users)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Please enter both username and password")
        return redirect(url_for('login'))

    if username not in users:
        flash("User not found. Try again or create an account.")
        return redirect(url_for('login'))

    if users[username] == password:
        session['username'] = username
        return redirect(url_for('home'))
    else:
        flash("Incorrect password.")
        return redirect(url_for('login'))

@app.route('/create_account', methods=['POST'])
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
    # Ensure the users.json file exists and is valid
    if not os.path.exists(USER_FILE):
        save_users(users)
    app.run(host='0.0.0.0', port=5001, debug=False)
