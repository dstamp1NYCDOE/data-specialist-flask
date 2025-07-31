import pandas as pd
import numpy as np
import os
import zipfile
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

from flask import current_app, session


def main(form, request):
    mapping_file = request.files[form.mapping_file.name]
    mapping_df = pd.read_excel(mapping_file)
    print(mapping_df)
    mapping_df["StudentID"] = mapping_df["Image file name"].apply(
        return_StudentID_from_filename
    )

    students_lst = mapping_df["StudentID"]

    df = photos_df[photos_df["StudentID"].isin(students_lst)]
    df = df.drop_duplicates(subset=["StudentID"])

    batch_size = form.batch_size.data
    batch_number = form.batch_number.data

    start = (batch_number - 1) * batch_size
    end = start + batch_size

    dff = df.iloc[start:end]
    files = dff["photo_filename"].to_list()
    f = return_zip_file(files)
    filename = f"ZippedPhotosBatch{batch_number}.zip"
    return f, filename


def return_zip_file(files):
    f = BytesIO()
    with zipfile.ZipFile(f, mode="w") as archive:
        for filename in files:
            archive.write(filename)
    f.seek(0)
    return f


def return_StudentID_from_filename(image_file_name):
    return int(image_file_name[0:9])
