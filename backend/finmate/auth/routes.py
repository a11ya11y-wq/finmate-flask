from flask import request, jsonify, make_response

from .service import AuthService
from backend.finmate.auth import bp



service = AuthService()

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    try:
        token = service.login_user(data)
        # Return token and set cookie as fallback for clients that can't persist localStorage
        resp = make_response(jsonify(access_token=token), 200)
        # Set cookie for current origin; not HttpOnly so frontend can read if needed in dev
        resp.set_cookie('finmate_token', token, path='/', samesite='Lax')
        return resp
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        new_user = service.create_user(data)
        return jsonify(new_user.to_dict()), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

