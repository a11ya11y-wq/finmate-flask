from finmate.extensions import db
from werkzeug.security import check_password_hash, generate_password_hash


class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    avatar = db.Column(db.String(200), nullable=False, default='avatars/default/default.svg')
    currency = db.Column(db.String(5), nullable=False, default='USD')
    password_hash = db.Column(db.String, nullable=False)
    last_real_balance = db.Column(db.Numeric(10, 2), default=0.0) # Actual balance from card
    initial_balance = db.Column(db.Numeric(10, 2), default=0) # Точка відліку при першій синхронізації
    monobank_api_token = db.Column(db.LargeBinary, nullable=True)
    refresh_token = db.Column(db.String(500), nullable=True, index=True) #TODO: Зробити мульти сесії

    budgets = db.relationship('Budget', back_populates='user', lazy=True, cascade="all, delete-orphan")
    categories = db.relationship('Category', back_populates='user', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transactions', back_populates='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


    def set_hash_pwd(self, password):
        self.password_hash = generate_password_hash(password)

    def chek_hash_pwd(self, password):
        return check_password_hash(self.password_hash, password)


    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "currency": self.currency,
            "monobank_token_is_set": self.monobank_api_token is not None,
            "avatar": self.avatar
        }