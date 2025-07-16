from flask_wtf import FlaskForm

from wtforms import (
    DateField,
    SelectField,
    StringField,
    SelectMultipleField,
    BooleanField,
)
from wtforms.validators import DataRequired, Regexp, InputRequired
from wtforms.widgets import TextArea


import datetime as dt


source_choices = [
    ("AP", "Assistant Principal"),
    ("AT", "Attendance Teacher"),
    ("CA", "Community Associate"),
    ("FA", "Family Assistant"),
    ("GC", "Guidance Counselor"),
    ("PR", "Principal"),
    ("PS","Pupil Accounting Secretary"),
    ("SA","School Aide"),
    ("SC","SAPSIS/SPARK Counselor"),
    ("SP","School Psychologist"),
    ("SS","Social Worker"),
    ("TE","Instructional Teacher"),
]

action_taken_choices = [
    ("1","Telephone Call"),
    ('A","Academic Intervention'),
    ("C","Met Parent - P/T Conference"),
    ("E","Email sent"),
    ("F","Fax sent"),
    ("H","Health referral"),
    ("M","Mentor Session"),
    ("N","News or Update: NOACT"),
    ("O","Contact Other Agenct"),
    ("S","School Mtg/Workshop"),
    ("T","Text or App Push Notification"),
    ("X","Extra-Curricular Activity"),
    ("2","Letter Sent"),
    ("3","Home visit"),
    ("4","school conference"),
    ("5","Referral to ACS"),
    ("6","Promotion in Doubt Ltr"),
    ("7","Summer School Ltr"),
    ("8","Subject Failure Ltr"),
    ]

action_taken_choices = [
    ("1","Telephone Call"),]

class iLogForm(FlaskForm):
    students_str = StringField("StudentID List", widget=TextArea())

    intervention_date = DateField(
        default=dt.datetime.today
    )

    source_str = SelectField(
        "Source",
        choices=source_choices,
        validators=[InputRequired()],
    )    

    action_taken_str = SelectField(
        "Action Taken",
        choices=action_taken_choices,
        validators=[InputRequired()],
    )    

    comments_str = StringField(
        "Comments",
        widget=TextArea(),
        validators=[DataRequired()],)
    
    ats_region = SelectField(
        "ATS Region",
        choices=[("ATSSUM", "ATSSUM"),("ATS", "ATS")],
        validators=[InputRequired()],
    )     