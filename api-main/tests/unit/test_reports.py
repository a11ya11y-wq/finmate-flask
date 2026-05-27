from datetime import datetime, timezone, timedelta

from flask import json
import pytest
from unittest.mock import MagicMock

from pydantic import ValidationError
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.models.report_model import ReportStatus

from core_service.reports.service import ReportService


@pytest.fixture
def report_uow():
    mock_uow = MagicMock()
    mock_uow.auth.find_user_by_id.return_value = MagicMock(
        username="testuser", 
        email="testuser@example.com"
    )
    return mock_uow

class TestGeneratePDFReport:

    def test_generate_report_success(self, report_uow, mock_redis_client):
        report_uow.reports.get_active_report_by_period.return_value = None

        fake_new_report = MagicMock(id=42, status=ReportStatus.PENDING)
        report_uow.reports.create_report.return_value = fake_new_report

        report_uow.transactions.get_tx_by_period.return_value = [{"amount": 100, "title": "Test TX"}]


        service = ReportService(report_uow)
        payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        assert status_code == 202
        assert response["id"] == 42
        assert response["status"] == ReportStatus.PENDING.value

        mock_redis_client.rpush.assert_called_once()

        assert report_uow.flush.call_count == 2

    def test_generate_report_no_transactions_failed(self, report_uow):
        report_uow.reports.get_active_report_by_period.return_value = None

        fake_new_report = MagicMock(id=43, status=ReportStatus.PENDING)
        report_uow.reports.create_report.return_value = fake_new_report

        report_uow.transactions.get_tx_by_period.return_value = []

        service = ReportService(report_uow)
        payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with pytest.raises(BusinessLogicError) as exc_info:
            service.generate_pdf_report(user_id=1, data=payload)

        assert str(exc_info.value) == "No transactions found for the specified period for report."

        report_uow.reports.update_report_status.assert_called_once_with(43, ReportStatus.FAILED)
        assert report_uow.flush.call_count == 2

    def test_generate_existing_report_success(self, report_uow):
        existing_report = MagicMock(
                                id=44, 
                                status=ReportStatus.PROCESSED, 
                                file_url="http://example.com/report.pdf", 
                                expire_at=datetime.now(timezone.utc) + timedelta(days=1)
                                )
        report_uow.reports.get_active_report_by_period.return_value = existing_report

        service = ReportService(report_uow)
        payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        assert status_code == 200
        assert response["id"] == 44
        assert response["status"] == ReportStatus.PROCESSED.value
        assert response["fileUrl"] == "http://example.com/report.pdf"

        report_uow.reports.create_report.assert_not_called()
        report_uow.transactions.get_tx_by_period.assert_not_called()
        report_uow.flush.assert_not_called()

    def test_generate_report_existing_pending_report_failed(self, report_uow):
        existing_report = MagicMock(id=45, status=ReportStatus.PENDING)
        report_uow.reports.get_active_report_by_period.return_value = existing_report

        service = ReportService(report_uow)
        payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with pytest.raises(BusinessLogicError) as exc_info:
            service.generate_pdf_report(user_id=1, data=payload)

        assert str(exc_info.value) == "Report generation is already in progress for the specified period."

        report_uow.reports.create_report.assert_not_called()
        report_uow.transactions.get_tx_by_period.assert_not_called()
        report_uow.flush.assert_not_called()


    def test_generate_report_existing_expired_report_success(self, report_uow, mock_redis_client):
        existing_report = MagicMock(
                            id=46, 
                            status=ReportStatus.PROCESSED, 
                            expire_at=datetime.now(timezone.utc) - timedelta(days=4)
                        )
        report_uow.reports.get_active_report_by_period.return_value = existing_report

        fake_new_report = MagicMock(id=47, status=ReportStatus.PENDING)
        report_uow.reports.create_report.return_value = fake_new_report

        report_uow.transactions.get_tx_by_period.return_value = [{"amount": 200, "title": "Another Test TX"}]

        service = ReportService(report_uow)
        payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        assert status_code == 202
        assert response["id"] == 47
        assert response["status"] == ReportStatus.PENDING.value

        report_uow.reports.update_report_status.assert_called_once_with(46, ReportStatus.EXPIRED)
        mock_redis_client.rpush.assert_called_once()

        assert report_uow.flush.call_count == 2

    def test_generate_report_existing_failed_report_success(self, report_uow, mock_redis_client):
        existing_report = MagicMock(id=48, status=ReportStatus.FAILED)
        report_uow.reports.get_active_report_by_period.return_value = existing_report

        fake_new_report = MagicMock(id=49, status=ReportStatus.PENDING)
        report_uow.reports.create_report.return_value = fake_new_report

        report_uow.transactions.get_tx_by_period.return_value = [{"amount": 300, "title": "Yet Another Test TX"}]

        service = ReportService(report_uow)
        payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        assert status_code == 202
        assert response["id"] == 49
        assert response["status"] == ReportStatus.PENDING.value

        report_uow.reports.update_report_status.assert_not_called()
        mock_redis_client.rpush.assert_called_once()

        assert report_uow.flush.call_count == 2

    def test_generate_report_user_not_found(self, report_uow):
        report_uow.auth.find_user_by_id.return_value = None

        service = ReportService(report_uow)
        payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with pytest.raises(ResourceNotFound) as exc_info:
            service.generate_pdf_report(user_id=999, data=payload)

        assert str(exc_info.value) == "User not found."

        report_uow.reports.get_active_report_by_period.assert_not_called()
        report_uow.reports.create_report.assert_not_called()
        report_uow.transactions.get_tx_by_period.assert_not_called()
        report_uow.flush.assert_not_called()

    def test_generate_report_redis_error(self, report_uow, mock_redis_client):
        report_uow.reports.get_active_report_by_period.return_value = None

        fake_new_report = MagicMock(id=50, status=ReportStatus.PENDING)
        report_uow.reports.create_report.return_value = fake_new_report

        report_uow.transactions.get_tx_by_period.return_value = [{"amount": 400, "title": "Test TX for Redis Error"}]

        mock_redis_client.rpush.side_effect = Exception("Redis is down")

        service = ReportService(report_uow)
        payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with pytest.raises(BusinessLogicError) as exc_info:
            service.generate_pdf_report(user_id=1, data=payload)

        assert str(exc_info.value) == "Failed to start report generation process. Please try again later."

        assert report_uow.flush.call_count == 3
    
    invalid_payloads = [
        ({"startDate": "2026-05-01"}), # Missing endDate
        ({"endDate": "2026-05-24"}),   # Missing startDate
        ({}),                          # Missing both
        ({"startDate": "", "endDate": ""}), # Empty strings
        ({"startDate": "invalid", "endDate": "invalid"}), # Invalid format
        ({"startDate": None, "endDate": None}), # None values
        ({"startDate": "2026-05-01", "endDate": "2026-04-30"}), # endDate before startDate
        ({"startDate": "2026-05-01", "endDate": "2026-05-01"}), # startDate equal to endDate
        ({"startDate": "2026/05/01", "endDate": "2026/05/24"}), # Wrong date format
        ({"startDate": "2026-13-01", "endDate": "2026-05-24"}), # Invalid month
        ({"startDate": "2026-00-01", "endDate": "2026-05-24"}), # Invalid month
        ({"startDate": "2026-05-32", "endDate": "2026-05-24"}), # Invalid day
        ({"startDate": "2026-05-01T00:00:00", "endDate": "2026-05-24T23:59:59"}), # Datetime instead of date
        ({"startDate": "2026-05-01", "endDate": 12345}) # endDate is not a string
    ]
    @pytest.mark.parametrize("payload", invalid_payloads)
    def test_generate_report_pydantic_validation_failed(self, report_uow, payload):
        service = ReportService(report_uow)

        with pytest.raises(ValidationError):
            service.generate_pdf_report(user_id=1, data=payload)

        report_uow.reports.get_active_report_by_period.assert_not_called()


class TestGetReportStatus:

    def test_get_report_status_success(self, report_uow):
        report_id = 51
        existing_report = MagicMock(id=report_id, status=ReportStatus.PROCESSED, user_id=1, expire_at=datetime.now(timezone.utc) + timedelta(days=1))
        report_uow.reports.get_report_by_id.return_value = existing_report

        service = ReportService(report_uow)
        response, status_code = service.get_report_status(1, report_id)

        assert status_code == 200
        assert response["id"] == report_id
        assert response["status"] == ReportStatus.PROCESSED.value

        report_uow.reports.get_report_by_id.assert_called_once_with(report_id)
    
    def test_get_report_status_when_expired(self, report_uow):
        report_id = 52
        existing_report = MagicMock(
            id=report_id, 
            status=ReportStatus.PROCESSED, 
            expire_at=datetime.now(timezone.utc) - timedelta(days=1),
            user_id=1
        )
        report_uow.reports.get_report_by_id.return_value = existing_report

        service = ReportService(report_uow)
        response, status_code = service.get_report_status(1,report_id)

        assert status_code == 410
        assert response["id"] == report_id
        assert response["status"] == ReportStatus.EXPIRED.value

        report_uow.reports.update_report_status.assert_called_once_with(report_id, ReportStatus.EXPIRED)

    def test_get_report_status_not_found(self, report_uow):
        report_id = 999
        report_uow.reports.get_report_by_id.return_value = None

        service = ReportService(report_uow)
        with pytest.raises(ResourceNotFound) as exc_info:
            service.get_report_status(1, report_id)

        assert str(exc_info.value) == "Report not found or access denied."

        report_uow.reports.get_report_by_id.assert_called_once_with(report_id)

    def test_get_report_status_access_denied(self, report_uow):
        report_id = 53
        existing_report = MagicMock(id=report_id, status=ReportStatus.PROCESSED, user_id=1)
        report_uow.reports.get_report_by_id.return_value = existing_report

        service = ReportService(report_uow)
        with pytest.raises(ResourceNotFound) as exc_info:
            service.get_report_status(999, report_id)

        assert str(exc_info.value) == "Report not found or access denied."

        report_uow.reports.get_report_by_id.assert_called_once_with(report_id)

    def test_get_report_status_failed(self, report_uow):
        report_id = 54
        existing_report = MagicMock(id=report_id, status=ReportStatus.FAILED, user_id=999)
        report_uow.reports.get_report_by_id.return_value = existing_report

        service = ReportService(report_uow)
        response, status_code = service.get_report_status(999, report_id)

        assert status_code == 400
        assert response["id"] == report_id
        assert response["status"] == ReportStatus.FAILED.value
        assert "error" in response

    def test_get_report_status_expired(self, report_uow):
        report_id = 55
        existing_report = MagicMock(id=report_id, status=ReportStatus.EXPIRED, user_id=999)
        report_uow.reports.get_report_by_id.return_value = existing_report

        service = ReportService(report_uow)
        response, status_code = service.get_report_status(999, report_id)

        assert status_code == 400
        assert response["id"] == report_id
        assert response["status"] == ReportStatus.EXPIRED.value
        assert "error" in response

    def test_get_report_status_pending_timeout(self, report_uow):
        report_id = 56
        existing_report = MagicMock(
            id=report_id, 
            status=ReportStatus.PENDING, 
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            user_id=1
        )
        report_uow.reports.get_report_by_id.return_value = existing_report

        service = ReportService(report_uow)
        response, status_code = service.get_report_status(1, report_id)

        assert status_code == 400
        assert response["id"] == report_id
        assert response["status"] == ReportStatus.FAILED.value
        assert "error" in response

        report_uow.reports.update_report_status.assert_called_once_with(report_id, ReportStatus.FAILED)


    def test_get_report_status_pending_still_processing(self, report_uow, mock_redis_client):
        report_id = 57
        existing_report = MagicMock(
            id=report_id, 
            status=ReportStatus.PENDING, 
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            user_id=999
        )
        report_uow.reports.get_report_by_id.return_value = existing_report
        mock_redis_client.get.return_value = None

        service = ReportService(report_uow)
        response, status_code = service.get_report_status(999, report_id)

        assert status_code == 202
        assert response["id"] == report_id
        assert response["status"] == ReportStatus.PENDING.value


    def test_get_report_status_pending_result_ready(self, report_uow, mock_redis_client):
        report_id = 58
        existing_report = MagicMock(
            id=report_id, 
            status=ReportStatus.PENDING, 
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            user_id=999
        )
        report_uow.reports.get_report_by_id.return_value = existing_report

        result_data = {"status": "success", "fileUrl": "http://example.com/report.pdf"}
        mock_redis_client.get.return_value = json.dumps(result_data)

        service = ReportService(report_uow)
        response, status_code = service.get_report_status(999, report_id)

        assert status_code == 200
        assert response["id"] == report_id
        assert response["status"] == ReportStatus.PROCESSED.value
        assert response["fileUrl"] == "http://example.com/report.pdf"
        
    def test_generate_report_redis_error_on_status_check(self, report_uow, mock_redis_client):
        report_id = 59
        existing_report = MagicMock(
            id=report_id, 
            status=ReportStatus.PENDING, 
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            user_id=999
        )
        report_uow.reports.get_report_by_id.return_value = existing_report

        mock_redis_client.get.side_effect = Exception("Redis is down")

        service = ReportService(report_uow)

        with pytest.raises(Exception) as exc_info:
            service.get_report_status(999, report_id)
    
            assert str(exc_info.value) == "Redis is down"

class TestGetReportHistory:
    def test_get_report_history_success(self, report_uow):
        user_id = 322
        fake_reports = [
            MagicMock(id=1, status=ReportStatus.PROCESSED, start_date=datetime(2026, 5, 1), end_date=datetime(2026, 5, 24), created_at=datetime(2026, 5, 25)),
            MagicMock(id=2, status=ReportStatus.FAILED, start_date=datetime(2026, 4, 1), end_date=datetime(2026, 4, 30), created_at=datetime(2026, 5, 1))
        ]
        report_uow.reports.get_report_history.return_value = fake_reports

        service = ReportService(report_uow)
        response = service.get_report_history(user_id)

        assert len(response) == 2
        assert response[0]["id"] == 1
        assert response[0]["status"] == ReportStatus.PROCESSED.value
        assert response[0]["startDate"] == "2026-05-01T00:00:00"
        assert response[0]["endDate"] == "2026-05-24T00:00:00"
        assert response[0]["createdAt"] == "2026-05-25T00:00:00"

        assert response[1]["id"] == 2
        assert response[1]["status"] == ReportStatus.FAILED.value
        assert response[1]["startDate"] == "2026-04-01T00:00:00"
        assert response[1]["endDate"] == "2026-04-30T00:00:00"
        assert response[1]["createdAt"] == "2026-05-01T00:00:00"

        report_uow.reports.get_report_history.assert_called_once_with(user_id)

    def test_get_report_history_no_reports(self, report_uow):
        user_id = 32
        report_uow.reports.get_report_history.return_value = []

        service = ReportService(report_uow)
        response = service.get_report_history(user_id)

        assert response == []
        report_uow.reports.get_report_history.assert_called_once_with(user_id)

    def test_get_report_history_user_not_found(self, report_uow):
        user_id = 991
        report_uow.reports.get_report_history.return_value = []

        service = ReportService(report_uow)
        response = service.get_report_history(user_id)

        assert response == []
        report_uow.reports.get_report_history.assert_called_once_with(user_id)