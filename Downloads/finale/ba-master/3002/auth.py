from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from models import db, User

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate missing fields
        if not username:
            flash("Username is required.", "auth-danger")
            return render_template('login.html')
        if not password:
            flash("Password is required.", "auth-danger")
            return render_template('login.html')

        # Validate user credentials
        user = User.get(username)
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "auth-success")
            return redirect(url_for('index'))  # Redirect to homepage
        else:
            flash("Invalid username or password.", "auth-danger")
            return render_template('login.html')  # Reload login page with error

    return render_template('login.html')  # Render login form for GET requests

@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "auth-info")
    return redirect(url_for('index'))  # Redirect to homepage

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate missing fields
        if not username:
            flash("Username is required.", "auth-danger")
            return render_template('register.html')
        if not password:
            flash("Password is required.", "auth-danger")
            return render_template('register.html')

        # Check if the user already exists
        existing_user = User.get(username)
        if existing_user:
            flash("Username already exists.", "auth-warning")
            return render_template('register.html')

        # Create a new user
        try:
            User.create_user(username, password)
            flash("Registration successful. Please log in.", "auth-success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f"An error occurred during registration: {str(e)}", "auth-danger")
            return render_template('register.html')

    return render_template('register.html')  # Render registration form for GET requests
