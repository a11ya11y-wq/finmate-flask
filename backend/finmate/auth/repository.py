from backend.finmate.extensions import db
from backend.finmate.models import Category, Users
from backend.finmate.constants import DEFAULT_CATEGORIES


class AuthRepository:


    def find_user_by_name(self, username):
        return Users.query.filter_by(username=username).first()

    def find_user_by_email(self, email):
        return Users.query.filter_by(email=email).first()


    def create_user_with_cat(self, data):
        new_user = Users(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('hashed_password')
        )
        categories_to_add = []
        try:
            db.session.add(new_user)
            new_cat = []
            for cat_data in DEFAULT_CATEGORIES:
                category = Category(
                    name=cat_data['name'],
                    user=new_user,
                    icon=cat_data['icon'],
                    mcc_code=cat_data['mcc_code']
                )
                categories_to_add.append(category)

            db.session.add_all(categories_to_add)
            db.session.commit()
            return new_user
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error while creating account in DB: {e}')

