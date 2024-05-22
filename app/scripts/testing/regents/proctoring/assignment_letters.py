import pandas as pd
import glob

from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import ListFlowable, ListItem
from reportlab.platypus import SimpleDocTemplate

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Normal_RIGHT',parent=styles['Normal'],alignment=TA_RIGHT,))
styles.add(ParagraphStyle(name='Body_Justify',parent=styles['BodyText'],alignment=TA_JUSTIFY,))

letter_head = [
    Paragraph('High School of Fashion Industries',styles['Normal']),
    Paragraph('225 W 24th St',styles['Normal']),
    Paragraph('New York, NY 10011',styles['Normal']),
    Paragraph('Principal, Daryl Blank',styles['Normal']),
    Spacer(width=0, height=0.25*inch),
]
closing = [
    Spacer(width=0, height=0.25*inch),
    Paragraph('Warmly,',styles['Normal_RIGHT']),
    Paragraph('Derek Stampone',styles['Normal_RIGHT']),
    Paragraph('Assistant Principal, Testing',styles['Normal_RIGHT']),
]

assignment_descriptions = ListFlowable(
    [
        Paragraph('Staff indicated as Proctor(AM or PM) or LATE should report to Room 202 to check-in and receive proctoring directions and materials.',
                    styles["Normal"]),
        Paragraph('Staff indicated as SUB PROCTOR should report to Room 202 to check-in in the AM and the PM. You may be used to substitute for the assignment of an absent colleague. If you are used to substitute for an afternoon exam and on AM schedule, you will be done prior to 3:20 PM. If you need to be on PM schedule, contact the testing office.',
                    styles["Normal"]),
        Paragraph('Staff indicated as Grading should report to their department supervisor. They will communicate to you your work day and location. Staff may be pulled from grading to serve as substitute proctors in the event of proctor absences.',
                    styles["Normal"]),
        Paragraph('Staff with alternate assignments should sign in the Clock room and follow their regular work schedule',
                    styles["Normal"]),
        Paragraph('Staff with organization assignments should sign in the Clock Room and report to their department supervisors',
                    styles["Normal"]),
    ],
    bulletType='1'
)

report_time_data = [
        [
            '',
            'Work Day Schedule',
            'Proctor Time',
            'Report to',
        ],
         [
            'AM\nProctor',
            '8:30 AM\nto\n3:20 PM',
            '8:45 AM\nto\n12:00 PM/1:30 PM/3:00 PM',
            'Room 202\nat\n8:40 AM',
            ],
        
        [
            'PM\nProctor',
            '10:00 AM\nto\n4:50 PM',
            '12:45 PM\nto\n4:45 PM',
            'Room 202\nat\n12:30 PM',
            ],
        [
        'Late\nProctor',
        '12:30 PM\nto\n7:20 PM',
        '4:45 PM\nto\n7:00 PM',
        'Room 202\nat\n4:15 PM'
        ]

    ]
colWidths = [100,100,100,100]
report_times_table = Table(report_time_data, colWidths=colWidths, repeatRows=1)
report_times_table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (100, 100), 'CENTER'),
    ('VALIGN', (0, 0), (100, 100), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (100, 100), 1),
    ('RIGHTPADDING', (0, 0), (100, 100), 1),
    ('BOTTOMPADDING', (0, 0), (100, 100), 1),
    ('TOPPADDING', (0, 0), (100, 100), 1),
    ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
]))


def main(data):
    administration = data["Administration"]
    proctor_schedule_filename = glob.glob(f"data/{administration}/*Grid-AlphaByDept.csv")[0]
    proctor_schedule_df = pd.read_csv(proctor_schedule_filename)
    proctor_schedule_df = proctor_schedule_df.sort_values(by=['Name'])

    print(proctor_schedule_df)


    output_pdf_filename = f"output/{administration}/{administration}_proctor_assignment_letters.pdf"
    my_doc = SimpleDocTemplate(output_pdf_filename,pagesize=letter,topMargin=0.50*inch,leftMargin=1.25*inch,rightMargin=1.25*inch,bottomMargin=0.25*inch)
    flowables = []

    for index, assignment_row in proctor_schedule_df.iterrows():
        assignment_df = pd.DataFrame(assignment_row)
        
        assignment_df = assignment_df.reset_index()
        assignment_df.columns = ['Date','Assignment']
        assignment_df = assignment_df.tail(4)

        flowables.extend(letter_head)

        name = assignment_row['Name']
        salutation = f"Dear{name.split(',')[1].title()} {name.split(',')[0].title()},"
        

        salutation = Paragraph(salutation, styles['Normal'])
        flowables.append(salutation)


        intro_paragraph = '''
        We will be administering Regents Exams to our students on Tuesday January 23rd through Friday January 26th.
        '''
        intro_paragraph = Paragraph(intro_paragraph, styles['Normal'])
        flowables.append(intro_paragraph)
        flowables.append(Spacer(width=0, height=0.25*inch))
        intro_paragraph = '''
        To ensure a smooth test administration, please carefully review the following proctoring schedule with your assignment and report time. Your department supervisor will communicate with you regarding the designated department activities days.
        '''
        intro_paragraph = Paragraph(intro_paragraph, styles['Normal'])
        flowables.append(intro_paragraph)
        flowables.append(Spacer(width=0, height=0.25*inch))

        colWidths = None
        

        assignment_T = return_schedule_df_as_table(assignment_df)

        flowables.append(assignment_T)
        
        flowables.append(Spacer(width=0, height=0.20*inch))


        flowables.append(report_times_table)
        flowables.append(Spacer(width=0, height=0.20*inch))

        flowables.append(assignment_descriptions)
        # flowables.append(Spacer(width=0, height=0.50*inch))

        flowables.append(Spacer(width=0, height=0.25*inch))

        closing_paragraph = '''
        If you have any questions or concerns, please connect with your immediate supervisor.
        '''
        closing_paragraph = Paragraph(closing_paragraph, styles['Normal'])
        flowables.append(closing_paragraph)
        flowables.append(Spacer(width=0, height=0.25*inch))



        flowables.extend(closing)
        flowables.append(PageBreak())


    
    my_doc.build(flowables)
    return True




def create_teacher_letter(assignment_row):
    flowables = []
    return flowables

def return_schedule_df_as_table(df, cols=None, colWidths= None, rowHeights=None):
    if cols is None:
        cols = df.columns
    table_data = df[cols].values.tolist()
    table_data.insert(0, cols)
    
    t = Table(table_data, colWidths=colWidths,
              repeatRows=1, rowHeights=rowHeights)
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (100, 100), 'CENTER'),
        ('VALIGN', (0, 0), (100, 100), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (100, 100), 1),
        ('RIGHTPADDING', (0, 0), (100, 100), 1),
        ('BOTTOMPADDING', (0, 0), (100, 100), 1),
        ('TOPPADDING', (0, 0), (100, 100), 1),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
    ]))
    return t



if __name__ == '__main__':
    data = {"Administration": "January2024"}
    main(data)