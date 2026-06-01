from core_service.extensions import db
from sqlalchemy import UniqueConstraint
import enum


class ReportStatus(enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    EXPIRED = "expired"
    

class Reports(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_url = db.Column(db.String(512), nullable=True)
    status = db.Column(db.Enum(ReportStatus), nullable=False, default=ReportStatus.PENDING)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    expire_at = db.Column(db.DateTime(timezone=True), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    user = db.relationship('Users', back_populates='reports', lazy=True)

    def __repr__(self):
        return f'<Reports {self.file_url} for user {self.user_id}>'

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "file_url": self.file_url,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat()
        }