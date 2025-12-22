from backend.finmate.extensions import db
from backend.finmate.models import Category, Users


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
            default_categories_with_mcc = [ #TODO: Придумати куда перенести цей список + дополнить його
                                ('Food', '5411, 5812, 5814, 5499'),
                                ('Transport', '5541, 5542, 4121, 4111, 4784'),
                                ('Entertainment', '5813, 7832, 7922, 7996, 7999'),
                                ('Shopping', '5311, 5691, 5732, 5912, 5941, 5942'),
                                ('Utilities', '4900, 4814, 4899'),
                                ('Salary', None),
                                ('Uncategorized', None)
                            ]
            for cat_name, mcc_code in default_categories_with_mcc:
                new_category = Category(name=cat_name, user=new_user, mcc_code=mcc_code)
                categories_to_add.append(new_category)

            db.session.add_all(categories_to_add)
            db.session.commit()
            return new_user
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error while creating account in DB: {e}')

