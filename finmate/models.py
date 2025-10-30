from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, func
from werkzeug.security import check_password_hash, generate_password_hash

from finmate import db

#flask db migrate -m " "
#flask db upgrade

class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, nullable=False, primary_key = True)
    amount = db.Column(db.Float, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_recurring = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship('Users', back_populates='budgets')
    category = db.relationship('Category', back_populates='budgets')


class Transactions(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(10), nullable=False) #income abo expense #potom na enum kak-to
    amount = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(128))
    note = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    category = db.relationship('Category', back_populates='transactions')
    user = db.relationship('Users', back_populates='transactions')


class Category(db.Model):
     __tablename__ ='categories'

     id = db.Column(db.Integer, primary_key=True)
     name = db.Column(db.String(128), nullable=False)
     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

     user = db.relationship('Users', back_populates='categories', lazy=True)
     transactions = db.relationship('Transactions', back_populates='category', lazy=True)
     budgets = db.relationship('Budget', back_populates='category', lazy=True)

     __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_category_name_uc'),)

     def __repr__(self):
         return f'<Category {self.name}>'

class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    avatar = db.Column(db.String(200), nullable=False, default='avatars/default/default.svg')
    currency = db.Column(db.String(5), nullable=False, default='USD')
    password_hash = db.Column(db.String, nullable=False)

    budgets = db.relationship('Budget', back_populates='user', lazy=True, cascade="all, delete-orphan")
    categories = db.relationship('Category', back_populates='user', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transactions', back_populates='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


    def set_hash_pwd(self, password):
        self.password_hash = generate_password_hash(password)

    def chek_hash_pwd(self, password):
        return check_password_hash(self.password_hash, password)





