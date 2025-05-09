from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import json
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'supersecretkey'  # Needed for session and flash messages

USER_FILE = 'users.json'

# Load users from file or create default user
def load_users():
    if not os.path.exists(USER_FILE):
        # Create a default user
        with open(USER_FILE, 'w') as f:
            json.dump({"user123": "pass123"}, f)
    with open(USER_FILE, 'r') as f:
        return json.load(f)

# Save users to file
def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

users = load_users()

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

    users[new_username] = new_password
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
    return send_from_directory('static', 'Top_Secret.txt')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
