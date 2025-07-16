from flask import current_app, session
from app.scripts import scripts, files_df, photos_df, gsheets_df
import app.scripts.utils as utils

from geopy.geocoders import GoogleV3

import os 
import pandas as pd

def main():
    path = os.path.join(current_app.root_path, f"data/geocoded_addresses.csv")
    cached_addresses_df = pd.read_csv(path)
    cached_addresses_lst = cached_addresses_df['full_address'].unique().tolist()

    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename).fillna("")
    
    addresses_df = cr_3_07_df[
        [ "Street","City","State",
            "Zip",
        ]
    ]

    addresses_df['full_address'] = addresses_df["Street"].astype(str) + ", " + addresses_df["City"] + ", " + addresses_df["State"] + " " + addresses_df["Zip"].astype(str)
    
    addresses_df = addresses_df.drop_duplicates()

    new_addresses_df = addresses_df[~addresses_df['full_address'].isin(cached_addresses_lst)]
    if len(new_addresses_df) == 0:
        print("No new addresses to geocode.")
        return cached_addresses_df

    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    
    new_addresses_df[['lat','lon']] =  new_addresses_df.apply(geocode_with_google, args=(GOOGLE_MAPS_API_KEY,),axis=1,result_type='expand')
    

    all_addresses_df = pd.concat([cached_addresses_df, new_addresses_df], ignore_index=True)
    
    all_addresses_df.to_csv(path,index=False)
    
    return all_addresses_df


def geocode_with_google(row, api_key):
    """
    Convert an address to longitude and latitude using Google Maps API via GeoPy.
    
    Args:
        address (str): The address to geocode
        api_key (str): Your Google Maps API key
        
    Returns:
        tuple: (longitude, latitude) if successful, None otherwise
    """
    # Initialize the Google geocoder with your API key
    geolocator = GoogleV3(api_key=api_key)
    address = row['full_address']
    print(address)
    try:
        # Geocode the address
        location = geolocator.geocode(address)
    
        if location:
            # Return coordinates as (longitude, latitude)
            return (location.latitude, location.longitude)
        else:
            print(f"Could not geocode address: {address}")
            return (None, None)
            
    except Exception as e:
        print(f"Error geocoding address: {e}")
        return (None, None)