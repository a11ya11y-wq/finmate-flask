import datetime

from core_service.extensions import db
from core_service.models.report_model import Reports, ReportStatus


class ReportRepository:

    def get_report_by_id(self, report_id: int) -> Reports:
        return Reports.query.get(report_id)

    def get_active_report_by_period(
        self, user_id: int, start_date: datetime.date, end_date: datetime.date
    ) -> Reports:
        return Reports.query.filter(
            Reports.user_id == user_id,
            Reports.start_date == start_date,
            Reports.end_date == end_date,
            Reports.status.in_([ReportStatus.PENDING, ReportStatus.PROCESSED]),
        ).first()

    def create_report(
        self, user_id: int, start_date: datetime.date, end_date: datetime.date
    ) -> Reports:
        report = Reports(
            user_id=user_id,
            status=ReportStatus.PENDING,
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(report)
        return report

    def update_report_status(
        self,
        report_id: int,
        status: ReportStatus,
        file_key: str = None,
        expire_at: datetime = None,
    ) -> Reports:
        report = self.get_report_by_id(report_id)
        if report:
            report.status = status
            if file_key:
                report.file_key = file_key
            if expire_at:
                report.expire_at = expire_at
            return report
        return None

    def get_report_history(self, user_id: int, limit: int = 7) -> list[Reports]:
        return (
            Reports.query.filter_by(user_id=user_id)
            .order_by(Reports.created_at.desc())
            .limit(limit)
            .all()
        )
