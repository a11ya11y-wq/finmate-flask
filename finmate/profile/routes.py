import os

from flask import render_template, request, url_for, flash, current_app
from flask_login import login_required, logout_user, current_user
from werkzeug.utils import redirect

from finmate import db
from finmate.models import Transactions, Users, Category
from finmate.profile import bp


@bp.route('/', methods=['POST', 'GET'])
@login_required
def profile():
    default_avatars_path = os.path.join(current_app.static_folder, 'avatars/default')
    default_avatars = os.listdir(default_avatars_path)
    categories =  Category.query.filter_by(user_id=current_user.id)

    if request.method == 'POST':
        new_username = request.form.get('username')
        if new_username and new_username != current_user.username:
            existing_user = Users.query.filter_by(username=new_username).first()
            if existing_user:
                flash(f"Username '{new_username}' is already taken. Please choose another one.", 'danger')
            else:
                current_user.username = new_username
                flash('Username updated!', category='success')

        selected_avatar = request.form.get('default_avatar')
        if selected_avatar:
            new_avatar_path = f'avatars/default/{selected_avatar}'
            if new_avatar_path != current_user.avatar:
                current_user.avatar = new_avatar_path
                flash('Avatar updated!', category='success')

        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        if old_password and new_password:
            if current_user.chek_hash_pwd(old_password):
                current_user.set_hash_pwd(new_password)
                flash("Password updated!", category='success')
            else:
                flash('Incorect password', category='danger')

        db.session.commit()
        return redirect(url_for('profile.profile'))
    return render_template('profile.html',
                           default_avatars=default_avatars,
                           categories=categories
                           )


@bp.route('/category/add', methods=['POST'])
@login_required
def add_category():
    name = request.form['category_name']
    user_id = current_user.id
    # category = Category.query.filter_by(name).first()
    if name:
        exist = Category.query.filter_by(name=name,user_id=user_id).first()
        if not exist:
            new_category = Category(
                name=name,
                user_id=user_id
            )
            db.session.add(new_category)
            db.session.commit()
            flash('Category added!', category='success')
        else:
            flash('Category already exists.', category='warning')
    return redirect(url_for('profile.profile'))


@bp.route('/category/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category_todelete = Category.query.get(category_id)
    transaction_exists = Transactions.query.filter_by(category_id=category_id).first()
    if category_todelete:
        if transaction_exists:
            flash('Cannot delete this category because it is linked to existing transactions.', category='danger')
            return redirect(url_for('profile.profile'))
        if category_todelete.user_id != current_user.id:
            return "Access denied", 403
        db.session.delete(category_todelete)
        db.session.commit()
        flash('Category deleted!', 'success')
    return redirect(url_for('profile.profile'))


@bp.route('/delete', methods=['POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        user_to_delete = Users.query.get(current_user.id)
        logout_user()
        db.session.delete(user_to_delete)
        db.session.commit()
    flash('Your account and all associated data have been permanently deleted.', 'success')
    return redirect(url_for('core.home'))
