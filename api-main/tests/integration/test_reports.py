import pytest
from core_service.models.transaction_model import Transactions
from core_service.models.report_model import ReportStatus, Reports
from core_service.models.user_model import Users
import json
from datetime import datetime, timezone, timedelta

@pytest.fixture
def arrange_tx(db_session):
    tx1 = Transactions(
            user_id=1, 
            amount=350.00,
            title="Сільпо",
            transaction_type="expense",
            category_id=1,
            created_at="2025-11-15"
        )
        
    tx2 = Transactions(
        user_id=1,
        amount=12000.00,
        title="Зарплата",
        transaction_type="income",
        category_id=2,
        created_at="2025-11-20"
    )

    db_session.add_all([tx1, tx2])
    db_session.flush()

CREATE_REPORT_PAYLOAD = {
        "startDate": "2024-01-01",
        "endDate": "2026-01-31"
    }

@pytest.mark.usefixtures("db_session")
class TestGenerateReport:
    
    def test_generate_report_success(self, client, auth_headers, test_redis, arrange_tx):
        """Test successful report generation."""

        response = client.post('api/v1/report/generate-pdf', 
                              json=CREATE_REPORT_PAYLOAD,
                              headers=auth_headers,
                              )
        assert response.status_code == 202

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.PENDING.value
        assert 'id' in response_data

        queue_len = test_redis.llen("pdf_task_queue")
        assert queue_len == 1, f"Task was not enqueued in Redis. Current queue length: {queue_len}"

        task_raw = test_redis.lpop("pdf_task_queue")
        task_data = json.loads(task_raw)

        assert task_data["reportId"] == response_data["id"]
        assert task_data["user"]["email"] == "test@test.com"
        
        assert len(task_data["transactions"]) == 2

    def test_generate_report_no_transactions(self, client, auth_headers, test_redis):
        """Test report generation when no transactions are found."""

        payload = {
            "startDate": "2023-01-01",
            "endDate": "2023-12-31"
        }

        response = client.post('api/v1/report/generate-pdf', 
                              json=payload,
                              headers=auth_headers,
                              )
        assert response.status_code == 400

        response_data = response.get_json()
        assert 'error' in response_data
        assert response_data['error'] == "No transactions found for the specified period for report."

        queue_len = test_redis.llen("pdf_task_queue")
        assert queue_len == 0, f"Task should not be enqueued in Redis when no transactions are found. Current queue length: {queue_len}"

    def test_generate_report_invalid_dates(self, client, auth_headers):
        """Test report generation with invalid date range."""

        payload = {
            "startDate": "2024-12-31",
            "endDate": "2024-01-01"
        }

        response = client.post('api/v1/report/generate-pdf', 
                              json=payload,
                              headers=auth_headers,
                              )
        assert response.status_code == 422

        response_data = response.get_json()
        assert 'details' in response_data
        assert 'Start date must be before end date' in response_data['details'][0]

    def test_generate_report_missing_fields(self, client, auth_headers):
        """Test report generation with missing required fields."""

        payload = {
            "startDate": "2024-01-01"
        }

        response = client.post('api/v1/report/generate-pdf', 
                              json=payload,
                              headers=auth_headers,
                              )
        assert response.status_code == 422

        response_data = response.get_json()
        assert 'error' in response_data
        assert "Validation Error" in response_data['error']

    def test_generate_report_unauthorized(self, client):
        """Test report generation without authentication."""

        response = client.post('api/v1/report/generate-pdf', 
                              json=CREATE_REPORT_PAYLOAD,
                              )
        assert response.status_code == 401

        response_data = response.get_json()
        assert 'details' in response_data
        assert response_data['details'] == "Missing Authorization Header"

    def test_generate_report_existing_pending(self, client, auth_headers, test_redis, arrange_tx):
        """Test generating a report when an existing pending report exists."""

        response1 = client.post('api/v1/report/generate-pdf', 
                              json=CREATE_REPORT_PAYLOAD,
                              headers=auth_headers,
                              )
        assert response1.status_code == 202

        response2 = client.post('api/v1/report/generate-pdf', 
                              json=CREATE_REPORT_PAYLOAD,
                              headers=auth_headers,
                              )
        assert response2.status_code == 400

        response_data = response2.get_json()
        assert 'error' in response_data
        assert response_data['error'] == "Report generation is already in progress for the specified period."

    def test_generate_report_existing_processed(self, client, auth_headers, test_redis, arrange_tx, db_session):
        """Test generating a report when an existing processed report exists."""
        report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PROCESSED,
            file_url="http://example.com/report.pdf"
        )

        db_session.add(report)
        db_session.flush()

        response = client.post('api/v1/report/generate-pdf', 
                                json=CREATE_REPORT_PAYLOAD,
                                headers=auth_headers,
                                )
        
        assert response.status_code == 200

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.PROCESSED.value
        assert response_data['fileUrl'] == "http://example.com/report.pdf"
        assert response_data['id'] == report.id
        
    def test_generate_report_existing_failed(self, client, auth_headers, test_redis, arrange_tx, db_session):
        """Test generating a report when an existing failed report exists."""
        report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.FAILED
        )

        db_session.add(report)
        db_session.flush()

        response = client.post('api/v1/report/generate-pdf', 
                                json=CREATE_REPORT_PAYLOAD,
                                headers=auth_headers,
                                )
        
        assert response.status_code == 202

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.PENDING.value
        assert response_data['id'] != report.id

        queue_len = test_redis.llen("pdf_task_queue")
        assert queue_len == 1, f"Task was not enqueued in Redis. Current queue length: {queue_len}"
        
        task_raw = test_redis.lpop("pdf_task_queue")
        task_data = json.loads(task_raw)
        assert task_data["reportId"] == response_data["id"]

    def test_generate_report_existing_expired(self, client, auth_headers, test_redis, arrange_tx, db_session):
        """Test generating a report when an existing expired report exists."""
        expired_report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PROCESSED,
            file_url="http://example.com/expired_report.pdf",
            expire_at=datetime.now(timezone.utc) - timedelta(days=1)
        )

        db_session.add(expired_report)
        db_session.flush()

        response = client.post('api/v1/report/generate-pdf', 
                                json=CREATE_REPORT_PAYLOAD,
                                headers=auth_headers,
                                )
        
        assert response.status_code == 202

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.PENDING.value
        assert response_data['id'] != expired_report.id

        queue_len = test_redis.llen("pdf_task_queue")
        assert queue_len == 1, f"Task was not enqueued in Redis. Current queue length: {queue_len}"
        
        task_raw = test_redis.lpop("pdf_task_queue")
        task_data = json.loads(task_raw)
        assert task_data["reportId"] == response_data["id"]

    def test_generate_report_redis_failure(self, client, auth_headers, test_redis, arrange_tx, mocker):
        """Test fallback when Redis fails to enqueue the task."""
 
        mocker.patch.object(test_redis, 'rpush', side_effect=Exception("Redis died"))
        
        response = client.post('api/v1/report/generate-pdf',
                               json=CREATE_REPORT_PAYLOAD,
                               headers=auth_headers)

        assert response.status_code == 400
        assert "Failed to start report generation process" in response.get_json()['error']

        history_response = client.get('api/v1/report/history', headers=auth_headers)
        assert history_response.status_code == 200
        
        history_data = history_response.get_json()
        
        latest_report = history_data[-1] 
        
        assert latest_report['status'] == ReportStatus.FAILED.value

    def test_generate_report_user_not_found(self, client, test_redis, mocker):
        """Test report generation when user in token no longer exists in DB."""

        from flask_jwt_extended import create_access_token
        fake_token = create_access_token(identity="999")
        headers = {"Authorization": f"Bearer {fake_token}"}

        response = client.post('api/v1/report/generate-pdf', 
                               json=CREATE_REPORT_PAYLOAD,
                               headers=headers)
        
        assert response.status_code == 404
        response_data = response.get_json()
        assert response_data['error'] == "User not found."

        assert test_redis.llen("pdf_task_queue") == 0

class TestGetReportStatus:

    def test_get_report_status_success(self, client, auth_headers, db_session):
        """Test successful retrieval of report status."""
        report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PROCESSED,
            file_url="http://example.com/report.pdf"
        )

        db_session.add(report)
        db_session.flush()

        response = client.get(f'api/v1/report/generate-pdf/{report.id}/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 200

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.PROCESSED.value
        assert response_data['fileUrl'] == "http://example.com/report.pdf"

    def test_get_report_status_not_found(self, client, auth_headers):
        """Test retrieval of report status for non-existent report."""
        response = client.get('api/v1/report/generate-pdf/999/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 404

        response_data = response.get_json()
        assert 'error' in response_data
        assert response_data['error'] == "Report not found or access denied."

    def test_get_report_status_unauthorized(self, client):
        """Test retrieval of report status without authentication."""
        response = client.get('api/v1/report/generate-pdf/1/status')
        
        assert response.status_code == 401

        response_data = response.get_json()
        assert 'details' in response_data
        assert response_data['details'] == "Missing Authorization Header"

    def test_get_report_status_invalid_id(self, client, auth_headers):
        """Test retrieval of report status with invalid report ID."""
        response = client.get('api/v1/report/generate-pdf/invalid_id/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 404

        response_data = response.get_json()
        print(response_data)
        assert 'message' in response_data
        assert response_data['message'] == "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."
        assert 'error' in response_data
        assert "Not Found" in response_data['error']

    def test_get_report_status_expired(self, client, auth_headers, db_session):
        """Test retrieval of report status for an expired report."""
        expired_report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PROCESSED,
            file_url="http://example.com/expired_report.pdf",
            expire_at=datetime.now(timezone.utc) - timedelta(days=1)
        )

        db_session.add(expired_report)
        db_session.flush()

        response = client.get(f'api/v1/report/generate-pdf/{expired_report.id}/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 410

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.EXPIRED.value
        assert 'error' in response_data
        assert response_data['error'] == "The report link has expired. Please generate a new report."

    def test_get_report_status_failed(self, client, auth_headers, db_session):
        """Test retrieval of report status for a failed report."""
        failed_report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.FAILED
        )

        db_session.add(failed_report)
        db_session.flush()

        response = client.get(f'api/v1/report/generate-pdf/{failed_report.id}/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 400

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.FAILED.value
        assert 'error' in response_data
        assert response_data['error'] == "Report generation failed."

    def test_get_report_status_pending_timeout(self, client, auth_headers, db_session):
        """Test retrieval of report status for a pending report that has timed out."""
        pending_report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PENDING,
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )

        db_session.add(pending_report)
        db_session.flush()

        response = client.get(f'api/v1/report/generate-pdf/{pending_report.id}/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 400

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.FAILED.value
        assert 'error' in response_data
        assert response_data['error'] == "The report generation timed out. Please request a new report."

    def test_get_report_status_pending_no_result(self, client, auth_headers, db_session):
        """Test retrieval of report status for a pending report that has no result in Redis."""
        pending_report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PENDING,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )

        db_session.add(pending_report)
        db_session.flush()

        response = client.get(f'api/v1/report/generate-pdf/{pending_report.id}/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 202

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.PENDING.value
        assert response_data['id'] == pending_report.id

    def test_get_report_status_pending_with_result(self, client, auth_headers, db_session, test_redis):
        """Test retrieval of report status for a pending report that has a result in Redis."""
        pending_report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PENDING,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )

        db_session.add(pending_report)
        db_session.flush()

        redis_result_key = f"report_result:{pending_report.id}"
        test_redis.set(redis_result_key, json.dumps({
            "status": "success",
            "fileUrl": "http://example.com/generated_report.pdf"
        }))

        response = client.get(f'api/v1/report/generate-pdf/{pending_report.id}/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 200

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.PROCESSED.value
        assert response_data['fileUrl'] == "http://example.com/generated_report.pdf"

    def test_get_report_status_pending_with_failed_result(self, client, auth_headers, db_session, test_redis):
        """Test retrieval of report status for a pending report that has a failed result in Redis."""
        pending_report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PENDING,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )

        db_session.add(pending_report)
        db_session.flush()

        redis_result_key = f"report_result:{pending_report.id}"
        test_redis.set(redis_result_key, json.dumps({
            "id": pending_report.id,
            "status": "error"
        }))

        response = client.get(f'api/v1/report/generate-pdf/{pending_report.id}/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 400

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.FAILED.value
        assert 'error' in response_data
        assert response_data['error'] == "An error occurred during report generation."

    def test_get_report_status_pending_with_invalid_result(self, client, auth_headers, db_session, test_redis):
        """Test retrieval of report status for a pending report that has an invalid result in Redis."""
        pending_report = Reports(
            user_id=1,
            start_date="2024-01-01",
            end_date="2026-01-31",
            status=ReportStatus.PENDING,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )

        db_session.add(pending_report)
        db_session.flush()

        redis_result_key = f"report_result:{pending_report.id}"
        test_redis.set(redis_result_key, json.dumps({
            "status": "success"
        }))

        response = client.get(f'api/v1/report/generate-pdf/{pending_report.id}/status', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 400

        response_data = response.get_json()
        assert response_data['status'] == ReportStatus.FAILED.value
        assert 'error' in response_data
        assert response_data['error'] == "Report generation failed due to missing file URL."


class TestGetReportHistory:

    def test_get_report_history_success(self, client, auth_headers, db_session, test_redis):
        """Test successful retrieval of report history."""
        report1 = Reports(
            user_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2026, 1, 31),
            status=ReportStatus.PROCESSED,
            file_url="http://example.com/report1.pdf"
        )

        report2 = Reports(
            user_id=1,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            status=ReportStatus.FAILED
        )

        db_session.add_all([report1, report2])
        db_session.flush()

        response = client.get('api/v1/report/history', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 200

        response_data = response.get_json()
        assert len(response_data) == 2

        assert response_data[0]['status'] == ReportStatus.PROCESSED.value
        assert response_data[0]['fileUrl'] == "http://example.com/report1.pdf"

        assert response_data[1]['status'] == ReportStatus.FAILED.value

    def test_get_report_history_unauthorized(self, client, test_redis):
        """Test retrieval of report history without authentication."""
        response = client.get('api/v1/report/history')
        
        assert response.status_code == 401

        response_data = response.get_json()
        assert 'details' in response_data
        assert response_data['details'] == "Missing Authorization Header"

    def test_get_report_history_no_reports(self, client, auth_headers, test_redis):
        """Test retrieval of report history when no reports exist."""
        response = client.get('api/v1/report/history', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 200

        response_data = response.get_json()
        assert isinstance(response_data, list)
        assert len(response_data) == 0

    def test_get_report_history_reports_with_expired_links(self, client, auth_headers, db_session, test_redis):
        """Test retrieval of report history when some reports have expired links."""
        expired_report = Reports(
            user_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2026, 1, 31),
            status=ReportStatus.PROCESSED,
            file_url="http://example.com/expired_report.pdf",
            expire_at=datetime.now(timezone.utc) - timedelta(days=1)
        )

        valid_report = Reports(
            user_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2026, 1, 31),
            status=ReportStatus.PROCESSED,
            file_url="http://example.com/valid_report.pdf",
            expire_at=datetime.now(timezone.utc) + timedelta(days=3)
        )

        db_session.add_all([expired_report, valid_report])
        db_session.flush()

        response = client.get('api/v1/report/history', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 200

        response_data = response.get_json()
        assert len(response_data) == 2

        assert response_data[0]['status'] == ReportStatus.EXPIRED.value
        assert response_data[0]['fileUrl'] == None

        assert response_data[1]['status'] == ReportStatus.PROCESSED.value
        assert response_data[1]['fileUrl'] == "http://example.com/valid_report.pdf"

    def test_get_report_history_reports_with_various_statuses(self, client, auth_headers, db_session, test_redis):
        """Test retrieval of report history when reports have various statuses."""
        pending_report = Reports(
            user_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2026, 1, 31),
            status=ReportStatus.PENDING
        )

        failed_report = Reports(
            user_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2026, 1, 31),
            status=ReportStatus.FAILED
        )

        processed_report = Reports(
            user_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2026, 1, 31),
            status=ReportStatus.PROCESSED,
            file_url="http://example.com/processed_report.pdf"
        )

        db_session.add_all([pending_report, failed_report, processed_report])
        db_session.flush()

        response = client.get('api/v1/report/history', 
                              headers=auth_headers,
                              )
        
        assert response.status_code == 200

        response_data = response.get_json()
        assert len(response_data) == 3

        assert response_data[0]['status'] == ReportStatus.PENDING.value
        assert response_data[0]['fileUrl'] == None

        assert response_data[1]['status'] == ReportStatus.FAILED.value
        assert response_data[1]['fileUrl'] == None

        assert response_data[2]['status'] == ReportStatus.PROCESSED.value
        assert response_data[2]['fileUrl'] == "http://example.com/processed_report.pdf"