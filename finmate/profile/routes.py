import os

from flask import render_template, request, url_for, flash, current_app
from flask_login import login_required, logout_user, current_user
from werkzeug.utils import redirect

from forms import ProfileForm, DeleteForm, CategoryForm
from finmate import db
from finmate.models import Transactions, Users, Category
from finmate.profile import bp


@bp.route('/', methods=['POST', 'GET'])
@login_required
def profile():
    form = ProfileForm(original_username=current_user.username)
    delete_form = DeleteForm()
    category_form = CategoryForm()

    if form.validate_on_submit():
        current_user.username = form.new_username.data
        current_user.avatar = form.avatar.data

        if form.new_password.data:
            current_user.set_hash_pwd(form.new_password.data)
            flash('Password successfully updated!', 'success')
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error during update: {e}', 'danger')
            return redirect(url_for('profile.profile'))

    elif request.method == 'GET':
        form.new_username.data  = current_user.username
        form.avatar.data = current_user.avatar


    categories = Category.query.filter_by(user_id=current_user.id)
    return render_template('profile.html',
                           form=form,
                           delete_form=delete_form,
                           categories=categories,
                           category_form=category_form
                           )


@bp.route('/category/add', methods=['POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        new_category = new_category = Category(
            mcc_code= form.mcc_codes.data,
            name=form.category_name.data,
            user_id=current_user.id
        )
        try:
            db.session.add(new_category)
            db.session.commit()
            flash('Category added!', category='success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('profile.profile'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{form[field].label.text}: {error}', 'danger')

    return redirect(url_for('profile.profile'))


@bp.route('/category/edit/<int:category_id>', methods=['POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.user_id != current_user.id:
        flash('','')
        return redirect(url_for('profile.profile'))

    form = CategoryForm()
    if form.validate_on_submit():
        category.name = form.category_name.data
        category.mcc_code = form.mcc_code.data
        try:
            db.session.commit()
            flash('Category updated!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {e}', 'danger')
            return redirect(url_for('profile.profile'))


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
