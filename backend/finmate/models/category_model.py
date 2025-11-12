from backend.finmate import db
from sqlalchemy import UniqueConstraint


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mcc_code = db.Column(db.String(200), nullable=True)

    user = db.relationship('Users', back_populates='categories', lazy=True)
    transactions = db.relationship('Transactions', back_populates='category', lazy=True)
    budgets = db.relationship('Budget', back_populates='category', lazy=True)

    __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_category_name_uc'),)

    def __repr__(self):
        return f'<Category {self.name}>'

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "mcc_code": self.mcc_code
        }