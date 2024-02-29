from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import (DataRequired, Regexp)

from werkzeug.utils import secure_filename


school_year_and_semester_choices = [
            ("2023-2", "Spring 2024"),
            ("2023-1", "Fall 2023"),
            ("2022-7", "Summer 2023"),
            ("2022-2", "Spring 2023"),
            ("2022-1", "Fall 2022"),
            ("2021-7", "Summer 2022"),
            ("2021-2", "Spring 2022"),
            ("2021-1", "Fall 2021"),
        ]

reports_choices = [
    ('scripts.programming.class_lists','Class Lists'),
    ('scripts.surveys.connect_google_survey_with_class_lists','Class Lists with Google Sheets Data'),
]

class SemesterSelectForm(FlaskForm):
    year_and_semester = SelectField(
        "School Year and Semester",
        choices=school_year_and_semester_choices,
    )
    def __init__(self, *args, **kwargs):
        super(ClassListWithGoogleFormResultsForm, self).__init__(*args, **kwargs)
        self.report.data = "scripts.programming.class_lists"


class FileForm(FlaskForm):
    file = FileField(validators=[FileRequired()])
    download_date = DateField()
    year_and_semester = SelectField(
        "School Year and Semester",
        choices=school_year_and_semester_choices,
    )

class JupiterUpdateForm(FlaskForm):
    year_and_semester = SelectField(
        "School Year and Semester", choices=school_year_and_semester_choices,
    )
    report = SelectField(
       "Jupiter File" ,
       choices = [
            ("rosters-and-grades", "Grades and Rosters"),
        ]
    )

class ReportForm(FlaskForm):
    year_and_semester = SelectField(
        "School Year and Semester", choices=school_year_and_semester_choices,
    )
    report = SelectField(
       "Report" ,
       choices = reports_choices
    )

class ClassListsForm(ReportForm):
    def __init__(self, *args, **kwargs):
        super(ClassListWithGoogleFormResultsForm, self).__init__(*args, **kwargs)
        self.report.data =  'scripts.programming.class_lists'


class ClassListWithGoogleFormResultsForm(ReportForm):
    def __init__(self, *args, **kwargs):
        super(ClassListWithGoogleFormResultsForm, self).__init__(*args, **kwargs)
        self.report.data =  'scripts.surveys.connect_google_survey_with_class_lists'

    gsheet_url = StringField('Google Sheet', 
                             validators=[
                            DataRequired('URL is required'),
                             ]
               )

    student_id_columns = SelectField(
        "Which Column in the Google Sheet does 'StudentID' Appear?",
        choices=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
            ("E", "E"),
        ],
    )
