from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import allure
import pytest
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.models.report_model import ReportStatus
from core_service.reports.service import ReportService
from flask import json
from pydantic import ValidationError


@pytest.fixture
@allure.title("Initialize Mocked Report UOW")
def report_uow():
    with allure.step("Initialize MagicMock for Report Unit of Work"):
        mock_uow = MagicMock()
        mock_uow.auth.find_user_by_id.return_value = MagicMock(
            username="testuser", email="testuser@example.com"
        )
        return mock_uow


@allure.feature("Reporting")
@allure.story("Generate PDF Report")
class TestGeneratePDFReport:

    @allure.title("Successfully initiate PDF report generation (Async)")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_generate_report_success(self, report_uow, mock_redis_client):
        with allure.step("Arrange: Ensure no active reports and mock transactions"):
            report_uow.reports.get_active_report_by_period.return_value = None
            fake_new_report = MagicMock(id=42, status=ReportStatus.PENDING)
            report_uow.reports.create_report.return_value = fake_new_report
            report_uow.transactions.get_tx_by_period.return_value = [
                {"amount": 100, "title": "Test TX"}
            ]
            service = ReportService(report_uow)
            payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with allure.step("Act: Request report generation"):
            response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        with allure.step("Assert: Verify 202 Accepted and Redis queue push"):
            assert status_code == 202
            assert response["id"] == 42
            assert response["status"] == ReportStatus.PENDING.value
            mock_redis_client.rpush.assert_called_once()
            assert report_uow.flush.call_count == 2

    @allure.title("Fail generation if no transactions found for period")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_no_transactions_failed(self, report_uow):
        with allure.step("Arrange: Mock empty transaction list"):
            report_uow.reports.get_active_report_by_period.return_value = None
            fake_new_report = MagicMock(id=43, status=ReportStatus.PENDING)
            report_uow.reports.create_report.return_value = fake_new_report
            report_uow.transactions.get_tx_by_period.return_value = []
            service = ReportService(report_uow)
            payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with allure.step("Act & Assert: Expect BusinessLogicError and FAILED status"):
            with pytest.raises(BusinessLogicError) as exc_info:
                service.generate_pdf_report(user_id=1, data=payload)
            assert (
                str(exc_info.value)
                == "No transactions found for the specified period for report."
            )
            report_uow.reports.update_report_status.assert_called_once_with(
                43, ReportStatus.FAILED
            )
            assert report_uow.flush.call_count == 2

    @allure.title("Return existing processed report if requested again")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_existing_report_success(self, report_uow):
        with allure.step("Arrange: Mock existing valid report"):
            existing_report = MagicMock(
                id=44,
                status=ReportStatus.PROCESSED,
                file_url="http://example.com/report.pdf",
                expire_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
            report_uow.reports.get_active_report_by_period.return_value = (
                existing_report
            )
            service = ReportService(report_uow)
            payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with allure.step("Act: Request report generation"):
            response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        with allure.step("Assert: Verify 200 OK and existing URL returned"):
            assert status_code == 200
            assert response["id"] == 44
            assert response["status"] == ReportStatus.PROCESSED.value
            assert response["fileUrl"] == "http://example.com/report.pdf"
            report_uow.reports.create_report.assert_not_called()
            report_uow.transactions.get_tx_by_period.assert_not_called()
            report_uow.flush.assert_not_called()

    @allure.title("Fail generation if report is already in PENDING status")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_existing_pending_report_failed(self, report_uow):
        with allure.step("Arrange: Mock PENDING report"):
            existing_report = MagicMock(id=45, status=ReportStatus.PENDING)
            report_uow.reports.get_active_report_by_period.return_value = (
                existing_report
            )
            service = ReportService(report_uow)
            payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with allure.step("Act & Assert: Expect BusinessLogicError"):
            with pytest.raises(BusinessLogicError) as exc_info:
                service.generate_pdf_report(user_id=1, data=payload)
            assert (
                str(exc_info.value)
                == "Report generation is already in progress for the specified period."
            )
            report_uow.reports.create_report.assert_not_called()
            report_uow.transactions.get_tx_by_period.assert_not_called()
            report_uow.flush.assert_not_called()

    @allure.title("Successfully start new generation if previous report is EXPIRED")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_report_existing_expired_report_success(
        self, report_uow, mock_redis_client
    ):
        with allure.step("Arrange: Mock expired report"):
            existing_report = MagicMock(
                id=46,
                status=ReportStatus.PROCESSED,
                expire_at=datetime.now(timezone.utc) - timedelta(days=4),
            )
            report_uow.reports.get_active_report_by_period.return_value = (
                existing_report
            )
            fake_new_report = MagicMock(id=47, status=ReportStatus.PENDING)
            report_uow.reports.create_report.return_value = fake_new_report
            report_uow.transactions.get_tx_by_period.return_value = [
                {"amount": 200, "title": "Another Test TX"}
            ]
            service = ReportService(report_uow)
            payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with allure.step("Act: Request report generation"):
            response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        with allure.step(
            "Assert: Verify old report marked EXPIRED and new PENDING started"
        ):
            assert status_code == 202
            assert response["id"] == 47
            assert response["status"] == ReportStatus.PENDING.value
            report_uow.reports.update_report_status.assert_called_once_with(
                46, ReportStatus.EXPIRED, None
            )
            mock_redis_client.rpush.assert_called_once()
            assert report_uow.flush.call_count == 2

    @allure.title("Successfully start new generation if previous report FAILED")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_existing_failed_report_success(
        self, report_uow, mock_redis_client
    ):
        with allure.step("Arrange: Mock FAILED report"):
            existing_report = MagicMock(id=48, status=ReportStatus.FAILED)
            report_uow.reports.get_active_report_by_period.return_value = (
                existing_report
            )
            fake_new_report = MagicMock(id=49, status=ReportStatus.PENDING)
            report_uow.reports.create_report.return_value = fake_new_report
            report_uow.transactions.get_tx_by_period.return_value = [
                {"amount": 300, "title": "Yet Another Test TX"}
            ]
            service = ReportService(report_uow)
            payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with allure.step("Act: Request report generation"):
            response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        with allure.step("Assert: Verify new PENDING report started"):
            assert status_code == 202
            assert response["id"] == 49
            assert response["status"] == ReportStatus.PENDING.value
            report_uow.reports.update_report_status.assert_not_called()
            mock_redis_client.rpush.assert_called_once()
            assert report_uow.flush.call_count == 2

    @allure.title("Fail generation if user is not found")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_user_not_found(self, report_uow):
        with allure.step("Arrange: Mock user missing"):
            report_uow.auth.find_user_by_id.return_value = None
            service = ReportService(report_uow)
            payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound) as exc_info:
                service.generate_pdf_report(user_id=999, data=payload)
            assert str(exc_info.value) == "User not found."

        with allure.step("Assert: Verify DB was not modified"):
            report_uow.reports.get_active_report_by_period.assert_not_called()
            report_uow.reports.create_report.assert_not_called()
            report_uow.transactions.get_tx_by_period.assert_not_called()
            report_uow.flush.assert_not_called()

    @allure.title("Handle Redis errors gracefully during report generation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_report_redis_error(self, report_uow, mock_redis_client):
        with allure.step("Arrange: Mock Redis exception"):
            report_uow.reports.get_active_report_by_period.return_value = None
            fake_new_report = MagicMock(id=50, status=ReportStatus.PENDING)
            report_uow.reports.create_report.return_value = fake_new_report
            report_uow.transactions.get_tx_by_period.return_value = [
                {"amount": 400, "title": "Test TX for Redis Error"}
            ]
            mock_redis_client.rpush.side_effect = Exception("Redis is down")
            service = ReportService(report_uow)
            payload = {"startDate": "2026-05-01", "endDate": "2026-05-24"}

        with allure.step("Act: Request report generation"):
            response, status_code = service.generate_pdf_report(user_id=1, data=payload)

        with allure.step("Assert: Verify 400 Bad Request error returned"):
            assert status_code == 400
            assert "error" in response
            assert "Failed to start report generation process" in response["error"]

    invalid_payloads = [
        ({"startDate": "2026-05-01"}),  # Missing endDate
        ({"endDate": "2026-05-24"}),  # Missing startDate
        ({}),  # Missing both
        ({"startDate": "", "endDate": ""}),  # Empty strings
        ({"startDate": "invalid", "endDate": "invalid"}),  # Invalid format
        ({"startDate": None, "endDate": None}),  # None values
        (
            {"startDate": "2026-05-01", "endDate": "2026-04-30"}
        ),  # endDate before startDate
        (
            {"startDate": "2026-05-01", "endDate": "2026-05-01"}
        ),  # startDate equal to endDate
        ({"startDate": "2026/05/01", "endDate": "2026/05/24"}),  # Wrong date format
        ({"startDate": "2026-13-01", "endDate": "2026-05-24"}),  # Invalid month
        ({"startDate": "2026-00-01", "endDate": "2026-05-24"}),  # Invalid month
        ({"startDate": "2026-05-32", "endDate": "2026-05-24"}),  # Invalid day
        (
            {"startDate": "2026-05-01T00:00:00", "endDate": "2026-05-24T23:59:59"}
        ),  # Datetime instead of date
        ({"startDate": "2026-05-01", "endDate": 12345}),  # endDate is not a string
    ]

    @allure.title("Validation fails on invalid date payloads")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("payload", invalid_payloads)
    def test_generate_report_pydantic_validation_failed(self, report_uow, payload):
        with allure.step("Act & Assert: Expect ValidationError on invalid payloads"):
            service = ReportService(report_uow)
            with pytest.raises(ValidationError):
                service.generate_pdf_report(user_id=1, data=payload)
            report_uow.reports.get_active_report_by_period.assert_not_called()


@allure.feature("Reporting")
@allure.story("Check Report Status")
class TestGetReportStatus:

    @allure.title("Successfully fetch status of a PROCESSED report")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_report_status_success(self, report_uow):
        with allure.step("Arrange: Mock PROCESSED report"):
            report_id = 51
            existing_report = MagicMock(
                id=report_id,
                status=ReportStatus.PROCESSED,
                user_id=1,
                expire_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            service = ReportService(report_uow)

        with allure.step("Act: Request status"):
            response, status_code = service.get_report_status(1, report_id)

        with allure.step("Assert: Verify 200 OK"):
            assert status_code == 200
            assert response["id"] == report_id
            assert response["status"] == ReportStatus.PROCESSED.value
            report_uow.reports.get_report_by_id.assert_called_once_with(report_id)

    @allure.title("Mark report as EXPIRED if deadline passed during status check")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_when_expired(self, report_uow):
        with allure.step("Arrange: Mock report with past expiration date"):
            report_id = 52
            existing_report = MagicMock(
                id=report_id,
                status=ReportStatus.PROCESSED,
                expire_at=datetime.now(timezone.utc) - timedelta(days=1),
                user_id=1,
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            service = ReportService(report_uow)

        with allure.step("Act: Request status"):
            response, status_code = service.get_report_status(1, report_id)

        with allure.step("Assert: Verify 410 Gone and EXPIRED status update"):
            assert status_code == 410
            assert response["id"] == report_id
            assert response["status"] == ReportStatus.EXPIRED.value
            report_uow.reports.update_report_status.assert_called_once_with(
                report_id, ReportStatus.EXPIRED, None
            )

    @allure.title("Fail status check if report is not found")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_not_found(self, report_uow):
        with allure.step("Arrange: Mock report missing"):
            report_id = 999
            report_uow.reports.get_report_by_id.return_value = None
            service = ReportService(report_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound) as exc_info:
                service.get_report_status(1, report_id)
            assert str(exc_info.value) == "Report not found or access denied."
            report_uow.reports.get_report_by_id.assert_called_once_with(report_id)

    @allure.title("Fail status check if user does not own the report (Access Denied)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_status_access_denied(self, report_uow):
        with allure.step("Arrange: Mock report belonging to another user"):
            report_id = 53
            existing_report = MagicMock(
                id=report_id, status=ReportStatus.PROCESSED, user_id=1
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            service = ReportService(report_uow)

        with allure.step("Act & Assert: Expect ResourceNotFound"):
            with pytest.raises(ResourceNotFound) as exc_info:
                service.get_report_status(999, report_id)
            assert str(exc_info.value) == "Report not found or access denied."
            report_uow.reports.get_report_by_id.assert_called_once_with(report_id)

    @allure.title("Return 400 Bad Request if report has FAILED status")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_failed(self, report_uow):
        with allure.step("Arrange: Mock FAILED report"):
            report_id = 54
            existing_report = MagicMock(
                id=report_id, status=ReportStatus.FAILED, user_id=999
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            service = ReportService(report_uow)

        with allure.step("Act: Request status"):
            response, status_code = service.get_report_status(999, report_id)

        with allure.step("Assert: Verify 400 Bad Request error"):
            assert status_code == 400
            assert response["id"] == report_id
            assert response["status"] == ReportStatus.FAILED.value
            assert "error" in response

    @allure.title("Return 400 Bad Request if report is already EXPIRED")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_expired(self, report_uow):
        with allure.step("Arrange: Mock already EXPIRED report"):
            report_id = 55
            existing_report = MagicMock(
                id=report_id, status=ReportStatus.EXPIRED, user_id=999
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            service = ReportService(report_uow)

        with allure.step("Act: Request status"):
            response, status_code = service.get_report_status(999, report_id)

        with allure.step("Assert: Verify 400 Bad Request error"):
            assert status_code == 400
            assert response["id"] == report_id
            assert response["status"] == ReportStatus.EXPIRED.value
            assert "error" in response

    @allure.title("Mark PENDING report as FAILED if generation timeout exceeded")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_status_pending_timeout(self, report_uow):
        with allure.step("Arrange: Mock PENDING report created > 2 hours ago"):
            report_id = 56
            existing_report = MagicMock(
                id=report_id,
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
                user_id=1,
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            service = ReportService(report_uow)

        with allure.step("Act: Request status"):
            response, status_code = service.get_report_status(1, report_id)

        with allure.step("Assert: Verify timeout handled and status updated to FAILED"):
            assert status_code == 400
            assert response["id"] == report_id
            assert response["status"] == ReportStatus.FAILED.value
            assert "error" in response
            report_uow.reports.update_report_status.assert_called_once_with(
                report_id, ReportStatus.FAILED
            )

    @allure.title(
        "Return 202 Accepted if PENDING report is still processing (No Redis result)"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_pending_still_processing(
        self, report_uow, mock_redis_client
    ):
        with allure.step("Arrange: Mock PENDING report within timeout and empty Redis"):
            report_id = 57
            existing_report = MagicMock(
                id=report_id,
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                user_id=999,
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            mock_redis_client.get.return_value = None
            service = ReportService(report_uow)

        with allure.step("Act: Request status"):
            response, status_code = service.get_report_status(999, report_id)

        with allure.step("Assert: Verify 202 Accepted returned"):
            assert status_code == 202
            assert response["id"] == report_id
            assert response["status"] == ReportStatus.PENDING.value

    @allure.title(
        "Update DB and return 200 OK if PENDING report result is ready in Redis"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_status_pending_result_ready(
        self, report_uow, mock_redis_client
    ):
        with allure.step("Arrange: Mock PENDING report and successful result in Redis"):
            report_id = 58
            existing_report = MagicMock(
                id=report_id,
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                user_id=999,
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            result_data = {
                "status": "success",
                "fileUrl": "http://example.com/report.pdf",
            }
            mock_redis_client.get.return_value = json.dumps(result_data)
            service = ReportService(report_uow)

        with allure.step("Act: Request status"):
            response, status_code = service.get_report_status(999, report_id)

        with allure.step("Assert: Verify 200 OK and file URL mapped"):
            assert status_code == 200
            assert response["id"] == report_id
            assert response["status"] == ReportStatus.PROCESSED.value
            assert response["fileUrl"] == "http://example.com/report.pdf"

    @allure.title("Handle Redis errors gracefully on status check")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_report_redis_error_on_status_check(
        self, report_uow, mock_redis_client
    ):
        with allure.step("Arrange: Mock Redis exception during status pull"):
            report_id = 59
            existing_report = MagicMock(
                id=report_id,
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                user_id=999,
            )
            report_uow.reports.get_report_by_id.return_value = existing_report
            mock_redis_client.get.side_effect = Exception("Redis is down")
            service = ReportService(report_uow)

        with allure.step("Act & Assert: Expect Exception bubble-up"):
            with pytest.raises(Exception) as exc_info:
                service.get_report_status(999, report_id)
            assert str(exc_info.value) == "Redis is down"


@allure.feature("Reporting")
@allure.story("Report History")
class TestGetReportHistory:

    @allure.title("Successfully fetch report history list")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_report_history_success(self, report_uow):
        with allure.step("Arrange: Mock multiple reports (PROCESSED and FAILED)"):
            user_id = 322
            fake_reports = [
                MagicMock(
                    id=1,
                    status=ReportStatus.PROCESSED,
                    start_date=datetime(2026, 5, 1),
                    end_date=datetime(2026, 5, 24),
                    created_at=datetime(2026, 5, 25),
                    expire_at=None,
                ),
                MagicMock(
                    id=2,
                    status=ReportStatus.FAILED,
                    start_date=datetime(2026, 4, 1),
                    end_date=datetime(2026, 4, 30),
                    created_at=datetime(2026, 5, 1),
                    expire_at=None,
                ),
            ]
            report_uow.reports.get_report_history.return_value = fake_reports
            service = ReportService(report_uow)

        with allure.step("Act: Fetch history"):
            response = service.get_report_history(user_id)

        with allure.step("Assert: Verify list mapping and format"):
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

    @allure.title("Return empty list if user has no report history")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_history_no_reports(self, report_uow):
        with allure.step("Arrange: Mock empty report history"):
            user_id = 32
            report_uow.reports.get_report_history.return_value = []
            service = ReportService(report_uow)

        with allure.step("Act: Fetch history"):
            response = service.get_report_history(user_id)

        with allure.step("Assert: Verify empty array is returned"):
            assert response == []
            report_uow.reports.get_report_history.assert_called_once_with(user_id)

    @allure.title("Return empty list if user is not found")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_history_user_not_found(self, report_uow):
        with allure.step("Arrange: Mock user missing"):
            user_id = 991
            report_uow.reports.get_report_history.return_value = []
            service = ReportService(report_uow)

        with allure.step("Act: Fetch history"):
            response = service.get_report_history(user_id)

        with allure.step("Assert: Verify empty array is returned"):
            assert response == []
            report_uow.reports.get_report_history.assert_called_once_with(user_id)
