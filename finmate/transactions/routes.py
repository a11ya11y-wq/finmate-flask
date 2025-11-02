from datetime import datetime, timedelta

from flask import url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import redirect

from finmate.services.monobank_service import MonoAPI
from forms import  TransactionForm, DeleteForm
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


@bp.route('/sync', methods=['POST'])
@login_required
def sync_transaction():
    form = DeleteForm()

    if form.validate_on_submit():
        token = current_user.monobank_api_token
        if not token:
            flash('API token not found!', 'danger')
            return redirect(url_for('core.settings'))

        api = MonoAPI(api_token=token)
        client_info = api.get_client_info()

        if not client_info:
            flash('Invalid API token or Monobank error.','danger')
            return redirect(url_for('core.settings'))

        account_id = client_info['accounts'][0]['id']
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        from_time = int(thirty_days_ago.timestamp())

        transactions_from_mono = api.get_transactions(account_id, from_time)
        if not transactions_from_mono:
            flash('No new transactions found.', 'info')
            return redirect(url_for('core.dashboard'))

        mono_ids = {t['id'] for t in transactions_from_mono}

        existing_ids_query = db.session.query(Transactions.mono_id).filter(
            Transactions.user_id == current_user.id,
            Transactions.mono_id.in_(mono_ids)
        )
        existing_ids_set = {str(id_tuple[0]) for id_tuple in existing_ids_query}
        new_transactions_to_add = []

        for t_dict in transactions_from_mono:
            if t_dict['id'] not in existing_ids_set:
                new_trans = Transactions(
                    title=t_dict['description'],
                    amount=abs(t_dict['amount'] / 100.0),
                    created_at=datetime.fromtimestamp(t_dict['time']),
                    user_id=current_user.id,
                    mono_id=t_dict['id'],
                    transaction_type='income' if t_dict['amount'] > 0 else 'expense',
                    category_id = 1
                )
                new_transactions_to_add.append(new_trans)
        if not new_transactions_to_add:
            flash('Your transactions are up to date.', 'info')
            return redirect(url_for('core.dashboard'))
        try:
            db.session.add_all(new_transactions_to_add)
            db.session.commit()
            flash(f'Successfully added {len(new_transactions_to_add)} new transactions!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving new transactions: {e}', 'danger')
    else:
        flash('Invalid request.', 'danger')

    return  redirect(url_for('core.dashboard'))