import json
import os
from datetime import datetime, timedelta, timezone

import allure
import pytest
from core_service.models.report_model import Reports, ReportStatus
from core_service.models.transaction_model import Transactions
from core_service.models.user_model import Users


@pytest.fixture
@allure.title("Setup initial transactions for report generation")
def arrange_tx(db_session):
    with allure.step("Insert test transactions (income and expense) into DB"):
        tx1 = Transactions(
            user_id=1,
            amount=350.00,
            title="Сільпо",
            transaction_type="expense",
            category_id=1,
            created_at="2025-11-15",
        )

        tx2 = Transactions(
            user_id=1,
            amount=12000.00,
            title="Зарплата",
            transaction_type="income",
            category_id=2,
            created_at="2025-11-20",
        )

        db_session.add_all([tx1, tx2])
        db_session.flush()


S3_URL = os.environ.get("R2_PUBLIC_URL")

CREATE_REPORT_PAYLOAD = {"startDate": "2024-01-01", "endDate": "2026-01-31"}


@allure.feature("Reporting")
@allure.story("Generate PDF Report")
@pytest.mark.usefixtures("db_session")
class TestGenerateReport:

    @allure.title("Successfully initiate report generation and queue in Redis")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_generate_report_success(
        self, client, auth_headers, test_redis, arrange_tx
    ):
        with allure.step("Act: Send POST request to start report generation"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=CREATE_REPORT_PAYLOAD,
                headers=auth_headers,
            )
        with allure.step("Assert: Verify 202 Accepted and PENDING status"):
            assert response.status_code == 202
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.PENDING.value
            assert "id" in response_data

        with allure.step("Assert: Verify task was successfully pushed to Redis queue"):
            queue_len = test_redis.llen("pdf_task_queue")
            assert (
                queue_len == 1
            ), f"Task was not enqueued in Redis. Current queue length: {queue_len}"
            task_raw = test_redis.lpop("pdf_task_queue")
            task_data = json.loads(task_raw)
            assert task_data["reportId"] == response_data["id"]
            assert task_data["user"]["email"] == "test@test.com"
            assert len(task_data["transactions"]) == 2

    @allure.title("Fail report generation when no transactions exist for period")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_no_transactions(self, client, auth_headers, test_redis):
        with allure.step("Arrange: Prepare payload with empty date range"):
            payload = {"startDate": "2023-01-01", "endDate": "2023-12-31"}

        with allure.step("Act: Send POST request"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=payload,
                headers=auth_headers,
            )
        with allure.step("Assert: Verify 400 Bad Request"):
            assert response.status_code == 400
            response_data = response.get_json()
            assert "error" in response_data
            assert (
                response_data["error"]
                == "No transactions found for the specified period for report."
            )

        with allure.step("Assert: Verify Redis queue remains empty"):
            queue_len = test_redis.llen("pdf_task_queue")
            assert (
                queue_len == 0
            ), f"Task should not be enqueued. Current queue length: {queue_len}"

    @allure.title("API Validation errors on invalid date ranges")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_report_invalid_dates(self, client, auth_headers):
        with allure.step("Arrange: Set startDate after endDate"):
            payload = {"startDate": "2024-12-31", "endDate": "2024-01-01"}

        with allure.step("Act: Send POST request"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=payload,
                headers=auth_headers,
            )
        with allure.step("Assert: Verify 422 Unprocessable Entity"):
            assert response.status_code == 422
            response_data = response.get_json()
            assert "details" in response_data
            assert "Start date must be before end date" in response_data["details"][0]

    @allure.title("API Validation errors on missing required fields")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_report_missing_fields(self, client, auth_headers):
        with allure.step("Arrange: Remove endDate from payload"):
            payload = {"startDate": "2024-01-01"}

        with allure.step("Act: Send POST request"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=payload,
                headers=auth_headers,
            )
        with allure.step("Assert: Verify 422 Unprocessable Entity"):
            assert response.status_code == 422
            response_data = response.get_json()
            assert "error" in response_data
            assert "Validation Error" in response_data["error"]

    @allure.title("Fail to generate report without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_report_unauthorized(self, client):
        with allure.step("Act: Send POST without auth headers"):
            response = client.post(
                "api/v1/report/generate-pdf", json=CREATE_REPORT_PAYLOAD
            )

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401
            response_data = response.get_json()
            assert "details" in response_data
            assert response_data["details"] == "Missing Authorization Header"

    @allure.title("Fail to start generation if existing report is still PENDING")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_existing_pending(
        self, client, auth_headers, test_redis, arrange_tx
    ):
        with allure.step("Arrange: Start initial report generation"):
            response1 = client.post(
                "api/v1/report/generate-pdf",
                json=CREATE_REPORT_PAYLOAD,
                headers=auth_headers,
            )
            assert response1.status_code == 202

        with allure.step("Act: Attempt to start generation for the same period again"):
            response2 = client.post(
                "api/v1/report/generate-pdf",
                json=CREATE_REPORT_PAYLOAD,
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 400 Bad Request (Already in progress)"):
            assert response2.status_code == 400
            response_data = response2.get_json()
            assert "error" in response_data
            assert (
                response_data["error"]
                == "Report generation is already in progress for the specified period."
            )

    @allure.title("Return existing PROCESSED report URL instead of regenerating")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_report_existing_processed(
        self, client, auth_headers, test_redis, arrange_tx, db_session
    ):
        with allure.step("Arrange: Insert existing processed report into DB"):
            report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PROCESSED,
                file_key="report.pdf",
            )
            db_session.add(report)
            db_session.flush()

        with allure.step("Act: Request report for the same period"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=CREATE_REPORT_PAYLOAD,
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 200 OK and existing URL returned"):
            assert response.status_code == 200
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.PROCESSED.value
            assert response_data["fileUrl"] == f"{S3_URL}/report.pdf"
            assert response_data["id"] == report.id

    @allure.title("Start new report generation if previous attempt FAILED")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_existing_failed(
        self, client, auth_headers, test_redis, arrange_tx, db_session
    ):
        with allure.step("Arrange: Insert failed report attempt into DB"):
            report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.FAILED,
            )
            db_session.add(report)
            db_session.flush()

        with allure.step("Act: Request report generation"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=CREATE_REPORT_PAYLOAD,
                headers=auth_headers,
            )

        with allure.step("Assert: Verify new PENDING report is created"):
            assert response.status_code == 202
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.PENDING.value
            assert response_data["id"] != report.id

        with allure.step("Assert: Verify new task is in Redis queue"):
            queue_len = test_redis.llen("pdf_task_queue")
            assert (
                queue_len == 1
            ), f"Task was not enqueued in Redis. Current queue length: {queue_len}"
            task_raw = test_redis.lpop("pdf_task_queue")
            task_data = json.loads(task_raw)
            assert task_data["reportId"] == response_data["id"]

    @allure.title("Start new report generation if previous link EXPIRED")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_existing_expired(
        self, client, auth_headers, test_redis, arrange_tx, db_session
    ):
        with allure.step("Arrange: Insert expired report into DB"):
            expired_report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PROCESSED,
                file_key="expired_report.pdf",
                expire_at=datetime.now(timezone.utc) - timedelta(days=1),
            )
            db_session.add(expired_report)
            db_session.flush()

        with allure.step("Act: Request report generation"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=CREATE_REPORT_PAYLOAD,
                headers=auth_headers,
            )

        with allure.step("Assert: Verify new PENDING report is created"):
            assert response.status_code == 202
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.PENDING.value
            assert response_data["id"] != expired_report.id

        with allure.step("Assert: Verify new task is in Redis queue"):
            queue_len = test_redis.llen("pdf_task_queue")
            assert (
                queue_len == 1
            ), f"Task was not enqueued in Redis. Current queue length: {queue_len}"
            task_raw = test_redis.lpop("pdf_task_queue")
            task_data = json.loads(task_raw)
            assert task_data["reportId"] == response_data["id"]

    @allure.title("Handle fallback gracefully when Redis fails (400 and FAILED status)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_report_redis_failure(
        self, client, auth_headers, test_redis, arrange_tx, mocker
    ):
        with allure.step("Arrange: Mock Redis crash on rpush"):
            mocker.patch.object(
                test_redis, "rpush", side_effect=Exception("Redis died")
            )

        with allure.step("Act: Request report generation"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=CREATE_REPORT_PAYLOAD,
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 400 Bad Request error response"):
            assert response.status_code == 400
            assert (
                "Failed to start report generation process"
                in response.get_json()["error"]
            )

        with allure.step("Assert: Verify report history recorded the FAILED attempt"):
            history_response = client.get("api/v1/report/history", headers=auth_headers)
            assert history_response.status_code == 200
            history_data = history_response.get_json()
            latest_report = history_data[-1]
            assert latest_report["status"] == ReportStatus.FAILED.value

    @allure.title("Fail report generation if user no longer exists in DB")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_report_user_not_found(self, client, test_redis, mocker):
        with allure.step("Arrange: Generate fake JWT token"):
            from flask_jwt_extended import create_access_token

            fake_token = create_access_token(identity="999")
            headers = {"Authorization": f"Bearer {fake_token}"}

        with allure.step("Act: Request report generation"):
            response = client.post(
                "api/v1/report/generate-pdf",
                json=CREATE_REPORT_PAYLOAD,
                headers=headers,
            )

        with allure.step("Assert: Verify 404 Not Found and empty Redis queue"):
            assert response.status_code == 404
            response_data = response.get_json()
            assert response_data["error"] == "User not found."
            assert test_redis.llen("pdf_task_queue") == 0


@allure.feature("Reporting")
@allure.story("Check Report Status")
class TestGetReportStatus:

    @allure.title("Successfully retrieve PROCESSED report status")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_report_status_success(self, client, auth_headers, db_session):
        with allure.step("Arrange: Insert processed report"):
            report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PROCESSED,
                file_key="report.pdf",
            )
            db_session.add(report)
            db_session.flush()

        with allure.step("Act: Send GET request to status endpoint"):
            response = client.get(
                f"api/v1/report/generate-pdf/{report.id}/status", headers=auth_headers
            )

        with allure.step("Assert: Verify 200 OK and fileKey presence"):
            assert response.status_code == 200
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.PROCESSED.value
            assert response_data["fileUrl"] == f"{S3_URL}/report.pdf"

    @allure.title("Fail to retrieve status for non-existent report")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_not_found(self, client, auth_headers):
        with allure.step("Act: Request status for ID 999"):
            response = client.get(
                "api/v1/report/generate-pdf/999/status", headers=auth_headers
            )

        with allure.step("Assert: Verify 404 Not Found"):
            assert response.status_code == 404
            response_data = response.get_json()
            assert "error" in response_data
            assert response_data["error"] == "Report not found or access denied."

    @allure.title("Fail to retrieve status without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_status_unauthorized(self, client):
        with allure.step("Act: Send GET without auth headers"):
            response = client.get("api/v1/report/generate-pdf/1/status")

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401
            response_data = response.get_json()
            assert response_data["details"] == "Missing Authorization Header"

    @allure.title("API Validation error on invalid report ID format")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_report_status_invalid_id(self, client, auth_headers):
        with allure.step("Act: Request status with string ID instead of integer"):
            response = client.get(
                "api/v1/report/generate-pdf/invalid_id/status", headers=auth_headers
            )

        with allure.step("Assert: Verify 404 Not Found (Flask routing)"):
            assert response.status_code == 404
            response_data = response.get_json()
            assert "message" in response_data
            assert "error" in response_data
            assert "Not Found" in response_data["error"]

    @allure.title("Return 410 Gone for expired report links")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_expired(self, client, auth_headers, db_session):
        with allure.step("Arrange: Insert expired report"):
            expired_report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PROCESSED,
                file_key="expired_report.pdf",
                expire_at=datetime.now(timezone.utc) - timedelta(days=1),
            )
            db_session.add(expired_report)
            db_session.flush()

        with allure.step("Act: Request status"):
            response = client.get(
                f"api/v1/report/generate-pdf/{expired_report.id}/status",
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 410 Gone and EXPIRED status"):
            assert response.status_code == 410
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.EXPIRED.value
            assert (
                response_data["error"]
                == "The report link has expired. Please generate a new report."
            )

    @allure.title("Return 400 Bad Request if report generation FAILED")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_failed(self, client, auth_headers, db_session):
        with allure.step("Arrange: Insert FAILED report"):
            failed_report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.FAILED,
            )
            db_session.add(failed_report)
            db_session.flush()

        with allure.step("Act: Request status"):
            response = client.get(
                f"api/v1/report/generate-pdf/{failed_report.id}/status",
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 400 Bad Request error"):
            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.FAILED.value
            assert response_data["error"] == "Report generation failed."

    @allure.title("Mark PENDING report as FAILED if timeout exceeded")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_status_pending_timeout(self, client, auth_headers, db_session):
        with allure.step("Arrange: Insert PENDING report older than 2 hours"):
            pending_report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
            db_session.add(pending_report)
            db_session.flush()

        with allure.step("Act: Request status"):
            response = client.get(
                f"api/v1/report/generate-pdf/{pending_report.id}/status",
                headers=auth_headers,
            )

        with allure.step("Assert: Verify timeout handled and 400 returned"):
            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.FAILED.value
            assert (
                response_data["error"]
                == "The report generation timed out. Please request a new report."
            )

    @allure.title(
        "Return 202 Accepted if PENDING report is still processing in background"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_pending_no_result(
        self, client, auth_headers, db_session, test_redis
    ):
        with allure.step("Arrange: Insert recent PENDING report"):
            pending_report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            )
            db_session.add(pending_report)
            db_session.flush()

        with allure.step("Act: Request status"):
            response = client.get(
                f"api/v1/report/generate-pdf/{pending_report.id}/status",
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 202 Accepted (No Redis result yet)"):
            assert response.status_code == 202
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.PENDING.value
            assert response_data["id"] == pending_report.id

    @allure.title(
        "Update DB and return 200 OK if PENDING report finished successfully in Redis"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_status_pending_with_result(
        self, client, auth_headers, db_session, test_redis
    ):
        with allure.step(
            "Arrange: Insert PENDING report and mock Redis success result"
        ):
            pending_report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            )
            db_session.add(pending_report)
            db_session.flush()

            redis_result_key = f"report_result:{pending_report.id}"
            test_redis.set(
                redis_result_key,
                json.dumps(
                    {
                        "status": "success",
                        "fileKey": "generated_report.pdf",
                    }
                ),
            )

        with allure.step("Act: Request status"):
            response = client.get(
                f"api/v1/report/generate-pdf/{pending_report.id}/status",
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 200 OK and report mapped to PROCESSED"):
            assert response.status_code == 200
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.PROCESSED.value
            assert response_data["fileUrl"] == f"{S3_URL}/generated_report.pdf"

    @allure.title("Handle Redis worker error (Status: error) and update DB to FAILED")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_status_pending_with_failed_result(
        self, client, auth_headers, db_session, test_redis
    ):
        with allure.step("Arrange: Insert PENDING report and mock Redis error result"):
            pending_report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            )
            db_session.add(pending_report)
            db_session.flush()

            redis_result_key = f"report_result:{pending_report.id}"
            test_redis.set(
                redis_result_key,
                json.dumps({"id": pending_report.id, "status": "error"}),
            )

        with allure.step("Act: Request status"):
            response = client.get(
                f"api/v1/report/generate-pdf/{pending_report.id}/status",
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 400 Bad Request and FAILED status"):
            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.FAILED.value
            assert (
                response_data["error"] == "An error occurred during report generation."
            )

    @allure.title("Handle invalid Redis JSON result (missing fileUrl) gracefully")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_status_pending_with_invalid_result(
        self, client, auth_headers, db_session, test_redis
    ):
        with allure.step("Arrange: Mock invalid JSON in Redis (no fileUrl)"):
            pending_report = Reports(
                user_id=1,
                start_date="2024-01-01",
                end_date="2026-01-31",
                status=ReportStatus.PENDING,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            )
            db_session.add(pending_report)
            db_session.flush()

            redis_result_key = f"report_result:{pending_report.id}"
            test_redis.set(redis_result_key, json.dumps({"status": "success"}))

        with allure.step("Act: Request status"):
            response = client.get(
                f"api/v1/report/generate-pdf/{pending_report.id}/status",
                headers=auth_headers,
            )

        with allure.step("Assert: Verify 400 Bad Request error returned"):
            assert response.status_code == 400
            response_data = response.get_json()
            assert response_data["status"] == ReportStatus.FAILED.value
            assert (
                response_data["error"]
                == "Report generation failed due to missing file URL."
            )


@allure.feature("Reporting")
@allure.story("Report History")
class TestGetReportHistory:

    @allure.title("Successfully fetch report history list")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_report_history_success(
        self, client, auth_headers, db_session, test_redis
    ):
        with allure.step("Arrange: Insert various reports into DB"):
            report1 = Reports(
                user_id=1,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2026, 1, 31),
                status=ReportStatus.PROCESSED,
                file_key="report1.pdf",
            )
            report2 = Reports(
                user_id=1,
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                status=ReportStatus.FAILED,
                file_key=None,
            )
            db_session.add_all([report1, report2])
            db_session.flush()

        with allure.step("Act: Fetch history"):
            response = client.get("api/v1/report/history", headers=auth_headers)

        with allure.step("Assert: Verify 200 OK and mapping format"):
            assert response.status_code == 200
            response_data = response.get_json()
            assert len(response_data) == 2
            assert response_data[0]["status"] == ReportStatus.PROCESSED.value
            assert response_data[0]["fileUrl"] == f"{S3_URL}/report1.pdf"
            assert response_data[1]["status"] == ReportStatus.FAILED.value

    @allure.title("Fail to fetch report history without authorization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_history_unauthorized(self, client, test_redis):
        with allure.step("Act: Fetch history without auth headers"):
            response = client.get("api/v1/report/history")

        with allure.step("Assert: Verify 401 Unauthorized"):
            assert response.status_code == 401
            response_data = response.get_json()
            assert response_data["details"] == "Missing Authorization Header"

    @allure.title("Return empty list if user has no report history")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_history_no_reports(self, client, auth_headers, test_redis):
        with allure.step("Act: Fetch empty history"):
            response = client.get("api/v1/report/history", headers=auth_headers)

        with allure.step("Assert: Verify 200 OK with empty array"):
            assert response.status_code == 200
            response_data = response.get_json()
            assert isinstance(response_data, list)
            assert len(response_data) == 0

    @allure.title("Map expired links to null inside report history")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_report_history_reports_with_expired_links(
        self, client, auth_headers, db_session, test_redis
    ):
        with allure.step("Arrange: Insert expired and valid reports"):
            expired_report = Reports(
                user_id=1,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2026, 1, 31),
                status=ReportStatus.PROCESSED,
                file_key="expired_report.pdf",
                expire_at=datetime.now(timezone.utc) - timedelta(days=1),
            )
            valid_report = Reports(
                user_id=1,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2026, 1, 31),
                status=ReportStatus.PROCESSED,
                file_key="valid_report.pdf",
                expire_at=datetime.now(timezone.utc) + timedelta(days=3),
            )
            db_session.add_all([expired_report, valid_report])
            db_session.flush()

        with allure.step("Act: Fetch history"):
            response = client.get("api/v1/report/history", headers=auth_headers)

        with allure.step("Assert: Verify expired link is replaced by None"):
            assert response.status_code == 200
            response_data = response.get_json()
            assert len(response_data) == 2
            assert response_data[0]["status"] == ReportStatus.EXPIRED.value
            assert response_data[0]["fileUrl"] is None
            assert response_data[1]["status"] == ReportStatus.PROCESSED.value
            assert response_data[1]["fileUrl"] == f"{S3_URL}/valid_report.pdf"

    @allure.title("Correctly fetch report history containing mixed statuses")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_report_history_reports_with_various_statuses(
        self, client, auth_headers, db_session, test_redis
    ):
        with allure.step("Arrange: Insert PENDING, FAILED, and PROCESSED reports"):
            pending_report = Reports(
                user_id=1,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2026, 1, 31),
                status=ReportStatus.PENDING,
            )
            failed_report = Reports(
                user_id=1,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2026, 1, 31),
                status=ReportStatus.FAILED,
            )
            processed_report = Reports(
                user_id=1,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2026, 1, 31),
                status=ReportStatus.PROCESSED,
                file_key="processed_report.pdf",
            )

            db_session.add_all([pending_report, failed_report, processed_report])
            db_session.flush()

        with allure.step("Act: Fetch history"):
            response = client.get("api/v1/report/history", headers=auth_headers)

        with allure.step("Assert: Verify all 3 statuses are properly mapped"):
            assert response.status_code == 200
            response_data = response.get_json()
            assert len(response_data) == 3
            assert response_data[0]["status"] == ReportStatus.PENDING.value
            assert response_data[0]["fileUrl"] is None
            assert response_data[1]["status"] == ReportStatus.FAILED.value
            assert response_data[1]["fileUrl"] is None
            assert response_data[2]["status"] == ReportStatus.PROCESSED.value
            assert response_data[2]["fileUrl"] == f"{S3_URL}/processed_report.pdf"
