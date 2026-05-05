import logging
import time

from .schemas import ReportRequestSchema
from core_service.exceptions import BusinessLogicError, ResourceNotFound
from core_service.uow import UnitOfWork
import uuid
import json
from core_service import extensions
import os
from flask import send_from_directory



logger = logging.getLogger(__name__)



class ReportService:

    def __init__(self):
        self.upload_folder = "/app/uploads"

    def generate_pdf_report(self, user_id: int, data: dict):

        validated_data = ReportRequestSchema.model_validate(data)
        payload = validated_data.model_dump(mode='json', exclude_unset=True)
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
            "pattern": 'reports_queue',
            "data": payload,
            "id": str(job_id)
        }

        channel = 'reports_queue'
        reply_channel = f'{channel}.reply'

        pubsub = extensions.redis_client.pubsub()
        pubsub.subscribe(reply_channel)

        start_time = time.time()
        timeout = 30  # seconds
        try:
            pubsub.publish(channel, json.dumps(message))
            logger.info(f"Published job {job_id} to {channel}. Waiting for NestJS...")

            while time.time() - start_time < timeout:

                raw_message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1)

                if raw_message:
                    response_payload = json.loads(raw_message['data'])

                    if response_payload.get('id') == job_id:

                        if 'err' in response_payload:
                            logger.error(f"NestJS returned an error: {response_payload['err']}")
                            raise BusinessLogicError(f"Microservice error: {response_payload['err']}")

                        data = response_payload.get('response')

                        if data is None:
                            logger.error(f"Received empty response for job {job_id}")
                            raise BusinessLogicError("Empty response from report service.")

                        logger.info(f"Successfully received report result for job {job_id}")
                        return data

            logger.error(f"Timeout waiting for NestJS response on job {job_id}")
            raise BusinessLogicError("Report service timeout.")

        except Exception as e:
            logger.error(f"Failed to publish report generation job to Redis channel '{channel}'")
            raise BusinessLogicError("Failed to initiate report generation.")

        finally:
            pubsub.unsubscribe(reply_channel)
            pubsub.close()


    def download_report(self, file_name: str):
        file_path = os.path.join(self.upload_folder, file_name)

        if not os.path.exists(file_path):
            raise BusinessLogicError("Report file not found on server.")

        return send_from_directory(
            self.upload_folder,
            file_name,
            as_attachment=True
        )

