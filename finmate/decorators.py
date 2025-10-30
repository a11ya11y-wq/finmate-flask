from functools import wraps

from flask import redirect, url_for, flash
from flask_login import current_user


def anonymous_user_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash('You are already logged in.', 'info')
            return redirect(url_for('main.dashboard'))
        return func(*args, **kwargs)
    return decorated_function