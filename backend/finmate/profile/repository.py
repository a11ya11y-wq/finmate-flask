from finmate.extensions import db
from finmate.models import Users




class ProfileRepository:

    def get_user_info(self, user_id) -> Users:
        return Users.query.get(user_id)


    def get_by_username(self, username):
        return Users.query.filter_by(username=username).first()


    def update_user(self, user_obj : Users, data):
        try:
            user_obj.username = data.get('username', user_obj.username)
            user_obj.email = data.get('email', user_obj.email)
            user_obj.currency = data.get('currency',   user_obj.currency)
            user_obj.avatar = data.get('avatar', user_obj.avatar)
            if 'monobank_api_token' in data:
                user_obj.monobank_api_token = data.get('monobank_api_token')
            db.session.commit()
            return user_obj
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while updating transaction in DB: {e}")


    def delete_monobank_token(self, user_obj):
        try:
            user_obj.monobank_api_token = None
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while deleting Monobank token in DB: {e}")


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


    def setup_initial_balance(self, user_obj: Users, initial_balance):
        try:
            user_obj.initial_balance = initial_balance
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while setup initial balance in DB: {e}")

    def update_real_balance(self, user_obj: Users, new_balance):
        try:
            user_obj.last_real_balance = new_balance
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error while updating last balance in DB: {e}")