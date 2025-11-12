from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
from backend.finmate.profile import bp
from .service import ProfieService



service = ProfieService()


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        user_id = int(get_jwt_identity())
        user = service.get_user_info(user_id)
        return jsonify(user.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_user():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        updated_user = service.update_user(user_id, data)
        return jsonify(updated_user.to_dict()), 200

    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"error": str(e)}), status_code

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_account():
    user_id = int(get_jwt_identity())
    try:
        service.delete_user(user_id)
        return '', 204

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        service.change_password(user_id, data)
        return jsonify({"message": "Password updated successfully"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# @bp.route('/', methods=['POST', 'GET'])
# @login_required
# def profile():
#     form = ProfileForm(original_username=current_user.username)
#     delete_form = DeleteForm()
#     category_form = CategoryForm()
#     confirm_delete_form = ConfirmDeleteForm()
#
#     #Progres bar
#     current_user_categories = Category.query.filter_by(user_id=current_user.id).count()
#     max_category_limit =MAX_CATEGORIES_PER_USER
#
#     if form.validate_on_submit():
#         current_user.username = form.new_username.data
#         current_user.avatar = form.avatar.data
#
#         if form.new_password.data:
#             current_user.set_hash_pwd(form.new_password.data)
#             flash('Password successfully updated!', 'success')
#         try:
#             db.session.commit()
#         except Exception as e:
#             db.session.rollback()
#             flash(f'Error during update: {e}', 'danger')
#             return redirect(url_for('profile.profile'))
#
#     elif request.method == 'GET':
#         form.new_username.data  = current_user.username
#         form.avatar.data = current_user.avatar
#
#
#     categories = Category.query.filter_by(user_id=current_user.id)
#     return render_template('profile.html',
#                            form=form,
#                            delete_form=delete_form,
#                            categories=categories,
#                            category_form=category_form,
#                            current_user_categories=current_user_categories,
#                            max_category_limit=max_category_limit,
#                            confirm_delete_form=confirm_delete_form
#                            )
