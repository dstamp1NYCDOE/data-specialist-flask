from dotenv import load_dotenv
import os

load_dotenv()

import datetime as dt
import requests

import pandas as pd


def lookup_student_commute(student_dict):
    if student_dict.get("Street") is None:
        return None
    StudentID = student_dict["StudentID"]

    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY")

    google_maps_url = "https://maps.googleapis.com/maps/api/directions/json?"
    school_address = "225+W24th+St+New+York+NY+10011"

    student_address_str = (
        student_dict["Street"]
        + " "
        + student_dict["City"]
        + ", "
        + student_dict["State"]
        + " "
        + str(int(student_dict["Zip"]))
    )
    today = dt.date.today()
    weekday = today.weekday()
    if weekday in [0, 1, 2, 3, 6]:
        next_day = today + dt.timedelta(days=1)
    elif weekday == 4:
        next_day = today + dt.timedelta(days=3)
    elif weekday == 5:
        next_day = today + dt.timedelta(days=2)
    t = dt.time(hour=8, minute=00)
    arrival_time = dt.datetime.combine(next_day, t)
    arrival_time = int(arrival_time.timestamp())

    request_url = (
        google_maps_url
        + f"origin={student_address_str}"
        + f"&destination={school_address}"
        + "&mode=transit&transit_mode=subway&transit_routing_preference=fewer_transfers&arrival_time="
        + str(arrival_time)
        + "&key="
        + google_maps_key
    )

    response = requests.get(request_url).json()
    lines = []
    for step in response["routes"][0]["legs"][0]["steps"]:
        if step["travel_mode"] == "TRANSIT":
            if step["transit_details"]["line"]["vehicle"]["type"] == "SUBWAY":
                transit_step = {
                    "short_name": step["transit_details"]["line"]["short_name"],
                    "color": step["transit_details"]["line"]["color"],
                    "icon": step["transit_details"]["line"]["vehicle"]["icon"],
                }
            else:
                transit_step = {
                    "short_name": step["transit_details"]["line"]["name"],
                    "color": step["transit_details"]["line"]["color"],
                    "icon": step["transit_details"]["line"]["vehicle"]["icon"],
                }
            lines.append(transit_step)

    try:
        departure_time = response["routes"][0]["legs"][0]["departure_time"]["text"]
    except:
        departure_time = "Within Walking Distance"

    commute_dict = {
        "StudentID": StudentID,
        "FirstName": student_dict["FirstName"],
        "LastName": student_dict["LastName"],
        "departure_time": departure_time,
        "address_str": student_address_str,
        "duration": response["routes"][0]["legs"][0]["duration"]["text"],
        "durationTime": round(
            response["routes"][0]["legs"][0]["duration"]["value"] / 60
        ),
        "starting_station": return_starting_station(response),
        "ending_station": return_ending_station(response),
        "steps": lines,
        "address_lon": response["routes"][0]["legs"][0]["start_location"]["lng"],
        "address_lat": response["routes"][0]["legs"][0]["start_location"]["lat"],
        "API_Response": response,
    }

    return commute_dict


def return_ending_station(API_Response):
    steps = API_Response["routes"][0]["legs"][0]["steps"]
    for step in reversed(steps):
        if step.get("travel_mode") == "TRANSIT":
            station_name = step["transit_details"]["departure_stop"]["name"]
            subway_line = step["transit_details"]["line"].get("short_name")
            return f"{station_name} ({subway_line})"


def return_starting_station(API_Response):
    steps = API_Response["routes"][0]["legs"][0]["steps"]
    for step in steps:
        if step.get("travel_mode") == "TRANSIT":
            station_name = step["transit_details"]["departure_stop"]["name"]
            subway_line = step["transit_details"]["line"].get("short_name")
            return f"{station_name} ({subway_line})"


def return_list_of_directions(API_Response):
    student_steps = []
    steps = API_Response["routes"][0]["legs"][0]["steps"]

    for step in steps:
        html_instructions = step["html_instructions"]
        duration = step["duration"]["text"]
        direction_str = f"{html_instructions} (<b>{duration}</b>)"
        if step.get("transit_details"):
            arrival_stop = step["transit_details"]["arrival_stop"]["name"]
            subway_line = step["transit_details"]["line"].get("short_name", "")
            num_of_stops = step["transit_details"]["num_stops"]
            direction_str = f"Take the <b>{subway_line}</b> {html_instructions} <b>{num_of_stops}</b> stops and get off at {arrival_stop} (<b>{duration}</b>)"

        student_steps.append(direction_str)

    return student_steps


def return_walk_to_first_step(API_Response):
    steps = API_Response["routes"][0]["legs"][0]["steps"]
    duration = steps[0]["duration"]["value"]
    return round(duration / 60)


if __name__ == "__main__":
    student_dict = {
        "StudentID": 123456789,
        "Street": "9 E 124th St",
        "City": "New York",
        "State": "New York",
        "Zip": "10035",
    }
    student_commute = lookup_student_commute(student_dict)
    print(student_commute)
