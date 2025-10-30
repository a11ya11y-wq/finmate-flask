import calendar
from datetime import datetime, timezone

from flask import render_template, request, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import redirect

from finmate import db
from finmate.budgets import bp
from finmate.models import Transactions, Category, Budget


@bp.route('/', methods=['GET'])
@login_required
def budgets():
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    user_budgets = Budget.query.filter_by(user_id=current_user.id).all()
    budgets_data = []

    recurring_budgets = [b for b in user_budgets if b.is_recurring]
    recurring_ids = [b.category_id for b in recurring_budgets]

    today = datetime.now(timezone.utc)
    start_of_month = today.replace(day=1,hour=0,minute=0,second=0,microsecond=0)

    spent_map = {}

    if recurring_ids:
        recurring_expenses_query = (db.session.query(
            Transactions.category_id,
            func.sum(Transactions.amount).label('total_spent')
        ).filter(
                Transactions.user_id == current_user.id,
                Transactions.transaction_type == 'expense',
                Transactions.created_at >= start_of_month,
                Transactions.category_id.in_(recurring_ids)
            ).group_by(Transactions.category_id).all())

        spent_map = {item.category_id: float(item.total_spent) for item in recurring_expenses_query}

    for budget in user_budgets:

        if budget.is_recurring:
            total_spent = spent_map.get(budget.category_id, 0.0) #вернет 0.0, если трат не было
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            days_left = days_in_month - today.day

            if days_left > 1:
                deadline_info = f"{days_left} days left"
            elif days_left == 1:
                deadline_info = "1 day left"
            else:
                deadline_info = "Ends today"

        else:
            total_spent = db.session.query(db.func.sum(Transactions.amount)).filter(
                Transactions.category_id == budget.category_id,
                Transactions.user_id == current_user.id,
                Transactions.transaction_type == 'expense',
                Transactions.created_at >= budget.created_at
            ).scalar() or 0.0
            total_spent = float(total_spent)

            aware_created_at = budget.created_at.replace(tzinfo=timezone.utc)
            delta = today - aware_created_at
            days_active = delta.days

            if days_active > 1:
                deadline_info = f"Active for {days_active} days"
            elif days_active == 1:
                deadline_info = "Active for 1 day"
            else:
                deadline_info = "Started today"

        percentage = 0
        if budget.amount > 0:
            percentage = (total_spent / float(budget.amount)) * 100
        remaining = float(budget.amount) - total_spent

        budgets_data.append({
            'budget': budget,
            'total_spent': total_spent,
            'percentage': percentage,
            'remaining': remaining,
            'deadline_info': deadline_info
        })

    return render_template('budget.html',
                           categories=categories,
                           budgets_data=budgets_data
                           )


@bp.route('/add', methods=['POST'])
@login_required
def add_budgets():
    if request.method=='POST':
        amount_str = request.form.get('amount')
        category_id_str = request.form.get('category')
        is_recurring_str = request.form.get('is_recurring')

        try:
            amount = float(amount_str)
            category_id = int(category_id_str)
            is_recurring = bool(is_recurring_str)
        except ValueError:
            flash('Invalid amount or category format.', 'danger')
            return redirect(url_for('budget.budgets'))

        budget_exist = Budget.query.filter_by(user_id=current_user.id,
                                              category_id=category_id).first()

        if budget_exist:
            budget_exist.amount = amount
            budget_exist.is_recurring = is_recurring
            flash('Budget updated!', 'success')
        else:
            new_budget=Budget(
                amount=amount,
                category_id=category_id,
                is_recurring=is_recurring,
                user_id=current_user.id
            )
            db.session.add(new_budget)
            flash('Budget added!', 'success')
        db.session.commit()
    return redirect(url_for('budget.budgets'))


@bp.route('/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    budget_to_delete = Budget.query.get(budget_id)
    if budget_to_delete.user_id != current_user.id:
        flash('You do not have permission to delete this budget.', 'danger')
        return redirect(url_for('budget.budgets'))
    if budget_to_delete:
        db.session.delete(budget_to_delete)
        db.session.commit()
        flash('Budget deleted successfully.', category='success')
    return redirect(url_for('budget.budgets'))