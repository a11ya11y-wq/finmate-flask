from .repository import ProfileRepository
from werkzeug.security import check_password_hash, generate_password_hash



class ProfieService:

    def __init__(self):
        self.repo = ProfileRepository()


    def get_user_info(self, user_id):
        user = self.repo.get_user_info(user_id)

        if not user:
            raise ValueError("User not found.")

        return user

    def update_user(self, user_id, data):
        user = self.get_user_info(user_id)

        if 'username' in data and not data['username']:
            raise ValueError("Username cannot be empty.")
        if 'email' in data and not data['email']:
            raise ValueError("Email cannot be empty.")

        updated_user = self.repo.update_user(user_id, data)

        return updated_user


    def delete_user(self, user_id):
        user_to_delete = self.repo.get_user_info(user_id)

        if not user_to_delete:
            raise ValueError(f"User with id {user_id} not found.")

        self.repo.delete_user(user_to_delete)

        return True


    def change_password(self, user_id, data):
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not old_password or not new_password or not confirm_password:
            raise ValueError("All fields (old_password, new_password, confirm_password) are required.")

        if new_password == old_password:
            raise ValueError("New password cannot be the same as the old password.")

        if new_password != confirm_password:
            raise ValueError("New password and confirmation do not match.")

        user_obj = self.get_user_info(user_id)

        if not user_obj:
            raise ValueError('User not found.')

        if not user_obj.chek_hash_pwd(old_password):
            raise ValueError("Invalid old password.")

        new_hash = generate_password_hash(new_password)

        self.repo.change_password_hash(user_obj, new_hash)

        return True