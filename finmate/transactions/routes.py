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
def sync_transaction():#TODO: Захист від спаму (в бд добавить ласт_моно_реквест(Дейттайм))
    form = DeleteForm()

    if form.validate_on_submit():

        token_bytes = current_user.monobank_api_token

        if not token_bytes:
            flash('API token not found! Please add it in the settings.','danger')
            return redirect(url_for('core.dashboard'))

        try:
            api = MonoAPI(encrypted_token_bytes=token_bytes)
            client_info = api.get_client_info()
        except Exception as e:
            flash(f'Error processing token: {e}. Please update your token.', 'danger')
            return redirect(url_for('core.dashboard'))

        if not client_info or 'accounts' not in client_info:
            error_msg = client_info.get('errorDescription', 'Invalid API token') if isinstance(client_info,
                                                                                               dict) else 'Invalid API token'
            flash(f'Monobank Error: {error_msg}', 'danger')
            return redirect(url_for('core.dashboard'))

        account_id = client_info['accounts'][0]['id']
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        from_time = int(thirty_days_ago.timestamp())

        transactions_from_mono = api.get_transactions(account_id, from_time)

        if isinstance(transactions_from_mono, dict):
            error_msg = transactions_from_mono.get('errorDescription', 'Unknown API Error')
            if error_msg == 'Too many requests':
                flash('Too many requests! The Monobank API allows 1 request per minute. Please wait.', 'warning')
            else:
                flash(f'API Error: {error_msg}', 'danger')

            return redirect(url_for('core.dashboard'))

        if transactions_from_mono is None:
            flash('Error connecting to Monobank API. Please try again in a moment.', 'danger')
            return redirect(url_for('core.dashboard'))

        if not transactions_from_mono:
            flash('No new transactions found.', 'info')
            return redirect(url_for('core.dashboard'))

        default_category = Category.query.filter_by(user_id=current_user.id, name="Uncategorized").first()

        if not default_category:
            default_category = Category(name="Uncategorized", user_id=current_user.id)
            db.session.add(default_category)
            try:
                db.session.commit()
            except Exception as e :
                db.session.rollback()
                flash(f'Could not create default category. {e}', 'danger')
                return redirect(url_for('core.dashboard'))

        default_category_id = default_category.id
        mcc_map = {}
        all_categories = Category.query.filter(Category.user_id == current_user.id).all()

        for cat in all_categories:
            if cat.mcc_code:
                codes = cat.mcc_code.split(',')
                for code in codes:
                    mcc_map[code.strip()] = cat.id

        mono_ids = {t['id'] for t in transactions_from_mono}

        existing_ids_query = db.session.query(Transactions.mono_id).filter(
            Transactions.user_id == current_user.id,
            Transactions.mono_id.in_(mono_ids)
        )

        existing_ids_set = {str(id_tuple[0]) for id_tuple in existing_ids_query}
        new_transactions_to_add = []

        for t_dict in transactions_from_mono:
            if t_dict['id'] not in existing_ids_set:

                mcc_code_str = str(t_dict.get('mcc', ''))
                assigned_category_id = mcc_map.get(mcc_code_str, default_category_id)

                new_trans = Transactions(
                    title=t_dict['description'],
                    amount=abs(t_dict['amount'] / 100.0),
                    created_at=datetime.fromtimestamp(t_dict['time']),
                    user_id=current_user.id,
                    mono_id=t_dict['id'],
                    transaction_type='income' if t_dict['amount'] > 0 else 'expense',
                    category_id =assigned_category_id
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