def return_assignment_difficulty(exam):
    Course = exam["Course Code"]
    Time = exam["Time"]
    Type = exam["Type"]

    difficulty = 1

    if "2x" in Type:
        if Time == "AM":
            difficulty = difficulty * 2
        elif Time == "PM":
            difficulty = difficulty * 1.25
    elif "1.5x" in Type:
        if Time == "AM":
            difficulty = difficulty * 1.5
        elif Time == "PM":
            difficulty = difficulty * 1.25
    elif "enl" in Type:
        if Time == "AM":
            difficulty = difficulty * 1.5
        elif Time == "PM":
            difficulty = difficulty * 1.25
    elif "SCRIBE" in Type:
        if Time == "AM":
            difficulty = difficulty * 1.5
        elif Time == "PM":
            difficulty = difficulty * 1.25

    if "QR" in Type or "SCRIBE" in Type:
        if Course[0] in ["E"]:
            difficulty = difficulty * 3
        if Course[0] in ["H"]:
            difficulty = difficulty * 2
        else:
            difficulty = difficulty * 1.5

    return difficulty


def return_number_of_proctors_needed(room):
    assignment_difficulty = room["assignment_difficulty"]
    Type = room["Type"]
    Time = room["Time"]
    Active = room["Active"]
    if "scribe" in Type.lower():
        return Active * 3

    if "QR" in Type:
        return 3
    if Time == "PM":
        return 2
    else:
        if "2x" in Type:
            return 3
        else:
            return 2
