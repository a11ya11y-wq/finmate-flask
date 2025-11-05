from datetime import date, timedelta

from flask import render_template, request, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import redirect

from cryptography.fernet import Fernet
from forms import DeleteForm, TransactionForm, CurrencyForm, ApiTokenForm
from finmate import db
from finmate.core import bp
from finmate.models import Transactions, Category

@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = TransactionForm()
    delete_form = DeleteForm()

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    form.category.choices = [(c.id, c.name) for c in categories]
    form.category.choices.insert(0, (0, 'Choose...'))

    if form.validate_on_submit():
        title = form.title.data
        transaction_type = form.type.data
        amount = form.amount.data
        created_at = form.date.data if form.date.data else date.today()
        category_id = form.category.data
        note = form.note.data

        new_transaction = Transactions(
            title=title,
            amount=amount,
            category_id=category_id,
            created_at=created_at,
            user_id=current_user.id,
            note=note,
            transaction_type=transaction_type
        )
        try:
            db.session.add(new_transaction)
            db.session.commit()
            flash("Transaction added successfully!", 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding transaction: {e}', 'danger')

        return redirect(url_for('core.dashboard'))
    base_query = Transactions.query.filter_by(user_id=current_user.id)
    today = date.today()
    period = request.args.get('period', 'all')

    if period == 'week':
        week_ago = today - timedelta(days=7)
        base_query = base_query.filter(Transactions.created_at >= week_ago)
    elif period == 'month':
        month_ago = today - timedelta(days=30)
        base_query = base_query.filter(Transactions.created_at >= month_ago)

    transactions = base_query.order_by(Transactions.created_at.desc()).limit(15).all()

    #Total expense/income
    total_income_by_period = base_query.filter(Transactions.transaction_type == 'income') \
                       .with_entities(func.sum(Transactions.amount)) \
                       .scalar() or 0.0

    total_expense_by_period = base_query.filter(Transactions.transaction_type == 'expense') \
                        .with_entities(func.sum(Transactions.amount)) \
                        .scalar() or 0.0

    base_query_without_period = Transactions.query.filter_by(user_id=current_user.id)

    # Current balance
    total_income = base_query_without_period.filter(Transactions.transaction_type == 'income') \
                       .with_entities(func.sum(Transactions.amount)) \
                       .scalar() or 0.0

    total_expense = base_query_without_period.filter(Transactions.transaction_type == 'expense') \
                        .with_entities(func.sum(Transactions.amount)) \
                        .scalar() or 0.0

    balance = total_income - total_expense

    expenses_by_category = base_query.filter(
        Transactions.transaction_type == 'expense'
    ).outerjoin(Category).group_by(Category.name).with_entities(
        Category.name,
        func.sum(Transactions.amount)
    ).order_by(func.sum(Transactions.amount).desc()).all()

    category_labels = [item[0] for item in expenses_by_category]
    category_amounts = [float(item[1]) for item in expenses_by_category]

    tr_for_balance = base_query.order_by(Transactions.created_at.asc()).all()
    balance_labels = []
    balance_data = []
    current_balance = 0.0

    for t in tr_for_balance:
        if t.transaction_type == 'income':
            current_balance += t.amount
        else:
            current_balance -= t.amount
        balance_labels.append(t.created_at.strftime('%Y-%m-%d'))
        balance_data.append(round(current_balance, 2))

    return render_template('dashboard.html',
                           transactions=transactions,
                           period=period,
                           categories=categories,
                           total_income=total_income_by_period,
                           total_expense=total_expense_by_period,
                           balance=balance,
                           category_labels=category_labels,
                           category_amounts=category_amounts,
                           balance_labels=balance_labels,
                           balance_data=balance_data,
                           form=form,
                           delete_form=delete_form
                           )


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():#TODO: Добавить функцию выкачивать данные в джсон файл або ссв
    form = CurrencyForm()
    token_form = ApiTokenForm()

    if token_form.validate_on_submit() and token_form.submit.data:
        #Шифровка моно токена при сохранении
        try:
            key = current_app.config['ENCRYPTION_KEY']

            cipher_suite = Fernet(key)

            token_bytes = token_form.token.data.encode()
            encrypted_token = cipher_suite.encrypt(token_bytes)
            current_user.monobank_api_token = encrypted_token


            db.session.commit()
            flash('Monobank API token saved!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Token saving error: {e}', 'danger')
            return redirect(url_for('core.settings'))

    if form.validate_on_submit() and form.submit.data:
        current_user.currency = form.currency.data
        try:
            db.session.commit()
            flash('Currency settings updated!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Save error: {e}', 'danger')
        return redirect(url_for('core.settings'))

    elif request.method == 'GET':
        form.currency.data = current_user.currency
    return render_template('settings.html', form=form, token_form=token_form)
