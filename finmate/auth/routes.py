from flask import render_template, request, url_for, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.utils import redirect

from finmate import db
from finmate.auth import bp
from finmate.decorators import anonymous_user_required
from finmate.models import Users, Category


@bp.route('/register', methods=['GET', 'POST'])
@anonymous_user_required
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    email = request.form.get('email')

    if request.method == "POST":
        if password == confirm_password:
            new_user = Users(username=username, email=email)
            user_by_username = Users.query.filter_by(username=username).first()
            if user_by_username:
                flash('This username is already taken. Please choose another.', category='danger')
                return redirect(url_for('auth.register'))

            user_by_email = Users.query.filter_by(email=email).first()
            if user_by_email:
                flash('This email is already registered. Please try to log in.', category='info')
                return redirect(url_for('auth.register'))

            new_user.set_hash_pwd(password)
            db.session.add(new_user)

            default_categories = ["Food", "Transport", "Entertainment", "Shopping", "Salary", "Utilities"]
            for category_name in default_categories:
                new_category = Category(name=category_name, user=new_user)
                db.session.add(new_category)

            db.session.commit()
            flash('You have successfully registered! Please log in.', category='success')
            return redirect(url_for('auth.login'))
        else:
            flash('Password is not correct', category='warning')
    return render_template('registration.html')


@bp.route('/login', methods=['GET', 'POST'])
@anonymous_user_required
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username and password:
            user = Users.query.filter_by(username=username).first()

            if user and user.chek_hash_pwd(password):
                login_user(user)
                return redirect(url_for('core.dashboard'))
            else:
                flash('Login or password is incorrect', category='danger')
        else:
            flash('Please fill in both fields', category='danger')

    return render_template('login.html')


@bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('core.home'))