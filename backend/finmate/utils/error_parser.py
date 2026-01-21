from pydantic import ValidationError

from finmate.exceptions import FinMateError
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)


def parse_exception(e: Exception):
    if isinstance(e, FinMateError):
        logger.warning(f"Business error on {request.path}: {str(e)}")
        return jsonify({"error": str(e)}), e.code

    if isinstance(e, ValidationError):
        errors = []
        for err in e.errors():
            if err['loc']:
                field = err['loc'][-1]
                message = f"{field}: {err['msg']}"
            else:
                message = err['msg']
            errors.append(message)

        logger.warning(f"Validation error on {request.path}: {errors}")
        return jsonify({"error": "Validation Error", "details": errors}), 422

    logger.exception("Unhandled exception occurred")

    return jsonify({
        "error": "Internal Server Error",
        "message": "Something went wrong on our side. Please try again later."
    }), 500
