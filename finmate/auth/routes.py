from flask import render_template, request, url_for, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.utils import redirect

from forms import LoginForm, RegistrationForm, DeleteForm
from finmate import db
from finmate.auth import bp
from finmate.decorators import anonymous_user_required
from finmate.models import Users, Category


@bp.route('/register', methods=['GET', 'POST'])
@anonymous_user_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = Users(username=form.username.data, email=form.email.data)
        new_user.set_hash_pwd(form.password.data)
        try:
            db.session.add(new_user)
            default_categories_with_mcc = [
                ('Food', '5411, 5812, 5814, 5499'),
                ('Transport', '5541, 5542, 4121, 4111, 4784'),
                ('Entertainment', '5813, 7832, 7922, 7996, 7999'),
                ('Shopping', '5311, 5691, 5732, 5912, 5941, 5942'),
                ('Utilities', '4900, 4814, 4899'),
                ('Salary', None),
                ('Uncategorized', None)
            ]
            for cat_name, mcc_code in default_categories_with_mcc:
                new_category = Category(name=cat_name, user=new_user, mcc_code=mcc_code)
                db.session.add(new_category)

            db.session.commit()
            flash('You have successfully registered! Please log in.', category='success')
            return redirect(url_for('auth.login'))

        except Exception as e:

            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'danger')

    return render_template('registration.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
@anonymous_user_required
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()

        if user and user.chek_hash_pwd(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('core.dashboard'))
        else:
            flash('Login or password is incorrect', 'danger')
            return redirect(url_for('auth.login'))
    return render_template('login.html', form=form)


@bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    form = DeleteForm()
    logout_user()
    flash('You have logged out of the system.', 'success')
    return redirect(url_for('auth.login'))