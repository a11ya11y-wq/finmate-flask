from datetime import date
from datetime import date

from flask import request, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import redirect

from finmate import db
from finmate.models import Transactions
from finmate.transactions import bp


@bp.route('/add', methods=['POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        title = request.form.get('title')
        amount = request.form.get('amount')
        category_id = request.form.get('category_id')
        created_at = request.form.get('created_at')
        note = request.form.get('note')
        transaction_type = request.form.get('transaction_type')

        if created_at == '':
            created_at = date.today()

        if not title or not amount or not category_id:
            flash('Please enter all fields.',category='warning')
            return redirect(url_for('core.dashboard'))

        new_transaction = Transactions(
            title=title,
            amount=amount,
            category_id=category_id,
            created_at=created_at,
            user=current_user,
            note=note,
            transaction_type=transaction_type
        )
        db.session.add(new_transaction)
        db.session.commit()
        flash("Transaction added successfully!", category='success')

    return redirect(url_for('core.dashboard'))


@bp.route('/edit/<int:transaction_id>', methods=['POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transactions.query.get_or_404(transaction_id)
    if transaction.user_id != current_user.id:
        return 'Error', 403

    transaction.title = request.form.get('title')
    transaction.amount = request.form.get('amount')
    transaction.category_id = request.form.get('category_id')
    transaction.created_at = request.form.get('created_at')
    transaction.note = request.form.get('note')
    transaction.transaction_type = request.form.get('transaction_type')

    db.session.commit()
    flash('Transaction updated!', 'success')

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