from flask import jsonify, request

import app.scripts.utils as utils
from app.api_1_0 import api, files_df

@api.route("/classes")
def return_classes():
    year_and_semester = request.args.get('year_and_semester')
    if year_and_semester:
        cr_1_01_filename = utils.return_most_recent_report_by_semester(
            files_df, "1_01", year_and_semester
        )
    else:
        cr_1_01_filename = utils.return_most_recent_report(files_df,'1_01')

    cr_1_01_df = utils.return_file_as_df(cr_1_01_filename).fillna('')

    class_list_df = cr_1_01_df.drop_duplicates(subset=['Course','Section'])

    cols = ['Course','Section','Period','Teacher1','Teacher2']
    class_list_df = class_list_df[cols]
    class_list_df = class_list_df.sort_values(by=['Teacher1','Period','Course'])

    return jsonify(class_list_df.to_dict('records'))
