from flask import jsonify
from werkzeug.exceptions import HTTPException
from core_service.extensions import jwt

def register_error_handlers(app):

    #HTTP Exception handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            "error": "Too many requests",
            "message": "You have exceeded your request rate limit. Please try again later."
        }), 429

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        response = e.get_response()
        response.data = jsonify({
            "code": e.code,
            "error": e.name,
            "message": e.description
        }).data
        response.content_type = "application/json"
        return response

    # Auth error handlers
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "error": "Invalid token",
            "details": error
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "error": "Missing token",
            "details": error
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": "Token expired",
            "message": "The token has expired. Please log in again."
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": "Token revoked",
            "message": "The token has been revoked. Please log in again."
        }), 401