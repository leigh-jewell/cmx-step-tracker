from flask_wtf import Form
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.fields.html5 import EmailField
from wtforms import validators
from wtforms import Form
from wtforms_components import DateField
from wtforms_components import IntegerField
from wtforms import RadioField
from wtforms import StringField

class RegistrationForm(Form):
    email = EmailField('email', validators=[validators.DataRequired(), validators.Email()])
    nickname = StringField('nickname', validators=[validators.DataRequired()])
    password = PasswordField('password', validators=[validators.DataRequired(), validators.Length(min=4, message="Please choose a password of at least 4 characters")])
    password2 = PasswordField('password2', validators=[validators.DataRequired(), validators.EqualTo('password', message='Passwords must match')])
    submit = SubmitField('submit', [validators.DataRequired()])


class AddDevice(Form):
    mac = StringField('mac', validators=[validators.DataRequired(), validators.MacAddress(),
                                         validators.NoneOf(['00:00:00:00:00:00','FF:FF:FF:FF:FF:FF'], message='Mac must be valid.')])


class LeaderboardForm(Form):
    date = DateField(
            'Date',format='%Y-%m-%d', validators=[validators.DataRequired()]
        )
    number_delegates = IntegerField(
        'Number',
        validators=[validators.NumberRange(
            min=1,
            max=1000
        )])
    format = RadioField('format', choices=[('graph', 'Graph'), ('table', 'Table')], default='graph')


class SparkLeaderboardForm(Form):
    spark_post = StringField('spark_post', validators=[validators.DataRequired()])
    submit = SubmitField('submit', [validators.DataRequired()])
