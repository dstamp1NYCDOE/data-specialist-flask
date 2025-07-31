from flask import current_app, session
from app.scripts import scripts, files_df, photos_df, gsheets_df
import app.scripts.utils.utils as utils

import geopandas as gpd
from shapely.geometry import Point

import os 
import pandas as pd

def main():
    path = os.path.join(current_app.root_path, f"data/geocoded_addresses.csv")
    cached_addresses_df = pd.read_csv(path)



    cached_addresses_df = cached_addresses_df
    cached_addresses_df[['BoroCD']] = cached_addresses_df.apply(check_within_nyc_district, axis=1, result_type='expand')
    cached_addresses_df['Borough'] = cached_addresses_df['BoroCD'].apply(convert_boro_cd_to_borough)
    cached_addresses_df['District'] = cached_addresses_df['BoroCD'].apply(convert_boro_cd_to_district)

    path = os.path.join(current_app.root_path, f"data/community_districts.csv")
    cached_addresses_df.to_csv(path, index=False)

    return cached_addresses_df


def convert_boro_cd_to_borough(boro_cd):
    """
    Convert a BoroCD value to its corresponding borough name.
    
    Args:
        boro_cd (str): The BoroCD value to convert
        
    Returns:
        str: The name of the borough
    """
    boro_cd = str(boro_cd)

    
    boroughs = {
        "1": "Manhattan",
        "2": "Bronx",
        "3": "Brooklyn",
        "4": "Queens",
        "5": "Staten Island"
    }
    
    return boroughs.get(boro_cd[0], None)

def convert_boro_cd_to_district(boro_cd):
    """
    Convert a BoroCD value to its corresponding borough name.
    
    Args:
        boro_cd (str): The BoroCD value to convert
        
    Returns:
        str: The name of the borough
    """
    boro_cd = str(boro_cd)
    return boro_cd[1:3]

def check_within_nyc_district(row):
    """
    Check if a point with given longitude and latitude is within any NYC Community District.
    
    Args:
        longitude (float): Longitude of the point to check
        latitude (float): Latitude of the point to check
        
    Returns:
        dict: Information about the district if found, None otherwise
    """
    # Create a Point object from the coordinates
    longitude = row['lon']
    latitude = row['lat']
    point = Point(longitude, latitude)
    
    # Path to save the NYC districts shapefile
    shapefile_path =  os.path.join(current_app.root_path, f"data/community_districts.geojson")
    
    # Load the shapefile
    nyc_districts = gpd.read_file(shapefile_path)
    
    
    # Create a GeoDataFrame with the point
    point_gdf = gpd.GeoDataFrame(geometry=[point], crs=nyc_districts.crs)
    
    # Check which district contains the point
    for idx, district in nyc_districts.iterrows():
        if district.geometry.contains(point):
            # Return information about the district
            return (
                district.get('BoroCD'),
            )
    return None