import os

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, NumberRange
from flask_login import current_user

from finmate.models import Users, Category, Transactions, Budget
from flask import current_app


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=6, max=50, message='The username must be at least 6 characters long.')])
    email = StringField('Email', validators=[DataRequired(), Email(message="Please enter a valid email address.")]) # pip install email-validator
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message='The password must be at least 6 characters long.')])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Please use a different email address.')


class ProfileForm(FlaskForm):
    new_username = StringField('New Username', validators=[DataRequired(), Length(min=6, max=50, message='The username must be at least 6 characters long.')])
    avatar = RadioField('Choose Avatar', validators=[DataRequired(message='Please select an avatar.')])
    old_password = PasswordField('Old Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6, message='The password must be at least 6 characters long.')])
    confirm_new_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('new_password', message='Passwords must match.')])
    submit = SubmitField('Save Changes')


    def __init__(self, original_username, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

        try:
            default_avatars_path = os.path.join(current_app.static_folder, 'avatars/default')
            default_avatars = os.listdir(default_avatars_path)
            self.avatar.choices = [(f'avatars/default/{avatar}', avatar) for avatar in default_avatars]
        except Exception as e:
            print(f"CRITICAL: Could not load avatars. Error: {e}")
            self.avatar.choices = []


    def validate_new_username(self, new_username):
        if new_username.data !=self.original_username:
            user = Users.query.filter_by(username=new_username.data).first()
            if user:
                raise ValidationError('This username is already taken. Please choose another one.')


    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        if self.new_password.data:
            if not self.old_password.data:
                self.old_password.errors.append('You need to enter your old password to set a new one.')
                return False

            if not current_user.check_hash_pwd(self.old_password.data):
                self.old_password.errors.append('Incorrect old password.')
                return False

            if self.new_password.data == self.old_password.data:
                self.new_password.errors.append('The new password must not be the same as the old one.')
                return False

            if not self.confirm_new_password.data:
                self.confirm_new_password.errors.append('Please confirm your new password.')
                return False
        return True



    def validate_new_password(self, new_password):
        if new_password.data == self.old_password.data:
            raise ValidationError('The new password must not be the same as the old one.')


    def validate_old_password(self, old_password):
        if not current_user.chek_hash_pwd(old_password.data):
            raise ValidationError('Incorrect old password.')


class CategoryForm(FlaskForm):
    category_name = StringField('Enter New Category Name', validators=[DataRequired(message='The category name cannot be empty.')])
    submit = SubmitField('Add')


    def validate_category_name(self, category_name):
        category_exsist=  Category.query.filter_by(name=category_name.data, user_id=current_user.id).first()
        if category_exsist:
            raise ValidationError('A category with this name already exists.')


# Для делита категорий\транзакций і логаута
class DeleteForm(FlaskForm): #TODO: Допилить отдельне модульне окно на подтверждение пароля для делита акк
    submit = SubmitField('Delete Account')


class TransactionForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=1, max=100)])
    type = RadioField('Type', choices=[('expense', 'Expense'), ('income', 'Income')], validators=[DataRequired()]) #WTForms вимагає тапл з вибору (value, label)
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])# Встановить мін значение яке можна ввести в форму
    category = SelectField('Category', coerce=int, validators=[NumberRange(min=1,message='Please, enter a category.')]) # coerce=int автоматично перетворить цей рядок назад на число
    date = DateField('Date', validators=[Optional()])
    note = StringField('Note', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Add Transaction')

    def validate_category(self, category):
        exsist_category = Category.query.filter_by(id=category.data, user_id=current_user.id).first()
        if not exsist_category:
            raise ValidationError('An invalid category has been selected. Please refresh the page.')


class CurrencyForm(FlaskForm):
    currency = SelectField('Currency', choices=[('USD', '$ (USD)'), ('EUR', '€ (EUR)'), ('UAH', '₴ (UAH)')], validators=[DataRequired()])
    submit = SubmitField('Save Settings')



#TODO: Сделать форми для транзакций, бюджетов і для голов в будущем(Ще не реалізовано), подумать над сетингс мб тоже добавить
#TODO: ХТМЛ пересобрать под форми

