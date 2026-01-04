from flask import request, jsonify, make_response
from flask_jwt_extended import jwt_required

from .service import AuthService
from backend.finmate.auth import bp
from finmate.utils.error_parser import parse_exception



service = AuthService()

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        remember_me = data.get('remember_me', False)

        access_token, refresh_token, delta = service.login_user(data, remember_me)
        resp = make_response(jsonify({
            "access_token": access_token,
            "message": "Login successful."
        }), 200)

        resp.set_cookie(
            key='finmate_refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,  # На продакшн сервері має бути True і в логаут добавить!
            samesite='Lax',
            path='/api/auth/refresh',
            max_age=delta
        )
        return resp

    except Exception as e:
        return parse_exception(e)


@bp.route('/refresh', methods=['POST'])
def refresh():
    refresh_token = request.cookies.get("finmate_refresh_token")
    if not refresh_token:
        return jsonify({"error": "Missing refresh token, please login again"}), 401

    try:
        new_access_token = service.refresh_access_token(refresh_token)
        return jsonify(access_token=new_access_token), 200
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


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"msg": "Invalid Token Format"}), 401

        access_token = auth_header.split(" ")[1]

        service.logout_user(access_token)

        resp = make_response(jsonify({"message": "Successfully logged out"}), 200)

        resp.set_cookie(
            'finmate_refresh_token',
            '',
            expires=0,
            httponly=True,
            secure=False,
            path='/api/auth/refresh'
        )
        return resp
    except Exception as e:
        return parse_exception(e)
