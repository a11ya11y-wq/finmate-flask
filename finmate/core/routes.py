from datetime import date, timedelta

from flask import render_template, request, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import redirect

from finmate import db
from finmate.core import bp
from finmate.models import Transactions, Category


@bp.route('/home')
@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    base_query = Transactions.query.filter_by(user_id=current_user.id)
    today = date.today()
    period = request.args.get('period', 'all')

    if period == 'week':
        week = today - timedelta(days=7)
        base_query = base_query.filter(Transactions.created_at >= week)
    elif period == 'month':
        month_ago = today - timedelta(days=30)
        base_query = base_query.filter(Transactions.created_at >= month_ago)
 # Карточки доходов і тд
    income = base_query.filter_by(transaction_type='income').all()
    total_income = sum([t.amount for t in income])

    expense = base_query.filter_by(transaction_type='expense').all()
    total_expense = sum([t.amount for t in expense])

    expenses_by_category = base_query.filter( # Пздц а не запрос
        Transactions.transaction_type == 'expense'
    ).join(Category).group_by(Category.name).with_entities(
        Category.name,
        func.sum(Transactions.amount)
    ).order_by(func.sum(Transactions.amount).desc()).all()

    balance = total_income - total_expense
#Pie-chart
    category_labels = [item[0] for item in expenses_by_category]
    category_amounts = [float(item[1]) for item in expenses_by_category]

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    transactions = base_query.order_by(Transactions.created_at.desc()).limit(15).all()

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
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           category_labels=category_labels,
                           category_amounts=category_amounts,
                           balance_labels=balance_labels,
                           balance_data=balance_data
                           )


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        currency = request.form.get('currency')
        if currency in ['USD', 'EUR', 'UAH']:
            current_user.currency = currency
            db.session.commit()
            flash('Currency settings updated!', 'success')
            return redirect(url_for('core.settings'))
        else:
            flash('Invalid currency selected.', 'danger')
    return render_template('settings.html')