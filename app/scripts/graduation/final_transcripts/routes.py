import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import files_df
import app.scripts.utils as utils


from app.scripts.graduation import graduation

from app.scripts.graduation.final_transcripts.forms import PrepareFinalTranscriptWithDischargeDateForm
import app.scripts.graduation.final_transcripts.final_transcripts_with_discharge_date as final_transcripts_with_discharge_date


@graduation.route("final_transcripts_with_discharge_date", methods=["GET", "POST"])
def return_final_transcripts_with_discharge_date():
    if request.method == "GET":
        form = PrepareFinalTranscriptWithDischargeDateForm()
        return render_template(
            "/graduation/templates/graduation/final_transcripts/final_transcripts_with_discharge_date_form.html",
            form=form,
        )
    else:
        form = PrepareFinalTranscriptWithDischargeDateForm(request.form)
        f = final_transcripts_with_discharge_date.main(form, request)
        school_year = session["school_year"]
        download_name = f"Class of {school_year+1} Final Transcripts.pdf"
        # return ""
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
