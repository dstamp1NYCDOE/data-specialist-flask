import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils

from app.scripts.testing.regents.day_of_org.main import return_exambook_for_index


@scripts.route("testing/regents/day_of_org")
def return_regents_day_of_org():
    exambook = return_exambook_for_index()
    return render_template(
        "/testing/regents/day_of_org/templates/day_of_org/index.html", exambook=exambook
    )


from app.scripts.testing.regents.day_of_org.student_labels import (
    main as return_student_labels,
)

from app.scripts.testing.regents.day_of_org.folder_labels import (
    main as return_folder_labels,
)

from app.scripts.testing.regents.day_of_org.ENL_rosters import (
    main as return_ENL_rosters,
)

from app.scripts.testing.regents.day_of_org.bag_labels import (
    main as return_bag_labels,
)
from app.scripts.testing.regents.day_of_org.bathroom_passes import (
    main as return_bathroom_passes,
)

from app.scripts.testing.regents.day_of_org.direction_labels import (
    main as return_direction_labels,
)

from app.scripts.testing.regents.day_of_org.proctors_and_room_grid import (
    main as return_proctors_and_room_grid,
)

from app.scripts.testing.regents.day_of_org.checkout_roster import (
    main as return_checkout_roster,
)


@scripts.route("/testing/regents/day_of_org/<course>/<file>")
def return_regents_day_of_org_files(course, file):

    if file == "StudentLabels":
        f, download_name = return_student_labels(course, request)
    if file == "FolderLabels":
        f, download_name = return_folder_labels(course, request)
    if file == "ENLRosters":
        f, download_name = return_ENL_rosters(course, request)
    if file == "BagLabels":
        f, download_name = return_bag_labels(course, request)
    if file == "BathroomPasses":
        f, download_name = return_bathroom_passes(course, request)
    if file == "DirectionLabels":
        f, download_name = return_direction_labels(course, request)
    if file == "ProctorsAndRoomGrid":
        f, download_name = return_proctors_and_room_grid(course, request)
    if file == "CheckoutRoster":
        f, download_name = return_checkout_roster(course, request)        
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )
