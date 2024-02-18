from flask import render_template

import app.scripts.utils as utils
from app.scripts import scripts, files_df

import app.main.forms as report_forms
from app.scripts.programming.class_lists import generate_class_list
from app.scripts.surveys.connect_google_survey_with_class_lists import (
    connect_google_survey_with_class_lists,
)


@scripts.route("/programming")
def return_programming_reports():
    forms = {
        "class_list_form": report_forms.ReportForm(),
        "class_list_with_google_sheets_form": report_forms.ClassListWithGoogleFormResultsForm(),
    }
    return render_template("programming/templates/programming/index.html", forms=forms)
