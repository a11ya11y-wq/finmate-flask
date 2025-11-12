from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import bp
from .service import TransactionService


service = TransactionService()


@bp.route('/', methods=['POST'])
@jwt_required()
def create_transaction():

    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        new_tx = service.create_transaction(data, user_id)
        return jsonify(new_tx.to_dict()), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:tx_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(tx_id):
    user_id = get_jwt_identity()
    try:
        service.delete_transaction(tx_id, user_id)
        return '', 204

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:tx_id>', methods=['PUT'])
@jwt_required()
def update_transaction(tx_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        updated_tx = service.update_transaction(tx_id, user_id, data)
        return jsonify(updated_tx.to_dict()), 200

    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"error": str(e)}), status_code

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@bp.route('/<int:tx_id>', methods=['GET'])
@jwt_required()
def get_transaction(tx_id):
    user_id = get_jwt_identity()
    try:
        transaction = service.get_transaction(tx_id, user_id)
        return jsonify(transaction.to_dict()), 200

    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify({"error": str(e)}), status_code

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# @bp.route('/sync', methods=['POST'])
# @login_required
# def sync_transaction():#TODO: Захист від спаму (в бд добавить ласт_моно_реквест(Дейттайм))
#     form = DeleteForm()
#
#     if form.validate_on_submit():
#
#         token_bytes = current_user.monobank_api_token
#
#         if not token_bytes:
#             flash('API token not found! Please add it in the settings.','danger')
#             return redirect(url_for('core.dashboard'))
#
#         try:
#             api = MonoAPI(encrypted_token_bytes=token_bytes)
#             client_info = api.get_client_info()
#         except Exception as e:
#             flash(f'Error processing token: {e}. Please update your token.', 'danger')
#             return redirect(url_for('core.dashboard'))
#
#         if not client_info or 'accounts' not in client_info:
#             error_msg = client_info.get('errorDescription', 'Invalid API token') if isinstance(client_info,
#                                                                                                dict) else 'Invalid API token'
#             flash(f'Monobank Error: {error_msg}', 'danger')
#             return redirect(url_for('core.dashboard'))
#
#         account_id = client_info['accounts'][0]['id']
#         thirty_days_ago = datetime.utcnow() - timedelta(days=30)
#         from_time = int(thirty_days_ago.timestamp())
#
#         transactions_from_mono = api.get_transactions(account_id, from_time)
#
#         if isinstance(transactions_from_mono, dict):
#             error_msg = transactions_from_mono.get('errorDescription', 'Unknown API Error')
#             if error_msg == 'Too many requests':
#                 flash('Too many requests! The Monobank API allows 1 request per minute. Please wait.', 'warning')
#             else:
#                 flash(f'API Error: {error_msg}', 'danger')
#
#             return redirect(url_for('core.dashboard'))
#
#         if transactions_from_mono is None:
#             flash('Error connecting to Monobank API. Please try again in a moment.', 'danger')
#             return redirect(url_for('core.dashboard'))
#
#         if not transactions_from_mono:
#             flash('No new transactions found.', 'info')
#             return redirect(url_for('core.dashboard'))
#
#         default_category = Category.query.filter_by(user_id=current_user.id, name="Uncategorized").first()
#
#         if not default_category:
#             default_category = Category(name="Uncategorized", user_id=current_user.id)
#             db.session.add(default_category)
#             try:
#                 db.session.commit()
#             except Exception as e :
#                 db.session.rollback()
#                 flash(f'Could not create default category. {e}', 'danger')
#                 return redirect(url_for('core.dashboard'))
#
#         default_category_id = default_category.id
#         mcc_map = {}
#         all_categories = Category.query.filter(Category.user_id == current_user.id).all()
#
#         for cat in all_categories:
#             if cat.mcc_code:
#                 codes = cat.mcc_code.split(',')
#                 for code in codes:
#                     mcc_map[code.strip()] = cat.id
#
#         mono_ids = {t['id'] for t in transactions_from_mono}
#
#         existing_ids_query = db.session.query(Transactions.mono_id).filter(
#             Transactions.user_id == current_user.id,
#             Transactions.mono_id.in_(mono_ids)
#         )
#
#         existing_ids_set = {str(id_tuple[0]) for id_tuple in existing_ids_query}
#         new_transactions_to_add = []
#
#         for t_dict in transactions_from_mono:
#             if t_dict['id'] not in existing_ids_set:
#
#                 mcc_code_str = str(t_dict.get('mcc', ''))
#                 assigned_category_id = mcc_map.get(mcc_code_str, default_category_id)
#
#                 new_trans = Transactions(
#                     title=t_dict['description'],
#                     amount=abs(t_dict['amount'] / 100.0),
#                     created_at=datetime.fromtimestamp(t_dict['time']),
#                     user_id=current_user.id,
#                     mono_id=t_dict['id'],
#                     transaction_type='income' if t_dict['amount'] > 0 else 'expense',
#                     category_id =assigned_category_id
#                 )
#                 new_transactions_to_add.append(new_trans)
#         if not new_transactions_to_add:
#             flash('Your transactions are up to date.', 'info')
#             return redirect(url_for('core.dashboard'))
#         try:
#             db.session.add_all(new_transactions_to_add)
#             db.session.commit()
#             flash(f'Successfully added {len(new_transactions_to_add)} new transactions!', 'success')
#         except Exception as e:
#             db.session.rollback()
#             flash(f'Error saving new transactions: {e}', 'danger')
#     else:
#         flash('Invalid request.', 'danger')
#
#     return  redirect(url_for('core.dashboard'))