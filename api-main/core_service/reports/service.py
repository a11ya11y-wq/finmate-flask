import logging

from .schemas import ReportRequestSchema
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.uow import UnitOfWork
import uuid
import json
from core_service import extensions

logger = logging.getLogger(__name__)



class ReportService:

    def generate_pdf_report(self, user_id: int, data: dict):

        validated_data = ReportRequestSchema.model_validate(data)
        payload = validated_data.model_dump(exclude_unset=True)
        if not payload:
            raise BusinessLogicError("No valid fields to generate report.")
        payload['userId'] = user_id

        with UnitOfWork() as uow:
            user = uow.auth.find_user_by_id(user_id)

        if not user:
            logger.warning(f"User entity not found for user_id: {user_id}")
            raise ResourceNotFound("User not found.")

        job_id = str(uuid.uuid4())

        message = {
            "patterns": 'reports_queue',
            "data": payload,
            "jobId": job_id
        }

        channel = 'reports_queue'
        try:
            extensions.redis_client.publish(channel, json.dumps(message))
            logger.info(f"Published report generation job to Redis channel '{channel}' with job ID: {job_id}")
        except Exception as e:
            logger.error(f"Failed to publish report generation job to Redis channel '{channel}'")
            raise BusinessLogicError("Failed to initiate report generation.")

        return {"job_id": job_id, "status": "processing"}





