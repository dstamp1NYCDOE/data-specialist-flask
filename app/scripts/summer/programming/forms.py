from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp, InputRequired

from werkzeug.utils import secure_filename

import datetime as dt


class UpdateGradebooksForm(FlaskForm):
    class_date = DateField(default=dt.datetime.today)


class SendingSchoolForm(FlaskForm):
    sending_school = SelectField()
