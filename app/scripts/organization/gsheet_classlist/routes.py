import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils

from app.scripts.organization.gsheet_classlist.forms import UpdateClassListsOnGoogle
from app.scripts.organization.gsheet_classlist import main as update_gsheet_classlist


@scripts.route("/organization/classlists/update", methods=["GET", "POST"])
def return_updated_google_sheet_classlists():
    if request.method == "GET":
        form = UpdateClassListsOnGoogle()
        return render_template(
            "organization/templates/organization/gsheet_classlist/update_gsheet_classlist.html",
            form=form,
        )
    else:
        form = UpdateClassListsOnGoogle(request.form)
        df = update_gsheet_classlist.main(form, request)
        return df.to_html()
