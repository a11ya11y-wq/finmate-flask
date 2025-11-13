from backend.finmate import db
from sqlalchemy import func



class Transactions(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(10), nullable=False) #income abo expense #potom na enum kak-to
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    title = db.Column(db.String(128))
    note = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    mono_id = db.Column(db.String(50), nullable=True, unique=True)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    category = db.relationship('Category', back_populates='transactions')
    user = db.relationship('Users', back_populates='transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'category_id': self.category_id,

            'category_name': self.category.name if self.category else 'Uncategorized',

            'created_at': self.created_at.isoformat(),

            'note': self.note,
            'user_id': self.user_id
        }