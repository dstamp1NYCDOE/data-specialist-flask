import networkx as nx
from networkx.readwrite import json_graph
import itertools

import pandas as pd
import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for


def main():

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    cr_1_01_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(cr_1_01_filename)

    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)

    df = cr_1_01_df[(cr_1_01_df["Period"] >= 1) & (cr_1_01_df["Period"] <= 9)]
    df = df[df["Course"].str[0] != "Z"]
    ## Create Class Lists
    class_df = df[["Course", "Section"]].drop_duplicates()

    G = nx.Graph()
    lst_of_students = []
    for index, course_section in class_df.iterrows():
        course = course_section["Course"]
        section = course_section["Section"]
        students_df = df[(df["Course"] == course) & (df["Section"] == section)]
        students_temp = students_df["StudentID"].to_list()
        if len(students_temp) > 1:
            list_of_all_pairs = list(itertools.combinations(students_temp, 2))
            for student1, student2 in list_of_all_pairs:
                student1 = min(student1, student2)
                student2 = max(student1, student2)
                if student1 == student2:
                    pass
                elif G.has_edge(student1, student2):
                    G[student1][student2]["weight"] += 1
                else:
                    G.add_edge(student1, student2)
                    G[student1][student2]["weight"] = 1
                    lst_of_students.append(student1)

    lst_of_students = list(set(lst_of_students))
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)

    dc_calculations = []
    bc_calculations = []
    nodes = lst_of_students
    for node in nodes:
        dc_calculations += [degree_centrality[node]]
        bc_calculations += [betweenness_centrality[node]]

    # create a centrality data df to store values
    centrality_data = pd.DataFrame()

    # populate the df with the nodes and their centrality values
    centrality_data["StudentID"] = nodes
    centrality_data["Degree-Centrality"] = dc_calculations
    centrality_data["Betweenness-Centrality"] = bc_calculations

    output_df = centrality_data.merge(cr_3_07_df, on=["StudentID"], how="left")

    sheets = []
    sheets.append(("centrality", output_df))

    f = BytesIO()

    writer = pd.ExcelWriter(f)

    for sheet_name, sheet_df in sheets:
        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()
    f.seek(0)

    download_name = "network_analysis.xlsx"
    return f, download_name
