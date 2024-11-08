# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from models import db, User
from werkzeug.security import check_password_hash

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.get(username)
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "auth-success")  # Using 'auth-' prefix for message category
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "auth-danger")  # Error message for login failure
    return render_template('login.html')

@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "auth-info")  # Message for successful logout
    return redirect(url_for('index'))

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.get(username)
        if existing_user:
            flash("Username already exists.", "auth-warning")  # Message for existing username
            return redirect(url_for('auth.register'))

        User.create_user(username, password)
        flash("Registration successful. Please log in.", "auth-success")  # Message for successful registration
        return redirect(url_for('auth.login'))
    return render_template('register.html')
