from backend.finmate.db import db
from backend.finmate.models import Users




class ProfileRepository:

    def get_user_info(self, user_id):
        return Users.query.get(user_id)


    def update_user(self, user_obj, data):
        try:
            user_obj.username = data.get('username', user_obj.username)
            user_obj.email = data.get('email', user_obj.email)
            user_obj.currency = data.get('currency',   user_obj.currency)
            if 'monobank_api_token' in data:
                user_obj.monobank_api_token = data.get('monobank_api_token')
            db.session.commit()
            return user_obj
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while updating transaction in DB: {e}")


    def delete_user(self, user_obj):
        try:
            db.session.delete(user_obj)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while deleting user in DB: {e}")


    def change_password_hash(self, user_obj, password_hash):
        try:
            user_obj.password_hash = password_hash
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error while changing password in DB: {e}')
