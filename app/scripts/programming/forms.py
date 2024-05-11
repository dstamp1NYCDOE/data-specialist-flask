from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import NumberInput


from werkzeug.utils import secure_filename

import datetime as dt


class StudentVettingForm(FlaskForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InitialRequestForm(FlaskForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InitialRequestInformLetters(FlaskForm):

    date_of_letter = DateField(validators=[InputRequired()])

    due_date = DateField(validators=[InputRequired()])

    def __init__(self, *args, **kwargs):
        self.date_of_letter.data = dt.datetime.today()
        self.due_date.data = dt.datetime.today() + dt.timedelta(days=14)
        super().__init__(*args, **kwargs)


class MajorReapplicationForm(FlaskForm):
    num_of_photography_seats = IntegerField(
        "Number of Photography Seats",
        widget=NumberInput(min=0, max=2 * 25, step=1),
        default=25,
    )

    num_of_vp_seats = IntegerField(
        "Number of Visual Presentation Seats",
        widget=NumberInput(min=0, max=2 * 25, step=1),
        default=25,
    )

    num_of_software_design_seats = IntegerField(
        "Number of Software Design Seats",
        widget=NumberInput(min=0, max=2 * 25, step=1),
        default=25,
    )

    num_of_business_seats = IntegerField(
        "Number of Business Seats",
        widget=NumberInput(min=0, max=3 * 25, step=1),
        default=50,
    )

    num_of_fashion_seats = IntegerField(
        "Number of Fashion Design Seats",
        widget=NumberInput(min=0, max=6 * 25, step=1),
        default=5 * 25,
    )

    num_of_art_and_design_seats = IntegerField(
        "Number of Art and Design Design Seats",
        widget=NumberInput(min=0, max=8 * 25, step=1),
        default=6 * 25,
    )

    student_survey_file = FileField(
        "Student Survey File",
        validators=[FileRequired()],
    )

    student_requests_file = FileField(
        "Student Requests (CR 4.01)",
        validators=[FileRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
