from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import (DataRequired, Regexp, InputRequired)

from werkzeug.utils import secure_filename



class OrganizeStudentRecordsForm(FlaskForm):
    student_records_pdf = FileField(
        "Student Records as PDF",
        validators=[FileRequired()],
        )
    
    student_records_pdf_orientation = SelectField(
        "Student Records PDF Page Orientation",
        choices = [
            ('landscape','Landscape'),
            ('portrait','Portrait')
        ], 
        validators=[InputRequired()],
    )

    student_list = FileField(
        "Student List as Spreadsheet",
        validators=[FileRequired()]
        )
    
    student_list_source = SelectField(
        "StudentID Column",
        choices = [
            ('STARS_Classlist_Report','STARS Classlist Report')
        ], 
        validators=[InputRequired()],
    )



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
