from flask import request, jsonify, make_response

from .service import AuthService
from backend.finmate.auth import bp
from finmate.utils.error_parser import parse_exception



service = AuthService()

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        token = service.login_user(data)
        # Return token and set cookie as fallback for clients that can't persist localStorage
        resp = make_response(jsonify(access_token=token), 200)
        # Set cookie for current origin; not HttpOnly so frontend can read if needed in dev
        resp.set_cookie('finmate_token', token, path='/', samesite='Lax')
        return resp

    except Exception as e:
        return parse_exception(e)


@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        new_user = service.create_user(data)
        return jsonify(new_user.to_dict()), 201

    except Exception as e:
        return parse_exception(e)

