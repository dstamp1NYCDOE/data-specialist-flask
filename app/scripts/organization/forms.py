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


class OrganizeStudentRecordsForm(FlaskForm):
    student_records_pdf = FileField(
        "Student Records as PDF",
        validators=[FileRequired()],
    )

    student_records_pdf_orientation = SelectField(
        "Student Records PDF Page Orientation",
        choices=[("landscape", "Landscape"), ("portrait", "Portrait")],
        validators=[InputRequired()],
    )

    student_list = FileField(
        "Student List as Spreadsheet",
        description="File must be saved as .xlsx",
        validators=[FileRequired()],
    )

    student_list_source = SelectField(
        "StudentID Column",
        choices=[
            ("STARS_Classlist_Report", "STARS Classlist Report"),
            ("teacher_and_room_list", "Teacher + Room List"),
        ],
        validators=[InputRequired()],
    )

    include_classlist_boolean = BooleanField("Include Classlist")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ClassListCountsFromSubsetForm(FlaskForm):
    subset_lst = StringField("StudentID List", widget=TextArea())
    subset_title = StringField("Subgroup title")


class ClassRostersFromList(FlaskForm):
    subset_lst = StringField("StudentID List", widget=TextArea())
    subset_title = StringField("Subgroup title")

    teacher = SelectField(
        "Teacher",
        choices=[
            ("BOTH", "BOTH"),
            ("Teacher1", "Teacher1"),
            ("Teacher2", "Teacher2"),
            ("NoTeacherPages", "None"),
        ],
        validators=[InputRequired()],
    )

    periods = SelectMultipleField(
        "Periods",
        choices=[
            ("ALL", "ALL"),
            ("1", "P1"),
            ("2", "P2"),
            ("3", "P3"),
            ("4", "P4"),
            ("5", "P5"),
            ("6", "P6"),
            ("7", "P7"),
            ("8", "P8"),
            ("9", "P9"),
        ],
        validators=[InputRequired()],
        default=["ALL"],
    )

    course_lst = StringField("Course List - Leave blank to include all courses", widget=TextArea())

    computer_labs_flag = BooleanField("Computer Labs Only", default=False)

    include_counselors_flag = BooleanField("Include Counselors", default=False)

    inner_or_outer = SelectField(
        "Mode",
        choices=[
            ("inner", "Return Students In List"),
            ("outer", "Return Students Not In List"),
            ("combined", "Full List with True False"),
        ],
        validators=[InputRequired()],
    )


class CareerDayReportsForm(FlaskForm):
    survey_responses = FileField(
        "Student Survey Responses",
        description="Each sheet of the spreadsheet should be the responses from a interest form",
        validators=[FileRequired()],
    )
    locations_file = FileField(
        "Locations (.CSV)",
        description="Locations as .csv file",
        validators=[FileRequired()],
    )
    output_file = SelectField(
        "Output File",
        choices=[("xlsx", "Assignments as Spreadsheet"), ("pdf", "Assignment Letters")],
        validators=[InputRequired()],
    )


class MailingLabelsByPeriod(FlaskForm):

    periods = SelectMultipleField(
        "Periods",
        choices=[
            ("ALL", "ALL"),
            ("1", "P1"),
            ("2", "P2"),
            ("3", "P3"),
            ("4", "P4"),
            ("5", "P5"),
            ("6", "P6"),
            ("7", "P7"),
            ("8", "P8"),
            ("9", "P9"),
        ],
        validators=[InputRequired()],
        default=["ALL"],
    )


class FolderLabelsByTeacherForm(FlaskForm):

    student_list = FileField(
        "Student List as Spreadsheet",
        description="File must be saved as .xlsx",
        validators=[FileRequired()],
    )

    student_list_source = SelectField(
        "StudentID Column",
        choices=[
            ("STARS_Classlist_Report", "STARS Classlist Report"),
            ("teacher_and_room_list", "Teacher + Room List"),
        ],
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StudentPrivilegeSummaryForm(FlaskForm):

    StudentID = SelectField(
        "Select Student",
        choices=[(0, "Select Student")],
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
