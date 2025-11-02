
from flask import request, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import redirect

from forms import  TransactionForm
from finmate import db
from finmate.models import Transactions, Category
from finmate.transactions import bp


@bp.route('/edit/<int:transaction_id>', methods=['POST'])
@login_required
def edit_transaction(transaction_id):
    form = TransactionForm()
    transaction = Transactions.query.get_or_404(transaction_id)

    if transaction.user_id != current_user.id:
        flash('You do not have permission to edit this transaction.', 'danger')
        return redirect(url_for('core.dashboard'))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category.choices = [
        (c.id, c.name) for c in categories
    ]
    form.category.choices.insert(0, (0, 'Choose...'))

    if form.validate_on_submit():
        transaction.title = form.title.data
        transaction.amount = form.amount.data
        transaction.category_id = form.category.data
        transaction.note = form.note.data
        transaction.transaction_type = form.type.data
        if form.date.data:
            transaction.created_at = form.date.data

        try:
            db.session.commit()
            flash('Transaction updated!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating transaction: {e}', 'danger')
        return redirect(url_for('core.dashboard'))

    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{form[field].label.text}: {error}', 'danger')
        return redirect(url_for('core.dashboard'))



@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transactions.query.get(id)
    if transaction:
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction deleted successfully."

, category='success')

    return redirect(url_for('core.dashboard'))