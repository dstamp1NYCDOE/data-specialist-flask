from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (
    DateField,
    SelectField,
    StringField,
    SelectMultipleField,
    BooleanField,
)
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import TextArea

from werkzeug.utils import secure_filename


class ReturnMailingLabelsFromStudentPDFForm(FlaskForm):
    student_records_pdf = FileField(
        "Student Records as PDF",
        validators=[FileRequired()],
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ReturnMailingLabelsByStudentIDListForm(FlaskForm):
    subset_lst = StringField("StudentID List", widget=TextArea())
    
