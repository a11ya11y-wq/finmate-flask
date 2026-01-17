from pydantic import ValidationError

from finmate.exceptions import FinMateError
import traceback
from flask import jsonify

def parse_exception(e: Exception):
    if isinstance(e, FinMateError):
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
        return jsonify({"error": "Validation Error", "details": errors}), 422

    print("!CRITICAL SERVER ERROR!")
    traceback.print_exc()

    return jsonify({
        "error": "Internal Server Error",
        "message": "Something went wrong on our side. Please try again later."
    }), 500
