from backend.finmate import db
from sqlalchemy import func


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, nullable=False, primary_key = True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_recurring = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship('Users', back_populates='budgets')
    category = db.relationship('Category', back_populates='budgets')


    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "category_id": self.category_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "is_recurring": self.is_recurring
        }